"""
[심화실습] 구조적 로깅 및 컨텍스트 추적 (Contextual Logging)
────────────────────────────────────────────────────────────────────────
목적 (prompt.md 기반):
  Kubernetes/MSA 등 수만 개 프로세스가 동시 실행되는 클라우드 네이티브 환경에서
  "대체 어디서 에러가 났는가?"를 추적할 수 있는 구조적 로깅 시스템 설계

핵심 점검:
  1. Race Condition : 여러 프로세스가 하나의 파일에 동시 write() → 로그 줄 손상·섞임
  2. JSON Logging   : ELK/Splunk 파싱 가능한 JSON 포맷 표준화
  3. ProcessID      : 어떤 OS 프로세스가 실행했는지 추적
  4. TaskID         : 작업 단위 고유 ID로 분산 환경 트레이싱
"""

import json
import logging
import os
import time
import uuid
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Pool, Queue, cpu_count
from typing import List, Tuple


# ══════════════════════════════════════════════════════════════
# 1. JSON 포맷터
#    LogRecord 기본 속성(process, levelname 등) +
#    extra={"task_id": ...} 로 주입한 TaskID를 JSON 한 줄로 직렬화
#    → ELK/Splunk에서 log.process_id, log.task_id 필드로 바로 쿼리 가능
# ══════════════════════════════════════════════════════════════

class JsonFormatter(logging.Formatter):
    """ELK/Splunk 호환 JSON 로그 포맷터."""

    def format(self, record: logging.LogRecord) -> str:
        obj = {
            "timestamp":  self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level":      record.levelname,
            "process_id": record.process,                   # OS PID (LogRecord 기본 제공)
            "task_id":    getattr(record, "task_id", "—"),  # extra={"task_id":...} 로 주입
            "logger":     record.name,
            "message":    record.getMessage(),
        }
        if record.exc_info:
            obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(obj, ensure_ascii=False)


# ══════════════════════════════════════════════════════════════
# 2. Race Condition 시연 (UNSAFE — 문제 상황)
#
#    각 워커가 동일한 파일 경로로 FileHandler를 직접 열어 로그를 씀
#    → 여러 프로세스가 각자의 fd로 같은 파일에 동시 write() 호출
#    → write()와 flush() 사이 컨텍스트 스위치 발생 시 줄이 물리적으로 섞임
#    → 특히 메시지 크기가 클수록(> OS atomic-write 한계) 손상 확률 증가
#    → TaskID/ProcessID가 없으면 어느 프로세스 로그인지 식별 자체가 불가
# ══════════════════════════════════════════════════════════════

_UNSAFE_LOG = "race_condition.log"


def _unsafe_worker(worker_id: int) -> None:
    """
    [UNSAFE] 각 워커 프로세스가 FileHandler를 직접 열어 파일에 씀.

    문제:
      - 프로세스마다 별도 fd로 open() → OS 레벨에서 write 순서 보장 없음
      - 긴 메시지(~3 KB)를 write + flush 하는 사이 다른 프로세스가 끼어들 수 있음
      - 결과: JSON 파싱 불가한 손상된 줄(broken lines) 발생
    """
    handler = logging.FileHandler(_UNSAFE_LOG, encoding="utf-8", mode="a")
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger = logging.getLogger(f"unsafe_{worker_id}")
    logger.handlers.clear()  # 프로세스 fork로 복사된 핸들러 초기화
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    for i in range(20):
        # 긴 페이로드: write-flush 사이 인터리빙 확률을 높이기 위해 ~3 KB 이상으로 설정
        payload = json.dumps({
            "seq": i,
            "worker": worker_id,
            "data": "UNSAFE_LOG_" * 200,  # ~3 KB → PIPE_BUF(4 KB) 근접, 손상 가능
        })
        logger.info(payload)
        time.sleep(0.0005)  # 미세 지연으로 다른 프로세스 write와 겹칠 기회 생성

    handler.close()


def demo_race_condition(n_workers: int) -> None:
    """Race Condition 데모 실행 및 결과 출력."""
    if os.path.exists(_UNSAFE_LOG):
        os.remove(_UNSAFE_LOG)

    with Pool(n_workers) as pool:
        pool.map(_unsafe_worker, range(n_workers))

    with open(_UNSAFE_LOG, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    broken = sum(1 for line in lines if not _is_valid_json(line))
    total = len(lines)
    rate = broken / total * 100 if total else 0

    print(f"  총 {total}줄  |  손상(JSON 파싱 불가) 줄: {broken}개 ({rate:.1f}%)")
    if broken == 0:
        # macOS 등 일부 OS는 short write가 atomic하게 처리되어 손상이 안 나올 수 있음
        # 그래도 ProcessID·TaskID 없이 로그가 섞여 추적 불가한 구조적 문제는 동일
        print("  ※ 이 환경에서는 물리적 손상이 없으나, 로그에 ProcessID·TaskID가 없어")
        print("    어느 프로세스·작업의 로그인지 추적이 불가합니다. (논리적 Race Condition)")
    print(f"  → '{_UNSAFE_LOG}' 파일을 열어 섞인 로그를 직접 확인하세요.")


# ══════════════════════════════════════════════════════════════
# 3. 안전한 구조적 로깅 (SAFE — 해결책)
#
#    QueueHandler + QueueListener 패턴:
#
#      [워커 프로세스]  →  QueueHandler.put()  →  multiprocessing.Queue
#                                                          │ (IPC)
#      [메인 프로세스]  ←  QueueListener.dequeue()  ←  FileHandler (단 1개)
#
#    핵심:
#      - 워커는 Queue에 레코드를 넣기만 함 (파일 접근 없음, 논블로킹)
#      - 파일 쓰기는 메인 프로세스 핸들러 1개만 담당 → write() 충돌 원천 차단
#      - ProcessID는 LogRecord.process 자동 기록
#      - TaskID는 extra={"task_id": uuid} 로 청크마다 고유하게 주입
# ══════════════════════════════════════════════════════════════

def setup_safe_logging(log_file: str) -> Tuple[Queue, QueueListener]:
    """
    멀티프로세스 안전 로깅 환경 구성.
    반환된 Queue를 각 워커 프로세스에 전달해야 한다.
    종료 시 반드시 listener.stop() 호출 → 잔여 레코드 flush + 핸들러 close 보장.
    """
    queue: Queue = Queue()

    # 파일 핸들러: 메인 프로세스에만 존재 → write() 경쟁 없음
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(JsonFormatter())

    # 콘솔 핸들러: 실시간 확인용 (운영 환경에서는 레벨 조정 또는 제거)
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter(
        "  [%(levelname)-8s] PID=%(process)d  %(message)s"
    ))

    listener = QueueListener(queue, fh, ch, respect_handler_level=True)
    listener.start()
    return queue, listener


