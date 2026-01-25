# 국토교통부 디지털트윈국토 사이트에서 인증키를 발급받아야 함
# https://www.vworld.kr/dev/v4dv_geocoderguide2_s001.do
# 간편인증, 개발키 받음.
# 요청URL을 전송하면 지오코딩 서비스를 사용하실 수 있으며 일일 지오코딩 요청건수는 최대 40,000건 입니다.

import requests

# 발급받은 API Key
MAP_API_KEY = "644F5AF8-9BF1-39DE-A097-22CACA23352F"

def geocode_vworld(address: str) -> tuple[float, float]:
    """
    vWorld 지오코딩 API를 호출해 도로명 주소의 위도/경도 좌표를 반환합니다.
    :param address: 조회할 도로명 주소 문자열
    :return: (latitude, longitude)
    :raises Exception: API 오류 또는 좌표 미발견 시
    """
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",        # 좌표 변환 요청
        "format": "json",             # JSON 응답
        "crs": "epsg:4326",           # WGS84 좌표계
        "type": "parcel",               # road: 도로명, parcel: 지번
        "address": address,
        "key": MAP_API_KEY
    }

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()

    data = resp.json()
    # 응답 구조: data["response"]["status"] == "OK" 인지 확인
    if data.get("response", {}).get("status") != "OK":
        #raise Exception(f"API error: {data.get('response', {}).get('error', 'Unknown error')}")
        return 0.0, 0.0

    # 좌표는 data["response"]["result"]["point"]["y"], ["x"]
    result = data["response"]["result"]
    point  = result.get("point")
    if not point or "x" not in point or "y" not in point:
        #raise Exception("좌표를 찾을 수 없습니다.")
        return 0.0, 0.0

    lat = float(point["y"])
    lng = float(point["x"])
    return lat, lng

if __name__ == "__main__":
    # 테스트
    # 1) 테스트용 주소 리스트
    addresses = [
        { "type": "real",    "address": "경기 김포시 운양동 0111-3",                         "date": "2025-06-04", "year": 2010, "floor": "3층", "area": "13.36평", "price": "158,000,000원" },
        { "type": "real",    "address": "경기 김포시 운양동 1435-1",                         "date": "2025-06-04", "year": 2012, "floor": "5층", "area": "17.01평", "price": "195,000,000원" },
        { "type": "real",    "address": "경기 김포시 운양동 1297-7",                         "date": "2025-06-04", "year": 2008, "floor": "2층", "area": "11.63평", "price": "130,000,000원" },
        { "type": "real",    "address": "경기 김포시 운양동 1306-6",                         "date": "2025-04-04", "year": 2015, "floor": "3층", "area": "30.63평", "price": "470,000,000원" },
        { "type": "real",    "address": "경기 김포시 운양동 1288-1",                         "date": "2025-05-04", "year": 2008, "floor": "1층", "area": "11.63평", "price": "170,000,000원" },
        { "type": "auction", "address": "경기 김포시 운양동 1307-5, 1층114호 (운양동,에이치씨티)", "date": "2024-12-04", "year": 2009, "floor": "1층", "area": "15.16평", "price": "120,000,000원" },
        { "type": "auction", "address": "경기 김포시 운양동 1307-4, 2층210호 (운양동,그랜드타워)", "date": "2024-12-04", "year": 2011, "floor": "2층", "area": "14.49평", "price": "135,000,000원" },
        { "type": "auction", "address": "경기 김포시 운양동 1298-3, 1층107호 (운양동,김포헤리움타운)", "date": "2024-12-04", "year": 2013, "floor": "1층", "area": "12.70평", "price": "110,000,000원" }
    ]

    # 2) 각 주소에 대해 geocode 수행
    for item in addresses:
        addr = item["address"]
        try:
            lat, lng = geocode_vworld(addr)
            print(f"[{item['type']}] {addr} → 위도: {lat:.6f}, 경도: {lng:.6f}")
        except Exception as e:
            print(f"[ERROR] {addr} → {e}")