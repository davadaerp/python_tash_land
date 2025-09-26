# population_db.py
# -*- coding: utf-8 -*-
"""
SQLite DB: public_data.db
Table: population
Schema: 행정동 성·연령별 인구 스키마 + id(PK)

기능:
- 테이블 생성/삭제
- INSERT (복합키 중복 검사)
- UPDATE (복합키 기준)
- DELETE (복합키 기준)
- READ   (조건 검색)
"""

import os
import sqlite3
from typing import Dict, List, Any

# ===== 0) DB 경로 / 상수 =====
DB_FILENAME = os.path.join(os.path.dirname(__file__), "public_data.db")
TABLE_NAME = "population"

# 복합키(유일 키)
KEY_FIELDS = ("statsYm", "admmCd", "dongNm", "tong", "ban")

# 숫자 변환 헬퍼
def _as_int(v) -> int:
    try:
        if v in (None, "", "null", "None"):
            return 0
        return int(str(v).replace(",", ""))
    except Exception:
        return 0

def _as_str(v) -> str:
    return "" if v is None else str(v).strip()


# ===== 테이블 생성/삭제 =====
def create_population_table():
    """
    population 테이블 생성 (없으면 생성).
    UNIQUE(statsYm, admmCd, dongNm, tong, ban)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            statsYm TEXT NOT NULL,           -- 통계년월 (YYYYMM 또는 YYYY-MM)
            admmCd TEXT NOT NULL,            -- 행정기관코드
            ctpvNm TEXT NOT NULL,            -- 시도명
            sggNm  TEXT NOT NULL,            -- 시군구명
            dongNm TEXT NOT NULL,            -- 행정동명
            tong   TEXT NOT NULL,            -- 통
            ban    TEXT NOT NULL,            -- 반
            totNmprCnt INTEGER DEFAULT 0,    -- 총인구수
            maleNmprCnt INTEGER DEFAULT 0,   -- 남자인구수
            femlNmprCnt INTEGER DEFAULT 0,   -- 여자인구수
            male0AgeNmprCnt INTEGER DEFAULT 0,    -- 만0~9세 남자
            male10AgeNmprCnt INTEGER DEFAULT 0,   -- 만10~19세 남자
            male20AgeNmprCnt INTEGER DEFAULT 0,   -- 만20~29세 남자
            male30AgeNmprCnt INTEGER DEFAULT 0,   -- 만30~39세 남자
            male40AgeNmprCnt INTEGER DEFAULT 0,   -- 만40~49세 남자
            male50AgeNmprCnt INTEGER DEFAULT 0,   -- 만50~59세 남자
            male60AgeNmprCnt INTEGER DEFAULT 0,   -- 만60~69세 남자
            male70AgeNmprCnt INTEGER DEFAULT 0,   -- 만70~79세 남자
            male80AgeNmprCnt INTEGER DEFAULT 0,   -- 만80~89세 남자
            male90AgeNmprCnt INTEGER DEFAULT 0,   -- 만90~99세 남자
            male100AgeNmprCnt INTEGER DEFAULT 0,  -- 만100세 이상 남자
            feml0AgeNmprCnt INTEGER DEFAULT 0,    -- 만0~9세 여자
            feml10AgeNmprCnt INTEGER DEFAULT 0,   -- 만10~19세 여자
            feml20AgeNmprCnt INTEGER DEFAULT 0,   -- 만20~29세 여자
            feml30AgeNmprCnt INTEGER DEFAULT 0,   -- 만30~39세 여자
            feml40AgeNmprCnt INTEGER DEFAULT 0,   -- 만40~49세 여자
            feml50AgeNmprCnt INTEGER DEFAULT 0,   -- 만50~59세 여자
            feml60AgeNmprCnt INTEGER DEFAULT 0,   -- 만60~69세 여자
            feml70AgeNmprCnt INTEGER DEFAULT 0,   -- 만70~79세 여자
            feml80AgeNmprCnt INTEGER DEFAULT 0,   -- 만80~89세 여자
            feml90AgeNmprCnt INTEGER DEFAULT 0,   -- 만90~99세 여자
            feml100AgeNmprCnt INTEGER DEFAULT 0,  -- 만100세 이상 여자
            stdgNm TEXT NOT NULL DEFAULT '', -- 법정동명
            stdgCd TEXT NOT NULL DEFAULT '', -- 법정동코드
            liNm   TEXT NOT NULL DEFAULT '' -- 리명
        )
    """)
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_statsYm ON {TABLE_NAME}(statsYm)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_admmCd ON {TABLE_NAME}(admmCd)")
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_region ON {TABLE_NAME}(ctpvNm, sggNm, dongNm)")
    conn.commit()
    conn.close()

