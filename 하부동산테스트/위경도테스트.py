import requests

def get_lat_lng(address: str, api_key: str):
    print(f"주소: {address}")
    # Geocoding API URL 생성
    # (google api 사용은 하루에 2,500건, 초당 10건의 요청에 한해서만 무료입니다. 그 이상 사용하려면 유료로 전환해야 합니다.)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

    # API 요청 보내기
    response = requests.get(url)
    data = response.json()

    # 결과 확인 및 위도, 경도 반환
    if data['status'] == 'OK':
        lat = data['results'][0]['geometry']['location']['lat']
        lng = data['results'][0]['geometry']['location']['lng']
        return lat, lng
    else:
        print(f"Geocoding API 요청 오류: {data['status']}")
        return 0, 0

if __name__ == "__main__":
    # 예시 주소
    address = "충북 청주시 흥덕구 복대동 3379, 105동 45층 4504호 (복대동,신영지웰시티1차)"
    # 실제 API 키로 교체하세요.
    api_key = "AIzaSyBzacpsf9Cw3CRRqWXUHbHkRDNbYlaXGCI"

    # 위도와 경도 가져오기
    lat, lng = get_lat_lng(address, api_key)

    print("====================================")
    print(f"주소: {address}")
    print(f"위도: {lat}")
    print(f"경도: {lng}")
