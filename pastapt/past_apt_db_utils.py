import os
import sqlite3
import json

from config import PAST_APT_BASE_PATH

# 상단 경로/DB 정보 설정
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
PAST_APT_TABLE = "past_apt"
PAST_PRICE_TABLE = "past_apt_price"

def past_apt_create_table():
    print(DB_FILENAME)

    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    # 아파트 기본 정보 테이블
    cur.execute(f'''
           CREATE TABLE IF NOT EXISTS {PAST_APT_TABLE} (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               region_name TEXT,
               mcode_name TEXT,
               sname TEXT,
               apt_name TEXT,
               size TEXT,
               total_households TEXT,
               move_in_date TEXT,
               builder TEXT,
               building_floors TEXT,
               parking TEXT,
               heating_type TEXT
           )
       ''')

    # 아파트 시세 정보 테이블 (apt_name 컬럼 추가됨)
    cur.execute(f'''
           CREATE TABLE IF NOT EXISTS {PAST_PRICE_TABLE} (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               apt_id INTEGER,
               region_name TEXT,
               mcode_name TEXT,
               sname TEXT,
               apt_name TEXT,
               size TEXT,
               month TEXT,
               sale_low TEXT,
               sale_high TEXT,
               sale_change TEXT,
               rent_low TEXT,
               rent_high TEXT,
               rent_change TEXT,
               FOREIGN KEY (apt_id) REFERENCES {PAST_APT_TABLE}(id)
           )
       ''')

    conn.commit()
    conn.close()

def insert_apt_and_prices(apt_name, detail, region_name, mcode_name, sname, size):
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    profile = detail.get("profile", {})
    market_prices = detail.get("market_prices", [])

    # 아파트 기본 정보 삽입
    cur.execute(f'''
            INSERT INTO {PAST_APT_TABLE} (
                region_name, mcode_name, sname, apt_name, size,
                total_households, move_in_date, builder, building_floors, parking, heating_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
        region_name, mcode_name, sname, apt_name, size,
        profile.get("total_households", "정보 없음"),
        profile.get("move_in_date", "정보 없음"),
        profile.get("builder", "정보 없음"),
        profile.get("building_floors", "정보 없음"),
        profile.get("parking", "정보 없음"),
        profile.get("heating_type", "정보 없음")
    ))

    apt_id = cur.lastrowid

    # 아파트 시세 정보 삽입 (apt_name 포함)
    for d in market_prices:
        cur.execute(f'''
                INSERT INTO {PAST_PRICE_TABLE} (
                    apt_id, region_name, mcode_name, sname, apt_name, size, 
                    month, sale_low, sale_high, sale_change,
                    rent_low, rent_high, rent_change
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            apt_id, region_name, mcode_name, sname, apt_name, size,
            d.get('month'),
            d.get('sale_low'),
            d.get('sale_high'),
            d.get('sale_change'),
            d.get('rent_low'),
            d.get('rent_high'),
            d.get('rent_change')
        ))

    conn.commit()
    conn.close()


def fetch_grouped_apt_data(region_name, mcode_name, sname, houseCnt):
    """
    지정된 조건에 맞는 데이터를 가져옵니다.
    매개변수:
      - region_name: 예) '제주특별자치도'
      - mcode_name: 예) '제주시'
      - sname: 예) '화북동'
      - houseCnt: 'all' 이면 전체, 숫자(문자열)면 해당 숫자 이상(예: '500'이면 500이상)
    """
    import sqlite3
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 컬럼명으로 접근 가능하도록 설정
    cur = conn.cursor()

    # houseCnt 조건절을 동적으로 추가 (houseCnt가 'all'이면 조건절 없이, 아니면 조건절 추가)
    if houseCnt != "all":
        # total_households에서 '가구'를 제거한 후 정수형으로 변환하여 비교
        house_condition = "WHERE CAST(REPLACE(REPLACE(pa.total_households, ',', ''), '가구', '') AS INTEGER) >= ?"
    else:
        house_condition = ""

    query = f"""
    WITH min_max_month AS (
        SELECT
            apt_id,
            MIN(month) AS min_month,
            MAX(month) AS max_month
        FROM
            past_apt_price
        WHERE region_name = ?
          AND mcode_name = ?
          AND sname = ?
        GROUP BY
            apt_id
    ),
    min_month_data AS (
        SELECT
            a.apt_id,
            a.region_name,
            a.mcode_name,
            a.sname,
            a.apt_name,
            a.size,
            ROUND(CAST(REPLACE(a.size, '㎡', '') AS REAL) / 3.3, 2) || '평' AS size_py,
            pa.move_in_date,
            pa.total_households,
            a.month,
            m.min_month,
            m.max_month,
            CAST(REPLACE(a.sale_high, ',', '') AS INTEGER) AS sale_high,
            CAST(REPLACE(a.rent_high, ',', '') AS INTEGER) AS rent_high
        FROM
            past_apt_price a
            JOIN min_max_month m ON a.apt_id = m.apt_id AND a.month = m.min_month
            LEFT JOIN past_apt pa ON pa.id = a.apt_id
        {house_condition}
    )
    SELECT
        apt_id,
        region_name,
        mcode_name,
        sname,
        apt_name,
        size,
        size_py,
        total_households,
        move_in_date,
        min_month,
        max_month,
        sale_high,
        rent_high,
        (sale_high - rent_high) AS sale_rent_diff
    FROM
        min_month_data;
    """

    parameters = [region_name, mcode_name, sname]
    if houseCnt != "all":
        parameters.append(houseCnt)  # houseCnt 값이 조건절의 ?에 대입됨

    cur.execute(query, tuple(parameters))
    rows = cur.fetchall()
    conn.close()

    # 결과를 딕셔너리 리스트로 변환하여 리턴
    return [dict(row) for row in rows]

