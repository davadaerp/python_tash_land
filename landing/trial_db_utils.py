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
    trial_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    now_str = trial_now_str()

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            name, email, phone, category, memo, privacy_agree, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    try:
        cursor.execute(insert_query, (
            name,
            email,
            phone,
            category,
            memo,
            privacy_agree,
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