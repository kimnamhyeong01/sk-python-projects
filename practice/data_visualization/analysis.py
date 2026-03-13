# =============================================================================
# [파이썬 3일차 - 16. 시각화] Pandas + Seaborn 분석 실습
#
# 분석 대상: reviews_1000.csv (고객 리뷰 1000건)
# 컬럼 구성:
#   - review_id      : 리뷰 고유 ID
#   - product_id     : 상품 ID
#   - category       : 상품 카테고리 (fashion / home / sports 등)
#   - review_text    : 리뷰 원문 텍스트
#   - review_length  : 리뷰 텍스트의 문자 수 (길이)
#   - num_words      : 리뷰 텍스트의 단어 수
#   - sentiment_score: 감성 분석 점수 (-1 ~ 1, 양수=긍정 / 음수=부정)
#   - rating         : 고객 평점 (1 ~ 5)
#
# 분석 목적:
#   고객 리뷰 데이터를 LLM 임베딩 기반 추천 시스템에 활용하기 전,
#   데이터 품질을 점검하고 변수 간 관계를 파악하는 EDA(탐색적 데이터 분석) 수행
# =============================================================================

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# -----------------------------------------------------------------------------
# 시각화 기본 설정
# - macOS 환경에서 matplotlib 한글이 깨지지 않도록 AppleGothic 폰트 지정
# - unicode_minus=False: 음수 기호(-)가 네모로 깨지는 현상 방지
# -----------------------------------------------------------------------------
plt.rcParams['font.family'] = 'AppleGothic'
plt.rcParams['axes.unicode_minus'] = False


# =============================================================================
# 1단계: 데이터 전처리
# =============================================================================
print("=" * 60)
print("1단계: 데이터 전처리")
print("=" * 60)

# -----------------------------------------------------------------------------
# 1-1. 데이터 로드
# - pandas read_csv()로 CSV 파일을 DataFrame으로 불러옴
# - shape: (행 수, 열 수) → 데이터 전체 크기 확인
# - dtypes: 각 컬럼의 데이터 타입 확인 (숫자형 / 문자형 구분에 필요)
# - head(): 실제 데이터가 올바르게 로드됐는지 상위 5행으로 육안 확인
# -----------------------------------------------------------------------------
df = pd.read_csv("reviews_1000.csv")
print(f"\n[데이터 로드 완료]")
print(f"Shape: {df.shape}")
print(f"\n[컬럼 목록]\n{df.dtypes}")
print(f"\n[상위 5행]\n{df.head()}")

# -----------------------------------------------------------------------------
# 1-2. 결측치 확인
# - isnull().sum(): 각 컬럼별 결측치(NaN) 개수를 집계
# - 결측치 비율(%) = (결측치 수 / 전체 행 수) × 100
#   → 비율이 높을수록 해당 컬럼의 신뢰도가 낮아지므로 처리 전략을 다르게 가져가야 함
# -----------------------------------------------------------------------------
print("\n[결측치 확인]")
missing = df.isnull().sum()
print(missing)
missing_pct = (missing / len(df) * 100).round(2)
print(f"\n[결측치 비율(%)]\n{missing_pct}")

