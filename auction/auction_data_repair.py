# ============================================================
# 경매 데이터 위/경도 재처리
#
# 기능:
#   1. DB에서 latitude/longitude가 0인 자료 조회
#   2. 기존 crawling 방식(address1 + parcel)으로 먼저 조회
#   3. 실패한 경우에만 auction_geocode_utils 추가 보완조회
#   4. 성공하면 case_number 기준 latitude/longitude만 UPDATE
# ============================================================
import time as time_module
from datetime import datetime, time

from common.vworld_utils import VWorldGeocoding
from config import MAP_API_KEY

from auction_db_utils import (
    auction_read_no_latlng,
    auction_update_latlng_by_case_number
)

from auction_geocode_utils import (
    is_valid_latlng,
    retry_geocode_failed_address
)


# ============================================================
# 한 건 위경도 조회
# ============================================================
def geocode_auction_row(row, geocoder):
    """
    auction_crawling.py와 동일한 순서로 위/경도를 조회한다.

    1. 기존 성공 로직 유지:
       address1 전체를 parcel로 먼저 조회

    2. 기존 조회가 실패(0,0 등)한 경우에만:
       auction_geocode_utils.retry_geocode_failed_address() 호출

    3. 최종 성공하면 결과 dict 반환
       최종 실패하면 None 반환
    """

    case_number = row.get(
        "case_number",
        ""
    )

    address1 = (
        row.get("address1", "")
        or ""
    )

    address2 = (
        row.get("address2", "")
        or ""
    )

    latitude = "0"
    longitude = "0"

    # --------------------------------------------------------
    # 1. 기존 크롤링 성공 로직 그대로 재실행
    # --------------------------------------------------------
    try:

        print(
            f"[기존조회] "
            f"case_number={case_number} / "
            f"address1={address1} / "
            f"type=parcel"
        )

        latitude, longitude = geocoder.get_lat_lng(
            address1,
            "parcel"
        )

        print(
            f"[기존조회 결과] "
            f"lat={latitude}, "
            f"lng={longitude}"
        )

    except Exception as e:

        print(
            f"[기존조회 오류] "
            f"case_number={case_number} / "
            f"{e}"
        )

        latitude = "0"
        longitude = "0"

    # --------------------------------------------------------
    # 기존 방식 성공
    # --------------------------------------------------------
    if is_valid_latlng(
        latitude,
        longitude
    ):

        print(
            f"[기존조회 성공] "
            f"{case_number}"
        )

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "address": address1,
            "address_type": "parcel",
            "source": "original-address1"
        }

    # --------------------------------------------------------
    # 2. 기존 방식 실패 시에만 추가 보완조회
    # --------------------------------------------------------
    print(
        f"[기존조회 실패] "
        f"{case_number} "
        f"-> 추가 주소 후보 재조회"
    )

    try:

        latitude, longitude = retry_geocode_failed_address(
            geo_service=geocoder,
            case_number=case_number,
            address1=address1,
            address2=address2
        )

    except Exception as e:

        print(
            f"[추가조회 오류] "
            f"case_number={case_number} / "
            f"{e}"
        )

        return None

    # --------------------------------------------------------
    # 추가 보완조회 성공
    # --------------------------------------------------------
    if is_valid_latlng(
        latitude,
        longitude
    ):

        print(
            f"[추가조회 성공] "
            f"{case_number} / "
            f"{latitude}, {longitude}"
        )

        return {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "address": "추가 보완주소",
            "address_type": "fallback",
            "source": "retry-geocode"
        }

    # 기존조회 + 추가조회 모두 실패
    return None


# ============================================================
# 위경도 재처리 메인 함수
# ============================================================
def repair_latlng(case_number=""):

    print()
    print("=" * 80)
    print("경매 데이터 위/경도 재처리")

    if case_number:
        print(
            f"테스트 사건번호 : {case_number}"
        )
    else:
        print(
            "처리조건 : latitude/longitude 미처리 전체"
        )

    print("=" * 80)

    # --------------------------------------------------------
    # DB에서 위경도 미처리 자료 조회
    # --------------------------------------------------------
    rows = auction_read_no_latlng(
        case_number=case_number
    )

    if not rows:

        print(
            "[처리종료] "
            "위경도 재처리 대상이 없습니다."
        )

        return

    print(
        f"\n총 대상건수 : {len(rows)}건"
    )

    # --------------------------------------------------------
    # VWorld 객체는 한번만 생성
    # --------------------------------------------------------
    geocoder = VWorldGeocoding(
        MAP_API_KEY
    )

    success_count = 0
    fail_count = 0

    # --------------------------------------------------------
    # 위경도 재조회
    # --------------------------------------------------------
    for index, row in enumerate(
        rows,
        start=1
    ):

        current_case_number = row.get(
            "case_number",
            ""
        )

        print()
        print("-" * 80)

        print(
            f"[{index}/{len(rows)}] "
            f"{current_case_number}"
        )

        print(
            f"address1 : "
            f"{row.get('address1', '')}"
        )

        print(
            f"address2 : "
            f"{row.get('address2', '')}"
        )

        print(
            f"기존좌표 : "
            f"{row.get('latitude')} / "
            f"{row.get('longitude')}"
        )

        # ----------------------------------------------------
        # VWorld 조회
        # ----------------------------------------------------
        result = geocode_auction_row(
            row,
            geocoder
        )

        # 조회 실패
        if result is None:

            print(
                f"[최종실패] "
                f"{current_case_number}"
            )

            fail_count += 1

            # 다음 레코드 처리 전 1초 대기
            time_module.sleep(0.5)

            continue

        # ----------------------------------------------------
        # DB 위경도 UPDATE
        # ----------------------------------------------------
        updated = (
            auction_update_latlng_by_case_number(
                current_case_number,
                result["latitude"],
                result["longitude"]
            )
        )

        if updated > 0:

            success_count += 1

            print(
                f"[성공] "
                f"{current_case_number} / "
                f"{result['address']} / "
                f"{result['latitude']}, "
                f"{result['longitude']}"
            )

        else:

            fail_count += 1

            print(
                f"[DB UPDATE 실패] "
                f"{current_case_number}"
            )

        # ====================================================
        # 한 건 처리가 완전히 끝났으므로
        # 다음 레코드 처리 전 0.3초 대기
        # ====================================================
        time_module.sleep(0.3)  # 1초 대기 (VWorld API 호출 제한 고려)

    # --------------------------------------------------------
    # 최종 결과
    # --------------------------------------------------------
    print()
    print("=" * 80)

    print("위경도 재처리 완료")

    print(
        f"전체 : {len(rows)}건"
    )

    print(
        f"성공 : {success_count}건"
    )

    print(
        f"실패 : {fail_count}건"
    )

    print("=" * 80)


# ============================================================
# 테스트 실행
# ============================================================
if __name__ == "__main__":

    # 특정 사건번호만 테스트
    TEST_CASE_NUMBER = "2025-507728"

    # 전체 위경도 0 데이터 처리 시:
    #TEST_CASE_NUMBER = ""

    repair_latlng(
        case_number=TEST_CASE_NUMBER
    )