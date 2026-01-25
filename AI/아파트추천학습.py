import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# 1. 지역/단지명 포함 샘플 데이터 생성
data = pd.DataFrame({
    '지역':   ['서울', '서울', '부산', '부산', '대구', '대구', '서울', '서울', '부산', '대구'],
    '단지명': ['A단지', 'B단지', 'C단지', 'C단지', 'D단지', 'D단지', 'A단지', 'B단지', 'C단지', 'D단지'],
    '매매가':    [1.2, 1.4, 1.6, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.2],
    '전세가':    [1.0, 1.2, 1.3, 1.4, 1.5, 1.5, 1.8, 2.0, 2.1, 2.2],
    '매매지수': [90, 92, 95, 97, 98, 100, 102, 105, 107, 110],
    '소득수준': [2500, 2600, 2700, 2800, 3000, 3200, 3400, 3600, 3700, 4000],
    '공급량':   [100, 120, 150, 180, 200, 250, 230, 210, 180, 160],
    '금리':     [3.0, 3.0, 3.2, 3.5, 3.7, 4.0, 4.2, 4.3, 4.5, 4.8],
    '평형':     [59, 59, 59, 84, 84, 84, 84, 84, 101, 101],
    '타이밍':   ['매수', '매수', '매수', '매도', '매도', '매도', '매도', '매도', '매도', '매도']
})

# 2. PIR 계산
data['PIR'] = data['매매가'] * 10000 / data['소득수준']  # 단위 맞춤

# 3. Label Encoding
le_region = LabelEncoder()
le_complex = LabelEncoder()
data['지역'] = le_region.fit_transform(data['지역'])
data['단지명'] = le_complex.fit_transform(data['단지명'])

# 4. 학습 데이터 구성
X = data[['지역', '단지명', '매매가', '전세가', '매매지수', '소득수준', '공급량', '금리', '평형', 'PIR']]
y = data['타이밍']

# 5. 학습/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 6. 모델 학습
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# 7. 테스트 결과 출력
y_pred = model.predict(X_test)
print("=== 테스트 결과 ===")
print(classification_report(y_test, y_pred))

# 8. 새로운 단지 예측
new_row = {
    '지역': le_region.transform(['서울'])[0],
    '단지명': le_complex.transform(['A단지'])[0],
    '매매가': 2.1,
    '전세가': 1.9,
    '매매지수': 90,
    '소득수준': 8000,
    '공급량': 0,
    '금리': 3.1,
    '평형': 84
}
new_row['PIR'] = new_row['매매가'] * 10000 / new_row['소득수준']
pir_value = new_row['PIR']

# 9. PIR 해석 기준
if pir_value <= 5:
    pir_judgement = "저PIR (매수 가능성 ↑)"
elif pir_value <= 8:
    pir_judgement = "중간 PIR (신중 접근)"
else:
    pir_judgement = "고PIR (매수 부담 ↑, 매도 가능성 ↑)"

# 10. 예측
new_apartment = pd.DataFrame([new_row])
prediction = model.predict(new_apartment)[0]

# 11. 결과 출력
print("\n==")
print(f"▶️ 타이밍 추천: {prediction}")
print(f"🔢 PIR 값: {pir_value:.2f}")
print(f"📌 PIR 해석: {pir_judgement}")
print(f"📊 해석: PIR이 {pir_value:.2f}이므로 '{pir_judgement}'입니다. 예측된 행동은 '{prediction}'입니다.")