# -----------------------------------------------------------------------------
# 1-2. 결측치 처리 전략
#
# [수치형 컬럼] → 중앙값(median)으로 대체
#   - 평균(mean)이 아닌 중앙값을 사용하는 이유:
#     평균은 이상치(outlier)에 민감하게 반응해 전체 분포를 왜곡할 수 있음.
#     예) sentiment_score에 극단적인 -0.99 값이 몇 개 섞여 있으면
#         평균은 크게 낮아지지만, 중앙값은 영향을 거의 받지 않음.
#   - 따라서 이상치가 존재할 가능성이 있는 수치형 데이터는 중앙값 대체가 더 안전함.
#
# [범주형(문자열) 컬럼] → 최빈값(mode)으로 대체
#   - 범주형 데이터에는 "평균"이나 "중앙값" 개념이 없음.
#     (예: category='fashion', 'home', 'sports' → 이들의 평균은 의미 없음)
#   - 가장 많이 등장한 값(최빈값)으로 채우는 것이 분포를 최대한 유지하는 방법.
#   - mode()는 리스트를 반환하므로 [0]으로 첫 번째(가장 빈도 높은) 값만 사용.
#
# [삭제 방식을 선택하지 않은 이유]
#   - 행을 통째로 삭제하면 데이터 수가 줄어 분석 신뢰도가 낮아짐.
#   - 특히 데이터가 1000건으로 많지 않은 경우, 행 삭제보다 대체 방식이 권장됨.
# -----------------------------------------------------------------------------
if missing.sum() > 0:
    # 수치형 컬럼 순회: 결측치가 있는 컬럼만 중앙값으로 채움
    # pandas 2.x 이상 Copy-on-Write 정책으로 inplace=True가 원본에 반영되지 않으므로
    # df[col] = df[col].fillna(...) 형태로 재할당해야 실제로 적용됨
    for col in df.select_dtypes(include='number').columns:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].median())

    # 문자열(범주형) 컬럼 순회: 결측치가 있는 컬럼만 최빈값으로 채움
    # include='str': pandas 3.x에서 'object' deprecated 대응
    for col in df.select_dtypes(include='str').columns:
        if df[col].isnull().sum() > 0:
            df[col] = df[col].fillna(df[col].mode()[0])

    print("\n[결측치 처리 완료 - 수치형: 중앙값, 범주형: 최빈값 대체]")
else:
    print("\n결측치 없음 - 처리 불필요")

# -----------------------------------------------------------------------------
# 1-3. 분포 시각화 및 이상치 탐지
#
# 분석 대상 수치형 컬럼 4개를 선정하여 각각 두 가지 그래프로 시각화
#   [위쪽] 히스토그램: 전체 분포 형태(정규분포 여부, 치우침 등) 파악
#   [아래쪽] 박스플롯: IQR(사분위범위) 기준 이상치 탐지
#
# IQR(Inter Quartile Range) 이상치 기준:
#   - IQR = Q3(75%) - Q1(25%)
#   - 이상치 범위: Q1 - 1.5×IQR 미만 or Q3 + 1.5×IQR 초과
#   - 이 범위를 벗어난 데이터 포인트는 박스플롯에서 점(●)으로 표시됨
# -----------------------------------------------------------------------------
numeric_cols = ['review_length', 'num_words', 'sentiment_score', 'rating']

# 2행 4열 서브플롯 생성 (위: 히스토그램, 아래: 박스플롯)
fig, axes = plt.subplots(2, 4, figsize=(18, 8))
fig.suptitle('1단계: 수치형 변수 분포 및 이상치 탐지', fontsize=14, fontweight='bold')

for i, col in enumerate(numeric_cols):

    # [위쪽] 히스토그램: 데이터 분포 형태 시각화
    axes[0, i].hist(df[col], bins=20, color='steelblue', edgecolor='white', alpha=0.8)
    axes[0, i].set_title(f'{col} - 분포')
    axes[0, i].set_xlabel(col)
    axes[0, i].set_ylabel('빈도')
    mean_val = df[col].mean()
    # 평균값 위치에 빨간 점선 표시 → 분포 중심을 한눈에 파악
    axes[0, i].axvline(mean_val, color='red', linestyle='--', linewidth=1.5,
                       label=f'평균: {mean_val:.2f}')
    axes[0, i].legend(fontsize=8)

    # [아래쪽] 박스플롯: IQR 기반 이상치 탐지
    # - patch_artist=True: 박스 내부를 색으로 채워서 가독성 향상
    # - boxprops: 박스 테두리 및 색상 설정
    # - medianprops: 중앙값 선 색상/굵기 강조
    axes[1, i].boxplot(df[col], patch_artist=True,
                       boxprops=dict(facecolor='lightcoral', color='darkred'),
                       medianprops=dict(color='navy', linewidth=2))
    axes[1, i].set_title(f'{col} - 이상치 탐지')
    axes[1, i].set_ylabel(col)

    # IQR 계산 및 이상치 필터링
    Q1 = df[col].quantile(0.25)  # 1사분위수 (하위 25%)
    Q3 = df[col].quantile(0.75)  # 3사분위수 (상위 25%)
    IQR = Q3 - Q1
    outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
    # x축 레이블에 이상치 개수 표시
    axes[1, i].set_xlabel(f'이상치: {len(outliers)}개')

