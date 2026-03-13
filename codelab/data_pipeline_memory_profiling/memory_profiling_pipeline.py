"""
대용량 데이터 파이프라인의 메모리 프로파일링
- 1,000만 개의 정수 데이터를 처리할 때
  1) List Comprehension
  2) Generator Expression
  의 메모리 점유율을 tracemalloc으로 측정한다.
- 결과를 통해 파이썬의 Lazy Evaluation(지연 평가) 원리를 설명한다.

실행 환경:
- Python 3.8+
- 별도 외부 라이브러리 불필요 (표준 라이브러리만 사용)

주의:
- 1,000만 개의 정수 리스트는 메모리를 꽤 사용하므로,
  메모리가 부족한 환경에서는 실행 시간이 오래 걸리거나 메모리 압박이 있을 수 있다.
"""

import ast
import time
import tracemalloc
from typing import Any, Dict


# -------------------------------------------------------------------
# 설정값
# -------------------------------------------------------------------
DATA_SIZE = 10_000_000


# -------------------------------------------------------------------
# 데이터 처리 함수
# -------------------------------------------------------------------
def process_with_list_comprehension(n: int) -> int:
    """
    List Comprehension 방식으로 0 ~ n-1 범위의 정수를 생성하고,
    각 값을 제곱한 리스트를 메모리에 한 번에 만든 뒤,
    전체 합계를 반환한다.

    동작 방식:
    - [x * x for x in range(n)] 에 의해 결과 전체가 즉시 리스트로 생성된다.
    - 즉, 계산 결과 전체가 메모리에 적재된다.
    - 이후 sum()이 리스트를 순회하면서 합계를 계산한다.

    장점:
    - 이미 리스트가 만들어져 있으므로 재사용이 가능하다.
    - 일부 상황에서는 순회 속도가 빠를 수 있다.

    단점:
    - 대용량 데이터에서는 메모리 사용량이 매우 커진다.
    """
    squared_numbers = [x * x for x in range(n)]
    return sum(squared_numbers)


def process_with_generator_expression(n: int) -> int:
    """
    Generator Expression 방식으로 0 ~ n-1 범위의 정수를 처리하고,
    각 값을 제곱한 값을 '필요할 때마다 하나씩' 생성하여 합계를 반환한다.

    동작 방식:
    - (x * x for x in range(n)) 는 제너레이터 객체만 먼저 만든다.
    - 실제 값은 sum()이 하나씩 꺼내 쓸 때 계산된다.
    - 결과 전체를 리스트처럼 한 번에 메모리에 보관하지 않는다.

    장점:
    - 메모리 사용량이 매우 적다.
    - 대용량 데이터 파이프라인에 적합하다.

    단점:
    - 한 번 소비하면 재사용이 어렵다.
    - 랜덤 접근(인덱싱)이 불가능하다.
    """
    squared_numbers = (x * x for x in range(n))
    return sum(squared_numbers)


# -------------------------------------------------------------------
# 프로파일링 유틸리티
# -------------------------------------------------------------------
def profile_memory_and_time(func, n: int) -> Dict[str, Any]:
    """
    전달받은 함수(func)를 실행하면서
    - 현재 메모리 사용량(current memory)
    - 최대 메모리 사용량(peak memory)
    - 실행 시간
    - 결과값
    을 측정하여 반환한다.

    tracemalloc 설명:
    - 파이썬이 할당한 메모리를 추적한다.
    - get_traced_memory()는 (current, peak) 형태의 튜플을 반환한다.
      * current: 현재 추적 중인 메모리 사용량
      * peak: 추적 시작 이후 최대 메모리 사용량
    """
    # 이전 측정 흔적이 남지 않도록 tracemalloc 시작
    tracemalloc.start()

    start_time = time.perf_counter()
    result = func(n)
    end_time = time.perf_counter()

    current, peak = tracemalloc.get_traced_memory()

    # 이번 측정을 종료하여 다음 측정과 분리
    tracemalloc.stop()

    return {
        "result": result,
        "execution_time_sec": end_time - start_time,
        "current_memory_bytes": current,
        "peak_memory_bytes": peak,
    }


def bytes_to_mb(num_bytes: int) -> float:
    """
    바이트 단위를 MB 단위로 변환한다.
    출력 가독성을 높이기 위한 보조 함수.
    """
    return num_bytes / (1024 * 1024)


