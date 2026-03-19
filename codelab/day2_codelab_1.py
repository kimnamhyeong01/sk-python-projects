"""
[심화실습] 병렬 데이터 마스킹 및 텍스트 정규화 (Multiprocessing + Normalization)
────────────────────────────────────────────────────────────────────────────────
목적 (prompt.md 기반):
  1. Privacy-Preserving RAG
     Vector DB 임베딩 전, 이메일·전화번호를 마스킹하여 외부 모델 전송 시 보안 사고 예방

  2. 검색 정확도 향상 (Normalization for Better Retrieval)
     금칙어·비속어가 섞인 채 임베딩되면 유사도 검색 품질이 저하됨
     정규화로 노이즈를 제거하여 임베딩 벡터 품질 향상

  3. 대규모 데이터 처리 효율성 (Scalability & Throughput)
     500만 건을 순차 처리하면 수일 소요 → 멀티프로세스 청킹으로 처리 시간 단축
     단, IPC 비용으로 데이터가 너무 작으면 오히려 느려지는 지점을 파악

핵심 포인트:
  - Regex 오버헤드 : re.compile()로 1회만 컴파일, 반복 호출 시 파싱 비용 없음
  - 데이터 청킹   : 전체 데이터를 cpu_count()개 청크로 분할 후 Pool.map으로 병렬 분산
  - IPC 비용      : 청크 크기가 너무 작으면 pickle 직렬화 + 프로세스 생성 오버헤드가
                    처리 이득을 초과 → 실제 Speedup이 1.0 미만으로 나타남
"""

import re
import time
import logging
from multiprocessing import Pool, cpu_count
from typing import List, Tuple

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 1. 정규표현식 패턴 — 모듈 로드 시 단 1회 컴파일
#    re.compile()을 호출 루프 바깥에서 한 번만 실행하면
#    매 리뷰마다 발생하는 패턴 파싱 비용(CPU 오버헤드)을 완전히 제거할 수 있다.
# ══════════════════════════════════════════════════════════════

# 이메일 주소: user.name+tag@sub.domain.com 형태까지 포함
_RE_EMAIL = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

# 한국 휴대전화: 국제형(+82) 및 지역형(010/011/016/017/018/019) 모두 포함
# 구분자로 -, ., 공백 허용
_RE_PHONE = re.compile(r'(\+?82[-.\s]?|0)1[0-9][-.\s]?\d{3,4}[-.\s]?\d{4}')

# 금칙어 → 표준 표현 매핑 (순서 보장을 위해 list of tuple 사용)
_BANNED: List[Tuple[re.Pattern, str]] = [
    (re.compile(r'바보|멍청이'),   '표현주의'),
    (re.compile(r'쓰레기|형편없'), '개선필요'),
    (re.compile(r'최악|최하'),     '불만족'),
]


# ══════════════════════════════════════════════════════════════
# 2. 단건 처리 함수
# ══════════════════════════════════════════════════════════════

def _mask_pii(text: str) -> str:
    """이메일·전화번호를 '****'로 마스킹. (Privacy-Preserving)"""
    text = _RE_EMAIL.sub('****', text)
    text = _RE_PHONE.sub('****', text)
    return text


def _normalize(text: str) -> str:
    """금칙어를 표준 표현으로 치환. (Normalization for Better Retrieval)"""
    for pattern, replacement in _BANNED:
        text = pattern.sub(replacement, text)
    return text


def process_review(review: str) -> str:
    """단일 리뷰 전처리 파이프라인: PII 마스킹 → 금칙어 정규화."""
    return _normalize(_mask_pii(review))


# ══════════════════════════════════════════════════════════════
# 3. 멀티프로세스 워커
#    Pool.map은 인수를 pickle로 직렬화하여 워커 프로세스에 전달한다.
#    청크 단위로 묶어서 전달해야 IPC 횟수를 최소화할 수 있다.
# ══════════════════════════════════════════════════════════════

def _process_chunk(chunk: List[str]) -> List[str]:
    """청크(부분 리스트) 전체를 처리하여 반환. 워커 프로세스에서 실행."""
    return [process_review(review) for review in chunk]


# ══════════════════════════════════════════════════════════════
# 4. 실행 전략 비교
# ══════════════════════════════════════════════════════════════

def run_single(reviews: List[str]) -> Tuple[List[str], float]:
    """단일 프로세스 순차 처리 — 기준(Baseline) 측정."""
    t0 = time.perf_counter()
    results = [process_review(r) for r in reviews]
    return results, time.perf_counter() - t0


