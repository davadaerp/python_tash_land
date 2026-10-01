import re

from pubdata.public_land_lawd_code_db_utils import get_lawd_by_name

# ============================================================
# 위도 / 경도 유효성 검사
# ============================================================
def is_valid_latlng(latitude, longitude):
    """
    VWorld에서 받은 위도/경도가 실제 사용 가능한 값인지 확인.

    정상:
        37.12345 / 126.12345

    실패:
        0 / 0
        0.0 / 0.0
        "0" / "0"
        None / None
        "" / ""
    """

    try:
        lat = float(latitude)
        lng = float(longitude)

        if lat == 0.0 or lng == 0.0:
            return False

        if not -90.0 <= lat <= 90.0:
            return False

        if not -180.0 <= lng <= 180.0:
            return False

        return True

    except (TypeError, ValueError):
        return False

# ==========================================================
# 위경도 재조회 로직
# =========================================================
def retry_geocode_failed_address(
        geo_service,
        case_number,
        address1,
        address2
):
    """
    기존 address1/parcel 조회가 실패했을 때만 호출한다.
    """

    attempts = []

    # --------------------------------------------------------
    # 1. address2 도로명주소
    # --------------------------------------------------------
    road = clean_geocode_address(
        address2,
        "road"
    )

    if road:
        attempts.append(
            (
                "address2",
                road,
                "road"
            )
        )

    # --------------------------------------------------------
    # 2. address1 정리
    #
    # 일반적으로 parcel이지만
    # CSV 중 일부는 address1 자체가 도로명주소임
    # --------------------------------------------------------
    detected_type = detect_geocode_type(
        address1
    )

    cleaned1 = clean_geocode_address(
        address1,
        detected_type
    )

    if cleaned1:
        attempts.append(
            (
                "address1-clean",
                cleaned1,
                detected_type
            )
        )

    # --------------------------------------------------------
    # 3. 현재 법정동 DB를 이용한 최신 행정구역 주소 생성
    # --------------------------------------------------------
    try:
        lawd_info = get_lawd_by_name(
            clean_geocode_address(
                address1,
                "parcel"
            )
        ) or {}

    except Exception:
        lawd_info = {}

    # 최신 행정구역 + 도로명주소
    current_road = (
        replace_admin_prefix_for_road(
            address2,
            lawd_info
        )
    )

    if current_road:
        attempts.append(
            (
                "address2-current-admin",
                current_road,
                "road"
            )
        )

    # 최신 행정구역 + 지번주소
    current_parcel = (
        build_current_parcel_address(
            address1,
            lawd_info
        )
    )

    if current_parcel:
        attempts.append(
            (
                "address1-current-admin",
                current_parcel,
                "parcel"
            )
        )

    # --------------------------------------------------------
    # 4. 인천 2026 행정체제 개편 보완
    # --------------------------------------------------------
    attempts.extend(
        regional_reorg_candidates(
            address1,
            address2
        )
    )

    # --------------------------------------------------------
    # 중복 주소 제거 후 VWorld 순차 조회
    # --------------------------------------------------------
    seen = set()

    for label, addr, atype in attempts:

        key = (
            addr,
            atype
        )

        if not addr or key in seen:
            continue

        seen.add(key)

        try:

            print(
                f"[위경도 재시도] "
                f"case_number={case_number} / "
                f"{label}={addr} / "
                f"type={atype}"
            )

            lat, lng = geo_service.get_lat_lng(
                addr,
                atype
            )

            print(
                f"[위경도 재시도 결과] "
                f"lat={lat}, lng={lng}"
            )

            if is_valid_latlng(
                lat,
                lng
            ):
                return lat, lng

        except Exception as e:

            print(
                f"[위경도 재시도 오류] "
                f"case_number={case_number} / "
                f"{label} / {e}"
            )

    return "0", "0"