# 아파트별 상세내용
def fetch_apt_detail_data(apt_id):
    """
    주어진 apt_id에 해당하는 아파트 시세 정보를 past_apt_price 테이블에서 조회합니다.
    결과는 딕셔너리 리스트 형태로 반환됩니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 컬럼명을 키로 사용하기 위함
    cur = conn.cursor()

    query = f"""
    SELECT 
        id,
        apt_id,
        region_name,
        mcode_name,
        sname,
        apt_name,
        size,
        month,
        sale_low,
        sale_high,
        sale_change,
        rent_low,
        rent_high,
        rent_change
    FROM {PAST_PRICE_TABLE}
    WHERE apt_id = ?
    ORDER BY month DESC;
    """

    cur.execute(query, (apt_id,))
    rows = cur.fetchall()
    conn.close()

    # 결과를 딕셔너리 리스트로 변환하여 반환
    return [dict(row) for row in rows]


# json리스트 가져오기
def query_region_hierarchy(category, sel_code, parent_sel_code):
    """
    region_hierarchy.json 파일을 읽어서, 아래 조건에 맞게 하위 목록을 리턴합니다.
      - category가 "region"이면, sel_code와 일치하는 lcode를 가진 지역의 첫 번째 하위(시군구 목록)를
        {"코드": mcode, "코드명": mcode_name} 형태의 1레벨 구조로 리턴.
      - category가 "sigungu"이면, sel_code와 일치하는 mcode를 가진 시군구의 하위(읍면동 목록)를
        {"코드": sname_code, "코드명": sname} 형태의 1레벨 구조로 리턴.
    """
    try:
        filename = PAST_APT_BASE_PATH + "/region_hierarchy.json"
        with open(filename, encoding="utf-8-sig") as f:
            hierarchy = json.load(f)
    except FileNotFoundError:
        print(f"⚠️ 파일을 찾을 수 없습니다: {filename}")
        return None

    if category == "region":
        for region in hierarchy:
            if region.get("lcode") == sel_code:
                # 해당 지역의 하위(시군구 목록)를 {"코드": mcode, "코드명": mcode_name} 형태로 변환하여 리턴
                children = region.get("하위", [])
                return [{"code": child.get("mcode"), "name": child.get("mcode_name")} for child in children]
        return []  # 해당 lcode를 찾지 못한 경우 빈 리스트

    elif category == "sggNm":
        for region in hierarchy:
            if region.get("lcode") == parent_sel_code:
                for sigungu in region.get("하위", []):
                    if sigungu.get("mcode") == sel_code:
                        # 해당 시군구의 하위(읍면동 목록)를 {"코드": sname_code, "코드명": sname} 형태로 변환하여 리턴
                        children = sigungu.get("하위", [])
                        return [{"code": child.get("sname_code"), "name": child.get("sname")} for child in children]
        return []  # 해당 mcode를 찾지 못한 경우 빈 리스트

    else:
        print("❌ category는 'region' 또는 'sigungu'이어야 합니다.")
        return None
