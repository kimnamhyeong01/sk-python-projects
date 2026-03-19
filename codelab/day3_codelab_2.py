"""
[심화실습] Bcrypt 해시 기반 Rate Limiting 인증 시스템
────────────────────────────────────────────────────────────────────────
목적:
  무차별 대입 공격(Brute Force Attack)을 2중으로 차단하는 인증 시스템 설계

  방어 레이어 1 — bcrypt 해시:
    로그인 1회 시도에 수백 ms의 CPU 연산을 강제 → 초당 시도 횟수를 수 건 이하로 제한

  방어 레이어 2 — IP Rate Limiting + 지수 백오프:
    연속 실패 시 잠금 시간을 지수적으로 증가시켜 공격자를 물리적으로 배제
    잠금 시간 = BASE × 2^(실패 횟수-1), 최대 MAX 초로 상한

핵심 포인트:
  - bcrypt Work Factor (rounds): 2^rounds 번 해시 반복, 클수록 안전하지만 CPU 비용 증가
  - run_in_executor: bcrypt는 CPU-bound → ThreadPoolExecutor로 이벤트루프 블로킹 방지
  - timing-safe 비교: bcrypt.checkpw는 항상 일정 시간 소요 → Timing Attack 방어
"""

import asyncio
import time
import bcrypt
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# ══════════════════════════════════════════════════════════════
# 1. bcrypt 비밀번호 해시
#
#    bcrypt 특성:
#      - 매 해시마다 랜덤 salt 자동 생성 → 동일 비밀번호도 결과가 매번 다름
#      - rounds=12: 해시 1회에 ~200ms 소요 (초당 최대 5회 시도로 브루트포스 둔화)
#      - rounds를 1 증가시킬 때마다 연산 시간 2배 증가
#      - NIST/OWASP 권장 최소값: rounds=10, 실무 권장: 12~14
# ══════════════════════════════════════════════════════════════

BCRYPT_ROUNDS = 12  # 프로덕션 권장값; 데모 속도가 느리면 10으로 낮춰도 됨