# ============================================================
# VWorld 검색용 주소 정리
# ============================================================
def clean_geocode_address(address, address_type="parcel"):
    """
    VWorld 검색에 사용할 주소를 정리한다.

    parcel 예:
        인천 서구 검암동 678-1,
        101동 3층302호 (검암동,청라하이츠)

        -> 인천 서구 검암동 678-1

    road 예:
        (인천 서구 도요지로190번길 1)

        -> 인천 서구 도요지로190번길 1
    """

    if not address:
        return ""

    addr = str(address).strip()

    # --------------------------------------------------------
    # 주소 전체를 감싸고 있는 괄호 제거
    # --------------------------------------------------------
    if (
        addr.startswith("(")
        and addr.endswith(")")
    ):
        addr = addr[1:-1].strip()

    # --------------------------------------------------------
    # 지번주소
    # --------------------------------------------------------
    if address_type == "parcel":

        # 괄호 안 건물명/법정동명 제거
        addr = re.sub(
            r"\([^)]*\)",
            " ",
            addr
        )

        # 외 N필지 / 외 N개호 등 제거
        addr = re.sub(
            r"\s*외\s*\d+\s*"
            r"(?:개호|필지|호)?(?:.*)?$",
            " ",
            addr
        )

        # 쉼표 이후 동/층/호 등 상세주소 제거
        if "," in addr:
            addr = addr.split(
                ",",
                1
            )[0]

    # 연속 공백 제거
    addr = re.sub(
        r"\s+",
        " ",
        addr
    ).strip()

    return addr


# ============================================================
# 주소가 지번인지 도로명인지 자동 판별
# ============================================================
def detect_geocode_type(address):
    """
    address1이 일반적인 지번주소인지,
    예외적으로 도로명주소인지 판별한다.

    return:
        "road"
        "parcel"
    """

    if not address:
        return "parcel"

    addr = clean_geocode_address(
        address,
        "road"
    )

    # 예:
    # 해돋이로 59-12
    # 원흥로 11-11
    # 초례로16길 108-4
    if re.search(
        r"(?:대로|로|길)[^\s]*\s+"
        r"\d+(?:-\d+)?(?:\s|,|$)",
        addr
    ):
        return "road"

    return "parcel"


# ============================================================
# 도로명주소의 행정구역 앞부분을 현재 법정동 DB 기준으로 보정
# ============================================================
def replace_admin_prefix_for_road(address2, lawd_info):
    """
    기존 address2 자체를 수정하는 함수가 아니다.

    기존 VWorld 조회 실패 시,
    현재 법정동 DB의 region / sigungu_name을 이용하여
    추가 VWorld 검색 후보를 생성한다.
    """

    if not address2:
        return ""

    if not lawd_info:
        return ""

    road_address = clean_geocode_address(
        address2,
        "road"
    )

    if not road_address:
        return ""

    region = str(
        lawd_info.get("region", "") or ""
    ).strip()

    sigungu_name = str(
        lawd_info.get("sigungu_name", "") or ""
    ).strip()

    if not region:
        return ""

    parts = road_address.split()

    if len(parts) < 2:
        return ""

    # --------------------------------------------------------
    # 기존 주소 앞부분의
    # 시도 / 시군구를 제거한다.
    # --------------------------------------------------------
    remove_count = 1

    if len(parts) >= 2:

        second = parts[1]

        if (
            second.endswith("시")
            or second.endswith("군")
            or second.endswith("구")
        ):
            remove_count = 2

            # 예:
            # 경기 수원시 권선구 ...
            if (
                len(parts) >= 3
                and parts[2].endswith("구")
                and second.endswith("시")
            ):
                remove_count = 3

    detail = " ".join(
        parts[remove_count:]
    ).strip()

    if not detail:
        return ""

    # --------------------------------------------------------
    # 현재 행정구역으로 주소 재구성
    # --------------------------------------------------------
    if sigungu_name:

        new_address = (
            f"{region} "
            f"{sigungu_name} "
            f"{detail}"
        )

    else:

        # 세종 등 sigungu_name 없는 경우
        new_address = (
            f"{region} "
            f"{detail}"
        )

    return re.sub(
        r"\s+",
        " ",
        new_address
    ).strip()


