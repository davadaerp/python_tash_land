import os
import json
import re
import requests

from config import MAP_API_KEY


class VWorldGeocoding:
    """
    VWorld 지오코딩 API를 사용한 위경도 추출 공통 유틸리티
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.vworld.kr/req/address"

        # region_codes.json은 서비스 생성 시 1회만 로딩
        self.region_codes = self.load_region_codes()

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
    def validate_location(
        self,
        address: str,
        latitude: float,
        longitude: float
    ) -> tuple[bool, str]:
        """
        주소와 위경도가 동일 지역인지 검증
        region_codes.json 기준으로 원본 주소의 시도/시군구를 추출 후
        VWorld 역지오코딩 결과와 비교
        """

        if not address or not latitude or not longitude:
            return False, "입력값 오류"

        # 1. region_codes.json 로딩
        # 1. 서비스 생성 시 로딩된 region_codes 사용
        if not self.region_codes:
            return False, "region_codes.json 로딩 실패"

        region_codes = self.region_codes

        # 2. 원본 주소를 json 기준으로 파싱
        src_region = self.parse_address_region_by_json(address, region_codes)

        addr_sido = src_region.get("sido_name", "")
        addr_sigungu = src_region.get("sigungu_name", "")

        print("===== [validate_location] 원본주소 파싱 =====")
        print(f"주소: {address}")
        print(f"시도: {addr_sido}")
        print(f"시군구: {addr_sigungu}")

        if not addr_sido:
            return False, f"원본 주소 시도 파싱 실패: {address}"

        if not addr_sigungu:
            return False, f"원본 주소 시군구 파싱 실패: {address}"

        # 3. 좌표 → 행정구역
        region = self.reverse_geocode(latitude, longitude)

        if not region:
            return False, "역지오코딩 실패"

        coord_sido = self.normalize_sido_name(region.get("sido", ""), region_codes)
        coord_sigungu = self.normalize_sigungu_for_compare(region.get("sigungu", ""))

        print("===== [validate_location] 좌표주소 파싱 =====")
        print(f"시도: {coord_sido}")
        print(f"시군구: {coord_sigungu}")
        print(f"읍면동: {region.get('dong')}")
        print(f"전체주소: {region.get('full_address')}")

        # 4. 시도 검증
        if addr_sido != coord_sido:
            return False, f"시도 불일치 ({addr_sido} != {coord_sido})"

        # 5. 시군구 검증
        # 원본: 수원시 권선구 / 좌표: 수원시 권선구 → 정상
        # 원본: 수원시 권선구 / 좌표: 권선구 → 부분 포함도 정상 처리
        if addr_sigungu != coord_sigungu:
            if addr_sigungu not in coord_sigungu and coord_sigungu not in addr_sigungu:
                return False, f"시군구 불일치 ({addr_sigungu} != {coord_sigungu})"

        return True, "정상"

    # region_codes.json 로딩 및 주소 파싱
    def load_region_codes(self) -> list:
        """
        현재 py 파일 기준 디렉토리에서 region_codes.json 로딩
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(base_dir, "region_codes.json")

            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)

        except Exception as e:
            print(f"[VWorldGeocoding] region_codes.json 로딩 실패: {e}")
            return []


    def normalize_sido_name(self, sido_name: str, region_codes: list) -> str:
        """
        서울/서울특별시, 경기/경기도 같은 시도 약칭/정식명칭을 정규화
        """
        if not sido_name:
            return ""

        sido_name = sido_name.strip()

        for region in region_codes:
            names = [
                x.strip()
                for x in str(region.get("시도 이름", "")).split(",")
                if x.strip()
            ]

            if sido_name in names:
                return names[-1]

        return sido_name

    # region_codes.json 기준으로 시도/시군구 추출
    def parse_address_region_by_json(self, address: str, region_codes: list) -> dict:
        """
        원본 주소에서 region_codes.json 기준으로 시도/시군구를 추출

        개선 포인트:
        1. 시도만 단독 매칭하지 않음
        2. 시도 후보 + 해당 시도 하위 시군구 조합으로 우선 매칭
        3. 예: '경기 광주시'는 '경기도 + 광주시'로 정확히 매칭
        4. '광주'라는 단어만 보고 '광주광역시'로 오인하는 문제 방지
        """
        result = {
            "sido_code": "",
            "sido_name": "",
            "sido_aliases": [],
            "sigungu_code": "",
            "sigungu_name": "",
        }

        if not address or not region_codes:
            return result

        # 공백 정리
        clean_address = re.sub(r"\s+", " ", address).strip()

        matched_candidates = []

        for region in region_codes:
            sido_names = [
                x.strip()
                for x in str(region.get("시도 이름", "")).split(",")
                if x.strip()
            ]

            if not sido_names:
                continue

            # 정식 시도명은 region_codes.json의 마지막 alias를 사용
            # 예: "부산특별시,부산광역시,부산" 같은 경우 가장 긴 이름을 쓰면
            #     부산특별시가 잡힐 수 있으므로 마지막 값을 기준으로 사용
            official_sido_name = sido_names[-1]

            cities = region.get("시군구", [])

            for sido_alias in sido_names:
                if not sido_alias:
                    continue

                # 주소 안에 해당 시도명이 없으면 이 region은 후보 제외
                if sido_alias not in clean_address:
                    continue

                for city in cities:
                    city_name = str(city.get("시군구 이름", "")).strip()

                    if not city_name:
                        continue

                    # 시군구까지 같이 들어있는 경우만 강한 후보로 인정
                    if city_name in clean_address:
                        matched_candidates.append({
                            "sido_code": str(region.get("시도 코드", "")),
                            "sido_name": official_sido_name,
                            "sido_aliases": sido_names,
                            "sigungu_code": str(city.get("시군구 코드", "")),
                            "sigungu_name": city_name,
                            "score": len(sido_alias) + len(city_name),
                        })

        # 1순위: 시도 + 시군구 조합이 같이 매칭된 후보
        if matched_candidates:
            best = sorted(
                matched_candidates,
                key=lambda x: x.get("score", 0),
                reverse=True
            )[0]

            result["sido_code"] = best["sido_code"]
            result["sido_name"] = best["sido_name"]
            result["sido_aliases"] = best["sido_aliases"]
            result["sigungu_code"] = best["sigungu_code"]
            result["sigungu_name"] = best["sigungu_name"]

            return result

        # 2순위: 그래도 못 찾으면 기존처럼 시도만 매칭
        # 단, 긴 alias 우선으로 처리
        sido_only_candidates = []

        for region in region_codes:
            sido_names = [
                x.strip()
                for x in str(region.get("시도 이름", "")).split(",")
                if x.strip()
            ]

            if not sido_names:
                continue

            official_sido_name = sorted(sido_names, key=len, reverse=True)[0]

            for sido_alias in sido_names:
                if sido_alias and sido_alias in clean_address:
                    sido_only_candidates.append({
                        "sido_code": str(region.get("시도 코드", "")),
                        "sido_name": official_sido_name,
                        "sido_aliases": sido_names,
                        "score": len(sido_alias),
                        "region": region,
                    })

        if not sido_only_candidates:
            return result

        best_sido = sorted(
            sido_only_candidates,
            key=lambda x: x.get("score", 0),
            reverse=True
        )[0]

        result["sido_code"] = best_sido["sido_code"]
        result["sido_name"] = best_sido["sido_name"]
        result["sido_aliases"] = best_sido["sido_aliases"]

        # 시도만 찾은 뒤, 해당 시도 내부 시군구만 재검색
        cities = sorted(
            best_sido["region"].get("시군구", []),
            key=lambda x: len(str(x.get("시군구 이름", ""))),
            reverse=True
        )

        for city in cities:
            city_name = str(city.get("시군구 이름", "")).strip()

            if city_name and city_name in clean_address:
                result["sigungu_code"] = str(city.get("시군구 코드", ""))
                result["sigungu_name"] = city_name
                break

        return result

    def normalize_sigungu_for_compare(self, sigungu_name: str) -> str:
        """
        VWorld 역지오코딩 시군구와 원본 주소 시군구 비교용 정규화
        예: 수원시 권선구 / 권선구 비교 보완
        """
        if not sigungu_name:
            return ""

        sigungu_name = re.sub(r"\s+", " ", sigungu_name).strip()
        return sigungu_name


if __name__ == "__main__":
    #
    geo_service = VWorldGeocoding(MAP_API_KEY)

    test_address = "경기 용인시 처인구 양지면 남곡리 340-1"

    print("--- 주소 좌표 변환 테스트 시작 ---")
    print(f"입력 주소: {test_address}")

    # 1차: 도로명주소 road
    print("\n[1차] road 주소 타입으로 조회")
    latitude, longitude = geo_service.get_lat_lng(test_address, address_type="road")

    # 2차: 실패 시 지번주소 parcel
    if latitude == 0.0 or longitude == 0.0:
        print("⚠️ road 조회 실패 → 2차 parcel 재시도")
        latitude, longitude = geo_service.get_lat_lng(test_address, address_type="parcel")

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