plt.tight_layout()
plt.savefig('step1_distribution_outlier.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n[그래프 저장] step1_distribution_outlier.png")

# 콘솔에 이상치 탐지 결과 요약 출력
print("\n[IQR 기반 이상치 탐지 요약]")
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = df[(df[col] < Q1 - 1.5 * IQR) | (df[col] > Q3 + 1.5 * IQR)]
    print(f"  {col}: 이상치 {len(outliers)}개 ({len(outliers)/len(df)*100:.1f}%)")


# =============================================================================
# 2단계: 기술 통계 및 시각화
# =============================================================================
print("\n" + "=" * 60)
print("2단계: 기술 통계 및 시각화")
print("=" * 60)

# -----------------------------------------------------------------------------
# 2-1. 기술 통계 요약
# - describe(): count / mean / std / min / 25% / 50% / 75% / max 자동 계산
# - 각 수치형 변수의 전반적인 분포 특성을 수치로 한눈에 파악
# -----------------------------------------------------------------------------
print("\n[수치형 변수 기술 통계 요약]")
desc = df[numeric_cols].describe().round(3)
print(desc)

# 1행 3열 서브플롯 생성 (그래프 3개를 가로 배치)
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('2단계: 기술 통계 및 시각화', fontsize=14, fontweight='bold')

# -----------------------------------------------------------------------------
# 2-2. category별 평균 평점 barplot
# - groupby('category')로 카테고리별로 묶은 뒤, rating의 평균을 계산
# - sort_values: 평균 평점이 높은 카테고리부터 내림차순 정렬
# - axhline: 전체 평균 기준선을 빨간 점선으로 표시 → 카테고리 간 비교 기준 제공
# - 각 막대 위에 수치 레이블을 직접 표시 → 정확한 값 확인 가능
# -----------------------------------------------------------------------------
cat_rating = df.groupby('category')['rating'].mean().sort_values(ascending=False).reset_index()
colors = sns.color_palette("Blues_d", len(cat_rating))  # 진한 파랑 계열 색상 팔레트
bars = axes[0].bar(cat_rating['category'], cat_rating['rating'], color=colors, edgecolor='gray')
axes[0].set_title('카테고리별 평균 평점', fontsize=12)
axes[0].set_xlabel('Category')
axes[0].set_ylabel('평균 평점')
axes[0].set_ylim(0, 5.5)  # y축 범위 0~5.5로 고정 (평점 범위 1~5 기준)
for bar, val in zip(bars, cat_rating['rating']):
    # 막대 상단에 수치 레이블 표시 (가운데 정렬)
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                 f'{val:.2f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
# 전체 평균값을 가로 기준선으로 표시
axes[0].axhline(df['rating'].mean(), color='red', linestyle='--', linewidth=1.5,
                label=f'전체 평균: {df["rating"].mean():.2f}')
axes[0].legend()

# -----------------------------------------------------------------------------
# 2-3. 평점(rating)과 감성 점수(sentiment_score) 관계 시각화
# - 산점도(scatter): 두 변수의 관계를 점으로 나타냄
# - alpha=0.4: 점이 겹칠 때 투명도를 줘서 밀도 차이 시각화
# - 회귀선: np.polyfit()으로 1차 선형 회귀 계수(기울기, 절편) 계산 후 그래프에 표시
#   → 기울기가 양수면 양의 상관관계, 음수면 음의 상관관계
# - 상관계수(Pearson r): -1~1 사이 값, 1에 가까울수록 강한 양의 선형 관계
# -----------------------------------------------------------------------------
# seaborn regplot: scatter + 회귀선 + 신뢰구간을 한 번에 그려줌
# np.polyfit() 대신 사용 → SVD 수렴 실패 오류 없이 안정적으로 동작
# ci=95: 95% 신뢰구간을 음영으로 표시
sns.regplot(data=df, x='sentiment_score', y='rating',
            scatter_kws={'alpha': 0.4, 's': 20, 'color': 'steelblue'},
            line_kws={'color': 'red', 'linewidth': 2},
            ci=95, ax=axes[1])

corr = df['sentiment_score'].corr(df['rating'])  # 피어슨 상관계수 계산
axes[1].set_title(f'평점 vs 감성 점수\n(상관계수: {corr:.3f})', fontsize=12)
axes[1].set_xlabel('Sentiment Score')
axes[1].set_ylabel('Rating')

# -----------------------------------------------------------------------------
# 2-4. 텍스트 길이(review_length)와 평점(rating)의 관계 - Violin Plot
# - 바이올린 플롯: 박스플롯 + 커널 밀도 추정(KDE)을 합친 시각화
#   → 박스플롯보다 분포 형태(뾰족함, 두꺼운 부분 등)를 더 풍부하게 표현
# - inner='quartile': 바이올린 내부에 사분위수(Q1/중앙값/Q3) 선을 표시
# - rating_order: x축 평점을 1~5 순서로 정렬하기 위해 정렬된 리스트 전달
# -----------------------------------------------------------------------------
rating_order = sorted(df['rating'].unique())
sns.violinplot(data=df, x='rating', y='review_length', order=rating_order,
               hue='rating', palette='muted', inner='quartile', legend=False, ax=axes[2])
axes[2].set_title('텍스트 길이 vs 평점 (Violin Plot)', fontsize=12)
axes[2].set_xlabel('Rating')
axes[2].set_ylabel('Review Length')

plt.tight_layout()
plt.savefig('step2_statistics_visualization.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n[그래프 저장] step2_statistics_visualization.png")


# =============================================================================
# 3단계: AI 분석을 위한 인사이트 도출
#
# LLM 임베딩 기반 추천 시스템 구축을 위해 아래 3가지 핵심 질문에 답하는 분석
#   Q1. sentiment_score가 높을수록 rating도 높은가? (감성-평점 일치도)
#   Q2. review_length가 AI 임베딩 유사도에 영향을 줄 수 있는가? (텍스트 길이 영향)
#   Q3. category별로 감성 점수 평균에 차이가 존재하는가? (카테고리 편향 여부)
# =============================================================================
print("\n" + "=" * 60)
print("3단계: AI 분석을 위한 인사이트 도출")
print("=" * 60)

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle('3단계: AI 분석을 위한 인사이트 도출', fontsize=14, fontweight='bold')

# -----------------------------------------------------------------------------
# Q1. sentiment_score가 높을수록 평점(rating)이 높은가?
#
# - 평점(1~5) 구간별로 감성 점수의 평균을 계산하여 barplot으로 시각화
# - 막대 색상: 빨강(낮음) → 노랑 → 초록(높음) 그라데이션 (RdYlGn 팔레트)
# - axhline(0): 감성 점수 0(중립) 기준선 표시 → 음수/양수 구분에 활용
# - 피어슨 상관계수로 두 변수 간 선형 관계 강도를 수치로 보완
# -----------------------------------------------------------------------------
rating_sentiment = df.groupby('rating')['sentiment_score'].mean().reset_index()
colors_q1 = sns.color_palette("RdYlGn", len(rating_sentiment))
bars_q1 = axes[0].bar(rating_sentiment['rating'].astype(str),
                       rating_sentiment['sentiment_score'], color=colors_q1, edgecolor='gray')
for bar, val in zip(bars_q1, rating_sentiment['sentiment_score']):
    # 수치 레이블: 양수이면 막대 위, 음수이면 막대 아래에 표시
    axes[0].text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + (0.005 if val >= 0 else -0.02),
                 f'{val:.3f}', ha='center', va='bottom', fontsize=9)
axes[0].axhline(0, color='black', linewidth=0.8, linestyle='-')  # 중립선(0) 표시
axes[0].set_title('Q1. 평점별 평균 감성 점수\n(높은 평점 = 높은 감성?)', fontsize=11)
axes[0].set_xlabel('Rating')
axes[0].set_ylabel('평균 Sentiment Score')

corr_q1 = df['rating'].corr(df['sentiment_score'])  # 평점-감성점수 상관계수
print(f"\n[Q1] 평점-감성점수 상관계수: {corr_q1:.4f}")

# -----------------------------------------------------------------------------
# Q2. review_length가 AI 임베딩 유사도에 영향을 줄 수 있는가?
#
# - 텍스트 길이를 3개 구간으로 나눠 구간별 리뷰 수와 평균 감성 점수를 비교
#   · 짧음: 0~120자 / 보통: 121~150자 / 긺: 151자~
# - pd.cut(): 연속형 수치를 지정한 구간(bins)으로 범주화
# - twinx(): 하나의 axes에 두 개의 y축을 겹쳐서 서로 다른 단위의 데이터를 동시에 표시
#   → 왼쪽 y축: 리뷰 수(파랑) / 오른쪽 y축: 평균 감성 점수(주황)
# - 임베딩 관점: 너무 짧은 텍스트는 정보량 부족으로 임베딩 벡터의 표현력이 낮을 수 있음
# -----------------------------------------------------------------------------
df['length_bin'] = pd.cut(df['review_length'],
                           bins=[0, 120, 150, 200],
                           labels=['짧음(~120)', '보통(121~150)', '긺(151~)'])
length_counts = df['length_bin'].value_counts().sort_index()       # 구간별 리뷰 수
length_sentiment = df.groupby('length_bin', observed=True)['sentiment_score'].mean()  # 구간별 평균 감성 점수

x = np.arange(len(length_counts))  # x축 위치 배열 [0, 1, 2]
width = 0.35  # 막대 너비

# 왼쪽 y축: 리뷰 수 막대 (steelblue)
bars_count = axes[1].bar(x - width/2, length_counts.values, width,
                          label='리뷰 수', color='steelblue', alpha=0.8)
# 오른쪽 y축 생성: 평균 감성 점수 막대 (coral)
ax2_twin = axes[1].twinx()
bars_sent = ax2_twin.bar(x + width/2, length_sentiment.values, width,
                          label='평균 감성점수', color='coral', alpha=0.8)
axes[1].set_title('Q2. 텍스트 길이 구간별 분포\n(임베딩 품질 영향 분석)', fontsize=11)
axes[1].set_xticks(x)
axes[1].set_xticklabels(length_counts.index, fontsize=9)
axes[1].set_ylabel('리뷰 수', color='steelblue')
ax2_twin.set_ylabel('평균 감성 점수', color='coral')
# 두 y축의 범례를 하나로 합쳐서 표시
lines1, labels1 = axes[1].get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
axes[1].legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8)

