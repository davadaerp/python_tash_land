import requests

# 발급받은 API Key
API_KEY = "여기에_발급받은_API_KEY_입력"

def reverse_geocode_vworld(x: float, y: float) -> tuple[str, str]:
    """
    vWorld 역 지오코딩 API를 호출해 주어진 좌표의 지번주소와 도로명주소를 반환합니다.
    :param x: 경도 (EPSG:900913 기준)
    :param y: 위도 (EPSG:900913 기준)
    :return: (jibun_address, road_address)
    :raises Exception: API 오류 또는 결과 미발견 시
    """
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "version": "2.0",
        "request": "getaddress",   # 역 지오코딩 요청
        "format": "json",
        "type": "both",            # both: 지번 + 도로명
        "crs": "epsg:900913",      # vWorld 지도 내부 좌표계
        "point": f"{x},{y}",
        "key": API_KEY
    }

    resp = requests.get(url, params=params, timeout=5)
    resp.raise_for_status()
    data = resp.json()

    # 응답 상태 확인
    rsp = data.get("response", {})
    if rsp.get("status") != "OK":
        err = rsp.get("error") or "Unknown error"
        raise Exception(f"vWorld reverse geocode error: {err}")

    results = rsp.get("result", [])
    jibun_addr = ""
    road_addr  = ""

    # result 배열의 순서: 0=지번, 1=도로명 (서버 설정에 따라 다를 수 있으니 확인 필요)
    for entry in results:
        text = entry.get("text", "")
        if entry.get("structure", {}).get("type") == "parcel" or jibun_addr == "":
            # 지번주소
            jibun_addr = text
        else:
            # 도로명주소
            road_addr = text

    return jibun_addr, road_addr


if __name__ == "__main__":
    # 예제 좌표 (서울시청 바로 위경도, EPSG:900913)
    test_x, test_y = 14146386.27, 4526001.58

    try:
        jibun, road = reverse_geocode_vworld(test_x, test_y)
        print(f"지번주소: {jibun}")
        print(f"도로명주소: {road}")
    except Exception as e:
        print("역지오코딩 오류:", e)
