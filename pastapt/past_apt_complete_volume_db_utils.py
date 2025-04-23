# 아파트 시군구별 입주물량(2025~2029년)
import os
import sqlite3
from config import PAST_APT_BASE_PATH

# DB 파일 경로 설정 (interest_rate 모듈과 동일한 DB 사용)
DB_FILENAME = os.path.join(PAST_APT_BASE_PATH, "past_apt_data.db")
TABLE_NAME = "apt_complete_volume"


def create_apt_complete_volume_table():
    """
    apt_complete_volume 테이블을 생성합니다.
    필드: id, region, address, apt_name, year_month(YYYY-MM), volume(세대 수)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT NOT NULL,
            address TEXT NOT NULL,
            apt_name TEXT NOT NULL,
            year_month TEXT NOT NULL,
            volume INTEGER NOT NULL
        )
    ''')

    conn.commit()
    conn.close()


def insert_apt_complete_volume_record(region: str, address: str, apt_name: str, year_month: str, volume: int):
    """
    단일 레코드를 삽입합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()

    cur.execute(f'''
        INSERT INTO {TABLE_NAME} (region, address, apt_name, year_month, volume)
        VALUES (?, ?, ?, ?, ?)
    ''', (region, address, apt_name, year_month, volume))

    conn.commit()
    conn.close()


def process_apt_complete_volume_txt(txt_file_path: str):
    """
    주어진 txt 파일을 읽어 테이블에 데이터를 삽입합니다.
    파일의 각 행은 tab으로 구분된 4개 필드:
      1) 전체 지역 문자열 (예: "제주 제주 연동")
      2) 아파트 이름 (apt_name)
      3) "YYYY년 M월"
      4) "N,NNN세대"

    처리 방법:
    - region: 전체 지역 문자열에서 첫 공백 전까지 (예: "제주")
    - address: 전체 지역 문자열 원본
    - apt_name: 두 번째 필드
    - year_month: "YYYY-MM" 형식
    - volume: 숫자만 추출하여 int 변환
    """
    create_apt_complete_volume_table()

    with open(txt_file_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) != 4:
                continue

            full_region, apt_name_raw, ym_raw, volume_raw = parts
            # region: 첫 공백 전까지
            region = full_region.split()[0]
            # address: 전체 지역 문자열
            address = full_region
            # apt_name: 두 번째 필드
            apt_name = apt_name_raw

            # "2029년 8월" -> "2029-08"
            ym_clean = ym_raw.replace('년', '-').replace('월', '').strip()
            year, month = [x.strip() for x in ym_clean.split('-')]
            year_month = f"{year}-{month.zfill(2)}"

            # "2,264세대" -> 2264
            volume = int(volume_raw.replace('세대', '').replace(',', '').strip())

            # 필드 연결하여 출력
            print(f"{region} | {address} | {apt_name} | {year_month} | {volume}")

            insert_apt_complete_volume_record(region, address, apt_name, year_month, volume)


if __name__ == '__main__':
    # 예시 파일 경로: PAST_APT_BASE_PATH/아파트입주물량.txt
    txt_path = os.path.join(PAST_APT_BASE_PATH, '아파트입주물량.txt')
    process_apt_complete_volume_txt(txt_path)