def run_multiprocess(reviews: List[str], n_workers: int) -> Tuple[List[str], float]:
    """
    멀티프로세스 병렬 처리.

    청킹 전략:
      전체 데이터를 n_workers개 균등 청크로 분할 → Pool.map으로 각 워커에 분산
      청크 크기 = len(reviews) // n_workers  (나머지는 마지막 청크에 포함)

    IPC 비용 주의:
      데이터가 적으면 pickle 직렬화 + 프로세스 생성/통신 비용이 처리 이득을 초과하여
      Speedup < 1.0 이 될 수 있다. 실서비스(500만 건 이상)에서 이득이 발생한다.
    """
    size = max(1, len(reviews) // n_workers)
    # 리스트 슬라이싱으로 청크 생성 (제너레이터 대신 list를 써야 Pool.map이 길이를 알 수 있음)
    chunks = [reviews[i:i + size] for i in range(0, len(reviews), size)]

    t0 = time.perf_counter()
    with Pool(n_workers) as pool:
        # pool.map은 청크 순서를 보장하며 결과를 반환
        chunk_results = pool.map(_process_chunk, chunks)
    elapsed = time.perf_counter() - t0

    # 2차원 리스트를 1차원으로 flatten
    results = [r for chunk in chunk_results for r in chunk]
    return results, elapsed


# ══════════════════════════════════════════════════════════════
# 5. 샘플 데이터 생성 및 메인 벤치마크
# ══════════════════════════════════════════════════════════════

def _make_samples(n: int) -> List[str]:
    """
    벤치마크용 샘플 리뷰 생성.
    이메일·전화번호·금칙어를 균형 있게 포함하여 Regex 부하를 현실적으로 재현.
    """
    templates = [
        "이 제품 정말 바보 같아요. 환불 문의: refund@example.com",
        "배송이 쓰레기야. 연락처 010-1234-5678로 연락주세요.",
        "최악의 서비스입니다. 다시는 안 삽니다.",
        "품질이 형편없어요. 이메일 user@shop.co.kr 남깁니다.",
        "정말 좋아요! 강력 추천합니다.",
        "멍청이 같은 디자인이네요. +82-10-9876-5432 문의 바랍니다.",
    ]
    return [templates[i % len(templates)] for i in range(n)]


def _print_result(label: str, elapsed: float, throughput: float) -> None:
    print(f"  {label:<20} {elapsed:>7.3f}s   {throughput:>12,.0f} 건/s")


def main() -> None:
    # 실서비스 목표: 5_000_000건. 여기서는 테스트용으로 축소.
    # N_RECORDS = 5_000_000  # 실서비스 시 활성화
    N_RECORDS = 500_000
    N_WORKERS = cpu_count()

    logger.info(f"데이터 생성 중... ({N_RECORDS:,}건)")
    reviews = _make_samples(N_RECORDS)

    logger.info("단일 프로세스 처리 시작")
    _, t_single = run_single(reviews)
    tp_single = N_RECORDS / t_single

    logger.info(f"멀티프로세스 처리 시작 (workers={N_WORKERS})")
    _, t_multi = run_multiprocess(reviews, N_WORKERS)
    tp_multi = N_RECORDS / t_multi

    speedup = t_single / t_multi

    # ── 결과 출력 ─────────────────────────────────────────────
    print(f"\n{'─' * 58}")
    print(f"  레코드 수 : {N_RECORDS:,}건  |  CPU 코어 : {N_WORKERS}개")
    print(f"{'─' * 58}")
    print(f"  {'전략':<20} {'처리 시간':>8}   {'Throughput':>14}")
    print(f"{'─' * 58}")
    _print_result("단일 프로세스", t_single, tp_single)
    _print_result(f"멀티({N_WORKERS}코어)", t_multi, tp_multi)
    print(f"{'─' * 58}")
    print(f"  실제 Speedup : {speedup:.2f}x  (이론 최대 {N_WORKERS}x)")
    if speedup < 1.0:
        print("  ※ IPC 비용 > 처리 이득 → 데이터를 더 크게 늘리면 역전됩니다.")
    print(f"{'─' * 58}\n")

    # ── 마스킹 결과 샘플 확인 ─────────────────────────────────
    print("[ 처리 결과 샘플 ]")
    for original, processed in zip(reviews[:3], [process_review(r) for r in reviews[:3]]):
        print(f"  원문  : {original}")
        print(f"  결과  : {processed}\n")


if __name__ == "__main__":
    main()
