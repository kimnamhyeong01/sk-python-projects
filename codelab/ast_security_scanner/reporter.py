"""
reporter.py

이 파일은 보안 검사 결과를 화면에 출력하는 역할을 담당한다.

왜 별도 파일로 분리하는가?

프로그램의 관심사를 분리하기 위해서이다.

- scanner.py  : "탐지" 담당
- reporter.py : "출력" 담당

이렇게 나누면 장점이 있다.

1. 출력 형식을 바꾸기 쉽다.
   예: 텍스트 출력 -> JSON 출력 -> HTML 출력

2. 탐지 로직과 출력 로직이 섞이지 않아 유지보수가 쉬워진다.

3. 나중에 print 대신 파일 저장 기능을 추가하기도 쉬워진다.

이번 파일에서는 가장 기본적인 "콘솔 리포트 출력" 기능을 제공한다.
"""


def print_report(issues):
    """
    보안 검사 결과 리스트를 사람이 읽기 쉬운 형태로 출력하는 함수

    매개변수:
        issues:
            SecurityIssue 객체 리스트

    출력 내용:
    - 전체 제목
    - 각 위반 항목의 파일 경로
    - 줄 번호
    - 함수 이름
    - 위험 설명
    - 실제 코드 한 줄
    - 전체 위반 건수

    특징:
    - 파일명과 줄번호 순으로 정렬해 가독성을 높인다.
    """
    print("=" * 60)
    print("AST 기반 자동 보안 검사 결과")
    print("=" * 60)

    # 위반이 하나도 없으면 안내 메시지 출력 후 종료
    if not issues:
        print("취약점이 발견되지 않았습니다.")
        return

    # 출력 순서를 일정하게 맞추기 위해 정렬
    # 파일 경로 -> 줄 번호 순으로 정렬하면 같은 파일의 결과가 모여서 보기 좋다.
    issues = sorted(
        issues,
        key=lambda x: (x.file_path, x.line_number, x.col_offset)
    )

    # 각 위반 항목을 순차적으로 출력
    for issue in issues:
        print(
            f"[위험] 파일: {issue.file_path} | "
            f"줄: {issue.line_number} | "
            f"열: {issue.col_offset} | "
            f"함수: {issue.func_name}"
        )

        print(f"       설명: {issue.message}")

        # 실제 코드 줄이 있는 경우 함께 출력
        if issue.code_line:
            print(f"       코드: {issue.code_line}")

        # 각 항목 사이에 빈 줄을 넣어 가독성 향상
        print()

    print(f"총 {len(issues)}개의 보안 위험이 발견되었습니다.")