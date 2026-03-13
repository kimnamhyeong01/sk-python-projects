"""
models.py

이 파일은 보안 검사 결과를 저장하기 위한 "데이터 모델"을 정의하는 파일이다.

프로그램이 소스코드를 분석하다가 위험한 함수 호출을 발견하면,
그 결과를 단순 문자열로만 처리하지 않고, 일정한 형식으로 묶어서 관리하는 것이 좋다.

예를 들어 아래와 같은 정보가 필요하다.

- 어떤 파일에서 발견되었는가?
- 몇 번째 줄에서 발견되었는가?
- 어떤 함수가 호출되었는가?
- 왜 위험한가?
- 실제 코드 한 줄은 무엇인가?

이런 정보를 하나의 객체로 묶어서 다루기 위해 dataclass를 사용한다.
"""

from dataclasses import dataclass


@dataclass
class SecurityIssue:
    """
    보안 위반 1건에 대한 정보를 저장하는 데이터 클래스

    dataclass를 사용하면 __init__, __repr__ 등의 메서드를 자동 생성해주므로
    간단한 데이터 저장 객체를 만들 때 매우 편리하다.

    속성 설명:
        file_path:
            위험한 코드가 발견된 파일의 경로

        line_number:
            위험한 코드가 발견된 줄 번호 (1부터 시작)

        col_offset:
            해당 줄에서 몇 번째 위치(열)에서 시작하는지 나타내는 값
            AST 노드가 제공하는 col_offset 값을 사용한다.

        func_name:
            탐지된 위험 함수 이름
            예: "eval", "os.system", "pickle.load"

        message:
            왜 위험한지에 대한 설명 문구

        code_line:
            실제 원본 코드 한 줄
            보고서를 사람이 읽기 쉽게 만들기 위해 함께 저장한다.
    """

    file_path: str
    line_number: int
    col_offset: int
    func_name: str
    message: str
    code_line: str