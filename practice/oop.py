# ============================================================
# OOP 기반 AI 추천 주문 시스템
# ------------------------------------------------------------
# 이 코드는 온라인 음료 주문 플랫폼을 간단하게 객체지향적으로 구현한 예제입니다.
#
# [구현 기능]
# 1. 다양한 음료 메뉴 정의
# 2. 사용자별 주문 내역 저장
# 3. 최근 주문한 음료의 태그를 바탕으로 유사 음료 추천
# 4. 총 주문 금액, 평균 주문 금액 계산
#
# [객체지향 요소]
# - 클래스(Class)
# - 상속(Inheritance)
# - @property
# - 객체 간 역할 분리
#
# [실행 방식]
# 파일을 그대로 실행하면 아래 순서로 동작합니다.
# - 메뉴 생성
# - 사용자 생성
# - 몇 개의 음료 주문
# - 주문 내역 출력
# - 추천 음료 출력
# - 총합 / 평균 출력
# ============================================================


# datetime 모듈은 "주문 시간"을 기록하기 위해 사용합니다.
from datetime import datetime


# ============================================================
# 1. Beverage 클래스 (부모 클래스)
# ------------------------------------------------------------
# 모든 음료가 공통적으로 가지는 속성:
# - 이름(name)
# - 가격(price)
# - 태그(tags)
#
# 예:
# "아이스 아메리카노", 3000, ["커피", "콜드"]
#
# 이 클래스는 "모든 음료의 기본 틀" 역할을 합니다.
# ============================================================
class Beverage:
    def __init__(self, name, price, tags):
        # 실제 데이터는 보통 "숨겨진 내부 변수"로 저장합니다.
        # 그래서 name -> _name, price -> _price 같은 형태를 사용합니다.
        self._name = name
        self._price = price
        self._tags = tags

    # --------------------------------------------------------
    # @property
    # --------------------------------------------------------
    # @property를 사용하면
    # obj.name 처럼 "변수처럼" 접근할 수 있지만,
    # 실제로는 메서드처럼 동작합니다.
    #
    # 장점:
    # - 나중에 검증 로직을 추가하기 좋음
    # - 객체 외부에서는 더 자연스럽게 사용 가능
    # --------------------------------------------------------
    @property
    def name(self):
        return self._name

    @property
    def price(self):
        return self._price

    @property
    def tags(self):
        return self._tags

    @property
    def category(self):
        # 이 메서드는 상속받은 자식 클래스에서 재정의(override)할 수 있습니다.
        # 기본 Beverage는 구체적인 종류를 모르므로 "일반 음료"라고 반환합니다.
        return "일반 음료"

    def __str__(self):
        # 객체를 print() 했을 때 사람이 보기 좋은 형태로 출력되게 합니다.
        return f"{self.name} / {self.price}원 / 태그: {', '.join(self.tags)} / 분류: {self.category}"


# ============================================================
# 2. Coffee 클래스 (Beverage 상속)
# ------------------------------------------------------------
# Beverage를 상속받아 "커피 음료"를 표현하는 클래스입니다.
# 상속을 쓰는 이유는:
# - 이름, 가격, 태그 같은 공통 속성은 부모에게서 물려받고
# - 커피만의 특징은 따로 정의할 수 있기 때문입니다.
# ============================================================
class Coffee(Beverage):
    @property
    def category(self):
        return "커피"


# ============================================================
# 3. Tea 클래스 (Beverage 상속)
# ------------------------------------------------------------
# Beverage를 상속받아 "차 음료"를 표현하는 클래스입니다.
# ============================================================
class Tea(Beverage):
    @property
    def category(self):
        return "차"


# ============================================================
# 4. Order 클래스
# ------------------------------------------------------------
# "한 번의 주문"을 표현하는 클래스입니다.
#
# 주문에는 보통 다음 정보가 필요합니다.
# - 어떤 음료를 주문했는가?
# - 언제 주문했는가?
#
# 여기서는 한 주문 = 한 음료로 간단히 구성했습니다.
# ============================================================
class Order:
    def __init__(self, beverage):
        self._beverage = beverage
        self._ordered_at = datetime.now()

    @property
    def beverage(self):
        return self._beverage

    @property
    def ordered_at(self):
        return self._ordered_at

    @property
    def price(self):
        # 주문 금액은 주문된 음료의 가격과 같습니다.
        return self.beverage.price

    def __str__(self):
        # 날짜/시간을 사람이 읽기 쉬운 형식으로 바꿉니다.
        order_time = self.ordered_at.strftime("%Y-%m-%d %H:%M:%S")
        return f"[{order_time}] {self.beverage.name} - {self.price}원"