def hash_password(plain: str) -> bytes:
    """bcrypt로 비밀번호 해시. gensalt()가 매번 다른 salt를 생성."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))


def verify_password(plain: str, hashed: bytes) -> bool:
    """
    bcrypt 해시 검증.
    checkpw()는 내부적으로 timing-safe 비교를 수행하여
    Timing Attack(응답 시간으로 비밀번호 추측)을 원천 차단.
    """
    return bcrypt.checkpw(plain.encode(), hashed)


# ══════════════════════════════════════════════════════════════
# 2. IP별 실패 기록 및 지수 백오프 Rate Limiter
#
#    구조: {ip: IPRecord} 인메모리 딕셔너리 (실서비스는 Redis 사용)
#
#    지수 백오프 공식:
#      lockout = min(BASE_DELAY × 2^(failures-1), MAX_LOCKOUT)
#      1회 → 1s, 2회 → 2s, 3회 → 4s, 4회 → 8s, ... 10회 이상 → MAX
# ══════════════════════════════════════════════════════════════

BASE_DELAY  = 1.0    # 첫 실패 후 최소 잠금 시간 (초)
MAX_LOCKOUT = 300.0  # 최대 잠금 시간 = 5분 (무한 잠금 방지)


@dataclass
class IPRecord:
    failures: int = 0
    locked_until: float = 0.0  # 잠금 해제 시각 (Unix timestamp)


# 인메모리 상태 저장소: {ip_address: IPRecord}
_ip_store: Dict[str, IPRecord] = {}


def _record(ip: str) -> IPRecord:
    """IP 레코드 조회 또는 신규 생성 (없으면 기본값으로 초기화)."""
    return _ip_store.setdefault(ip, IPRecord())


def is_locked(ip: str) -> Tuple[bool, float]:
    """IP 잠금 여부와 남은 잠금 시간(초)을 반환."""
    remaining = _record(ip).locked_until - time.monotonic()
    return remaining > 0, max(0.0, remaining)


def record_failure(ip: str) -> float:
    """
    실패 횟수를 1 증가시키고 지수 백오프 잠금 시간을 계산하여 적용.
    반환값: 이번에 부과된 잠금 시간 (초)
    """
    rec = _record(ip)
    rec.failures += 1
    lockout = min(BASE_DELAY * (2 ** (rec.failures - 1)), MAX_LOCKOUT)
    rec.locked_until = time.monotonic() + lockout
    return lockout


def record_success(ip: str) -> None:
    """로그인 성공 시 해당 IP의 실패 기록을 초기화."""
    _ip_store.pop(ip, None)


# ══════════════════════════════════════════════════════════════
# 3. 인증 함수
#    IP Rate Limiting → 사용자 조회 → bcrypt 검증 순서로 처리
# ══════════════════════════════════════════════════════════════

@dataclass
class AuthResult:
    success: bool
    message: str
    lockout_sec: float = 0.0


# 가상 사용자 DB (실서비스에서는 RDB/NoSQL에서 hashed_password 조회)
print("사용자 DB 초기화 중 (bcrypt 해시 생성)...")
USER_DB: Dict[str, bytes] = {
    "alice": hash_password("correct_horse"),
    "bob":   hash_password("battery_staple"),
}


async def authenticate(ip: str, username: str, password: str) -> AuthResult:
    """
    인증 처리 파이프라인 (비동기).

    Step 1. IP Rate Limit 확인 — 잠금 상태면 즉시 거부 (bcrypt 연산도 하지 않음)
    Step 2. 사용자 존재 확인 — 없는 사용자도 '실패'로 처리 (Username Enumeration 방어)
    Step 3. bcrypt 검증 — run_in_executor로 비동기화:
              bcrypt는 CPU-bound 작업이므로 직접 await하면 이벤트 루프 전체가 차단됨
              ThreadPoolExecutor(None=기본값)에서 실행하여 다른 요청을 병행 처리 가능
    """
    # Step 1: IP 잠금 확인
    locked, remaining = is_locked(ip)
    if locked:
        return AuthResult(False, f"[차단] {remaining:.1f}초 후 재시도 가능", remaining)

    # Step 2: 사용자 조회 (없으면 즉시 실패 기록 — 타이밍 차이를 없애기 위해 dummy hash 비교도 가능)
    hashed = USER_DB.get(username)
    if hashed is None:
        lockout = record_failure(ip)
        return AuthResult(
            False,
            f"[실패] 인증 오류  실패={_record(ip).failures}회  잠금={lockout:.0f}s",
        )

    # Step 3: bcrypt 검증 (CPU-bound → 스레드 풀에서 실행하여 이벤트 루프 비차단)
    loop = asyncio.get_running_loop()
    is_valid = await loop.run_in_executor(None, verify_password, password, hashed)

    if is_valid:
        record_success(ip)
        return AuthResult(True, f"[성공] {username} 로그인 완료")
    else:
        lockout = record_failure(ip)
        return AuthResult(
            False,
            f"[실패] 인증 오류  실패={_record(ip).failures}회  잠금={lockout:.0f}s",
        )


# ══════════════════════════════════════════════════════════════
# 4. 데모
# ══════════════════════════════════════════════════════════════

async def main() -> None:
    NORMAL_IP = "192.168.1.100"
    ATTACK_IP = "10.0.0.1"

    # ── Part 1: 정상 로그인 흐름 ─────────────────────────────
    print(f"\n{'═' * 58}")
    print("  [Part 1] 정상 사용자 로그인")
    print(f"{'═' * 58}")

    r = await authenticate(NORMAL_IP, "alice", "wrong_pw")
    print(f"  시도 1 (오타): {r.message}")

    r = await authenticate(NORMAL_IP, "alice", "correct_horse")
    print(f"  시도 2 (정답): {r.message}")
    print(f"  → 성공 시 실패 카운터 초기화: {NORMAL_IP not in _ip_store}")

    # ── Part 2: 브루트포스 공격 시뮬레이션 ────────────────────
    print(f"\n{'═' * 58}")
    print("  [Part 2] 브루트포스 공격 시뮬레이션")
    print(f"{'═' * 58}")
    print("  공격자가 alice 계정에 짧은 시간 동안 반복 시도\n")

    for attempt in range(1, 11):
        r = await authenticate(ATTACK_IP, "alice", f"guess{attempt}")
        print(f"  시도 {attempt:>2} : {r.message}")

    # ── Part 3: 지수 백오프 테이블 출력 ──────────────────────
    print(f"\n{'═' * 58}")
    print("  [Part 3] 지수 백오프 잠금 시간 테이블")
    print(f"  BASE={BASE_DELAY}s  MAX={MAX_LOCKOUT}s")
    print(f"{'═' * 58}")
    print(f"  {'실패 횟수':>8}   {'잠금 시간':>12}   {'누적 차단 효과'}")
    print(f"  {'─' * 46}")
    for n in range(1, 11):
        lockout = min(BASE_DELAY * (2 ** (n - 1)), MAX_LOCKOUT)
        effect = "분" if lockout >= 60 else "초"
        val = lockout / 60 if lockout >= 60 else lockout
        print(f"  {n:>8}회   {lockout:>10.0f}s   {val:.0f}{effect} 대기 강제")

    print(f"\n  ※ 10회 이상 실패 → 모두 {MAX_LOCKOUT:.0f}s({MAX_LOCKOUT/60:.0f}분) 차단\n")


if __name__ == "__main__":
    asyncio.run(main())
