import os
import sqlite3
import datetime
from typing import Optional, Dict, List, Any
from config import MASTER_DB_PATH

# =========================================================
# 공통 변수
# =========================================================
DB_FILENAME = os.path.join(MASTER_DB_PATH, "master_data.db")
HIST_TABLE_NAME = "user_hist_data"

def _now_iso() -> str:
    # UTC 기준 ISO-8601 문자열 (YYYY-MM-DD HH:MM:SS)
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# =========================================================
# ✅ 1) user_hist_data 테이블 생성
# =========================================================
def user_hist_create_table() -> None:
    """
    사용자 이력 테이블 생성
    PK: (user_id, seq)  # user_id별 순번 증가
    kind: 구분 (SUBSCRIPTION, SMS_CHARGE 등)
    unit: 월/건수 (kind에 따라 의미가 달라짐)
    amount: 금액(원)
    status: 상태(active/request/canceled 등)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {HIST_TABLE_NAME} (
            user_id TEXT NOT NULL,
            seq INTEGER NOT NULL,                 -- user_id 별 순번
            kind TEXT NOT NULL,                   -- 구분: SUBSCRIPTION / SMS_CHARGE
            request_date TEXT,                    -- 요청일자
            start_date TEXT,                      -- 시작일자
            end_date TEXT,                        -- 종료일자
            unit INTEGER DEFAULT 0,               -- 월(구독)/건수(문자충전)
            amount INTEGER DEFAULT 0,             -- 금액
            status TEXT DEFAULT 'request',        -- 상태
            memo TEXT,                            -- 비고/메모(선택)
            created_at TEXT,
            updated_at TEXT,
            PRIMARY KEY (user_id, seq)
        )
    """)

    # 인덱스(조회 성능)
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{HIST_TABLE_NAME}_user_id ON {HIST_TABLE_NAME}(user_id)")
    # cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{HIST_TABLE_NAME}_kind ON {HIST_TABLE_NAME}(kind)")
    # cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{HIST_TABLE_NAME}_status ON {HIST_TABLE_NAME}(status)")
    # cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{HIST_TABLE_NAME}_request_date ON {HIST_TABLE_NAME}(request_date)")

    conn.commit()
    conn.close()


def _get_next_seq(conn: sqlite3.Connection, user_id: str) -> int:
    """
    user_id 별 seq 자동 증가 값 반환
    """
    cur = conn.cursor()
    cur.execute(
        f"SELECT COALESCE(MAX(seq), 0) + 1 FROM {HIST_TABLE_NAME} WHERE user_id = ?",
        (user_id,)
    )
    return int(cur.fetchone()[0])