# ============================================================
# 5. User 클래스
# ------------------------------------------------------------
# 사용자 한 명을 표현하는 클래스입니다.
#
# 사용자는 다음 정보를 가집니다.
# - 사용자 이름
# - 주문 내역 목록
#
# 기능:
# - 주문 추가
# - 최근 주문 확인
# - 총 주문 금액 계산
# - 평균 주문 금액 계산
# ============================================================
class User:
    def __init__(self, username):
        self._username = username
        self._orders = []

    @property
    def username(self):
        return self._username

    @property
    def orders(self):
        # 외부에서 orders를 읽을 수 있게 합니다.
        # 여기서는 단순 학습용이므로 그대로 반환합니다.
        return self._orders

    def add_order(self, beverage):
        # 사용자가 음료를 주문하면 Order 객체를 생성해 저장합니다.
        new_order = Order(beverage)
        self._orders.append(new_order)

    def get_latest_order(self):
        # 최근 주문을 반환합니다.
        # 주문이 하나도 없다면 None 반환
        if not self._orders:
            return None
        return self._orders[-1]

    def get_total_spent(self):
        # 총 주문 금액 = 각 주문 금액의 합
        total = sum(order.price for order in self._orders)
        return total

    def get_average_spent(self):
        # 평균 주문 금액 = 총합 / 주문 개수
        # 단, 주문이 하나도 없을 때는 0으로 처리
        if not self._orders:
            return 0
        return self.get_total_spent() / len(self._orders)

    def show_order_history(self):
        # 주문 내역을 보기 좋게 출력하는 메서드
        print(f"\n[{self.username}님의 주문 내역]")
        if not self._orders:
            print("주문 내역이 없습니다.")
            return

        for idx, order in enumerate(self._orders, start=1):
            print(f"{idx}. {order}")


# ============================================================
# 6. RecommendationEngine 클래스
# ------------------------------------------------------------
# "추천 기능"만 담당하는 클래스입니다.
#
# 왜 따로 클래스로 분리할까?
# - 사용자 정보 관리 책임(User)
# - 추천 알고리즘 책임(RecommendationEngine)
# 를 분리하면 코드가 더 깔끔해집니다.
#
# 추천 기준:
# - 사용자의 최근 주문 음료를 기준으로 함
# - 최근 주문 음료와 태그가 겹치는 음료를 추천
# - 최근 주문한 같은 음료는 추천 목록에서 제외
# - 태그가 많이 겹칠수록 더 우선 추천
# ============================================================
class RecommendationEngine:
    def recommend(self, user, menu, top_n=3):
        # 1. 사용자의 최근 주문을 가져옵니다.
        latest_order = user.get_latest_order()

        # 최근 주문이 없으면 추천할 기준이 없으므로 빈 리스트 반환
        if latest_order is None:
            return []

        latest_beverage = latest_order.beverage
        latest_tags = set(latest_beverage.tags)

        # 추천 후보를 저장할 리스트
        # (점수, 음료객체) 형태로 저장한 뒤 나중에 정렬할 예정입니다.
        candidates = []

        # 2. 메뉴 전체를 돌면서 유사한 음료를 찾습니다.
        for beverage in menu:
            # 방금 주문한 "같은 음료"는 제외합니다.
            if beverage.name == latest_beverage.name:
                continue

            # 현재 메뉴 음료의 태그와 최근 주문 태그가 얼마나 겹치는지 계산
            common_tags = latest_tags.intersection(set(beverage.tags))
            score = len(common_tags)

            # 태그가 하나라도 겹치면 추천 후보에 넣습니다.
            if score > 0:
                candidates.append((score, beverage))

        # 3. 점수가 높은 순으로 정렬합니다.
        # score가 클수록 더 유사한 음료입니다.
        candidates.sort(key=lambda x: x[0], reverse=True)

        # 4. 상위 top_n개만 잘라서 음료 객체만 반환합니다.
        recommended_beverages = [beverage for score, beverage in candidates[:top_n]]
        return recommended_beverages


