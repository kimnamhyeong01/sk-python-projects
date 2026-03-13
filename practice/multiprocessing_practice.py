import random
import time
import math
import multiprocessing


# ============================================================
# 1. 소수(prime number) 판별 함수
# ============================================================
# 소수란 1과 자기 자신으로만 나누어떨어지는 2 이상의 정수이다.
#
# 예:
#   2, 3, 5, 7, 11 ... 은 소수
#   1, 4, 6, 8, 9 ... 는 소수가 아님
#
# 이 함수는 전달받은 정수 n이 소수이면 True,
# 소수가 아니면 False를 반환한다.
# ============================================================
def is_prime(n):
    # 1 이하는 소수가 아니다.
    if n < 2:
        return False

    # 2는 가장 작은 소수이다.
    if n == 2:
        return True

    # 2를 제외한 짝수는 모두 소수가 아니다.
    # 예: 4, 6, 8, 10 ...
    if n % 2 == 0:
        return False

    # 어떤 수 n이 소수가 아닌 경우,
    # 반드시 sqrt(n) 이하의 약수를 하나는 가진다.
    # 따라서 3부터 sqrt(n)까지만 검사하면 된다.
    limit = int(math.sqrt(n)) + 1

    # 이미 짝수는 걸러냈으므로 홀수만 검사한다.
    # 3, 5, 7, 9, ...
    for i in range(3, limit, 2):
        if n % i == 0:
            return False

    return True


# ============================================================
# 2. 단일 프로세스 방식으로 소수 개수 세기
# ============================================================
# 하나의 프로세스(일반적인 파이썬 실행 흐름)에서
# 리스트의 모든 숫자를 순차적으로 검사한다.
#
# 매개변수:
#   numbers: 검사할 정수 리스트
#
# 반환값:
#   소수의 개수(int)
# ============================================================
def count_primes_single(numbers):
    prime_count = 0

    # 리스트를 처음부터 끝까지 하나씩 확인
    for number in numbers:
        if is_prime(number):
            prime_count += 1

    return prime_count


# ============================================================
# 3. 멀티프로세싱에서 사용할 "청크(chunk) 단위" 처리 함수
# ============================================================
# multiprocessing.Pool을 사용할 때는 보통 작업을 여러 조각으로 나누어
# 각 프로세스가 일부 데이터만 맡아서 처리하게 한다.
#
# 이 함수는 숫자 리스트의 "일부 구간(chunk)"를 받아서
# 그 안에 포함된 소수의 개수를 세고 반환한다.
#
# 매개변수:
#   chunk: 전체 리스트의 일부분(list)
#
# 반환값:
#   해당 chunk 안에 있는 소수 개수(int)
# ============================================================
def count_primes_in_chunk(chunk):
    count = 0
    for number in chunk:
        if is_prime(number):
            count += 1
    return count


# ============================================================
# 4. 리스트를 일정 크기의 청크(chunk)로 나누는 함수
# ============================================================
# 멀티프로세싱에서는 전체 데이터를 여러 프로세스에 나누어 주어야 한다.
# 이를 위해 긴 리스트를 잘게 나눈다.
#
# 예:
#   numbers = [1,2,3,4,5,6,7,8]
#   chunk_size = 3
#
# 결과:
#   [1,2,3], [4,5,6], [7,8]
#
# 매개변수:
#   data: 원본 리스트
#   chunk_size: 한 chunk에 들어갈 원소 수
#
# 반환값:
#   청크들의 리스트(list of lists)
# ============================================================
def split_into_chunks(data, chunk_size):
    chunks = []

    # 0, chunk_size, 2*chunk_size, ... 위치에서 잘라서 chunk 생성
    for i in range(0, len(data), chunk_size):
        chunks.append(data[i:i + chunk_size])

    return chunks


