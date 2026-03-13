"""
benchmark.py

이 파일은 timeit을 사용하여 다음 두 함수의 실행 성능을 비교한다.

- sum_of_squares_no_hint(numbers)
- sum_of_squares_with_hint(numbers: list[int]) -> int

핵심 목적:
- 타입 힌트를 사용한 함수와 사용하지 않은 함수의 실행 속도 차이를 측정
- 실제로는 속도 차이가 거의 없음을 확인

왜 거의 차이가 없나?
- 파이썬의 타입 힌트는 기본적으로 런타임 최적화를 위한 기능이 아니다.
- 타입 힌트는 주로 정적 분석(mypy), 문서화, IDE 지원에 활용된다.
- 따라서 함수 본체가 사실상 같다면 실행 시간도 거의 비슷하게 나온다.
"""

from timeit import timeit

from sum_squares import sum_of_squares_no_hint, sum_of_squares_with_hint


def run_benchmark() -> None:
    """
    두 버전의 함수를 동일한 입력으로 반복 실행하여 성능을 측정한다.

    측정 방식:
    - 테스트용 정수 리스트를 준비
    - 각 함수를 매우 여러 번 호출
    - 총 실행 시간을 측정
    - 결과를 출력

    참고:
    - 실행 환경(PC 사양, Python 버전, 백그라운드 프로세스)에 따라 수치는 달라질 수 있다.
    - 중요한 것은 절대값보다 "두 함수가 거의 비슷하다"는 경향이다.
    """

    # 비교용 입력 데이터
    # 길이가 너무 짧으면 측정 오차가 커질 수 있으므로 적당한 크기의 리스트를 사용한다.
    numbers = list(range(1, 1001))  # 1부터 1000까지의 정수 리스트

    # 반복 횟수
    # 반복 횟수를 충분히 크게 잡아야 비교가 조금 더 안정적이다.
    repeat_count = 10000

    # A 버전 측정
    # lambda를 사용하여 동일한 입력에 대해 함수를 반복 호출한다.
    time_a = timeit(
        stmt=lambda: sum_of_squares_no_hint(numbers),
        number=repeat_count,
    )

    # B 버전 측정
    time_b = timeit(
        stmt=lambda: sum_of_squares_with_hint(numbers),
        number=repeat_count,
    )

    # 결과 출력
    print("=== timeit 성능 측정 결과 ===")
    print(f"입력 데이터 크기: {len(numbers)}개")
    print(f"반복 횟수: {repeat_count:,}회")
    print()

    print(f"A 버전(타입 힌트 없음) 실행 시간: {time_a:.6f}초")
    print(f"B 버전(타입 힌트 있음) 실행 시간: {time_b:.6f}초")
    print()

    # 차이 계산
    difference = abs(time_a - time_b)
    print(f"절대 시간 차이: {difference:.6f}초")

    # 상대 차이(참고용)
    # time_a가 0일 가능성은 사실상 없지만, 안전하게 조건 처리
    if time_a != 0:
        percent_diff = (difference / time_a) * 100
        print(f"A 버전 기준 상대 차이: {percent_diff:.4f}%")

    print()
    print("해석:")
    print("- 두 함수의 로직은 동일하므로 실행 시간은 대체로 거의 비슷하다.")
    print("- 타입 힌트는 실행 속도 개선보다는 가독성, 안정성, 정적 검사 측면에서 이점이 있다.")


if __name__ == "__main__":
    run_benchmark()