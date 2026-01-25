#매매가·전세가, 매매지수·전세지수를 바탕으로 전세가율, 지수비율 등을 계산하고 투자 판단을 도와주는 자동화 파이썬 코드입니다:

def analyze_apartment(market_data):
    """
    KB지수 및 실거래 기반 아파트 투자 분석

    market_data: dict {
        'location': str,
        'area_m2': float,
        'price_sale': float,      # 매매가 (억)
        'price_lease': float,     # 전세가 (억)
        'index_sale': float,      # 매매지수
        'index_lease': float      # 전세지수
    }
    """

    # 전세가율
    lease_rate = market_data['price_lease'] / market_data['price_sale'] * 100

    # 지수 비율
    index_ratio = market_data['index_sale'] / market_data['index_lease']

    # 갭 투자 가능 자본
    gap_amount = market_data['price_sale'] - market_data['price_lease']

    print("📍 지역:", market_data['location'])
    print("🏠 면적: {:.1f}㎡".format(market_data['area_m2']))
    print("💰 매매가: {:.2f}억 / 전세가: {:.2f}억".format(
        market_data['price_sale'], market_data['price_lease']))
    print("📊 매매지수: {:.3f} / 전세지수: {:.3f}".format(
        market_data['index_sale'], market_data['index_lease']))
    print("🧮 전세가율: {:.1f}%".format(lease_rate))
    print("📐 매매/전세 지수 비율: {:.3f}".format(index_ratio))
    print("💸 갭투자 자본 필요액: {:.2f}억".format(gap_amount))

    print("\n🔍 투자 해석:")
    if lease_rate >= 80:
        print("- 전세가율이 높음 → 매매가 저평가 또는 전세가 과열")
    elif lease_rate <= 60:
        print("- 전세가율이 낮음 → 매매가 고평가 가능성")
    else:
        print("- 전세가율이 평균 수준")

    if index_ratio < 1:
        print("- 매매지수가 전세지수보다 낮음 → 매매 상대적 저평가")
    elif index_ratio > 1.1:
        print("- 매매지수가 높음 → 매매가 고평가 가능성")

    if gap_amount <= 0.3:
        print("- 소액(3천만 이하) 갭투자 진입 가능")
    else:
        print("- 초기 자본이 비교적 많이 필요함")

# 예시 사용
apartment_data = {
    'location': '충북 청주시 서원구',
    'area_m2': 59.0,
    'price_sale': 1.4,
    'price_lease': 1.2,
    'index_sale': 93.158,
    'index_lease': 95.77
}

analyze_apartment(apartment_data)