def drop_population_table():
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")

# ===== INSERT =====
def population_insert_record(record: Dict[str, Any]):
    """
    단일 레코드 삽입. (statsYm, admmCd, dongNm, tong, ban) 복합키 중복 시 삽입하지 않음.
    """
    create_population_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    # key = (
    #     _as_str(record.get("statsYm")),
    #     _as_str(record.get("admmCd")),
    #     _as_str(record.get("dongNm")),
    #     _as_str(record.get("tong")),
    #     _as_str(record.get("ban")),
    # )
    #
    # # 중복 확인
    # cursor.execute(
    #     f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE statsYm=? AND admmCd=? AND dongNm=? AND tong=? AND ban=?",
    #     key
    # )
    # count = cursor.fetchone()[0]
    count = 0

    if count == 0:
        # 1) 명시적 컬럼 목록(정확한 필드 대응)
        columns = [
            "statsYm", "admmCd", "ctpvNm", "sggNm", "dongNm", "tong", "ban",
            "totNmprCnt", "maleNmprCnt", "femlNmprCnt",
            "male0AgeNmprCnt", "male10AgeNmprCnt", "male20AgeNmprCnt", "male30AgeNmprCnt", "male40AgeNmprCnt",
            "male50AgeNmprCnt", "male60AgeNmprCnt", "male70AgeNmprCnt", "male80AgeNmprCnt", "male90AgeNmprCnt", "male100AgeNmprCnt",
            "feml0AgeNmprCnt", "feml10AgeNmprCnt", "feml20AgeNmprCnt", "feml30AgeNmprCnt", "feml40AgeNmprCnt",
            "feml50AgeNmprCnt", "feml60AgeNmprCnt", "feml70AgeNmprCnt", "feml80AgeNmprCnt", "feml90AgeNmprCnt", "feml100AgeNmprCnt",
            "stdgNm", "stdgCd", "liNm"
        ]  # 총 32개

        # 2) placeholder를 컬럼 수에 맞춰 자동 생성(오타 방지)
        placeholders = ",".join(["?"] * len(columns))

        insert_query = f"INSERT INTO {TABLE_NAME} ({','.join(columns)}) VALUES ({placeholders})"

        # 3) 값 매핑(문자/정수 변환 포함, 컬럼 순서와 1:1 대응)
        values = (
            _as_str(record.get("statsYm")),
            _as_str(record.get("admmCd")),
            _as_str(record.get("ctpvNm")),
            _as_str(record.get("sggNm")),
            _as_str(record.get("dongNm")),
            _as_str(record.get("tong")),
            _as_str(record.get("ban")),
            _as_int(record.get("totNmprCnt")),
            _as_int(record.get("maleNmprCnt")),
            _as_int(record.get("femlNmprCnt")),
            _as_int(record.get("male0AgeNmprCnt")),
            _as_int(record.get("male10AgeNmprCnt")),
            _as_int(record.get("male20AgeNmprCnt")),
            _as_int(record.get("male30AgeNmprCnt")),
            _as_int(record.get("male40AgeNmprCnt")),
            _as_int(record.get("male50AgeNmprCnt")),
            _as_int(record.get("male60AgeNmprCnt")),
            _as_int(record.get("male70AgeNmprCnt")),
            _as_int(record.get("male80AgeNmprCnt")),
            _as_int(record.get("male90AgeNmprCnt")),
            _as_int(record.get("male100AgeNmprCnt")),
            _as_int(record.get("feml0AgeNmprCnt")),
            _as_int(record.get("feml10AgeNmprCnt")),
            _as_int(record.get("feml20AgeNmprCnt")),
            _as_int(record.get("feml30AgeNmprCnt")),
            _as_int(record.get("feml40AgeNmprCnt")),
            _as_int(record.get("feml50AgeNmprCnt")),
            _as_int(record.get("feml60AgeNmprCnt")),
            _as_int(record.get("feml70AgeNmprCnt")),
            _as_int(record.get("feml80AgeNmprCnt")),
            _as_int(record.get("feml90AgeNmprCnt")),
            _as_int(record.get("feml100AgeNmprCnt")),
            _as_str(record.get("stdgNm")),
            _as_str(record.get("stdgCd")),
            _as_str(record.get("liNm")),
        )

        # (선택) 방어: 컬럼 수와 값 수가 꼭 일치하는지 확인
        if len(columns) != len(values):
            raise ValueError(f"Column count ({len(columns)}) != values count ({len(values)})")

        cursor.execute(insert_query, values)
        conn.commit()
        print(f"[INSERT] 레코드가 성공적으로 삽입되었습니다.")
    else:
        print(f"[SKIP] 이미 존재합니다. 삽입을 건너뜁니다.")

    conn.close()