print(f"\n[Q2] 텍스트 길이 구간별 리뷰 수:\n{length_counts}")
print(f"\n[Q2] 텍스트 길이 구간별 평균 감성 점수:\n{length_sentiment.round(4)}")

# -----------------------------------------------------------------------------
# Q3. category별로 감성 점수 평균에 차이가 존재하는가?
#
# - 카테고리별 평균(mean)은 모두 0.02~0.05로 차이가 매우 작고,
#   표준편차(std)는 약 0.6으로 평균의 20배 이상 → barplot + 오차막대 사용 시
#   막대 자체가 오차막대에 묻혀 거의 보이지 않는 가독성 문제 발생.
# - 해결: boxplot으로 교체하여 분포 전체(중앙값 / IQR / 최솟값~최댓값)를 보여줌.
#   평균값은 별도로 다이아몬드(◆) 마커로 overlay 표시.
# - 이 시각화로 '카테고리 간 차이가 작고 분포 폭이 넓다'는 사실을 직관적으로 전달.
# -----------------------------------------------------------------------------
cat_sentiment = df.groupby('category')['sentiment_score'].agg(['mean', 'std', 'count']).round(4)
print(f"\n[Q3] category별 감성 점수 통계:\n{cat_sentiment}")

# boxplot: 카테고리별 감성 점수 분포 전체를 시각화
sns.boxplot(data=df, x='category', y='sentiment_score',
            hue='category', palette='Set2', width=0.5,
            legend=False, ax=axes[2])