# Pool initializer 패턴: log_queue를 각 워커 프로세스 전역에 1회 주입
_log_queue: Queue = None


def _worker_init(queue: Queue) -> None:
    """Pool 생성 시 워커 프로세스마다 1회 호출. 전역 큐 레퍼런스 설정."""
    global _log_queue
    _log_queue = queue


def _safe_worker(args: Tuple[int, List[str]]) -> Tuple[int, List[str]]:
    """
    [SAFE] 워커: QueueHandler를 통해 로그를 큐에 put()만 하고 파일은 건드리지 않음.

    TaskID 활용:
      - 청크마다 고유한 task_id 생성
      - ELK/Splunk에서 task_id 필드로 필터링하면 이 청크의 실행 흐름
        (시작 → 완료 또는 에러)을 한 번에 추적 가능
      - 예: Kibana 쿼리 → task_id: "a3f9b1c2"
    """
    chunk_idx, items = args
    task_id = str(uuid.uuid4())[:8]  # 청크 단위 고유 TaskID (8자리로 로그 가독성 유지)

    logger = logging.getLogger(f"worker.{chunk_idx}")
    if not logger.handlers:  # 동일 이름 로거 재사용 시 핸들러 중복 방지
        logger.addHandler(QueueHandler(_log_queue))
        logger.setLevel(logging.DEBUG)

    extra = {"task_id": task_id}

    logger.info(f"청크[{chunk_idx}] 시작  size={len(items)}", extra=extra)

    results = []
    for item in items:
        try:
            results.append(item.upper())
        except Exception as e:
            # 에러 발생 시 task_id로 어느 청크·작업인지 즉시 추적 가능
            logger.error(f"처리 실패: {item!r}  reason={e}", extra=extra, exc_info=True)

    logger.info(f"청크[{chunk_idx}] 완료  processed={len(results)}", extra=extra)
    return chunk_idx, results


# ══════════════════════════════════════════════════════════════
# 4. 유틸리티 및 메인
# ══════════════════════════════════════════════════════════════

_SAFE_LOG = "safe_structured.log"


def _is_valid_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def main() -> None:
    N_WORKERS = min(4, cpu_count())  # 데모용 4개 제한 (실서비스는 cpu_count() 그대로)
    data = [f"review_{i}" for i in range(200)]

    # ── Part 1: Race Condition 시연 ──────────────────────────
    print(f"\n{'═' * 60}")
    print("  [Part 1] Race Condition 시연  (UNSAFE)")
    print(f"{'═' * 60}")
    print(f"  {N_WORKERS}개 프로세스가 동시에 동일 파일에 직접 FileHandler로 씀\n")
    demo_race_condition(N_WORKERS)

    # ── Part 2: 안전한 구조적 로깅 ──────────────────────────
    print(f"\n{'═' * 60}")
    print("  [Part 2] QueueHandler + QueueListener  (SAFE)")
    print(f"{'═' * 60}")
    print("  워커는 Queue에 put()만 → 메인 프로세스 1개가 파일에 씀\n")

    queue, listener = setup_safe_logging(_SAFE_LOG)

    size = max(1, len(data) // N_WORKERS)
    chunks = [(i, data[i:i + size]) for i in range(0, len(data), size)]

    with Pool(N_WORKERS, initializer=_worker_init, initargs=(queue,)) as pool:
        pool.map(_safe_worker, chunks)

    listener.stop()  # 큐 잔여 레코드를 모두 flush한 뒤 핸들러 종료

    # ── 결과 검증 ─────────────────────────────────────────────
    with open(_SAFE_LOG, encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    broken = sum(1 for line in lines if not _is_valid_json(line))
    print(f"\n  총 {len(lines)}줄  |  손상(JSON 파싱 불가) 줄: {broken}개")
    print(f"  → '{_SAFE_LOG}' 파일에서 JSON 구조를 확인하세요.")

    # ── JSON 로그 샘플 출력 ───────────────────────────────────
    print("\n[ JSON 로그 샘플 — 첫 4줄 ]")
    for line in lines[:4]:
        print(f"  {line}")

    # ── 두 방식 요약 비교 ────────────────────────────────────
    print(f"\n{'─' * 60}")
    print("  비교 요약")
    print(f"{'─' * 60}")
    print("  UNSAFE  │ 여러 프로세스 직접 쓰기 → 줄 손상, ProcessID/TaskID 없음")
    print("  SAFE    │ Queue 경유 → 손상 0줄, ProcessID·TaskID 포함 JSON 구조화")
    print(f"{'─' * 60}\n")


if __name__ == "__main__":
    main()