# =========================================================
# ✅ 2) 입력(Create)
# =========================================================
def user_hist_insert_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    단일 이력 레코드 삽입.
    - seq가 없으면 user_id 기준으로 자동 생성
    - created_at/updated_at 자동 세팅
    반환: 삽입된 (user_id, seq) 포함 record
    """
    if record is None:
        raise ValueError("record가 필요합니다.")
    user_id = record.get("user_id")
    if not user_id:
        raise ValueError("user_id가 필요합니다.")
    kind = (record.get("kind") or "").strip()
    if not kind:
        raise ValueError("kind가 필요합니다. (예: 'SUBSCRIPTION' 또는 'SMS_CHARGE')")

    # 테이블 생성 보장
    user_hist_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    try:
        # seq 생성의 원자성 확보(간단 대응)
        conn.execute("BEGIN IMMEDIATE")

        seq = record.get("seq")
        if seq is None:
            seq = _get_next_seq(conn, user_id)

        created_at = record.get("created_at") or _now_iso()
        updated_at = record.get("updated_at") or created_at

        insert_sql = f"""
            INSERT INTO {HIST_TABLE_NAME} (
                user_id, seq, kind,
                request_date, start_date, end_date,
                unit, amount, status,
                memo,
                created_at, updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
        """
        conn.execute(insert_sql, (
            user_id,
            int(seq),
            kind,
            record.get("request_date"),
            record.get("start_date"),
            record.get("end_date"),
            int(record.get("unit") or 0),
            int(record.get("amount") or 0),
            record.get("status") or "request",
            record.get("memo"),
            created_at,
            updated_at
        ))

        conn.commit()

        out = dict(record)
        out["seq"] = int(seq)
        out["created_at"] = created_at
        out["updated_at"] = updated_at
        return out

    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"삽입 실패(중복 PK 등): {e}") from e
    finally:
        conn.close()


# =========================================================
# ✅ 3) 수정(Update - 전체 컬럼 세팅)
# =========================================================
def user_hist_update_record(record: Dict[str, Any]) -> int:
    """
    user_id + seq 기준으로 전체 필드 업데이트
    반환: 영향 행 수(0 또는 1)
    """
    if record is None:
        raise ValueError("record가 필요합니다.")
    user_id = record.get("user_id")
    seq = record.get("seq")
    if not user_id or seq is None:
        raise ValueError("user_id, seq가 필요합니다.")

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT 1 FROM {HIST_TABLE_NAME} WHERE user_id = ? AND seq = ?",
        (user_id, int(seq))
    )
    if cursor.fetchone() is None:
        conn.close()
        return 0

    updated_at = record.get("updated_at") or _now_iso()

    update_sql = f"""
        UPDATE {HIST_TABLE_NAME}
           SET kind         = ?,
               request_date = ?,
               start_date   = ?,
               end_date     = ?,
               unit         = ?,
               amount       = ?,
               status       = ?,
               memo         = ?,
               updated_at   = ?
         WHERE user_id = ?
           AND seq     = ?
    """
    cursor.execute(update_sql, (
        record.get("kind"),
        record.get("request_date"),
        record.get("start_date"),
        record.get("end_date"),
        record.get("unit") if record.get("unit") is not None else 0,
        record.get("amount") if record.get("amount") is not None else 0,
        record.get("status"),
        record.get("memo"),
        updated_at,
        user_id,
        int(seq)
    ))
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows


# =========================================================
# ✅ 4) 수정(Update - 존재하는 컬럼만 동적 업데이트)
# =========================================================
def user_hist_update_exist_record(record: Dict[str, Any]) -> int:
    """
    record에 '있는' 컬럼만 동적으로 UPDATE.
    - 키 필드(user_id, seq)는 업데이트 대상에서 제외
    - updated_at은 미지정 시 자동 갱신
    반환: 영향 행 수(0 또는 1)
    """
    if record is None:
        raise ValueError("record가 필요합니다.")

    user_id = record.get("user_id")
    seq = record.get("seq")
    if not user_id or seq is None:
        raise ValueError("user_id, seq가 필요합니다.")

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(
        f"SELECT 1 FROM {HIST_TABLE_NAME} WHERE user_id = ? AND seq = ?",
        (user_id, int(seq))
    )
    if cursor.fetchone() is None:
        conn.close()
        return 0

    KEY_FIELDS = {"user_id", "seq"}
    ALL_UPDATABLE_FIELDS = {
        "kind",
        "request_date",
        "start_date",
        "end_date",
        "unit",
        "amount",
        "status",
        "memo",
        "created_at",
        "updated_at",
    }

    fields_to_update = [
        k for k in record.keys()
        if k in ALL_UPDATABLE_FIELDS and k not in KEY_FIELDS
    ]

    if "updated_at" not in fields_to_update:
        fields_to_update.append("updated_at")
        record["updated_at"] = _now_iso()

    if not fields_to_update:
        conn.close()
        return 0

    set_clause = ", ".join(f"{col} = ?" for col in fields_to_update)
    params = [record.get(col) for col in fields_to_update]
    params.extend([user_id, int(seq)])

    sql = f"UPDATE {HIST_TABLE_NAME} SET {set_clause} WHERE user_id = ? AND seq = ?"
    cursor.execute(sql, params)
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows


# =========================================================
# ✅ 5) 삭제(Delete)
# =========================================================
def user_hist_delete_record(user_id: str, seq: int) -> int:
    """user_id + seq 기준 삭제. 반환: 영향 행수(0 또는 1)"""
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM {HIST_TABLE_NAME} WHERE user_id = ? AND seq = ?",
        (user_id, int(seq))
    )
    conn.commit()
    rows = cursor.rowcount
    conn.close()
    return rows


def user_hist_drop_table() -> None:
    """테이블 삭제."""
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {HIST_TABLE_NAME}")
    conn.commit()
    conn.close()


# =========================================================
# ✅ 6) 단일 조회(Read One)
# =========================================================
def get_user_hist_info_db(user_id: str, seq: int) -> Optional[Dict]:
    """
    user_id + seq 기준으로 1건 dict 반환
    없으면 None
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT *
          FROM {HIST_TABLE_NAME}
         WHERE user_id = ?
           AND seq = ?
         LIMIT 1
        """,
        (user_id, int(seq))
    )
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# =========================================================
# ✅ 7) 멀티 조회(Read Many)
# =========================================================
def user_hist_read_db(
    user_id: str = "",
    kind: str = "",
    status: str = "",
    date_from: str = "",
    date_to: str = "",
    limit: int = 200
) -> List[Dict]:
    """
    이력 목록 조회
    - user_id: 정확일치
    - kind: 정확일치 (SUBSCRIPTION, SMS_CHARGE 등)
    - status: 정확일치
    - date_from/date_to: request_date 기준 범위(문자열 비교 가능하게 YYYY-MM-DD 또는 ISO 권장)
    - limit: 기본 200
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = f"SELECT * FROM {HIST_TABLE_NAME} WHERE 1=1"
    params: List[Any] = []

    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if kind:
        query += " AND kind = ?"
        params.append(kind)
    if status:
        query += " AND status = ?"
        params.append(status)
    if date_from:
        query += " AND request_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND request_date <= ?"
        params.append(date_to)

    query += " ORDER BY user_id, seq DESC"
    query += f" LIMIT {int(limit)}"

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# =========================================================
# ✅ (선택) 편의 함수: 구독/충전 이력 한방 입력 예시
# =========================================================
def add_subscription_hist(
    user_id: str,
    months: int,
    amount: int,
    status: str = "request",
    request_date: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    memo: str = ""
) -> Dict[str, Any]:
    """
    구독 이력 입력 편의 함수
    months: 0=체험, 1/2/3/6/12...
    """
    rec = {
        "user_id": user_id,
        "kind": "SUBSCRIPTION",
        "request_date": request_date or _now_iso(),
        "start_date": start_date,
        "end_date": end_date,
        "unit": int(months),
        "amount": int(amount),
        "status": status,
        "memo": memo,
    }
    return user_hist_insert_record(rec)


def add_sms_charge_hist(
    user_id: str,
    count: int,
    amount: int,
    status: str = "request",
    request_date: Optional[str] = None,
    memo: str = ""
) -> Dict[str, Any]:
    """
    문자충전 이력 입력 편의 함수
    count: 충전 건수
    """
    rec = {
        "user_id": user_id,
        "kind": "SMS_CHARGE",
        "request_date": request_date or _now_iso(),
        "unit": int(count),
        "amount": int(amount),
        "status": status,
        "memo": memo,
    }
    return user_hist_insert_record(rec)

#========================================================
# ✅ (선택) 편의 함수: 체험 신청 이력 건수 조회
def count_user_trial_hist_db(user_id: str) -> int:
    """
    체험(1주, plan=0) 신청 이력 건수
    - kind='SUBSCRIPTION'
    - unit=0  (체험 플랜을 0으로 저장한다는 전제)
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT COUNT(*)
          FROM {HIST_TABLE_NAME}
         WHERE user_id = ?
        """,
        (user_id,)
    )
    cnt = cursor.fetchone()[0] or 0
    conn.close()
    return int(cnt)