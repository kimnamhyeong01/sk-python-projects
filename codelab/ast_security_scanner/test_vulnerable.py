"""
test_vulnerable.py

이 파일은 AST 기반 보안 검사기를 테스트하기 위한 예제 코드이다.

의도적으로 여러 가지 보안 취약 패턴을 포함하고 있다.
보안 검사기를 실행하면 아래 함수들이 탐지되어야 한다.

포함된 취약 함수 예시

1. eval()
2. exec()
3. os.system()
4. pickle.load()

이 파일은 실제 보안 코드가 아니라
"탐지 테스트용 샘플 코드"이다.
"""

import os
import pickle


def test_eval(user_input):
    """
    eval() 취약점 테스트

    eval은 문자열을 그대로 Python 코드로 실행한다.

    예:
        user_input = "__import__('os').system('rm -rf /')"

    이런 입력이 들어오면 시스템 명령이 실행될 수 있다.
    따라서 대부분의 보안 정책에서 금지된다.
    """

    result = eval(user_input)

    return result


def test_exec(code):
    """
    exec() 취약점 테스트

    exec 역시 문자열 코드를 실행한다.
    eval보다 더 강력한 기능을 가진다.

    공격자가 입력값을 조작하면
    임의 코드 실행이 가능하다.
    """

    exec(code)


def test_os_system():
    """
    os.system() 취약점 테스트

    os.system은 운영체제 쉘 명령을 실행한다.

    사용자 입력을 그대로 넣으면
    command injection 취약점이 발생할 수 있다.
    """

    command = "ls -al"

    os.system(command)


def test_pickle():
    """
    pickle.load() 취약점 테스트

    pickle은 Python 객체를 직렬화 / 역직렬화하는 라이브러리이다.

    문제는 pickle.load()는 역직렬화 시
    객체 내부 코드를 실행할 수 있기 때문에
    악성 payload가 포함된 pickle 파일을 읽으면
    코드 실행 취약점이 발생할 수 있다.
    """

    with open("data.pkl", "rb") as f:
        data = pickle.load(f)

    return data