# ===== UPDATE =====
def population_update_record(record: Dict[str, Any]):
    """
    복합키(statsYm, admmCd, dongNm, tong, ban)로 대상 행을 찾아 **키 외의 모든 컬럼**을 업데이트.
    사용자 스타일의 명시적 컬럼 매핑과 위치 파라미터 사용.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    key = (
        _as_str(record.get("statsYm")),
        _as_str(record.get("admmCd")),
        _as_str(record.get("dongNm")),
        _as_str(record.get("tong")),
        _as_str(record.get("ban")),
    )

    # 존재 여부 확인
    cursor.execute(
        f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE statsYm=? AND admmCd=? AND dongNm=? AND tong=? AND ban=?",
        key
    )
    exists = cursor.fetchone()[0]

    if exists == 0:
        print(f"[MISS] {key} 는 존재하지 않습니다. 업데이트를 건너뜁니다.")
    else:
        update_query = f"""
            UPDATE {TABLE_NAME}
               SET ctpvNm            = ?,
                   sggNm             = ?,
                   totNmprCnt        = ?,
                   maleNmprCnt       = ?,
                   femlNmprCnt       = ?,
                   male0AgeNmprCnt   = ?,
                   male10AgeNmprCnt  = ?,
                   male20AgeNmprCnt  = ?,
                   male30AgeNmprCnt  = ?,
                   male40AgeNmprCnt  = ?,
                   male50AgeNmprCnt  = ?,
                   male60AgeNmprCnt  = ?,
                   male70AgeNmprCnt  = ?,
                   male80AgeNmprCnt  = ?,
                   male90AgeNmprCnt  = ?,
                   male100AgeNmprCnt = ?,
                   feml0AgeNmprCnt   = ?,
                   feml10AgeNmprCnt  = ?,
                   feml20AgeNmprCnt  = ?,
                   feml30AgeNmprCnt  = ?,
                   feml40AgeNmprCnt  = ?,
                   feml50AgeNmprCnt  = ?,
                   feml60AgeNmprCnt  = ?,
                   feml70AgeNmprCnt  = ?,
                   feml80AgeNmprCnt  = ?,
                   feml90AgeNmprCnt  = ?,
                   feml100AgeNmprCnt = ?,
                   stdgNm           = ?,
                   stdgCd           = ?,
                   liNm             = ?
             WHERE statsYm=? AND admmCd=? AND dongNm=? AND tong=? AND ban=?
        """
        cursor.execute(update_query, (
            _as_str(record.get("ctpvNm")),
            _as_str(record.get("sggNm")),
            _as_int(record.get("totNmprCnt")),
            _as_int(record.get("maleNmprCnt")),
            _as_int(record.get("femlNmprCnt")),
            _as_int(record.get("male0AgeNmprCnt")),
            _as_int(record.get("male10AgeNmprCnt")),
            _as_int(record.get("male20AgeNmprCnt")),
            _as_int(record.get("male30AgeNmprCnt")),
            _as_int(record.get("male40AgeNmprCnt")),
            _as_int(record.get("male50AgeNmprCnt")),
            _as_int(record.get("male60AgeNmprCnt")),
            _as_int(record.get("male70AgeNmprCnt")),
            _as_int(record.get("male80AgeNmprCnt")),
            _as_int(record.get("male90AgeNmprCnt")),
            _as_int(record.get("male100AgeNmprCnt")),
            _as_int(record.get("feml0AgeNmprCnt")),
            _as_int(record.get("feml10AgeNmprCnt")),
            _as_int(record.get("feml20AgeNmprCnt")),
            _as_int(record.get("feml30AgeNmprCnt")),
            _as_int(record.get("feml40AgeNmprCnt")),
            _as_int(record.get("feml50AgeNmprCnt")),
            _as_int(record.get("feml60AgeNmprCnt")),
            _as_int(record.get("feml70AgeNmprCnt")),
            _as_int(record.get("feml80AgeNmprCnt")),
            _as_int(record.get("feml90AgeNmprCnt")),
            _as_int(record.get("feml100AgeNmprCnt")),
            _as_str(record.get("stdgNm")),
            _as_str(record.get("stdgCd")),

            # WHERE 키
            key[0], key[1], key[2], key[3], key[4]
        ))
        conn.commit()
        print(f"[UPDATE] {key} 레코드를 성공적으로 업데이트했습니다.")

    conn.close()


# ===== DELETE =====
def population_delete_record(statsYm: str, admmCd: str, dongNm: str, tong: str, ban: str):
    """
    복합키 기준 레코드 삭제.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    key = (_as_str(statsYm), _as_str(admmCd), _as_str(dongNm), _as_str(tong), _as_str(ban))

    cursor.execute(
        f"DELETE FROM {TABLE_NAME} WHERE statsYm=? AND admmCd=? AND dongNm=? AND tong=? AND ban=?",
        key
    )
    if cursor.rowcount == 0:
        print(f"[MISS] {key} 는 존재하지 않습니다. 삭제를 건너뜁니다.")
    else:
        conn.commit()
        print(f"[DELETE] {key} 레코드를 성공적으로 삭제했습니다.")

    conn.close()


