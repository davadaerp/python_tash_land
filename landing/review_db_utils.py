import os
import sqlite3
from datetime import datetime
from math import ceil

# 공통 변수
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILENAME = os.path.join(BASE_DIR, "landing.db")
TABLE_NAME = "reviews"
DEFAULT_PAGE_SIZE = 3


def review_create_table():
    """
    landing.db 안에 reviews 테이블을 생성합니다.
    테이블이 없을 때만 생성합니다.
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
                writer TEXT,
                title TEXT,
                rating INTEGER,
                content TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        conn.commit()
        print(f"테이블 '{TABLE_NAME}' 생성 완료.")

    conn.close()


def review_now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def review_insert_single(writer, title, rating, content):
    """
    단일 후기 레코드를 삽입합니다.
    """
    review_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    insert_query = f"""
        INSERT INTO {TABLE_NAME} (
            writer, title, rating, content, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """

    now_str = review_now_str()

    try:
        cursor.execute(insert_query, (
            writer,
            title,
            max(1, min(5, int(rating))),
            content,
            now_str,
            now_str
        ))
        conn.commit()
        review_id = cursor.lastrowid
        return review_select_single(review_id)
    except Exception as e:
        print("후기 삽입 오류:", e)
        return None
    finally:
        conn.close()


def review_update_single(review_id, writer, title, rating, content):
    """
    id 기준으로 단일 후기 레코드를 수정합니다.
    """
    review_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    update_query = f"""
        UPDATE {TABLE_NAME}
        SET writer = ?,
            title = ?,
            rating = ?,
            content = ?,
            updated_at = ?
        WHERE id = ?
    """

    try:
        cursor.execute(update_query, (
            writer,
            title,
            max(1, min(5, int(rating))),
            content,
            review_now_str(),
            int(review_id)
        ))
        conn.commit()

        if cursor.rowcount < 1:
            return None

        return review_select_single(review_id)
    except Exception as e:
        print("후기 수정 오류:", e)
        return None
    finally:
        conn.close()


def review_delete_single(review_id):
    """
    id 기준으로 단일 후기 레코드를 삭제합니다.
    """
    review_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    delete_query = f"DELETE FROM {TABLE_NAME} WHERE id = ?"

    try:
        cursor.execute(delete_query, (int(review_id),))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print("후기 삭제 오류:", e)
        return False
    finally:
        conn.close()


def review_select_single(review_id):
    """
    id 기준으로 단일 후기 레코드를 조회합니다.
    """
    review_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    select_query = f"SELECT * FROM {TABLE_NAME} WHERE id = ?"

    try:
        cursor.execute(select_query, (int(review_id),))
        row = cursor.fetchone()
        return dict(row) if row else None
    except Exception as e:
        print("후기 단건 조회 오류:", e)
        return None
    finally:
        conn.close()


def review_read_list(page=1, page_size=None):
    """
    후기 목록을 페이지 단위로 조회합니다.
    """
    review_create_table()

    try:
        page = int(page or 1)
    except (TypeError, ValueError):
        page = 1

    if page < 1:
        page = 1

    try:
        page_size = int(page_size or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE

    if page_size < 1:
        page_size = DEFAULT_PAGE_SIZE

    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
        total_count = cursor.fetchone()[0]
        total_pages = max(1, ceil(total_count / page_size))

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * page_size

        cursor.execute(f"""
            SELECT *
            FROM {TABLE_NAME}
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """, (page_size, offset))
        rows = cursor.fetchall()
        items = [dict(row) for row in rows]

        return {
            "result": "Success",
            "items": items,
            "page": page,
            "page_size": page_size,
            "total_count": total_count,
            "total_pages": total_pages
        }
    except Exception as e:
        print("후기 목록 조회 오류:", e)
        return {
            "result": "Fail",
            "items": [],
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "total_pages": 1
        }
    finally:
        conn.close()