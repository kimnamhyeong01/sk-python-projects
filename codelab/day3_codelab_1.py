"""
[심화실습] 비동기 I/O 기반 API Aggregator (asyncio)
────────────────────────────────────────────────────────────────────────
목적:
  MSA 환경에서 여러 마이크로서비스의 응답을 하나로 모으는 API Aggregator 구현
  동기(Sequential) vs 비동기(Concurrent) 방식의 Latency 차이를 직접 측정

핵심 개념:
  - asyncio.gather  : 여러 코루틴을 동시에 실행, 모두 완료될 때까지 대기
                      총 소요 시간 ≈ max(각 서비스 응답 시간)  [순차: sum]
  - return_exceptions: 일부 서비스 실패 시 전체 중단 없이 예외를 결과에 포함
  - asyncio.Semaphore: 동시 요청 수 제한 (외부 API Rate Limit 준수)
  - asyncio.wait_for : 서비스별 타임아웃 → 느린 서비스가 전체를 블로킹하지 않게 차단
"""

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List


# ══════════════════════════════════════════════════════════════
# 1. 마이크로서비스 정의
#    실제 환경에서는 각 서비스가 별도의 HTTP 엔드포인트를 가짐
#    여기서는 asyncio.sleep으로 네트워크 I/O 지연을 현실적으로 시뮬레이션
# ══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Service:
    name: str
    latency: float       # 평균 응답 시간 (초)
    failure_rate: float  # 무작위 실패 확률 (0.0 ~ 1.0)


# 서비스별 응답 시간의 합 = 순차 처리 예상 시간
# 서비스별 응답 시간의 최대 = 동시 처리 예상 시간
SERVICES: List[Service] = [
    Service("user-service",    latency=0.30, failure_rate=0.0),
    Service("product-service", latency=0.50, failure_rate=0.1),  # 간헐적 실패
    Service("order-service",   latency=0.40, failure_rate=0.0),
    Service("review-service",  latency=0.20, failure_rate=0.0),
    Service("payment-service", latency=0.60, failure_rate=0.1),  # 간헐적 실패
]
# 순차 예상: 0.30+0.50+0.40+0.20+0.60 = 2.00s
# 동시 예상: max(0.60) ≈ 0.60s → 약 3.3× 단축


# ══════════════════════════════════════════════════════════════
# 2. 단일 서비스 호출
#    asyncio.wait_for로 타임아웃 적용 → 느린 서비스가 전체를 블로킹하지 않음
# ══════════════════════════════════════════════════════════════

async def fetch(svc: Service, timeout: float = 1.0) -> Dict[str, Any]:
    """
    마이크로서비스 1개 호출 시뮬레이션.

    asyncio.wait_for:
      지정 시간 안에 응답이 없으면 asyncio.TimeoutError 발생
      → Aggregator 전체가 느린 서비스 1개에 묶이는 현상(head-of-line blocking) 방지
    """
    async def _call() -> Dict[str, Any]:
        await asyncio.sleep(svc.latency)  # 네트워크 왕복 지연 시뮬레이션
        if random.random() < svc.failure_rate:
            raise ConnectionError(f"{svc.name}: 서비스 응답 오류")
        return {"service": svc.name, "latency_ms": int(svc.latency * 1000), "status": "ok"}

    return await asyncio.wait_for(_call(), timeout=timeout)


# ══════════════════════════════════════════════════════════════
# 3. 순차 방식 (Sequential)
#    await를 하나씩 순서대로 실행 → 앞 서비스 응답이 와야 다음 서비스 호출
#    총 소요 시간 = Σ(각 서비스 latency)
# ══════════════════════════════════════════════════════════════

async def aggregate_sequential(services: List[Service]) -> List[Dict[str, Any]]:
    """순차 방식 Aggregator. 각 서비스를 직렬로 하나씩 호출."""
    results = []
    for svc in services:
        try:
            results.append(await fetch(svc))
        except Exception as e:
            # 에러가 발생해도 나머지 서비스는 계속 호출
            results.append({"service": svc.name, "status": "error", "error": str(e)})
    return results


