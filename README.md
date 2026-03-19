# Python Applications Portfolio

Python의 핵심 개념을 실습하고 심화 적용한 프로젝트 모음입니다.
`codelab/` 은 심화 실습 과제, `practice/` 는 개념 학습 실습으로 구성되어 있습니다.

---

## 목차

- [Codelab (심화 실습)](#codelab-심화-실습)
  - [AST 기반 보안 취약점 스캐너](#1-ast-기반-보안-취약점-스캐너)
  - [대용량 데이터 파이프라인 메모리 프로파일링](#2-대용량-데이터-파이프라인-메모리-프로파일링)
  - [병렬 데이터 마스킹 및 텍스트 정규화](#3-병렬-데이터-마스킹-및-텍스트-정규화)
  - [구조적 로깅 및 컨텍스트 추적 시스템](#4-구조적-로깅-및-컨텍스트-추적-시스템)
  - [비동기 I/O 기반 API Aggregator](#5-비동기-io-기반-api-aggregator)
  - [Bcrypt 기반 Rate Limiting 인증 시스템](#6-bcrypt-기반-rate-limiting-인증-시스템)
- [Practice (개념 학습 실습)](#practice-개념-학습-실습)
  - [데이터 시각화 및 EDA 분석](#7-데이터-시각화-및-eda-분석)
  - [OOP 기반 AI 추천 주문 시스템](#8-oop-기반-ai-추천-주문-시스템)
  - [멀티프로세싱 소수 판별기](#9-멀티프로세싱-소수-판별기)
  - [제너레이터 기반 메모리 절약형 로직](#10-제너레이터-기반-메모리-절약형-로직)
  - [실행 시간 측정 데코레이터](#11-실행-시간-측정-데코레이터)
  - [타입 힌트 성능 벤치마크](#12-타입-힌트-성능-벤치마크)
  - [환경 변수 및 구조적 로깅 실습](#13-환경-변수-및-구조적-로깅-실습)
  - [함수형 데이터 필터링](#14-함수형-데이터-필터링)

---

## Codelab (심화 실습)

### 1. AST 기반 보안 취약점 스캐너

**경로:** `codelab/ast_security_scanner/`

Python 파일을 정적 분석하여 `eval`, `exec` 등 위험 함수 호출을 탐지하는 CLI 도구입니다.

**핵심 기술**
- `ast.NodeVisitor`를 상속해 AST를 순회하며 `Call` 노드 탐지
- 단순 문자열 검색이 아닌 구문 트리 기반 분석으로 오탐률 최소화
- 파일 단위 / 디렉터리 재귀 탐색 지원

**구조**
```
main.py      # 진입점, 경로 수집 및 오케스트레이션
scanner.py   # AST 분석 핵심 로직 (SecurityVisitor)
rules.py     # 위험 함수 목록 정의
models.py    # SecurityIssue 데이터 모델
reporter.py  # 리포트 출력
file_utils.py # .py 파일 탐색 유틸리티
```

**실행 예시**
```bash
python main.py sample.py
python main.py ./project
```

---

### 2. 대용량 데이터 파이프라인 메모리 프로파일링

**경로:** `codelab/data_pipeline_memory_profiling/memory_profiling_pipeline.py`

1,000만 개 정수 데이터를 처리할 때 List Comprehension과 Generator Expression의 메모리 사용량을 비교합니다.

**핵심 기술**
- `tracemalloc`으로 피크 메모리 사용량 측정
- Lazy Evaluation(지연 평가) 원리 실증
- 처리 시간과 메모리 트레이드오프 분석

**주요 결과**
| 방식 | 메모리 사용 | 특징 |
|------|-----------|------|
| List Comprehension | 수백 MB | 전체 데이터를 즉시 메모리에 적재 |
| Generator Expression | 수 KB | 값을 하나씩 필요할 때 생성 |

---

### 3. 병렬 데이터 마스킹 및 텍스트 정규화

**경로:** `codelab/day2_codelab_1.py`

Privacy-Preserving RAG 파이프라인을 위한 대규모 텍스트 전처리 시스템입니다.

**핵심 기술**
- `multiprocessing.Pool.map`으로 데이터를 CPU 코어 수만큼 청크 분할 병렬 처리
- `re.compile()`로 정규식 1회 컴파일, 반복 호출 오버헤드 제거
- 이메일·전화번호 마스킹으로 외부 모델 전송 시 개인정보 보호
- IPC 비용 분석: 청크가 너무 작으면 pickle 직렬화 오버헤드가 처리 이득 초과

**활용 시나리오**
- 500만 건 이상의 문서를 벡터 DB에 임베딩하기 전 전처리 단계
- 비속어·노이즈 제거로 임베딩 벡터 품질 향상

---

### 4. 구조적 로깅 및 컨텍스트 추적 시스템

**경로:** `codelab/day2_codelab_2.py`

Kubernetes/MSA 환경에서 분산 프로세스의 에러를 추적할 수 있는 구조적 로깅 시스템입니다.

**핵심 기술**
- JSON 포맷 로그로 ELK / Splunk 파싱 지원
- `QueueHandler` + `QueueListener`로 Race Condition 없는 멀티프로세스 로깅
- 각 작업에 UUID 기반 `task_id` 부여 → 분산 환경 트레이싱
- `process_id` 필드로 OS 프로세스 단위 추적

**해결한 문제**
- 여러 프로세스가 하나의 파일에 동시에 `write()`할 때 발생하는 로그 줄 손상 방지

---

### 5. 비동기 I/O 기반 API Aggregator

**경로:** `codelab/day3_codelab_1.py`

MSA 환경에서 여러 마이크로서비스 응답을 하나로 집계하는 API Aggregator입니다.

**핵심 기술**
- `asyncio.gather`: 여러 서비스를 동시 호출 → 총 지연 ≈ max(개별 지연) vs 순차: sum(지연)
- `asyncio.Semaphore`: 동시 요청 수 제한으로 외부 API Rate Limit 준수
- `asyncio.wait_for`: 서비스별 타임아웃 설정, 느린 서비스가 전체를 블로킹하지 않도록 차단
- `return_exceptions=True`: 일부 서비스 실패 시에도 나머지 결과 정상 반환

**성능 비교**
| 방식 | 3개 서비스 (각 1초 지연) |
|------|----------------------|
| 순차(Sequential) | ~3초 |
| 비동기(asyncio.gather) | ~1초 |

---

### 6. Bcrypt 기반 Rate Limiting 인증 시스템

**경로:** `codelab/day3_codelab_2.py`

무차별 대입 공격(Brute Force Attack)을 2중으로 방어하는 비동기 인증 시스템입니다.

**핵심 기술**
- **방어 레이어 1 — bcrypt 해시**: Work Factor로 로그인 1회에 수백 ms CPU 연산 강제
- **방어 레이어 2 — IP Rate Limiting + 지수 백오프**: 연속 실패 시 잠금 시간을 지수적으로 증가
- `run_in_executor`: CPU-bound인 bcrypt를 `ThreadPoolExecutor`에서 실행해 이벤트루프 블로킹 방지
- Timing-safe 비교(`bcrypt.checkpw`)로 Timing Attack 방어

---

## Practice (개념 학습 실습)

### 7. 데이터 시각화 및 EDA 분석

**경로:** `practice/data_visualization/`

고객 리뷰 1,000건 데이터셋을 대상으로 LLM 임베딩 추천 시스템 적용 전 탐색적 데이터 분석(EDA)을 수행합니다.

**핵심 기술**
- `pandas`: 결측치 처리, 이상치 탐지, 통계 요약
- `seaborn` + `matplotlib`: 분포 시각화, 상관관계 히트맵, 카테고리별 비교 시각화
- 감성 점수(`sentiment_score`)와 평점(`rating`) 간 상관관계 분석

**분석 단계**
1. 데이터 전처리 및 품질 검증
2. 분포 및 이상치 시각화
3. 변수 간 통계적 관계 분석
4. 인사이트 리포트 생성 (`Pandas+Seaborn 분석 리포트_김남형.pdf`)

---

### 8. OOP 기반 AI 추천 주문 시스템

**경로:** `practice/oop.py`

객체지향 설계 원칙을 적용한 음료 주문 플랫폼 시뮬레이터입니다.

**핵심 기술**
- 상속(Inheritance): `Beverage` 부모 클래스 → 세부 음료 타입 확장
- `@property` 데코레이터로 캡슐화된 속성 관리
- 태그 기반 유사 음료 추천 알고리즘
- 주문 내역 기반 총액 / 평균 금액 계산

---

### 9. 멀티프로세싱 소수 판별기

**경로:** `practice/multiprocessing_practice.py`

단일 프로세스와 멀티프로세스 방식의 소수 판별 성능을 비교합니다.

**핵심 기술**
- `multiprocessing.Pool`로 작업 분산
- `math.sqrt(n)` 최적화로 불필요한 연산 제거
- GIL 제약 없이 CPU-bound 작업을 병렬화

---

### 10. 제너레이터 기반 메모리 절약형 로직

**경로:** `practice/generator.py`, `practice/generator_2.py`

리스트와 제너레이터의 메모리 사용량 차이를 `sys.getsizeof()`로 직접 측정합니다.

**핵심 기술**
- `yield` 키워드를 활용한 제너레이터 함수 구현
- Lazy Evaluation 원리 이해
- 100만 개 정수 처리 시 메모리 사용량 비교

---

### 11. 실행 시간 측정 데코레이터

**경로:** `practice/decorator.py`

어떤 함수에도 적용 가능한 범용 실행 시간 측정 데코레이터를 구현합니다.

**핵심 기술**
- `functools.wraps`로 원본 함수 메타데이터(`__name__`, `__doc__`) 보존
- `*args`, `**kwargs`로 임의의 함수 시그니처 처리
- 클로저(Closure) 기반 래퍼 함수 패턴

---

### 12. 타입 힌트 성능 벤치마크

**경로:** `practice/typing_mypy_perf/`

타입 힌트 유무에 따른 함수 실행 속도 차이를 `timeit`으로 측정합니다.

**핵심 기술**
- `timeit`을 활용한 정밀 성능 측정
- `mypy`를 통한 정적 타입 검사
- 타입 힌트가 런타임 최적화가 아닌 정적 분석 도구임을 실증

---

### 13. 환경 변수 및 구조적 로깅 실습

**경로:** `practice/env_logging_example/`

`.env` 파일에서 환경 변수를 로드하고 콘솔과 파일에 동시에 로그를 출력하는 실습입니다.

**핵심 기술**
- `python-dotenv`로 `LOG_LEVEL`, `APP_NAME` 환경 변수 로드
- `logging.FileHandler` + `logging.StreamHandler` 동시 사용
- `%(asctime)s | %(levelname)s | %(message)s` 포맷 구조화

---

### 14. 함수형 데이터 필터링

**경로:** `practice/data_filtering.py`

직원 데이터를 함수형 프로그래밍 기법으로 필터링하고 정렬합니다.

**핵심 기술**
- `filter()` + `lambda`로 조건부 데이터 추출
- `sorted(key=lambda ...)`로 급여 기준 내림차순 정렬
- List Comprehension을 활용한 간결한 데이터 변환

---

## 기술 스택

| 분류 | 기술 |
|------|------|
| 언어 | Python 3.8+ |
| 동시성 | `asyncio`, `multiprocessing` |
| 보안 | `ast`, `bcrypt` |
| 데이터 분석 | `pandas`, `numpy` |
| 시각화 | `matplotlib`, `seaborn` |
| 로깅 | `logging`, `python-dotenv` |
| 타입 검사 | `mypy`, `typing` |
| 성능 측정 | `tracemalloc`, `timeit` |
