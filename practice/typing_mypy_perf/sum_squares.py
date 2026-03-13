"""
sum_squares.py

과제 요구사항:
- 입력: 정수 리스트
- 출력: 각 원소의 제곱을 더한 합

이 파일에는 두 가지 버전의 함수를 정의한다.

A 버전:
- 타입 힌트를 사용하지 않은 함수
- 런타임에서는 문제없이 동작할 수 있지만,
  정적 타입 검사 도구(mypy)가 함수 인자/반환값을 명확히 추론하기 어렵다.

B 버전:
- 타입 힌트를 적용한 함수
- mypy 같은 정적 타입 검사 도구가 코드를 분석할 수 있다.
- 코드 가독성과 유지보수성 측면에서도 장점이 있다.

중요:
- 파이썬의 타입 힌트는 기본적으로 "실행 속도 최적화" 목적이 아니라
  "문서화 + 정적 분석 + IDE 지원" 목적이다.
- 따라서 A/B 버전의 실행 성능은 대체로 거의 비슷하게 나온다.
"""


def sum_of_squares_no_hint(numbers):
    """
    A 버전: 타입 힌트를 사용하지 않은 함수

    매개변수:
        numbers
            정수들이 들어 있는 리스트를 기대하지만,
            타입 힌트가 없기 때문에 코드만 봐서는 정확한 의도를 알기 어렵다.

    반환값:
        각 원소를 제곱한 뒤 모두 더한 정수 합계를 반환한다.

    예:
        [1, 2, 3] -> 1^2 + 2^2 + 3^2 = 14

    동작 설명:
        1) 합계를 저장할 변수 total을 0으로 시작
        2) 리스트를 순회하면서 각 원소를 제곱
        3) total에 누적
        4) 최종 합계를 반환

    주의:
        타입 힌트가 없으므로, 잘못된 값이 들어와도 사전에 확인하기 어렵다.
        예를 들어 문자열이 섞여 있으면 실행 중(TypeError) 문제가 발생할 수 있다.
    """
    total = 0

    for number in numbers:
        total += number * number

    return total


def sum_of_squares_with_hint(numbers: list[int]) -> int:
    """
    B 버전: 타입 힌트를 적용한 함수

    매개변수:
        numbers: list[int]
            정수(int)만 담긴 리스트여야 함을 명시한다.

    반환값:
        int
            각 원소를 제곱한 뒤 모두 더한 정수 합계를 반환한다.

    예:
        [1, 2, 3] -> 14

    타입 힌트 장점:
        - 다른 사람이 코드를 읽을 때 의도를 즉시 이해할 수 있다.
        - IDE 자동완성 및 정적 분석 지원이 좋아진다.
        - mypy로 사전에 타입 오류를 검사할 수 있다.

    중요:
        타입 힌트는 "힌트"이므로 파이썬 인터프리터가 기본적으로 강제하지는 않는다.
        즉, 잘못된 타입을 넘겨도 즉시 막히는 것이 아니라,
        mypy 같은 도구를 통해 사전에 점검하는 방식이다.
    """
    total: int = 0

    for number in numbers:
        total += number * number

    return total


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때 간단한 동작 예시를 보여준다.
    sample_numbers = [1, 2, 3, 4, 5]

    print("샘플 입력:", sample_numbers)
    print("A 버전 결과:", sum_of_squares_no_hint(sample_numbers))
    print("B 버전 결과:", sum_of_squares_with_hint(sample_numbers))

    # 아래는 타입 오류 예시 설명용 주석이다.
    # 실제로 실행하면 A/B 모두 런타임에서 문제를 일으킬 수 있다.
    #
    # wrong_data = [1, 2, "3", 4]
    # print(sum_of_squares_no_hint(wrong_data))
    # print(sum_of_squares_with_hint(wrong_data))
    #
    # 차이점은:
    # - A 버전은 mypy가 명확하게 체크하기 어려움
    # - B 버전은 mypy가 list[int]가 아니라는 점을 사전에 알려줄 수 있음