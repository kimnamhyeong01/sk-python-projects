"""
test_safe.py

이 파일은 정상적인 코드 예제이다.

보안 검사기가 실행될 때
이 파일에서는 어떠한 취약점도 탐지되지 않아야 한다.

즉, 결과 리포트에 이 파일은 등장하지 않아야 정상이다.
"""


def add(a, b):
    """
    단순 덧셈 함수
    """

    return a + b


def greet(name):
    """
    문자열 출력 함수
    """

    print("Hello", name)


def file_read():
    """
    안전한 파일 읽기 예제
    """

    with open("sample.txt", "r") as f:
        content = f.read()

    return content