# ============================================================
# 현재 법정동 DB를 이용하여 지번주소 재생성
# ============================================================
def build_current_parcel_address(address1, lawd_info):
    """
    기존 address1에서 지번을 추출하고,
    현재 법정동 DB 결과를 이용하여
    VWorld 재검색용 지번주소를 만든다.

    기존 address1 데이터 자체는 수정하지 않는다.
    """

    if not address1:
        return ""

    if not lawd_info:
        return ""

    cleaned = clean_geocode_address(
        address1,
        "parcel"
    )

    if not cleaned:
        return ""

    region = str(
        lawd_info.get("region", "") or ""
    ).strip()

    sigungu_name = str(
        lawd_info.get("sigungu_name", "") or ""
    ).strip()

    umd_name = str(
        lawd_info.get("umd_name", "") or ""
    ).strip()

    if not region or not umd_name:
        return ""

    # --------------------------------------------------------
    # 지번 추출
    #
    # 인천 서구 검암동 678-1
    #                  ↓
    #                 678-1
    # --------------------------------------------------------
    lot_match = re.search(
        r"\b(\d+(?:-\d+)?)\b",
        cleaned
    )

    if not lot_match:
        return ""

    lot_number = lot_match.group(1)

    address_parts = [
        region
    ]

    if sigungu_name:
        address_parts.append(
            sigungu_name
        )

    address_parts.append(
        umd_name
    )

    address_parts.append(
        lot_number
    )

    new_address = " ".join(
        address_parts
    )

    return re.sub(
        r"\s+",
        " ",
        new_address
    ).strip()


# ============================================================
# 현재 법정동 정보 조회
# ============================================================
def get_current_lawd_info(address1):
    """
    public_land_lawd_code_db_utils.py의
    get_lawd_by_name()을 공통으로 호출한다.

    실패하면 빈 dict 반환.
    """

    try:

        search_address = clean_geocode_address(
            address1,
            "parcel"
        )

        if not search_address:
            return {}

        return (
            get_lawd_by_name(
                search_address
            )
            or {}
        )

    except Exception as e:

        print(
            f"[법정동 조회 오류] "
            f"address={address1} / {e}"
        )

        return {}


# ============================================================
# VWorld 추가 검색 후보 생성
# ============================================================
def build_geocode_candidates(address1, address2):
    """
    VWorld에서 기존 검색이 실패했을 때 사용할
    추가 검색 후보를 순서대로 생성한다.

    반환:
        [
            (label, address, address_type),
            ...
        ]
    """

    candidates = []

    # ========================================================
    # 1. address2 도로명주소
    # ========================================================
    road = clean_geocode_address(
        address2,
        "road"
    )

    if road:

        candidates.append(
            (
                "address2",
                road,
                "road"
            )
        )

    # ========================================================
    # 2. address1 정리 후 재조회
    # ========================================================
    detected_type = detect_geocode_type(
        address1
    )

    cleaned1 = clean_geocode_address(
        address1,
        detected_type
    )

    if cleaned1:

        candidates.append(
            (
                "address1-clean",
                cleaned1,
                detected_type
            )
        )

    # ========================================================
    # 3. 현재 법정동 DB 조회
    # ========================================================
    lawd_info = get_current_lawd_info(
        address1
    )

    if lawd_info:

        # ----------------------------------------------------
        # 현재 행정구역 + 도로명주소
        # ----------------------------------------------------
        current_road = (
            replace_admin_prefix_for_road(
                address2,
                lawd_info
            )
        )

        if current_road:

            candidates.append(
                (
                    "address2-current-admin",
                    current_road,
                    "road"
                )
            )

        # ----------------------------------------------------
        # 현재 행정구역 + 지번주소
        # ----------------------------------------------------
        current_parcel = (
            build_current_parcel_address(
                address1,
                lawd_info
            )
        )

        if current_parcel:

            candidates.append(
                (
                    "address1-current-admin",
                    current_parcel,
                    "parcel"
                )
            )

    # ========================================================
    # 4. 인천 행정체제 개편 후보
    # ========================================================
    candidates.extend(
        regional_reorg_candidates(
            address1,
            address2
        )
    )

    # ========================================================
    # 중복 제거
    # ========================================================
    result = []
    seen = set()

    for label, address, address_type in candidates:

        if not address:
            continue

        key = (
            address,
            address_type
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            (
                label,
                address,
                address_type
            )
        )

    return result