# -------------------------------------------------------------------
# AST 활용: 식(Expression) 구조 확인
# 과제 설명에 import ast가 제시되어 있으므로,
# List Comprehension과 Generator Expression의 문법 구조 차이를 간단히 확인하는 예시를 포함한다.
# 필수는 아니지만, 보고서/발표 시 설명 보강에 유용하다.
# -------------------------------------------------------------------
def inspect_expression_types() -> None:
    """
    List Comprehension과 Generator Expression이
    AST 상에서 각각 어떤 노드 타입으로 파싱되는지 출력한다.

    출력 예시:
    - List Comprehension -> ListComp
    - Generator Expression -> GeneratorExp

    이 함수는 성능 측정과 직접 관련되지는 않지만,
    두 문법이 언어 차원에서 다른 표현식이라는 점을 보여준다.
    """
    list_code = "[x * x for x in range(10)]"
    gen_code = "(x * x for x in range(10))"

    list_tree = ast.parse(list_code, mode="eval")
    gen_tree = ast.parse(gen_code, mode="eval")

    print("\n[AST 확인]")
    print(f"List Comprehension AST 타입      : {type(list_tree.body).__name__}")
    print(f"Generator Expression AST 타입   : {type(gen_tree.body).__name__}")


# -------------------------------------------------------------------
# 결과 출력 및 해석
# -------------------------------------------------------------------
def print_profile_result(title: str, profile: Dict[str, Any]) -> None:
    """
    프로파일링 결과를 보기 좋은 형식으로 출력한다.
    """
    print(f"\n[{title}]")
    print(f"- 계산 결과(합계)         : {profile['result']}")
    print(f"- 실행 시간               : {profile['execution_time_sec']:.4f}초")
    print(f"- 현재 메모리 사용량      : {bytes_to_mb(profile['current_memory_bytes']):.2f} MB")
    print(f"- 최대 메모리 사용량(peak): {bytes_to_mb(profile['peak_memory_bytes']):.2f} MB")


def explain_lazy_evaluation() -> None:
    """
    실험 결과를 바탕으로 보고서/발표에 그대로 활용할 수 있는 형태의 설명을 출력한다.
    """
    print("\n[결론 및 해석]")
    print(
        "1) List Comprehension은 계산 결과 전체를 즉시 리스트로 생성하므로,\n"
        "   대용량 데이터 처리 시 메모리 사용량이 크게 증가한다."
    )
    print(
        "2) Generator Expression은 값을 한 번에 모두 만들지 않고,\n"
        "   필요한 시점에 하나씩 생성한다."
    )
    print(
        "3) 이 방식이 바로 Lazy Evaluation(지연 평가)이며,\n"
        "   대용량 데이터 파이프라인에서 메모리 효율성을 크게 높인다."
    )
    print(
        "4) 따라서 전체 결과를 반드시 메모리에 저장할 필요가 없는 작업(예: 합계, 필터링, 순차 처리)에서는\n"
        "   Generator Expression이 더 적합하다."
    )
    print(
        "5) 반면, 결과를 여러 번 재사용하거나 인덱싱해야 한다면 리스트가 더 적합할 수 있다."
    )


# -------------------------------------------------------------------
# 메인 실행 함수
# -------------------------------------------------------------------
def main() -> None:
    """
    전체 실험을 실행하는 메인 함수.
    """
    print("대용량 데이터 파이프라인 메모리 프로파일링 시작")
    print(f"비교 대상 데이터 크기: {DATA_SIZE:,}개 정수")

    # 문법 구조 차이 확인 (선택적 보조 설명)
    inspect_expression_types()

    # 1) List Comprehension 프로파일링
    list_profile = profile_memory_and_time(process_with_list_comprehension, DATA_SIZE)
    print_profile_result("List Comprehension", list_profile)

    # 2) Generator Expression 프로파일링
    generator_profile = profile_memory_and_time(process_with_generator_expression, DATA_SIZE)
    print_profile_result("Generator Expression", generator_profile)

    # 추가 비교 출력
    peak_diff_mb = bytes_to_mb(
        list_profile["peak_memory_bytes"] - generator_profile["peak_memory_bytes"]
    )

    print("\n[비교 요약]")
    print(
        f"- List Comprehension이 Generator Expression보다 "
        f"최대 약 {peak_diff_mb:.2f} MB 더 많은 메모리를 사용할 수 있다."
    )

    # Lazy Evaluation 설명
    explain_lazy_evaluation()


if __name__ == "__main__":
    main()