# 법정동코드 생성 및 변환 유틸리티
# -*- coding: utf-8 -*-
import os
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Iterable, Tuple, Any
from crawling.lawd_code_db_utils import get_lawd_by_code

from config import CRAWLING_BASE_PATH

DB_PATH = os.path.join(CRAWLING_BASE_PATH, "crawling_data.db")
TABLE_NAME = "crawl_lawd_codes"

# ==========================
# 공용: DB 커넥션
# ==========================
def get_conn(db_path: str = DB_PATH) -> sqlite3.Connection:
    # timeout을 30초로 설정하여 DB 잠금 시 대기하도록 함
    conn = sqlite3.connect(db_path, timeout=30)
    try:
        # WAL 모드 설정 시 발생할 수 있는 I/O 에러를 catch
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
    except sqlite3.OperationalError as e:
        if "disk I/O error" in str(e):
            print(f"⚠️ Disk I/O Error 감지: {db_path}. 잠시 후 재시도 권장.")
        # 에러가 발생해도 커넥션은 유지하거나, 필요 시 다시 생성 로직 추가
    return conn


# ==========================
# 1) 검색할 법정동코드 저장 테이블 초기화
# ==========================
def init_crawl_lawd_codes_db(db_path: str = DB_PATH) -> None:
    """
    crawl_lawd_codes 테이블 초기화
    - id: INTEGER PRIMARY KEY AUTOINCREMENT
    - lawd_cd + trade_type 복합 인덱스 생성
    """
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        lawd_cd    TEXT NOT NULL,
        lawd_name  TEXT NOT NULL,
        batch_start_date TEXT,
        batch_end_date TEXT,
        batch_cycle TEXT DEFAULT '5',   -- 배치주기(5일)
        batch_count INTEGER DEFAULT 0,  -- 배치총건수
        trade_type TEXT DEFAULT 'SG'    -- 거래유형 (APT: 아파트, VILLA: 빌라, SG: 상가)
    );
    """

    index_sql = f"""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_{TABLE_NAME}_lawd_trade
    ON {TABLE_NAME} (lawd_cd, trade_type);
    """

    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(ddl)
        cur.execute(index_sql)
        conn.commit()
        print(f"✅ {TABLE_NAME} 테이블과 복합 인덱스가 정상 생성되었습니다.")
    finally:
        conn.close()

# ==========================
# 2) 단건/대량 입력(UPSERT) 함수
# ==========================
def insert_crawl_lawd_code(
    lawd_cd: str,
    lawd_name: str,
    batch_start_date: Optional[str] = None,
    batch_end_date: Optional[str] = None,
    batch_cycle: Optional[str] = None,
    batch_count: Optional[int] = None,
    trade_type: str = "SG",
    db_path: str = DB_PATH
) -> int:
    """
    단건 입력/업데이트(UPSERT)
    - lawd_cd가 존재하면 lawd_name, trade_type 업데이트
    - 존재하지 않으면 INSERT
    반환: 변경된 행 수(rowcount)
    """
    sql = f"""
    INSERT INTO {TABLE_NAME} (lawd_cd, lawd_name, batch_start_date, batch_end_date, batch_cycle, batch_count, trade_type)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(lawd_cd, trade_type) DO UPDATE SET
        lawd_name = excluded.lawd_name;
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, (lawd_cd, lawd_name, batch_start_date, batch_end_date, batch_cycle, batch_count, trade_type))
        conn.commit()
        print(f"🟢 UPSERT: {lawd_cd} / {lawd_name} / {trade_type}")
        return cur.rowcount
    finally:
        conn.close()


