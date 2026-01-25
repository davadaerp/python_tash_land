import requests

from config import MAP_API_KEY, VWORLD_URL

# [설정] API 및 기본 정보
def get_lat_lng(address: str) -> tuple[float, float]:
    """
    단일 주소를 입력받아 위도, 경도를 반환하는 핵심 로직 함수
    """
    params = {
        "service": "address",
        "request": "getcoord",
        "format": "json",
        "crs": "epsg:4326",
        "type": "parcel",  # road: 도로명, parcel: 지번
        "address": address,
        "key": MAP_API_KEY
    }

    try:
        response = requests.get(VWORLD_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("response", {}).get("status") == "OK":
            point = data["response"]["result"]["point"]
            return float(point["y"]), float(point["x"])

    except Exception as e:
        print(f"[Error] {address}: {e}")

    return 0.0, 0.0


def process_address_list(addresses: list):
    """
    주소 리스트를 순회하며 좌표를 출력하고 결과를 리스트로 반환하는 메인 로직 함수
    """
    results = []

    print(f"{'No':<3} | {'주소':<25} | {'위도':^12} | {'경도':^12}")
    print("-" * 70)

    for idx, addr in enumerate(addresses, 1):
        lat, lng = get_lat_lng(addr)
        results.append({"address": addr, "lat": lat, "lng": lng})

        # 결과 출력 (좌표가 없을 경우 분기 처리)
        if lat == 0.0:
            coord_str = "검색 실패"
            print(f"{idx:<3} | {addr:<25} | {coord_str}")
        else:
            print(f"{idx:<3} | {addr:<25} | {lat:<12.7f} | {lng:<12.7f}")

    return results


def check_vworld_api() -> bool:
    """
        vWorld 지오코딩 API를 호출합니다.
        'road'(도로명)로 먼저 시도하고, 실패 시 'parcel'(지번)로 재시도합니다.
    """
    url = "https://api.vworld.kr/req/address"
    test_address = "경기도 김포시 운양동 1340-7"
    #api_key = "644F5AF8-9BF1-39DE-A097-22CACA23352F"  # 사용자님의 키
    api_key = MAP_API_KEY  # config.py에 설정된 키 사용
    params = {
        "service": "address",
        "request": "getcoord",
        "format": "json",
        "crs": "epsg:4326",
        "type": "parcel",  # road: 도로명, parcel: 지번
        "address": test_address,
        "key": api_key
    }

    print(f"--- API 호출 테스트 시작 ---")
    try:
        response = requests.get(url, params=params, timeout=10)

        # 1. HTTP 연결 상태 확인 (200 OK 여부)
        print(f"1. HTTP 상태 코드: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            status = data.get("response", {}).get("status")

            # 2. vWorld 서비스 로직 상태 확인
            if status == "OK":
                print("2. 결과: 성공! API가 정상 동작 중입니다.")
                point = data["response"]["result"]["point"]
                print(f"   위도: {point['y']}, 경도: {point['x']}")
                return True
            else:
                error_msg = data.get("response", {}).get("error", "알 수 없는 에러")
                print(f"2. 결과: 실패 (vWorld 에러)")
                print(f"   에러 상태: {status}")
                print(f"   에러 내용: {error_msg}")
        else:
            print("1. 결과: 서버 연결 실패 (URL을 확인하거나 서버 점검 중일 수 있습니다.)")

    except requests.exceptions.RequestException as e:
        print(f"연결 오류 발생: {e}")

    return False

# [실행] 프로그램 시작점
if __name__ == "__main__":
    # 1. API 상태 체크 시도 (성공할 경우에만 내부 블록 실행)
    if check_vworld_api():
        print("\nAPI 체크 성공! 주소 변환 작업을 시작합니다...")

        # 2. 대상 주소 데이터 배열
        sample_addresses = [
            "경기도 김포시 운양동 1340-7",
            "서울특별시 중구 을지로2가 199-4",
            "부산광역시 연제구 연산동 1445-5"
        ]

        # 3. 프로세스 실행
        final_data = process_address_list(sample_addresses)

        # 4. 결과 보고
        print("\n" + "=" * 75)
        print(f"작업 완료: 총 {len(final_data)}건 처리되었습니다.")
    else:
        print("\n⚠ API 상태가 비정상적이므로 주소 변환 작업을 중단합니다.")