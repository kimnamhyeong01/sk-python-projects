import sys
import time


def even_square_gen(n):
    """
    0 이상 n 미만의 정수 중에서 짝수만 골라
    그 제곱값을 하나씩 생성하는 제너레이터 함수.
    """
    for i in range(n):
        # 짝수인 경우에만 제곱값을 하나씩 생성
        if i % 2 == 0:
            yield i ** 2

def list_method(n):
    """
    리스트 방식으로 짝수의 제곱값 전체를 한 번에 만든 뒤 합계를 구한다.

    반환:
        even_squares (list): 짝수 제곱값이 담긴 리스트
        total_sum (int): 리스트 원소들의 총합
        elapsed_time (float): 처리 시간(초)
    """
    start_time = time.time()

    # 리스트 컴프리헨션으로 짝수의 제곱값을 한 번에 모두 생성
    even_squares = [i ** 2 for i in range(n) if i % 2 == 0]

    # 생성된 리스트의 모든 값을 더함
    total_sum = sum(even_squares)

    end_time = time.time()
    elapsed_time = end_time - start_time

    return even_squares, total_sum, elapsed_time


def generator_method(n):
    """
    제너레이터 방식으로 짝수의 제곱값을 하나씩 생성하면서 합계를 구한다.

    처리 순서:
    1) even_square_gen(n) 제너레이터 생성
    2) sum()이 제너레이터에서 값을 하나씩 꺼내며 합산
    3) 전체 값을 리스트처럼 메모리에 저장하지 않음

    반환:
        gen_obj (generator): 생성된 제너레이터 객체
        total_sum (int): 제너레이터가 만들어 낸 값들의 총합
        elapsed_time (float): 처리 시간(초)
    """
    start_time = time.time()

    # 제너레이터 객체 생성
    gen_obj = even_square_gen(n)

    # 값을 하나씩 꺼내며 합산
    total_sum = sum(gen_obj)

    end_time = time.time()
    elapsed_time = end_time - start_time

    return gen_obj, total_sum, elapsed_time


def main():
    """
    프로그램의 메인 실행 함수.

    요구사항:
    1) 0부터 999,999까지의 정수를 기준으로 계산
    2) 리스트 방식과 제너레이터 방식 비교
    3) 총합, 메모리 사용량, 처리 시간을 출력
    """
    n = 1_000_001

    print("=" * 70)
    print("제너레이터 기반 메모리 절약형 로직 비교")
    print(f"비교 범위: 0 이상 {n:,} 미만")
    print("대상: 짝수의 제곱 총합")
    print("=" * 70)

    # -----------------------------
    # 1. 리스트 방식 수행
    # -----------------------------
    list_result, list_sum, list_time = list_method(n)

    # sys.getsizeof()는 '리스트 객체 자체의 크기'를 보여준다.
    # 즉, 리스트 안에 들어 있는 모든 정수 객체의 실제 총 메모리까지
    # 완벽하게 포함한 값은 아니다.
    # 하지만 리스트 객체와 제너레이터 객체의 차이를 비교하는 용도로는 충분하다.
    list_memory = sys.getsizeof(list_result)

    print("\n[1] 리스트 방식")
    print(f"총합               : {list_sum:,}")
    print(f"리스트 객체 크기   : {list_memory:,} bytes")
    print(f"처리 시간          : {list_time:.6f} 초")

    # -----------------------------
    # 2. 제너레이터 방식 수행
    # -----------------------------
    gen_result, gen_sum, gen_time = generator_method(n)

    # 제너레이터 객체의 메모리 크기 측정
    gen_memory = sys.getsizeof(gen_result)

    print("\n[2] 제너레이터 방식")
    print(f"총합               : {gen_sum:,}")
    print(f"제너레이터 크기    : {gen_memory:,} bytes")
    print(f"처리 시간          : {gen_time:.6f} 초")

    # -----------------------------
    # 3. 결과 검증
    # -----------------------------
    print("\n[3] 결과 검증")
    if list_sum == gen_sum:
        print("두 방식의 총합이 같습니다. 결과가 정상적으로 일치합니다.")
    else:
        print("두 방식의 총합이 다릅니다. 로직을 다시 확인해야 합니다.")

    # -----------------------------
    # 4. 메모리 / 속도 비교
    # -----------------------------
    print("\n[4] 비교 분석")
    print(f"리스트 방식 메모리   : {list_memory:,} bytes")
    print(f"제너레이터 메모리   : {gen_memory:,} bytes")
    print(f"메모리 차이         : {list_memory - gen_memory:,} bytes")

    print(f"\n리스트 방식 시간     : {list_time:.6f} 초")
    print(f"제너레이터 방식 시간 : {gen_time:.6f} 초")
    print("참고: 실행 시간은 PC 성능과 실행 환경에 따라 달라질 수 있습니다.")

    print("\n[5] 해설")
    print("- 리스트 방식은 데이터를 한 번에 모두 메모리에 저장한 뒤 계산합니다.")
    print("- 제너레이터 방식은 값을 필요할 때마다 하나씩 생성하면서 계산합니다.")
    print("- 따라서 큰 데이터를 다룰수록 제너레이터가 메모리 절약에 유리합니다.")
    print("- sys.getsizeof()는 객체 자체 크기만 보여주므로,")
    print("  리스트 내부 원소 전체의 실제 메모리를 완전히 반영하지는 않습니다.")
    print("  그래도 리스트와 제너레이터의 구조적 차이를 이해하는 데는 유용합니다.")


# 현재 파일이 직접 실행될 때만 main() 실행
if __name__ == "__main__":
    main()