"""
[실습] 제너레이터 기반 메모리 절약형 로직 작성

요구사항
1) 0부터 999,999까지의 정수를 담는 리스트를 생성하고 총합 구하기
2) 같은 결과를 제너레이터 함수로 구현하기
3) 두 방법의 메모리 사용 차이를 sys.getsizeof()로 확인하기

핵심 포인트
- 리스트(list)는 모든 데이터를 한 번에 메모리에 올린다.
- 제너레이터(generator)는 값을 하나씩 필요할 때 생성한다.
- 따라서 대용량 데이터 처리 시 제너레이터가 메모리 측면에서 유리하다.
"""

import sys


def list_sum_demo(start: int, end: int):
    """
    start 이상 end 이하의 정수를 모두 담는 리스트를 생성한 뒤,
    해당 리스트의 총합과 메모리 사용량을 반환한다.
    """

    # range(start, end + 1)을 list(...)로 감싸면
    # start부터 end까지의 모든 숫자를 한 번에 메모리에 저장한다.
    number_list = list(range(start, end + 1))

    # sum() 함수를 사용해 리스트에 들어있는 모든 값의 합을 구한다.
    total = sum(number_list)

    # sys.getsizeof()는 해당 객체 자체의 메모리 크기를 byte 단위로 반환한다.
    list_memory = sys.getsizeof(number_list)

    return number_list, total, list_memory


def number_generator(start: int, end: int):
    """
    start 이상 end 이하의 정수를 하나씩 생성하는 제너레이터 함수.

    """

    for number in range(start, end + 1):
        yield number


def generator_sum_demo(start: int, end: int):
    """
    제너레이터를 사용하여 start 이상 end 이하 숫자의 총합을 구하고,
    제너레이터 객체의 메모리 사용량을 반환한다.

    반환값
    -------
    tuple
        (제너레이터 객체, 총합, 제너레이터 객체 메모리 크기)
    """

    # 제너레이터 객체 생성
    gen = number_generator(start, end)

    # 제너레이터 객체 자체의 메모리 크기 측정
    generator_memory = sys.getsizeof(gen)

    # sum() 함수는 제너레이터로부터 값을 하나씩 꺼내 누적 합계를 계산한다.
    # 이 과정에서 전체 데이터를 리스트처럼 한꺼번에 메모리에 올리지 않는다.
    total = sum(gen)

    return gen, total, generator_memory


def print_result(title: str, total: int, memory_size: int):
    """
    결과를 보기 좋게 출력하기 위한 보조 함수.
    """

    print(f"\n[{title}]")
    print(f"총합: {total:,}")
    print(f"객체 메모리 크기: {memory_size:,} bytes")


def main():
    """
    프로그램 실행 진입점.

    여기서 다음 순서로 작업한다.
    1. 리스트 방식으로 0 ~ 999,999 생성 후 합계 계산
    2. 제너레이터 방식으로 같은 범위의 합계 계산
    3. 두 방식의 메모리 사용량 비교
    4. 결과 검증
    """

    # 문제 조건:
    # 0부터 999,999까지의 정수 100만 개 처리
    START = 0
    END = 999_999

    print("=" * 70)
    print("100만 개 숫자 처리: 일반 리스트 방식 vs 제너레이터 방식")
    print("=" * 70)

    # ------------------------------------------------------------
    # 1) 일반 리스트 방식
    # ------------------------------------------------------------
    number_list, list_total, list_memory = list_sum_demo(START, END)

    print_result("일반 리스트 방식", list_total, list_memory)

    # 리스트 길이 확인
    print(f"리스트 원소 개수: {len(number_list):,}개")

    # ------------------------------------------------------------
    # 2) 제너레이터 방식
    # ------------------------------------------------------------
    gen, generator_total, generator_memory = generator_sum_demo(START, END)

    print_result("제너레이터 방식", generator_total, generator_memory)

    # 제너레이터 객체는 len()을 사용할 수 없다.
    # 이유: 제너레이터는 전체 데이터를 미리 갖고 있지 않기 때문이다.
    print("제너레이터는 값을 필요할 때마다 하나씩 생성하므로 len() 사용 불가")

    # ------------------------------------------------------------
    # 3) 결과 비교
    # ------------------------------------------------------------
    print("\n" + "=" * 70)
    print("비교 결과")
    print("=" * 70)

    # 두 방식의 합계가 같은지 확인
    if list_total == generator_total:
        print("합계 검증: 두 방식의 결과가 동일합니다.")
    else:
        print("합계 검증: 두 방식의 결과가 다릅니다. 코드 확인이 필요합니다.")

    # 메모리 차이 계산
    memory_difference = list_memory - generator_memory

    print(f"리스트 객체 메모리:      {list_memory:,} bytes")
    print(f"제너레이터 객체 메모리: {generator_memory:,} bytes")
    print(f"메모리 차이:            {memory_difference:,} bytes")

    # ------------------------------------------------------------
    # 추가 설명
    # ------------------------------------------------------------
    print("\n[설명]")
    print("- 리스트는 100만 개 숫자를 모두 메모리에 저장한 뒤 처리합니다.")
    print("- 제너레이터는 숫자를 하나씩 만들어 처리하므로 메모리 사용량이 매우 작습니다.")
    print("- 대용량 데이터, 파일 처리, 로그 스트리밍 등에 제너레이터가 특히 유리합니다.")
    print("- 단, 제너레이터는 한 번 소비하면 다시 처음부터 재사용할 수 없으므로 필요 시 재생성해야 합니다.")


# 현재 파일이 직접 실행될 때만 main() 함수를 호출
if __name__ == "__main__":
    main()