# ===== READ =====
def population_read_db(
    statsYm: str = "",
    admmCd: str = "",
    ctpvNm: str = "",
    sggNm: str = "",
    dongNm: str = "",
    tong: str = "",
    ban: str = "",
    limit: int = 130
) -> List[Dict[str, Any]]:
    """
    조건부 검색. (부분 일치: 명칭류 LIKE, 코드/월/통/반: = )
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params: List[Any] = []

    if statsYm:
        query += " AND statsYm = ?"
        params.append(_as_str(statsYm))
    if admmCd:
        query += " AND admmCd = ?"
        params.append(_as_str(admmCd))
    if ctpvNm:
        query += " AND ctpvNm LIKE ?"
        params.append(f"%{_as_str(ctpvNm)}%")
    if sggNm:
        query += " AND sggNm LIKE ?"
        params.append(f"%{_as_str(sggNm)}%")
    if dongNm:
        query += " AND dongNm LIKE ?"
        params.append(f"%{_as_str(dongNm)}%")
    if tong:
        query += " AND tong = ?"
        params.append(_as_str(tong))
    if ban:
        query += " AND ban = ?"
        params.append(_as_str(ban))

    query += " ORDER BY statsYm, ctpvNm, sggNm, dongNm, tong, ban"
    query += " LIMIT ?"
    params.append(int(limit))

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
