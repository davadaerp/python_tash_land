import requests

from config import MAP_API_KEY

class VWorldGeocoding:
    """
    VWorld 지오코딩 API를 사용한 위경도 추출 공통 유틸리티
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.vworld.kr/req/address"

    def get_lat_lng(self, address: str, address_type: str = "parcel") -> tuple[float, float]:
        """
        주소를 입력받아 위도/경도 좌표를 반환합니다.

        :param address: 조회할 주소 문자열
        :param address_type: 주소 타입 ("parcel": 지번 [기본값], "road": 도로명)
        :return: (latitude, longitude) - 실패 시 (0.0, 0.0)
        """
        if not address:
            return 0.0, 0.0

        params = {
            "service": "address",
            "request": "getcoord",
            "format": "json",
            "crs": "epsg:4326",  # WGS84 좌표계
            "type": address_type,  # parcel 또는 road
            "address": address,
            "key": self.api_key
        }

        try:
            resp = requests.get(self.url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # 응답 상태 확인
            if data.get("response", {}).get("status") != "OK":
                return 0.0, 0.0

            # 좌표 추출
            point = data["response"]["result"].get("point")
            if not point:
                return 0.0, 0.0

            lat = float(point["y"])
            lng = float(point["x"])
            return lat, lng

        except Exception as e:
            print(f"지오코딩 오류 ({address}): {e}")
            return 0.0, 0.0

    # ==== 테스트를 위한 메인 코드 추가 ====


if __name__ == "__main__":
    # 1. 발급받은 VWorld API 키를 입력하세요.
    API_KEY = MAP_API_KEY

    # 2. 유틸리티 인스턴스 생성
    geo_service = VWorldGeocoding(API_KEY)

    # 3. 테스트할 주소 설정
    test_address = "서울특별시 광진구 자양로 113"

    print(f"--- 주소 좌표 변환 테스트 시작 ---")
    print(f"입력 주소: {test_address}")

    # 4. 위경도 추출 (도로명 주소이므로 address_type="road" 설정)
    latitude, longitude = geo_service.get_lat_lng(test_address, address_type="road")

    # 5. 결과 출력
    if latitude != 0.0 and longitude != 0.0:
        print(f"변환 성공!")
        print(f"위도(Latitude): {latitude}")
        print(f"경도(Longitude): {longitude}")
    else:
        print("변환 실패: API 키를 확인하거나 주소가 올바른지 확인하세요.")