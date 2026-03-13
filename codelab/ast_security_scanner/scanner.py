"""
scanner.py

이 파일은 AST(Abstract Syntax Tree, 추상 구문 트리)를 이용해
파이썬 코드를 정적 분석하는 핵심 로직을 담고 있다.

[이 파일의 역할]
1. 소스코드를 AST로 변환한다.
2. AST를 순회하면서 함수 호출(Call) 노드를 찾는다.
3. 위험 함수 호출인지 검사한다.
4. 위험하다면 SecurityIssue 객체로 기록한다.

[왜 AST를 사용하는가?]
문자열 검색만으로는 정확한 분석이 어렵다.
예를 들어 단순히 "eval" 문자열이 포함되었다고 해서
반드시 eval 함수가 호출된 것은 아닐 수 있다.

예:
    text = "eval is dangerous"

이 경우 문자열에는 eval이 있지만 실제 함수 호출은 아니다.

반면 AST를 사용하면 코드 구조를 기준으로 분석할 수 있다.
즉, 실제로 함수 호출(Call)인지 아닌지를 구분할 수 있다.

[이번 과제와의 연결]
과제에서 요구한 핵심은 ast.NodeVisitor를 상속받아
모든 함수 호출 노드를 탐색하고, 위험 함수 사용 여부를 리포트하는 것이다.
이 파일이 그 핵심 기능을 담당한다.
"""

import ast

from models import SecurityIssue
from rules import RISKY_FUNCTIONS


class SecurityVisitor(ast.NodeVisitor):
    """
    AST를 순회하며 위험한 함수 호출을 찾는 Visitor 클래스

    ast.NodeVisitor는 파이썬 AST를 순회하기 위한 기본 클래스이다.
    이 클래스를 상속한 뒤,
    특정 노드 타입에 대응하는 메서드(예: visit_Call)를 구현하면
    해당 타입의 노드를 만났을 때 자동으로 그 메서드가 호출된다.

    즉,
    - visit_Call()   -> 함수 호출 노드를 만났을 때 실행
    - visit_Import() -> import 노드를 만났을 때 실행
    - visit_Assign() -> 대입문 노드를 만났을 때 실행

    과제 핵심이 "모든 함수 호출 탐지"이므로
    우리는 visit_Call() 메서드를 구현한다.
    """

    def __init__(self, file_path: str, source_code: str):
        """
        SecurityVisitor 초기화 메서드

        매개변수:
            file_path:
                현재 분석 중인 파일 경로

            source_code:
                현재 파일의 전체 소스코드 문자열

        내부적으로 수행하는 일:
        1. 파일 경로 저장
        2. 원본 소스코드 저장
        3. 탐지 결과를 담을 issues 리스트 생성
        4. 줄 번호 기반으로 실제 코드 줄을 쉽게 꺼내기 위해 splitlines() 수행
        """
        self.file_path = file_path
        self.source_code = source_code

        # 분석 도중 발견된 보안 위반 결과를 저장할 리스트
        self.issues = []

        # 원본 코드를 줄 단위로 나누어 저장한다.
        # 이후 AST 노드의 lineno 값을 이용해 실제 코드 한 줄을 쉽게 찾을 수 있다.
        self.lines = source_code.splitlines()

    def visit_Call(self, node: ast.Call):
        """
        함수 호출(Call) 노드를 방문할 때 실행되는 메서드

        파이썬 소스코드에서 함수 호출은 AST 상에서 ast.Call 노드로 표현된다.

        예:
            eval(user_input)
            os.system("ls")
            pickle.load(f)

        위와 같은 호출은 모두 ast.Call로 나타난다.

        처리 순서:
        1. 현재 Call 노드가 어떤 함수 호출인지 이름을 복원한다.
        2. 그 함수 이름이 위험 함수 목록에 있는지 검사한다.
        3. 위험 함수라면 위치 정보(파일, 줄, 열)와 함께 SecurityIssue로 저장한다.
        4. 이후 generic_visit(node)를 호출해 하위 노드도 계속 탐색한다.

        주의:
        visit_Call 안에서 generic_visit(node)를 호출하지 않으면
        현재 Call 노드의 내부 자식 노드 탐색이 누락될 수 있다.
        """
        # node.func는 "어떤 함수를 호출했는지"를 나타내는 AST 노드이다.
        # 예:
        #   eval(...)        -> Name(id='eval')
        #   os.system(...)   -> Attribute(value=Name(id='os'), attr='system')
        #
        # 이를 사람이 읽을 수 있는 문자열 형태로 바꾸기 위해 보조 메서드를 호출한다.
        func_name = self.get_function_name(node.func)

        # 복원한 함수 이름이 위험 함수 목록에 있다면 위반으로 처리한다.
        if func_name in RISKY_FUNCTIONS:
            # AST 노드는 보통 lineno(줄 번호), col_offset(열 위치)를 가진다.
            line = node.lineno
            col = node.col_offset

            # 보고서 가독성을 위해 실제 코드 한 줄도 함께 추출한다.
            code_line = ""
            if 1 <= line <= len(self.lines):
                # Python 리스트 인덱스는 0부터 시작하므로 line - 1 사용
                code_line = self.lines[line - 1].strip()

            # 보안 위반 결과를 객체로 생성
            issue = SecurityIssue(
                file_path=self.file_path,
                line_number=line,
                col_offset=col,
                func_name=func_name,
                message=RISKY_FUNCTIONS[func_name],
                code_line=code_line,
            )

            # 결과 리스트에 추가
            self.issues.append(issue)

        # 현재 Call 노드의 자식 노드들까지 계속 순회하도록 호출
        self.generic_visit(node)

    def get_function_name(self, node):
        """
        함수 호출 이름을 문자열로 복원하는 보조 메서드

        AST에서는 함수 이름 표현 방식이 여러 가지일 수 있다.
        가장 대표적인 두 가지는 다음과 같다.

        1. 단순 이름 호출
           예: eval(...)
           AST: ast.Name(id='eval')
           결과: "eval"

        2. 속성 접근 형태
           예: os.system(...)
               pickle.load(...)
           AST: ast.Attribute(...)
           결과: "os.system", "pickle.load"

        이 메서드는 재귀적으로 노드를 따라가며
        최종적으로 "점(.)으로 연결된 함수 이름 문자열"을 만든다.

        매개변수:
            node:
                함수 표현을 담고 있는 AST 노드

        반환값:
            함수 이름 문자열
            예: "eval", "os.system", "pickle.load"
            복원이 불가능하면 None 반환
        """
        # -------------------------------------------------------------------
        # case 1) 단순 함수 이름인 경우
        # -------------------------------------------------------------------
        # 예:
        #   eval("1+1")
        #
        # AST에서 func 부분은 대략 아래처럼 표현된다.
        #   Name(id='eval')
        #
        # 이 경우 함수 이름은 node.id 이다.
        # -------------------------------------------------------------------
        if isinstance(node, ast.Name):
            return node.id

        # -------------------------------------------------------------------
        # case 2) 객체.속성 형태인 경우
        # -------------------------------------------------------------------
        # 예:
        #   os.system("ls")
        #   pickle.load(f)
        #
        # AST에서는 Attribute 노드로 표현된다.
        # 예를 들어 os.system은:
        #   Attribute(
        #       value=Name(id='os'),
        #       attr='system'
        #   )
        #
        # 따라서 먼저 value 쪽 이름을 재귀적으로 복원한 뒤,
        # 마지막 attr을 점(.)으로 이어 붙이면 된다.
        # -------------------------------------------------------------------
        elif isinstance(node, ast.Attribute):
            parent = self.get_function_name(node.value)

            # parent가 있으면 "os" + "." + "system" 형태로 결합
            if parent:
                return f"{parent}.{node.attr}"

            # 혹시 상위 이름 복원이 안 되더라도 attr만 반환
            return node.attr

        # -------------------------------------------------------------------
        # case 3) 그 외 복잡한 형태
        # -------------------------------------------------------------------
        # 예:
        #   get_runner()(...)
        #   obj.factory().execute(...)
        #
        # 이번 과제 기본 수준에서는 이런 복잡한 호출 구조까지는
        # 정교하게 복원하지 않아도 된다.
        # 따라서 None을 반환한다.
        # -------------------------------------------------------------------
        return None