# ==========================================================
# 전국 주요 행정구역/주소체계 변경 후보 생성
#
# 목적:
#   과거 경매주소가 VWorld 최신 주소체계에서 검색되지 않는 경우
#   변경된 현재 주소를 fallback 후보로 생성한다.
#
# 현재 반영:
#
# 1. 인천광역시 2026-07-01
#    중구 -> 영종구 / 제물포구
#    동구 -> 제물포구
#    서구 -> 검단구 / 서해구
#
# 2. 광주광역시 + 전라남도 2026-07-01
#    -> 전남광주통합특별시
#
# 3. 경기도 용인시 처인구 2026-01-02
#    양지면 -> 양지읍
#
# 4. 충청북도 음성군 2026-03-25
#    대소면 -> 대소읍
#
# 5. 경기도 화성시 2026-02-01
#    일반구 신설
#
#    첨부 실패주소에서 확인된 지역:
#       향남읍 -> 만세구
#       서신면 -> 만세구
#       영천동 -> 동탄구
# ==========================================================
def regional_reorg_candidates(
        address1,
        address2
):
    """
    행정구역 개편으로 과거 주소가 VWorld에서
    검색되지 않을 경우 현재 주소체계의 후보를 생성한다.

    기존 address1/address2 자체는 변경하지 않는다.

    반환값:
        [
            (label, address, address_type),
            ...
        ]

    address_type:
        parcel : 지번주소
        road   : 도로명주소
    """

    # --------------------------------------------------------
    # 주소 정리
    # --------------------------------------------------------
    p = clean_geocode_address(
        address1,
        "parcel"
    )

    r = clean_geocode_address(
        address2,
        "road"
    )

    candidates = []

    # ========================================================
    # 1. 인천광역시
    #
    # 2026-07-01 행정체제 개편
    #
    # 중구:
    #     영종지역 -> 영종구
    #     나머지   -> 제물포구
    #
    # 동구:
    #     전체     -> 제물포구
    #
    # 서구:
    #     검단지역 -> 검단구
    #     나머지   -> 서해구
    # ========================================================

    gu_match = re.match(
        r"^인천(?:광역시|시)?\s+"
        r"(중구|동구|서구)\s+",
        p
    )

    if gu_match:

        old_gu = gu_match.group(1)

        # ----------------------------------------------------
        # 법정동 추출
        # ----------------------------------------------------
        dong_match = re.search(
            r"\s([가-힣0-9]+(?:동|가))\s",
            p + " "
        )

        dong = (
            dong_match.group(1)
            if dong_match
            else ""
        )

        new_gu = ""

        # ====================================================
        # 인천 중구
        # ====================================================
        if old_gu == "중구":

            yeongjong_dongs = {
                "운서동",
                "중산동",
                "운남동",
                "운북동",
                "을왕동",
                "남북동",
                "덕교동",
                "무의동"
            }

            if dong in yeongjong_dongs:

                new_gu = "영종구"

            else:

                new_gu = "제물포구"

        # ====================================================
        # 인천 동구
        # ====================================================
        elif old_gu == "동구":

            new_gu = "제물포구"

        # ====================================================
        # 인천 서구
        # ====================================================
        elif old_gu == "서구":

            # ------------------------------------------------
            # 검단구 법정동
            #
            # 주의:
            # 시천동은 경계조정 문제 때문에 별도 처리한다.
            # ------------------------------------------------
            geomdan_dongs = {
                "대곡동",
                "불로동",
                "금곡동",
                "마전동",
                "오류동",
                "왕길동",
                "당하동",
                "원당동",
                "백석동"
            }

            if dong in geomdan_dongs:

                new_gu = "검단구"

            elif dong == "시천동":

                # --------------------------------------------
                # 시천동은 행정구역 경계 조정이 있었으므로
                # 단순 동명만으로 한쪽 구를 확정하지 않는다.
                #
                # 두 후보를 모두 생성해서
                # 실제 VWorld에서 성공하는 주소를 사용한다.
                # --------------------------------------------
                for target_gu in (
                    "검단구",
                    "서해구"
                ):

                    for label, addr, atype in (
                        (
                            f"인천2026-{target_gu}-address2",
                            r,
                            "road"
                        ),
                        (
                            f"인천2026-{target_gu}-address1",
                            p,
                            "parcel"
                        )
                    ):

                        if not addr:
                            continue

                        new_addr = re.sub(
                            r"^인천(?:광역시|시)?\s+서구\s+",
                            f"인천광역시 {target_gu} ",
                            addr
                        )

                        if new_addr != addr:

                            candidates.append(
                                (
                                    label,
                                    new_addr,
                                    atype
                                )
                            )

                # 아래 일반적인 new_gu 생성은 하지 않음
                new_gu = ""

            else:

                new_gu = "서해구"

        # ----------------------------------------------------
        # 인천 일반 후보 생성
        # ----------------------------------------------------
        if new_gu:

            for label, addr, atype in (
                (
                    "인천2026-address2",
                    r,
                    "road"
                ),
                (
                    "인천2026-address1",
                    p,
                    "parcel"
                )
            ):

                if not addr:
                    continue

                new_addr = re.sub(
                    rf"^인천(?:광역시|시)?\s+"
                    rf"{old_gu}\s+",
                    f"인천광역시 {new_gu} ",
                    addr
                )

                if new_addr != addr:

                    candidates.append(
                        (
                            label,
                            new_addr,
                            atype
                        )
                    )

            print(
                f"[행정구역 개편] "
                f"인천 {old_gu} -> {new_gu} / "
                f"법정동={dong}"
            )

    # ========================================================
    # 2. 광주광역시 + 전라남도
    #
    # 2026-07-01
    #
    # 광주광역시
    # 전라남도
    #
    #       ↓
    #
    # 전남광주통합특별시
    # ========================================================

    for label, addr, atype in (
        (
            "광주전남2026-address2",
            r,
            "road"
        ),
        (
            "광주전남2026-address1",
            p,
            "parcel"
        )
    ):

        if not addr:
            continue

        new_addr = addr

        # ----------------------------------------------------
        # 광주광역시
        # ----------------------------------------------------
        if re.match(
            r"^광주(?:광역시)?\s+",
            addr
        ):

            new_addr = re.sub(
                r"^광주(?:광역시)?\s+",
                "전남광주통합특별시 ",
                addr
            )

        # ----------------------------------------------------
        # 전라남도
        # ----------------------------------------------------
        elif re.match(
            r"^(?:전라남도|전남)\s+",
            addr
        ):

            new_addr = re.sub(
                r"^(?:전라남도|전남)\s+",
                "전남광주통합특별시 ",
                addr
            )

        if new_addr != addr:

            candidates.append(
                (
                    label,
                    new_addr,
                    atype
                )
            )

            print(
                f"[행정구역 개편] "
                f"{addr} -> {new_addr}"
            )

    # ========================================================
    # 3. 경기도 용인시 처인구
    #
    # 2026-01-02
    #
    # 양지면 -> 양지읍
    #
    # 법정리:
    #   양지리
    #   남곡리
    #   평창리
    #   제일리
    #   추계리
    #   식금리
    #   정수리
    #   대대리
    #   주북리
    #   송문리
    # ========================================================

    for label, addr, atype in (
        (
            "용인2026-address2",
            r,
            "road"
        ),
        (
            "용인2026-address1",
            p,
            "parcel"
        )
    ):

        if not addr:
            continue

        new_addr = re.sub(
            r"^(?:경기도|경기)\s+"
            r"용인시\s+처인구\s+"
            r"양지면\s+",
            "경기도 용인시 처인구 양지읍 ",
            addr
        )

        if new_addr != addr:

            candidates.append(
                (
                    label,
                    new_addr,
                    atype
                )
            )

            print(
                f"[행정구역 개편] "
                f"용인시 처인구 양지면 -> 양지읍 / "
                f"{new_addr}"
            )

    # ========================================================
    # 4. 충청북도 음성군
    #
    # 2026-03-25
    #
    # 대소면 -> 대소읍
    #
    # 첨부자료에서 실제 확인:
    #
    # 태생리
    # 소석리
    # 성본리
    # 부윤리
    # 삼호리
    # 삼정리
    # 대풍리
    # 등
    #
    # 도로명주소 역시
    # "음성군 대소면" -> "음성군 대소읍"
    # ========================================================

    for label, addr, atype in (
        (
            "음성2026-address2",
            r,
            "road"
        ),
        (
            "음성2026-address1",
            p,
            "parcel"
        )
    ):

        if not addr:
            continue

        new_addr = re.sub(
            r"^(?:충청북도|충북)\s+"
            r"음성군\s+"
            r"대소면\s+",
            "충청북도 음성군 대소읍 ",
            addr
        )

        if new_addr != addr:

            candidates.append(
                (
                    label,
                    new_addr,
                    atype
                )
            )

            print(
                f"[행정구역 개편] "
                f"음성군 대소면 -> 대소읍 / "
                f"{new_addr}"
            )

    # ========================================================
    # 5. 경기도 화성시
    #
    # 2026-02-01 일반구 신설
    #
    # 첨부된 실패주소에서 실제 필요한 지역만 우선 처리
    #
    # 향남읍 -> 만세구
    # 서신면 -> 만세구
    # 영천동 -> 동탄구
    #
    # 기존:
    # 경기도 화성시 향남읍 ...
    #
    # 변경:
    # 경기도 화성시 만세구 향남읍 ...
    # ========================================================

    for label, addr, atype in (
        (
            "화성2026-address2",
            r,
            "road"
        ),
        (
            "화성2026-address1",
            p,
            "parcel"
        )
    ):

        if not addr:
            continue

        new_addr = addr
        target_gu = ""

        # ----------------------------------------------------
        # 만세구
        #
        # 첨부자료:
        #   향남읍
        #   서신면
        # ----------------------------------------------------
        if re.match(
            r"^(?:경기도|경기)\s+"
            r"화성시\s+"
            r"(?:향남읍|서신면)\s+",
            addr
        ):

            target_gu = "만세구"

            new_addr = re.sub(
                r"^(?:경기도|경기)\s+"
                r"화성시\s+",
                "경기도 화성시 만세구 ",
                addr
            )

        # ----------------------------------------------------
        # 동탄구
        #
        # 첨부자료:
        #
        # 경기도 화성시 동탄순환대로 29-9 ...
        #                     (영천동 ...)
        #
        # 도로명주소에는 영천동이 앞부분에 없을 수 있으므로
        # 동탄계열 도로명 또는 괄호 속 영천동도 확인한다.
        # ----------------------------------------------------
        elif (
            re.match(
                r"^(?:경기도|경기)\s+"
                r"화성시\s+동탄",
                addr
            )
            or
            re.search(
                r"\(영천동(?:,|\))",
                addr
            )
            or
            re.match(
                r"^(?:경기도|경기)\s+"
                r"화성시\s+영천동\s+",
                addr
            )
        ):

            target_gu = "동탄구"

            new_addr = re.sub(
                r"^(?:경기도|경기)\s+"
                r"화성시\s+",
                "경기도 화성시 동탄구 ",
                addr
            )

        # ----------------------------------------------------
        # 변경된 경우 후보 추가
        # ----------------------------------------------------
        if new_addr != addr:

            candidates.append(
                (
                    label,
                    new_addr,
                    atype
                )
            )

            print(
                f"[행정구역 개편] "
                f"화성시 -> 화성시 {target_gu} / "
                f"{new_addr}"
            )

    # ========================================================
    # 6. 중복 후보 제거
    # ========================================================

    result = []
    seen = set()

    for label, addr, atype in candidates:

        key = (
            addr,
            atype
        )

        if key in seen:
            continue

        seen.add(key)

        result.append(
            (
                label,
                addr,
                atype
            )
        )

    return result

