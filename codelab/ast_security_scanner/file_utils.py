"""
file_utils.py

이 파일은 파일/디렉터리 탐색과 관련된 보조 기능을 담당한다.

보안 검사기는 보통 아래 두 가지 방식으로 사용된다.

1. 특정 파일 하나 검사
   예: python main.py test.py

2. 특정 디렉터리 전체 검사
   예: python main.py ./project

따라서 입력값이 파일인지 디렉터리인지 구분하고,
최종적으로 검사해야 할 모든 .py 파일 목록을 반환하는 함수가 필요하다.

이 파일은 그 역할만 담당하도록 분리했다.
이렇게 하면 main.py는 실행 흐름 제어에 집중하고,
실제 파일 탐색 세부 구현은 file_utils.py가 맡게 되어 구조가 깔끔해진다.
"""

import os


def find_python_files(path: str):
    """
    주어진 경로에서 검사 대상이 되는 파이썬 파일(.py) 목록을 찾는 함수

    동작 방식:
    1. 입력이 파일이면:
       - 확장자가 .py 인 경우만 리스트에 담아 반환
    2. 입력이 디렉터리이면:
       - os.walk()를 사용해 하위 폴더까지 재귀적으로 탐색
       - 확장자가 .py 인 모든 파일을 리스트에 담아 반환

    매개변수:
        path:
            파일 경로 또는 디렉터리 경로

    반환값:
        .py 파일 경로 문자열들의 리스트
    """
    python_files = []

    # -------------------------------------------------------------------
    # case 1) 입력 경로가 "파일"인 경우
    # -------------------------------------------------------------------
    # 예:
    #   python main.py sample.py
    #
    # 이 경우 해당 파일이 .py 확장자라면 검사 대상에 포함한다.
    # -------------------------------------------------------------------
    if os.path.isfile(path):
        if path.endswith(".py"):
            python_files.append(path)

        return python_files

    # -------------------------------------------------------------------
    # case 2) 입력 경로가 "디렉터리"인 경우
    # -------------------------------------------------------------------
    # 예:
    #   python main.py ./my_project
    #
    # os.walk()는 현재 디렉터리와 하위 디렉터리를 재귀적으로 순회한다.
    # root  : 현재 탐색 중인 폴더 경로
    # dirs  : 현재 폴더 안의 하위 폴더 목록
    # files : 현재 폴더 안의 파일 목록
    # -------------------------------------------------------------------
    if os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            # __pycache__는 파이썬 바이트코드 캐시 폴더이므로 검사에서 제외한다.
            # 소스코드 분석과 직접 관련이 없고, 불필요한 순회를 줄일 수 있다.
            dirs[:] = [d for d in dirs if d != "__pycache__"]

            # 현재 폴더 안의 파일들 중 .py 확장자만 검사 대상에 포함
            for file_name in files:
                if file_name.endswith(".py"):
                    full_path = os.path.join(root, file_name)
                    python_files.append(full_path)

    return python_files