def bulk_insert_crawl_lawd_codes(
    rows: Iterable[Tuple[str, str, str]],
    db_path: str = DB_PATH
) -> int:
    """
    대량 입력/업데이트(UPSERT)
    rows: (lawd_cd, lawd_name, trade_type) 튜플 반복자
    반환: 처리 건수
    """
    sql = f"""
    INSERT INTO {TABLE_NAME} (lawd_cd, lawd_name, trade_type)
    VALUES (?, ?, ?)
    ON CONFLICT(lawd_cd, trade_type) DO UPDATE SET
        lawd_name = excluded.lawd_name;
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.executemany(sql, rows)
        conn.commit()
        count = cur.rowcount if cur.rowcount is not None else 0
        print(f"🟢 BULK UPSERT 처리: {count}건")
        return count
    finally:
        conn.close()

# ==========================
# 3) 수정
# ==========================
def update_crawl_lawd_code_fields(
    lawd_cd: str,
    trade_type: str,
    batch_start_date: Optional[str] = None,
    batch_end_date: Optional[str] = None,
    batch_cycle: Optional[str] = None,
    batch_count: Optional[int] = None,
    lawd_name: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """
    제공된(=None이 아닌) 필드만 부분 업데이트.
    """
    allowed = {
        "batch_start_date": batch_start_date,
        "batch_end_date": batch_end_date,
        "batch_cycle": batch_cycle,
        "batch_count": batch_count,
        "lawd_name": lawd_name,
    }
    sets = []
    vals = []
    for k, v in allowed.items():
        if v is not None:
            sets.append(f"{k} = ?")
            vals.append(v)

    if not sets:
        print("⚠️ 업데이트할 필드가 없습니다.")
        return 0

    vals.extend([lawd_cd, trade_type])

    sql = f"""
    UPDATE {TABLE_NAME}
       SET {", ".join(sets)}
     WHERE lawd_cd = ? AND trade_type = ?;
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, vals)
        conn.commit()
        print(f"✏️ UPDATE({lawd_cd},{trade_type}) → {cur.rowcount}건")
        return cur.rowcount or 0
    finally:
        conn.close()

# ==========================
# 단순 버전: 배치주기 업데이트 (trade_type 없으면 전체)
# ==========================
def update_batch_cycle_by_trade_type(trade_type: Optional[str], batch_cycle: str, db_path: str = DB_PATH) -> int:
    """
    trade_type이 지정되면 해당 구분만,
    없으면 전체 레코드의 batch_cycle을 업데이트합니다.
    """
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        if trade_type:  # 특정 구분만 업데이트
            cur.execute(f"""
                UPDATE {TABLE_NAME}
                   SET batch_cycle = ?
                 WHERE trade_type = ?;
            """, (batch_cycle, trade_type))
            print(f"🔄 UPDATE batch_cycle='{batch_cycle}' WHERE trade_type='{trade_type}' → {cur.rowcount}건")
        else:  # trade_type 없으면 전체 업데이트
            cur.execute(f"""
                UPDATE {TABLE_NAME}
                   SET batch_cycle = ?;
            """, (batch_cycle,))
            print(f"🔄 UPDATE batch_cycle='{batch_cycle}' (전체) → {cur.rowcount}건")

        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()

# ==========================
# 3) 조회
# ==========================
def search_crawl_lawd_codes(
    db_path: str = DB_PATH,
    lawd_cd: Optional[str] = None,
    lawd_name: Optional[str] = None,
    trade_type: Optional[str] = None
) -> Optional[List[Dict[str, str]]]:
    """
    crawl_lawd_codes에서 조건(lawd_cd, lawd_name, trade_type)에 맞는 레코드를 조회.
    반환: [{"lawd_cd": "...", "lawd_name": "...", "trade_type": "..."}] 리스트
    조건이 없으면 전체 조회.
    """
    conn = get_conn(db_path)

    try:
        sql = f"SELECT id, lawd_cd, lawd_name, batch_start_date, batch_end_date, batch_cycle, batch_count, trade_type FROM {TABLE_NAME}"
        params = []
        conditions = []

        if lawd_cd:
            conditions.append("lawd_cd = ?")
            params.append(str(lawd_cd))
        if lawd_name:
            conditions.append("lawd_name LIKE ?")
            params.append(f"%{lawd_name}%")
        if trade_type:
            conditions.append("trade_type = ?")
            params.append(str(trade_type))

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        sql += " ORDER BY trade_type, lawd_cd;"

        cur = conn.execute(sql, params)
        rows = cur.fetchall()

        if not rows:
            print("⚠️ 검색 결과가 없습니다.")
            return None

        results = [{"id": r[0], "lawd_cd": r[1], "lawd_name": r[2], "batch_end_date": r[4], "batch_count": r[6], "trade_type": r[7]} for r in rows]

        print(f"\n=== 검색 결과 ({len(results)}건) ===")
        for row in results:
            print(f"{row['id']}  | {row['lawd_cd']}  | {row['lawd_name']}  | {row['batch_count']} |  {row['trade_type']}")

        return results
    finally:
        conn.close()

