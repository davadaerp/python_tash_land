import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = os.path.join(BASE_DIR, "landing.db")
TABLE_NAME = "trial"


def trial_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def trial_create_table():
    """
    landing.db 안에 trial 테이블을 생성합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (TABLE_NAME,)
    )
    table_exists = cursor.fetchone() is not None

    if not table_exists:
        cursor.execute(f"""
            CREATE TABLE {TABLE_NAME} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                category TEXT,
                memo TEXT,
                privacy_agree TEXT,
                approve_status TEXT DEFAULT 'pending',
                approved_at TEXT,
                approved_message TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        print(f"테이블 '{TABLE_NAME}' 생성 완료.")

    conn.close()


def trial_insert_single(name, email, phone, category, memo, privacy_agree):
    """
    무료체험 요청 1건을 저장합니다.
    """
    trial_ensure_schema()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    now_str = trial_now_str()

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            name, email, phone, category, memo, privacy_agree,
            approve_status, approved_at, approved_message,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_query, (
            name,
            email,
            phone,
            category,
            memo,
            privacy_agree,
            "pending",
            None,
            None,
            now_str,
            now_str
        ))
        conn.commit()
        inserted_id = cursor.lastrowid
        return trial_select_single(inserted_id)
    except Exception as e:
        print("무료체험 요청 저장 오류:", e)
        return None
    finally:
        conn.close()


def trial_select_single(trial_id):
    """
    id 기준 단건 조회
    """
    trial_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (int(trial_id),))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print("무료체험 단건 조회 오류:", e)
        return None
    finally:
        conn.close()

def trial_delete_single(trial_id):
    """
    무료체험 요청 삭제
    """
    trial_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"DELETE FROM {TABLE_NAME} WHERE id = ?",
            (int(trial_id),)
        )
        conn.commit()

        return cursor.rowcount > 0
    except Exception as e:
        print("무료체험 삭제 오류:", e)
        return False
    finally:
        conn.close()

# 이메일 폰체크함
def trial_select_by_email_or_phone(email, phone):
    """
    이메일 또는 전화번호로 기존 무료체험 신청 이력이 있는지 확인합니다.
    둘 중 하나라도 일치하면 해당 레코드를 반환합니다.
    """
    trial_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"""
            SELECT *
            FROM {TABLE_NAME}
            WHERE email = ? OR phone = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (email, phone)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print("무료체험 중복 조회 오류:", e)
        return None
    finally:
        conn.close()


def trial_ensure_column(cursor, column_name, column_sql):
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        cursor.execute(f"ALTER TABLE {TABLE_NAME} ADD COLUMN {column_name} {column_sql}")


def trial_ensure_schema():
    """
    기존 trial 테이블에 승인 관련 컬럼이 없으면 자동 추가합니다.
    """
    trial_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    try:
        trial_ensure_column(cursor, "approve_status", "TEXT DEFAULT 'pending'")
        trial_ensure_column(cursor, "approved_at", "TEXT")
        trial_ensure_column(cursor, "approved_message", "TEXT")
        conn.commit()
    except Exception as e:
        print("trial 스키마 보강 오류:", e)
    finally:
        conn.close()


def trial_read_list(page=1, page_size=50, approve_status=""):
    """
    무료체험 요청 목록 조회
    최신 요청(id DESC) 순으로 반환
    """
    trial_ensure_schema()

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    page = max(int(page or 1), 1)
    page_size = max(int(page_size or 50), 1)
    offset = (page - 1) * page_size

    where_sql = ""
    params = []

    if approve_status:
        where_sql = "WHERE approve_status = ?"
        params.append(approve_status)

    try:
        count_query = f"""
             SELECT COUNT(*) AS cnt
             FROM {TABLE_NAME}
             {where_sql}
         """
        cursor.execute(count_query, params)
        total_count = cursor.fetchone()["cnt"]

        list_query = f"""
             SELECT *
             FROM {TABLE_NAME}
             {where_sql}
             ORDER BY id DESC
             LIMIT ? OFFSET ?
         """
        cursor.execute(list_query, params + [page_size, offset])
        rows = cursor.fetchall()

        items = [dict(row) for row in rows]

        return {
            "result": "Success",
            "items": items,
            "page": page,
            "page_size": page_size,
            "total_count": total_count
        }
    except Exception as e:
        print("무료체험 목록 조회 오류:", e)
        return {
            "result": "Fail",
            "items": [],
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "message": "무료체험 목록 조회 중 오류가 발생했습니다."
        }
    finally:
        conn.close()


def trial_approve_single(trial_id, approved_message):
    """
    무료체험 요청 승인 처리
    """
    trial_ensure_schema()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    now_str = trial_now_str()

    try:
        cursor.execute(
            f"""
             UPDATE {TABLE_NAME}
             SET approve_status = ?,
                 approved_at = ?,
                 approved_message = ?,
                 updated_at = ?
             WHERE id = ?
             """,
            ("approved", now_str, approved_message, now_str, int(trial_id))
        )
        conn.commit()

        if cursor.rowcount < 1:
            return None

        return trial_select_single(trial_id)
    except Exception as e:
        print("무료체험 승인 처리 오류:", e)
        return None
    finally:
        conn.close()