# 평균값을 다이아몬드 마커로 overlay
categories = cat_sentiment.index.tolist()
means = cat_sentiment['mean'].values
axes[2].scatter(range(len(categories)), means,
                marker='D', color='red', s=60, zorder=5, label='평균')

# 각 카테고리 평균값 수치 레이블 표시
for i, (cat, val) in enumerate(zip(categories, means)):
    axes[2].text(i, val + 0.04, f'{val:.3f}',
                 ha='center', va='bottom', fontsize=9, color='red', fontweight='bold')

# 전체 평균 기준선
axes[2].axhline(df['sentiment_score'].mean(), color='navy', linestyle='--',
                linewidth=1.5, label=f'전체 평균: {df["sentiment_score"].mean():.3f}')
axes[2].set_title('Q3. 카테고리별 감성 점수 분포\n(◆ = 평균, 박스 = IQR)', fontsize=11)
axes[2].set_xlabel('Category')
axes[2].set_ylabel('Sentiment Score')
axes[2].legend(fontsize=9)

plt.tight_layout()
plt.savefig('step3_ai_insight.png', dpi=150, bbox_inches='tight')
plt.show()
print("\n[그래프 저장] step3_ai_insight.png")

# =============================================================================
# 3줄 요약 Insight
# - 각 질문에 대한 분석 결론을 3줄로 요약하고, AI 활용 관점의 시사점 제시
# =============================================================================
print("\n" + "=" * 60)
print("[ 3줄 요약 Insight ]")
print("=" * 60)