def scan_file(file_path: str):
    """
    파이썬 파일 하나를 읽어서 AST 기반 보안 검사를 수행하는 함수

    이 함수는 scanner.py 외부에서 가장 직접적으로 사용되는 함수다.
    main.py에서는 파일 경로를 하나씩 넘겨주고,
    이 함수는 해당 파일의 보안 위반 목록을 반환한다.

    처리 순서:
    1. 파일을 읽는다.
    2. 소스코드를 AST로 파싱한다.
    3. SecurityVisitor로 트리를 순회한다.
    4. 발견된 issues 리스트를 반환한다.

    매개변수:
        file_path:
            검사할 파이썬 파일 경로

    반환값:
        SecurityIssue 객체들의 리스트
        문법 오류가 있거나 읽기 실패 시 빈 리스트를 반환할 수 있다.
    """
    try:
        # 파일을 UTF-8 기준으로 읽는다.
        # errors="replace"를 사용하면 일부 인코딩 문제가 있더라도
        # 전체 분석이 중단되지 않고 가능한 범위 내에서 계속 진행할 수 있다.
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            source = f.read()

    except Exception as e:
        # 파일 읽기 실패 시 분석을 진행할 수 없으므로 빈 리스트를 반환한다.
        # 실제 실무 도구라면 로깅을 남기거나 에러 보고 구조를 둘 수 있다.
        print(f"[오류] 파일 읽기 실패: {file_path} ({e})")
        return []

    try:
        # 소스코드를 AST로 변환한다.
        #
        # ast.parse()는 코드를 실행하지 않는다.
        # 오직 문법 구조를 트리 형태로 변환만 한다.
        tree = ast.parse(source, filename=file_path)

    except SyntaxError as e:
        # 문법 오류가 있는 파일은 AST를 만들 수 없으므로 분석 불가
        print(f"[오류] 문법 오류로 파싱 실패: {file_path} (line {e.lineno}: {e.msg})")
        return []

    except Exception as e:
        # 기타 파싱 관련 예외 처리
        print(f"[오류] AST 파싱 실패: {file_path} ({e})")
        return []

    # Visitor 객체를 생성하고 AST 전체를 순회한다.
    visitor = SecurityVisitor(file_path, source)
    visitor.visit(tree)

    # 분석 결과 리스트 반환
    return visitor.issues