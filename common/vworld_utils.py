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
            "crs": "epsg:4326",
            "type": address_type,
            "address": address,
            "key": self.api_key
        }

        try:
            resp = requests.get(self.url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            if data.get("response", {}).get("status") != "OK":
                return 0.0, 0.0

            point = data["response"]["result"].get("point")
            if not point:
                return 0.0, 0.0

            lat = float(point["y"])
            lng = float(point["x"])
            return lat, lng

        except Exception as e:
            print(f"지오코딩 오류 ({address}): {e}")
            return 0.0, 0.0

    # 검증절차 처리
    def reverse_geocode(self, latitude: float, longitude: float, address_type: str = "PARCEL") -> dict:
        """
        위도/경도를 입력받아 해당 좌표의 행정구역 정보를 반환합니다.

        :param latitude: 위도
        :param longitude: 경도
        :param address_type: 주소 타입 ("PARCEL": 지번, "ROAD": 도로명)
        :return:
            {
                "sido": "경기도",
                "sigungu": "김포시",
                "dong": "운양동",
                "full_address": "경기도 김포시 운양동 ..."
            }
            실패 시 {}
        """
        if not latitude or not longitude:
            return {}

        params = {
            "service": "address",
            "request": "getAddress",
            "format": "json",
            "crs": "epsg:4326",
            "type": address_type,
            "point": f"{longitude},{latitude}",
            "key": self.api_key
        }

        try:
            resp = requests.get(self.url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            if data.get("response", {}).get("status") != "OK":
                return {}

            result_list = data.get("response", {}).get("result", [])
            if not result_list:
                return {}

            item = result_list[0]
            structure = item.get("structure", {})

            return {
                "sido": structure.get("level1", ""),
                "sigungu": structure.get("level2", ""),
                "dong": structure.get("level3", ""),
                "full_address": item.get("text", "")
            }

        except Exception as e:
            print(f"역지오코딩 오류 ({latitude}, {longitude}): {e}")
            return {}

    # 위.경도 지역검증
    def validate_location(self, address: str, latitude: float, longitude: float) -> tuple[bool, str]:
        """
        주소와 위경도가 동일 지역인지 검증

        :param address: 원본 주소 ("경기도 김포시 운양동")
        :param latitude: 위도
        :param longitude: 경도
        :return: (True/False, 메시지)
        """

        if not address or not latitude or not longitude:
            return False, "입력값 오류"

        # 1. 주소 파싱
        addr_parts = address.split()
        addr_sido = addr_parts[0] if len(addr_parts) > 0 else ""
        addr_sigungu = addr_parts[1] if len(addr_parts) > 1 else ""

        # 2. 좌표 → 행정구역
        region = self.reverse_geocode(latitude, longitude)

        if not region:
            return False, "역지오코딩 실패"

        print(f"시도: {region.get('sido')}")
        print(f"시군구: {region.get('sigungu')}")
        print(f"읍면동: {region.get('dong')}")
        print(f"전체주소: {region.get('full_address')}")
        print(f"")

        coord_sido = region.get("sido", "")
        coord_sigungu = region.get("sigungu", "")

        # 3. 검증
        if addr_sido != coord_sido:
            return False, f"시도 불일치 ({addr_sido} != {coord_sido})"

        if addr_sigungu and addr_sigungu != coord_sigungu:
            return False, f"시군구 불일치 ({addr_sigungu} != {coord_sigungu})"

        return True, "정상"

if __name__ == "__main__":
    API_KEY = MAP_API_KEY

    geo_service = VWorldGeocoding(API_KEY)

    test_address = "서울특별시 광진구 자양로 113"

    print("--- 주소 좌표 변환 테스트 시작 ---")
    print(f"입력 주소: {test_address}")

    latitude, longitude = geo_service.get_lat_lng(test_address, address_type="road")

    if latitude != 0.0 and longitude != 0.0:
        print("변환 성공!")
        print(f"위도(Latitude): {latitude}")
        print(f"경도(Longitude): {longitude}")

        print("\n--- 주소 vs 좌표 검증 테스트 ---")

        is_valid, message = geo_service.validate_location(
            test_address,
            latitude,
            longitude
        )

        print(f"검증 결과: {is_valid}")
        print(f"메시지: {message}")

    else:
        print("변환 실패: API 키를 확인하거나 주소가 올바른지 확인하세요.")