# ============================================================
# 5. 메인 실행 영역
# ============================================================
# Windows 환경에서 multiprocessing을 사용할 때는 반드시
# "if __name__ == '__main__':" 블록 안에서 실행해야 한다.
#
# 그렇지 않으면 자식 프로세스가 코드를 다시 실행하면서
# 오류가 나거나 무한 생성 문제가 생길 수 있다.
# ============================================================
if __name__ == '__main__':
    # --------------------------------------------------------
    # (1) 실험용 데이터 생성
    # --------------------------------------------------------
    # 과제 요구사항:
    #   - random 사용
    #   - 1 ~ 10,000,000 사이 정수
    #   - 총 10,000,000개 생성
    #
    # 참고:
    #   이 작업만으로도 메모리를 꽤 많이 사용한다.
    # --------------------------------------------------------
    NUM_COUNT = 10_000_000
    MIN_NUM = 1
    MAX_NUM = 10_000_000

    print("난수 데이터를 생성하는 중입니다...")
    data_create_start = time.time()

    numbers = [random.randint(MIN_NUM, MAX_NUM) for _ in range(NUM_COUNT)]

    data_create_end = time.time()
    print(f"난수 생성 완료: {NUM_COUNT:,}개")
    print(f"데이터 생성 시간: {data_create_end - data_create_start:.4f}초")
    print()

    # --------------------------------------------------------
    # (2) 단일 프로세스 방식
    # --------------------------------------------------------
    # 한 개의 프로세스가 전체 리스트를 순서대로 검사한다.
    # --------------------------------------------------------
    print("단일 프로세스 방식으로 소수 개수를 계산하는 중입니다...")
    single_start = time.time()

    single_prime_count = count_primes_single(numbers)

    single_end = time.time()
    single_elapsed = single_end - single_start

    print("[단일 프로세스 결과]")
    print(f"소수 개수: {single_prime_count:,}")
    print(f"처리 시간: {single_elapsed:.4f}초")
    print()

    # --------------------------------------------------------
    # (3) 멀티 프로세스 방식
    # --------------------------------------------------------
    # multiprocessing.Pool을 사용하여 여러 프로세스가
    # 각자 일부 데이터(chunk)를 나누어 처리한다.
    #
    # 처리 순서:
    #   1) CPU 코어 수 확인
    #   2) 리스트를 여러 chunk로 분할
    #   3) Pool.map()으로 각 chunk를 병렬 처리
    #   4) 각 프로세스가 반환한 소수 개수를 모두 합산
    # --------------------------------------------------------
    print("멀티 프로세스 방식으로 소수 개수를 계산하는 중입니다...")

    # 현재 컴퓨터의 CPU 코어 수 확인
    process_count = multiprocessing.cpu_count()

    # chunk 크기 설정
    # 너무 작으면 프로세스 간 전달/관리 오버헤드가 커지고,
    # 너무 크면 작업 분배가 비효율적일 수 있다.
    #
    # 여기서는 CPU 코어 수를 기준으로 적당히 나누도록 설정한다.
    # 전체 데이터를 (프로세스 수 * 4) 개 정도의 chunk로 나눈다.
    chunk_size = len(numbers) // (process_count * 4)

    # 혹시 데이터가 너무 적어서 0이 되는 경우 방지
    if chunk_size == 0:
        chunk_size = 1

    chunks = split_into_chunks(numbers, chunk_size)

    multi_start = time.time()

    # Pool 생성:
    #   process_count 개수만큼 프로세스를 만들어 병렬 작업 수행
    with multiprocessing.Pool(processes=process_count) as pool:
        # 각 chunk에 대해 count_primes_in_chunk 함수를 병렬 적용
        partial_results = pool.map(count_primes_in_chunk, chunks)

    # 각 프로세스가 계산한 소수 개수를 모두 더해서 전체 개수 계산
    multi_prime_count = sum(partial_results)

    multi_end = time.time()
    multi_elapsed = multi_end - multi_start

    print("[멀티 프로세스 결과]")
    print(f"사용한 프로세스 수: {process_count}")
    print(f"분할된 chunk 수: {len(chunks)}")
    print(f"소수 개수: {multi_prime_count:,}")
    print(f"처리 시간: {multi_elapsed:.4f}초")
    print()

    # --------------------------------------------------------
    # (4) 결과 비교
    # --------------------------------------------------------
    # 단일 프로세스와 멀티 프로세스 결과가 같은지 확인하고,
    # 처리 시간 차이도 함께 보여준다.
    # --------------------------------------------------------
    print("===== 최종 비교 =====")
    print(f"단일 프로세스 소수 개수: {single_prime_count:,}")
    print(f"멀티 프로세스 소수 개수: {multi_prime_count:,}")

    if single_prime_count == multi_prime_count:
        print("검증 결과: 두 방식의 소수 개수가 일치합니다.")
    else:
        print("검증 결과: 두 방식의 소수 개수가 다릅니다. 코드 점검이 필요합니다.")

    print(f"단일 프로세스 처리 시간: {single_elapsed:.4f}초")
    print(f"멀티 프로세스 처리 시간: {multi_elapsed:.4f}초")

    # 멀티 프로세스가 더 빨랐을 때 속도 향상 배수 계산
    if multi_elapsed > 0:
        speedup = single_elapsed / multi_elapsed
        print(f"속도 향상 배수(단일 / 멀티): {speedup:.2f}배")