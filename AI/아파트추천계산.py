import pandas as pd
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

# 1. 지역 및 단지명 인코딩용 샘플 데이터
data = pd.DataFrame({
    '지역': ['서울', '서울', '부산', '부산', '대구', '대구', '서울', '서울', '부산', '대구'],
    '단지명': ['A단지', 'B단지', 'C단지', 'C단지', 'D단지', 'D단지', 'A단지', 'B단지', 'C단지', 'D단지'],
})

le_region = LabelEncoder()
le_complex = LabelEncoder()
data['지역_encoded'] = le_region.fit_transform(data['지역'])
data['단지명_encoded'] = le_complex.fit_transform(data['단지명'])

# 2. 소득수준 데이터 (뒤에서부터 최신년도 = 2024)
# 연도별 평균 소득수준 (단위: 천 원)
income_by_year = {
    2024: 8511,
    2023: 8165,
    2022: 8065
}

# 연도-월별 금리 데이터 (단위: %)
rate_by_month = {
    '2025-05': 3.1,
    '2025-01': 3.5
}

# 지역별 공급량 데이터 (단위: 세대)
supply_by_region = {
    '서울': 0,
    '부산': 180,
    '대구': 150,
    # 기타 지역은 기본값 0 처리
}

# 지역별 매매지수 데이터 (단위: 지수)
price_index_by_region = {
    '서울': 95,
    '부산': 98,
    '대구': 90,
    # 기타 지역은 기본값 100 처리
}

# 지역별 인구수 (단위: 만 명)
population_by_region = {
    '서울': 35,
    '부산': 340,
    '대구': 242,
    # 기타 지역은 0으로 처리
}

# 2. 소득수준
latest_year = max(income_by_year.keys())
income_selected = income_by_year[latest_year]

# 지역 공급량 자동 선택
le_region = data.loc[0, '지역']
le_complex = data.loc[0, '단지명']
region_supply = supply_by_region.get(le_region, 0)

# 지역 매매지수 자동 선택
price_index_selected = price_index_by_region.get(le_region, 100)

# 금리 자동 선택 (가장 최근 값 = 최종금리)
latest_rate = max(rate_by_month.keys())
rate_selected = rate_by_month[latest_rate]

# 지역 인구 수
region_population = population_by_region.get(le_region, 0)

# 4. 예측 대상 입력값 + 소득수준 반영
new_row = {
    '지역': le_region,
    '단지명': le_complex,
    '매매가': 1.85,
    '전세가': 1.65,
    '매매지수': price_index_selected,
    '소득수준': income_selected,
    '공급량': region_supply,
    '금리': rate_selected,
    '평형': 84
}

# 5. 지표 계산
# new_row['소득수준'] = income_selected
new_row['PIR'] = new_row['매매가'] * 10000 / new_row['소득수준']
new_row['전세가율'] = new_row['전세가'] / new_row['매매가'] * 100

# 6. 해석 기준
pir = new_row['PIR']
jeonse_ratio = new_row['전세가율']
rate = new_row['금리']
supply = new_row['공급량']
price_index = new_row['매매지수']
# 매매가, 전세가, 평형 값을 new_row에서 추출
sale_price = new_row['매매가']
rent_price = new_row['전세가']
area_size = new_row['평형']


if pir <= 5:
    pir_judgement = "저PIR (매수 가능성 ↑)"
elif pir <= 8:
    pir_judgement = "중간 PIR (신중 접근)"
else:
    pir_judgement = "고PIR (매수 부담 ↑, 매도 가능성 ↑)"

if jeonse_ratio >= 90:
    jeonse_judgement = "전세가율 높음 (매수 유리)"
elif jeonse_ratio >= 70:
    jeonse_judgement = "전세가율 중간 (보통 수준)"
else:
    jeonse_judgement = "전세가율 낮음 (매수 신중)"

if rate < 3.5:
    rate_judgement = "저금리 (매수 유리)"
elif rate <= 4.5:
    rate_judgement = "중간금리 (주의)"
else:
    rate_judgement = "고금리 (매도 유리)"

if supply < 150:
    supply_judgement = "공급 적음 (매수 유리)"
elif supply <= 220:
    supply_judgement = "공급 중간 (보통)"
else:
    supply_judgement = "공급 과잉 (매도 고려)"

if price_index >= 105:
    index_judgement = "매매지수 높음 (시장 과열, 매도 유리)"
elif price_index >= 100:
    index_judgement = "매매지수 보통 (안정적)"
elif price_index < 95:
    index_judgement = "매매지수 낮음 (시장 침체, 매수 유리)"
else:
    index_judgement = "매매지수 다소 낮음 (관망)"

# 7. 점수화 판단
buy_score = 0
sell_score = 0

if pir <= 6: buy_score += 1
else: sell_score += 1

if jeonse_ratio >= 90: buy_score += 1
elif jeonse_ratio < 70: sell_score += 1

if rate > 4.5: sell_score += 1
elif rate < 3.5: buy_score += 1

if supply >= 220: sell_score += 1
elif supply < 150: buy_score += 1

if price_index >= 105: sell_score += 1
elif price_index < 95: buy_score += 1

# 인구 기준 반영
if region_population >= 30:
    population_judgement = "인구 30만 이상 (시장 안정성 ↑)"
    buy_score += 1
else:
    population_judgement = "인구 부족 (유동성 낮음)"
    sell_score += 1

# 최종 판단
if buy_score > sell_score:
    final_judgement = "매수 추천"
elif sell_score > buy_score:
    final_judgement = "매도 추천"
else:
    final_judgement = "중립 (신중 판단 필요)"

# 8. 결과 출력
print("📊 예측 요약")
print(f"- 지역: {le_region} {le_complex}")
print(f"- 매매가: {sale_price}억원, 전세가: {rent_price}억원, 평형: {area_size}㎡")
print(f"- 연도소득기준: {latest_year}년 {income_selected}만원")
print(f"- PIR: {pir:.2f} → {pir_judgement}")
print(f"- 전세가율: {jeonse_ratio:.1f}% → {jeonse_judgement}")
print(f"- 금리: {rate:.2f}% → {rate_judgement}")
print(f"- 공급량: {supply}세대 → {supply_judgement}")
print(f"- 매매지수: {price_index} → {index_judgement}")
print(f"- 지역 인구: {region_population}만명 → {population_judgement}")
print(f"\n✅ 최종 판단: {final_judgement}")

# 갭투자금액 산정
if final_judgement == "매수 추천":
    gap_investment = (sale_price - rent_price) * 10000  # 단위: 만 원
    print(f"💰 예상 갭투자금: {gap_investment:.0f}만원")