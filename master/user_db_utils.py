import os
import sqlite3

from config import MASTER_DB_PATH

# 공통 변수 설정
DB_FILENAME = os.path.join(MASTER_DB_PATH, "tash_data.db")
TABLE_NAME = "users_data"

def user_create_table():
    """
    사용자 정보를 저장하는 테이블을 생성합니다.
    필드: user_id (PK), user_name, user_passwd, nick_name, access_token, etc
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            user_id TEXT PRIMARY KEY,
            user_name TEXT,
            user_passwd TEXT,
            user_phone_number TEXT,
            nick_name TEXT,
            access_token TEXT,
            apt_key TEXT,
            villa_key   TEXT,
            sanga_key   TEXT,
            registration_date TEXT,
            cancellation_date TEXT,  -- 탈퇴일자
            sms_charge_count TEXT,   -- 충전건수(건당 100원)
            recharge_amount TEXT,   -- 충전금액(건당 1000원)
            etc TEXT
        )
    """)
    conn.commit()
    conn.close()

def user_insert_record(record):
    """
    단일 레코드를 테이블에 삽입합니다.
    user_id를 기준으로 중복 여부를 확인하며, 중복되지 않을 경우에만 데이터를 삽입합니다.

    파라미터:
        record (dict): {
            "user_id": str,
            "user_name": str,
            "user_passwd": str,
            "nick_name": str,
            "access_token": str,
            "etc": str
        }
    """
    # 테이블이 없으면 생성
    user_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    user_id = record.get("user_id")
    # 동일한 user_id 값이 이미 존재하는지 확인
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]

    if count == 0:
        insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                user_id, user_name, user_passwd, nick_name, access_token, etc
            ) VALUES (?,?,?,?,?,?)
        """
        cursor.execute(insert_query, (
            user_id,
            record.get("user_name"),
            record.get("user_passwd"),
            record.get("nick_name"),
            record.get("access_token"),
            record.get("etc")
        ))
        conn.commit()
        print(f"user_id {user_id} 값의 레코드가 성공적으로 삽입되었습니다.")
    else:
        print(f"user_id {user_id} 는 이미 존재합니다. 삽입을 건너뜁니다.")

    conn.close()


def user_drop_table():
    """
    DB_FILENAME에 정의된 SQLite 데이터베이스에서 TABLE_NAME에 해당하는 테이블을 삭제합니다.
    테이블이 존재하지 않으면 아무런 오류 없이 넘어갑니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")


def user_read_db(user_id="", userName="", nickName=""):
    """
    SQLite DB에서 사용자 데이터를 읽어옵니다.
    파라미터 값에 따라 user_id, user_name, nick_name으로 필터링하여 최대 130건의 데이터를 반환합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row  # 각 행을 dict처럼 사용할 수 있게 함
    cur = conn.cursor()
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    if user_id:
        query += " AND user_id = ?"
        params.append(user_id)
    if userName:
        query += " AND user_name LIKE ?"
        params.append(f"%{userName}%")
    if nickName:
        query += " AND nick_name LIKE ?"
        params.append(f"%{nickName}%")
    query += " LIMIT 130"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]