# ============================================================
# 7. OrderSystem 클래스
# ------------------------------------------------------------
# 전체 시스템을 관리하는 클래스입니다.
#
# 역할:
# - 메뉴 관리
# - 사용자 주문 처리
# - 추천 결과 출력 보조
#
# 실무적으로 보면 "서비스 레이어" 비슷한 역할이라고 볼 수 있습니다.
# ============================================================
class OrderSystem:
    def __init__(self, menu):
        self._menu = menu
        self._recommender = RecommendationEngine()

    @property
    def menu(self):
        return self._menu

    def show_menu(self):
        print("\n[메뉴 목록]")
        for idx, beverage in enumerate(self.menu, start=1):
            print(f"{idx}. {beverage}")

    def order_by_name(self, user, beverage_name):
        # 메뉴에서 이름이 일치하는 음료를 찾아 주문 처리합니다.
        for beverage in self.menu:
            if beverage.name == beverage_name:
                user.add_order(beverage)
                print(f"\n주문 완료: {user.username}님이 '{beverage.name}'를 주문했습니다.")
                return

        # 메뉴에 없는 음료를 입력했을 경우
        print(f"\n오류: '{beverage_name}'는 메뉴에 없는 음료입니다.")

    def show_recommendations(self, user, top_n=3):
        recommendations = self._recommender.recommend(user, self.menu, top_n=top_n)

        print(f"\n[{user.username}님을 위한 추천 음료]")
        if not recommendations:
            print("추천할 음료가 없습니다. 먼저 주문을 진행해 주세요.")
            return

        for idx, beverage in enumerate(recommendations, start=1):
            print(f"{idx}. {beverage}")


# ============================================================
# 8. 메인 실행부
# ------------------------------------------------------------
# 실제로 프로그램을 실행해 보는 부분입니다.
# 여기서는 메뉴를 만들고, 사용자를 만들고, 몇 번 주문한 뒤,
# 추천 결과와 통계를 출력합니다.
# ============================================================
if __name__ == "__main__":
    # --------------------------------------------------------
    # 메뉴 생성
    # --------------------------------------------------------
    # 문제 이미지에 나온 예시를 반영하면서,
    # 상속 구조를 보여주기 위해 Coffee / Tea 객체로 생성합니다.
    # --------------------------------------------------------
    menu = [
        Coffee("아이스 아메리카노", 3000, ["커피", "콜드"]),
        Coffee("카페라떼", 3500, ["커피", "밀크"]),
        Tea("녹차", 2800, ["차", "뜨거운"]),
        Tea("허브티", 3000, ["차", "차가운"]),
        Coffee("바닐라라떼", 4000, ["커피", "밀크", "달콤한"]),
        Coffee("콜드브루", 3800, ["커피", "콜드"]),
        Tea("레몬티", 3200, ["차", "상큼한", "뜨거운"]),
    ]

    # 시스템 생성
    system = OrderSystem(menu)

    # 사용자 생성
    user1 = User("김남형")

    # 메뉴 출력
    system.show_menu()

    # --------------------------------------------------------
    # 주문 시뮬레이션
    # --------------------------------------------------------
    # 사용자가 실제로 몇 개의 음료를 주문했다고 가정합니다.
    # 최근 주문 기준 추천이므로 마지막 주문이 중요합니다.
    # --------------------------------------------------------
    system.order_by_name(user1, "카페라떼")
    system.order_by_name(user1, "바닐라라떼")
    system.order_by_name(user1, "아이스 아메리카노")

    # 주문 내역 출력
    user1.show_order_history()

    # 추천 결과 출력
    system.show_recommendations(user1, top_n=3)

    # --------------------------------------------------------
    # 통계 출력
    # --------------------------------------------------------
    total = user1.get_total_spent()
    average = user1.get_average_spent()

    print(f"\n[{user1.username}님의 주문 통계]")
    print(f"총 주문 금액: {total}원")
    print(f"평균 주문 금액: {average:.2f}원")