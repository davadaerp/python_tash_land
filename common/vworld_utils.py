import requests


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