# ==========================
# 3) 단건 조회 (lawd_cd + trade_type)
def get_crawl_lawd_code_by_cd_type(
    lawd_cd: str,
    trade_type: str,
    db_path: str = DB_PATH
) -> Optional[Dict[str, str]]:
    """lawd_cd + trade_type로 단건 조회. 없으면 None"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, lawd_cd, lawd_name, batch_start_date, batch_end_date, batch_cycle, batch_count, trade_type  FROM {TABLE_NAME} "
            "WHERE lawd_cd = ? AND trade_type = ? LIMIT 1;",
            (lawd_cd, trade_type)
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "lawd_cd": row[1],
            "lawd_name": row[2],
            "batch_start_date": row[3],
            "batch_end_date": row[4],
            "batch_cycle": row[5],
            "batch_count": row[6],
            "trade_type": row[7]
        }
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능
# ==========================
def delete_crawl_lawd_code_by_cd(lawd_cd: str, db_path: str = DB_PATH) -> int:
    """법정동코드(lawd_cd)로 단건 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME} WHERE lawd_cd = ?;", (lawd_cd,))
        conn.commit()
        print(f"🗑️ DELETE by code: {lawd_cd} → {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()

# ==========================
# 4) 삭제 / 초기화 기능 (id 기준)
# ==========================
def delete_crawl_lawd_code_by_id(record_id: int, db_path: str = DB_PATH) -> int:
    """id로 단건 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?;", (int(record_id),))
        conn.commit()
        print(f"🗑️ DELETE by id: {record_id} → {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()


def delete_crawl_lawd_codes(
    db_path: str = DB_PATH,
    lawd_cd: Optional[str] = None,
    lawd_name: Optional[str] = None,
    trade_type: Optional[str] = None
) -> int:
    """
    조건 삭제(다건). 하나도 조건이 없으면 안전을 위해 삭제하지 않음.
    반환: 삭제 행 수
    """
    if not any([lawd_cd, lawd_name, trade_type]):
        print("⛔ 최소 한 가지 조건(lawd_cd, lawd_name, trade_type)이 필요합니다. 전체삭제 방지.")
        return 0

    conn = get_conn(db_path)
    try:
        sql = f"DELETE FROM {TABLE_NAME}"
        params = []
        conditions = []

        if lawd_cd:
            conditions.append("lawd_cd = ?")
            params.append(str(lawd_cd))
        if lawd_name:
            conditions.append("lawd_name LIKE ?")
            params.append(f"%{lawd_name}%")
        if trade_type:
            conditions.append("trade_type = ?")
            params.append(str(trade_type))

        sql += " WHERE " + " AND ".join(conditions)

        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        print(f"🗑️ 조건 삭제: {cur.rowcount}건")
        return cur.rowcount
    finally:
        conn.close()


def clear_crawl_lawd_codes(db_path: str = DB_PATH) -> int:
    """테이블의 모든 데이터(TRUNCATE 유사) 삭제. 반환: 삭제 행 수"""
    conn = get_conn(db_path)
    try:
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {TABLE_NAME};")
        conn.commit()
        print(f"🧹 CLEAR: {TABLE_NAME} 모든 행 삭제({cur.rowcount}건)")
        return cur.rowcount
    finally:
        conn.close()


def drop_crawl_lawd_codes_table(db_path: str = DB_PATH) -> None:
    """테이블 자체를 완전히 삭제(DROP TABLE)."""
    conn = get_conn(db_path)
    try:
        conn.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        conn.commit()
        print(f"[DROP] {TABLE_NAME} 테이블이 삭제되었습니다.")
    finally:
        conn.close()


# ==========================
# 5) 크롤링 락 획득/갱신 함수 (SQLite 전용)
# ==========================
def acquire_crawl_lock_sqlite(
    lawd_cd: Optional[str] = None,
    trade_type: Optional[str] = None,
    sync_id: Optional[str] = None,
    ttl_sec: int = 10800,
    db_path: str = DB_PATH,
) -> Tuple[bool, Dict[str, Any], int]:
    """
    crawl_lawd_codes에서 (lawd_cd, trade_type) 단위로 락 획득/갱신 시도.

    필요 컬럼(권장):
      - batch_status TEXT
      - batch_start_date TEXT
      - batch_end_date TEXT
      - lock_owner TEXT
      - lock_expires_at INTEGER

    반환:
      (ok, payload, http_status)
      - ok=True  -> 락 획득 성공
      - ok=False -> 다른 프로세스가 락 보유 중(409) 또는 관리대상 없음(404) 등
    """
    if not lawd_cd or not trade_type or not sync_id:
        return False, {"ok": False, "reason": "missing params", "error": "missing params"}, 400

    now_ts = int(time.time())
    expires_at = now_ts + int(ttl_sec)
    #
    start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_conn(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE;")  # ✅ 동시성 확보(쓰기 락 선점)

        # 1) 현재 상태 조회
        cur.execute(
            f"""SELECT batch_status, lock_owner, lock_expires_at, batch_start_date, batch_end_date
                FROM {TABLE_NAME}
                WHERE lawd_cd=? AND trade_type=?
                LIMIT 1""",
            (lawd_cd, trade_type)
        )
        row = cur.fetchone()
        if not row:
            # 관리 대상 없음 → 신규 삽입 및 락 획득
            lawd_row = get_lawd_by_code(lawd_cd)
            lawd_name = lawd_row["lawd_name"]
            print("⚠️ 관리 대상이 없습니다. 신규 삽입 및 락 획득 시도. lawd_name:", lawd_name)
            cur.execute(
                f"""
                INSERT INTO {TABLE_NAME} (
                    lawd_cd,
                    lawd_name,
                    trade_type,
                    batch_status,
                    batch_start_date,
                    batch_end_date,
                    batch_count,
                    lock_owner,
                    lock_expires_at
                ) VALUES (?, ?, ?, 'RUNNING', ?, '', 0, ?, ?)
                """,
                (lawd_cd, lawd_name, trade_type, start_date, sync_id, expires_at)
            )
            conn.commit()
            return True, {
                "ok": True,
                "reason": "lock acquired (insert)",
                "lock_owner": sync_id,
                "lock_expires_at": expires_at,
                "batch_start_date": start_date
            }, 200

        # hold lock 정보 파싱
        batch_end_str = (row["batch_end_date"] or "").strip()

        # ✅ COMPLETED(또는 FINISHED) 이후 40~48시간 hold
        # - batch_status가 COMPLETED인데, end_dt가 있고, 아직 hold window 안이면 "locked" 처리
        if batch_end_str:
            end_dt = datetime.strptime(batch_end_str, "%Y-%m-%d %H:%M:%S")
            hold_until = end_dt + timedelta(hours=48)
            if datetime.now() < hold_until:
                conn.rollback()
                return False, {
                    "ok": False,
                    "reason": "hold_window",
                    "batch_end_date": batch_end_str,
                    "hold_until": hold_until.strftime("%Y-%m-%d %H:%M:%S"),
                }, 409

        #
        batch_status = (row["batch_status"] or "READY").upper()
        lock_owner = row["lock_owner"]
        lock_expires = int(row["lock_expires_at"] or 0)

        # 2) 락 유효 판단
        lock_active = (batch_status == "RUNNING") and (lock_owner is not None) and (lock_expires >= now_ts)

        if lock_active and lock_owner != sync_id:
            # 다른 클라이언트가 작업 중
            conn.rollback()
            return False, {
                "ok": False,
                "reason": "locked",
                "locked_by": lock_owner,
                "lock_expires_at": lock_expires,
                "batch_status": batch_status
            }, 409

        # 3) 락 획득/갱신(내가 이미 owner거나, 만료된 락 선점)
        cur.execute(
            f"""UPDATE {TABLE_NAME}
                SET batch_status='RUNNING',
                    batch_start_date=?,
                    batch_end_date='',
                    lock_owner=?,
                    lock_expires_at=?
                WHERE lawd_cd=? AND trade_type=?""",
            (start_date, sync_id, expires_at, lawd_cd, trade_type)
        )

        conn.commit()
        return True, {
            "ok": True,
            "reason": "lock acquired",
            "lock_owner": sync_id,
            "lock_expires_at": expires_at,
            "batch_start_date": start_date
        }, 200

    except Exception as e:
        conn.rollback()
        return False, {"ok": False, "error": str(e)}, 500
    finally:
        conn.close()

# ==========================
# 6) 크롤링 락 해제 함수 (SQLite 전용)
def release_crawl_lock_sqlite(
    lawd_cd: str,
    trade_type: str,
    sync_id: str,
    final_status: str = "COMPLETED",
    db_path: str = DB_PATH,
) -> Tuple[bool, Dict[str, Any], int]:
    """
    (lawd_cd, trade_type) 락 해제 처리.
    - lock_owner == sync_id 인 경우에만 해제
    - 성공 시: lock_owner/lock_expires_at 해제 + batch_end_date 기록 + batch_status 갱신

    필요 컬럼:
      - lock_owner TEXT
      - lock_expires_at INTEGER
      - batch_end_date TEXT
      - batch_status TEXT
    """
    if not lawd_cd or not trade_type or not sync_id:
        return False, {"ok": False, "error": "missing params"}, 400

    end_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    final_status = (final_status or "COMPLETED").upper()

    conn = get_conn(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("BEGIN IMMEDIATE;")

        # owner 검증 + 해제
        cur.execute(
            f"""
            UPDATE {TABLE_NAME}
               SET lock_owner = NULL,
                   lock_expires_at = NULL,
                   batch_end_date = ?,
                   batch_status = ?
             WHERE lawd_cd = ?
               AND trade_type = ?
               AND lock_owner = ?
            """,
            (end_date, final_status, lawd_cd, trade_type, sync_id)
        )

        if cur.rowcount == 0:
            conn.rollback()
            # 케이스1) 레코드 자체 없음, 케이스2) owner 불일치, 케이스3) 이미 해제됨
            return False, {
                "ok": False,
                "error": "lock_not_owned_or_already_released",
                "lawd_cd": lawd_cd,
                "trade_type": trade_type,
                "sync_id": sync_id
            }, 409

        conn.commit()
        return True, {
            "ok": True,
            "reason": "released",
            "lawd_cd": lawd_cd,
            "trade_type": trade_type,
            "sync_id": sync_id,
            "batch_end_date": end_date,
            "batch_status": final_status
        }, 200

    except Exception as e:
        conn.rollback()
        return False, {"ok": False, "error": str(e)}, 500
    finally:
        conn.close()

# ==========================
# 사용 예시
# ==========================
if __name__ == "__main__":
    # 초기화
    #init_crawl_lawd_codes_db()

    # sample_data = {
    #     "운양동": "4157010300",
    #     "장기동": "4157010400",
    #     "구래동": "4157010500",
    # }

    # [수정] 단건 UPSERT 샘플: 배치 윈도우/사이클/카운트 함께 입력
    insert_crawl_lawd_code(
        "41570103xx",
        "경기도 김포시 배치동",
        "2025-10-01",
        "",
        "5",  # 5일
        0,
        "APT"
    )

    # [신규] 부분 수정 예시: batch_start_date, batch_count만 갱신
    # update_crawl_lawd_code_fields(
    #     "4157010500", "APT",
    #     batch_start_date="2025-11-01",
    #     batch_count=11
    # )

    # 대량 UPSERT
    # [신규] 대량 UPSERT 샘플(딕셔너리 방식: 행마다 제공된 필드만 반영)
    # bulk_upsert_crawl_lawd_codes_dict([
    #     {
    #         "lawd_cd": "4157010400", "lawd_name": "경기도 김포시 장기동", "trade_type": "APT",
    #         "batch_start_date": "2025-10-01", "batch_end_date": "2025-10-31", "batch_cycle": "7"
    #     },
    #     {
    #         "lawd_cd": "4157010500", "lawd_name": "경기도 김포시 구래동", "trade_type": "APT",
    #         "batch_cycle": "3", "batch_count": 10
    #     },
    # ])

    # # 조회 예시
    # search_crawl_lawd_codes(trade_type="SG")
    #
    # # 조건 삭제(예: 상가만 삭제)
    # delete_crawl_lawd_codes(trade_type="SG")
    #
    # # 단건 삭제
    # delete_crawl_lawd_code_by_cd("4113510900")
    #
    # # 데이터만 전체 삭제
    # clear_crawl_lawd_codes()
    #
    # # 테이블 삭제
    # drop_crawl_lawd_codes_table()