corr_q1 = df['rating'].corr(df['sentiment_score'])  # Q1 최종 상관계수
best_cat = cat_sentiment['mean'].idxmax()            # Q3 감성 점수 최고 카테고리
worst_cat = cat_sentiment['mean'].idxmin()           # Q3 감성 점수 최저 카테고리

print(f"""
1. [Q1] 평점과 감성 점수의 상관계수는 {corr_q1:.3f}로, 뚜렷한 양의 상관관계가 없어
   감성 점수가 높다고 반드시 높은 평점으로 이어지지는 않음.
   → 텍스트 감성 분석 결과를 평점 예측에 그대로 사용하기 어려우므로 별도 보정 필요.

2. [Q2] 리뷰 텍스트 길이는 100~180자 범위에 집중되어 있으며, 길이 차이에 따른
   감성 점수 편차는 크지 않아 임베딩 품질에 미치는 직접적 영향은 제한적일 수 있음.
   → 단, 너무 짧은 리뷰(~120자)는 LLM 임베딩 시 정보량 부족으로 유사도 신뢰성이 낮을 수 있음.

3. [Q3] 카테고리별 평균 감성 점수에서 '{best_cat}'이 가장 높고 '{worst_cat}'이 가장 낮으나,
   표준편차가 크고 카테고리 간 차이가 통계적으로 유의미한지는 추가 검정이 필요함.
   → AI 추천 시 카테고리별 감성 기준선(baseline)을 다르게 설정하는 전략을 고려할 것.
""")

print("=" * 60)
print("분석 완료! 저장된 그래프:")
print("  - step1_distribution_outlier.png")
print("  - step2_statistics_visualization.png")
print("  - step3_ai_insight.png")
print("=" * 60)