# ══════════════════════════════════════════════════════════════
# 4. 동시 방식 (Concurrent) — asyncio.gather
#    모든 코루틴을 이벤트 루프에 동시 등록 → I/O 대기 중 다른 작업 진행
#    총 소요 시간 ≈ max(각 서비스 latency)
# ══════════════════════════════════════════════════════════════

async def aggregate_concurrent(
    services: List[Service],
    max_concurrency: int = 10,
) -> List[Dict[str, Any]]:
    """
    동시 방식 Aggregator. asyncio.gather로 모든 서비스를 병렬 호출.

    Semaphore(max_concurrency):
      외부 API의 Rate Limit이나 서버 부하를 고려하여 동시 요청 수를 제한
      max_concurrency=10이면 최대 10개 요청이 동시에 진행됨
      → 서비스가 수백 개로 늘어나도 서버를 과부하하지 않는 안전한 패턴

    return_exceptions=True:
      일부 서비스에서 예외 발생 시 asyncio.gather가 즉시 취소되지 않고
      예외 객체를 결과 리스트에 담아 반환 → 부분 성공/실패 처리 가능
    """
    sem = asyncio.Semaphore(max_concurrency)

    async def _fetch_with_sem(svc: Service) -> Dict[str, Any]:
        # Semaphore로 동시 진입 수 제한 (컨텍스트 매니저가 acquire/release 자동 처리)
        async with sem:
            return await fetch(svc)

    tasks = [_fetch_with_sem(svc) for svc in services]
    raw = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for svc, result in zip(services, raw):
        if isinstance(result, Exception):
            results.append({"service": svc.name, "status": "error", "error": str(result)})
        else:
            results.append(result)
    return results


# ══════════════════════════════════════════════════════════════
# 5. 메인 벤치마크
# ══════════════════════════════════════════════════════════════

async def main() -> None:
    expected_seq = sum(s.latency for s in SERVICES)
    expected_conc = max(s.latency for s in SERVICES)

    print(f"\n{'═' * 60}")
    print("  API Aggregator 벤치마크")
    print(f"  서비스 수  : {len(SERVICES)}개")
    print(f"  순차 예상  : {expected_seq:.2f}s  (Σ latency)")
    print(f"  동시 예상  : {expected_conc:.2f}s  (max latency)")
    print(f"{'═' * 60}")

    # ── Sequential ──────────────────────────────────────────
    t0 = time.perf_counter()
    seq_results = await aggregate_sequential(SERVICES)
    t_seq = time.perf_counter() - t0

    # ── Concurrent ──────────────────────────────────────────
    t0 = time.perf_counter()
    conc_results = await aggregate_concurrent(SERVICES)
    t_conc = time.perf_counter() - t0

    speedup = t_seq / t_conc

    # ── 결과 출력 ────────────────────────────────────────────
    print(f"\n  {'방식':<12} {'실측 시간':>10}   {'예상 시간':>10}   결과")
    print(f"  {'─'*50}")
    print(f"  {'Sequential':<12} {t_seq:>9.3f}s   {expected_seq:>9.2f}s   {_summary(seq_results)}")
    print(f"  {'Concurrent':<12} {t_conc:>9.3f}s   {expected_conc:>9.2f}s   {_summary(conc_results)}")
    print(f"  {'─'*50}")
    print(f"  Latency 개선 : {speedup:.2f}×  ({(1 - t_conc / t_seq) * 100:.0f}% 단축)")

    # ── 서비스별 상세 ────────────────────────────────────────
    print(f"\n  {'서비스':<20} {'상태':>8}   {'latency(ms)':>12}")
    print(f"  {'─'*44}")
    for r in conc_results:
        status = r.get("status", "?")
        latency = f"{r['latency_ms']}ms" if "latency_ms" in r else r.get("error", "—")
        print(f"  {r['service']:<20} {status:>8}   {latency:>12}")
    print()


def _summary(results: List[Dict]) -> str:
    ok = sum(1 for r in results if r.get("status") == "ok")
    err = len(results) - ok
    return f"{ok}성공 / {err}실패" if err else f"{ok}개 모두 성공"


if __name__ == "__main__":
    asyncio.run(main())
