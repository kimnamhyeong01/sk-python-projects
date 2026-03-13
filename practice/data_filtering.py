# 직원 데이터
employees = [
    {"name": "Alice", "department": "Engineering", "age": 30, "salary": 85000},
    {"name": "Bob", "department": "Marketing", "age": 25, "salary": 60000},
    {"name": "Charlie", "department": "Engineering", "age": 35, "salary": 95000},
    {"name": "David", "department": "HR", "age": 45, "salary": 70000},
    {"name": "Eve", "department": "Engineering", "age": 28, "salary": 78000},
]

print("----- 1번 문제 -----")
# filter + list comprehension
engineering_high_salary = list(
    filter(lambda emp: emp["department"] == "Engineering" and emp["salary"] >= 80000, employees)
)

result1 = [emp["name"] for emp in engineering_high_salary]
print(result1)


print("\n----- 2번 문제 -----")
# for + if
result2 = []

for emp in employees:
    if emp["age"] >= 30:
        result2.append((emp["name"], emp["department"]))

print(result2)


print("\n----- 3번 문제 -----")
# salary 기준 내림차순 정렬 후 상위 3명
sorted_employees = sorted(employees, key=lambda emp: emp["salary"], reverse=True)

top3 = []
count = 0

for emp in sorted_employees:
    if count < 3:
        top3.append((emp["name"], emp["salary"]))
        count += 1

print(top3)


print("\n----- 4번 문제 -----")
# 모든 부서별 평균 급여

# 부서 목록 추출 (list comprehension)
departments = list(set([emp["department"] for emp in employees]))

for dept in departments:
    
    # 해당 부서 직원 필터링 (filter 사용)
    dept_employees = list(filter(lambda emp: emp["department"] == dept, employees))
    
    # 급여 리스트 생성 (list comprehension)
    salaries = [emp["salary"] for emp in dept_employees]
    
    # 평균 계산
    avg_salary = sum(salaries) / len(salaries)
    
    print(dept, "평균 급여:", avg_salary)