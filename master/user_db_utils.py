import os
import sqlite3
import datetime

from config import MASTER_DB_PATH

# 공통 변수 설정
DB_FILENAME = os.path.join(MASTER_DB_PATH, "tash_data.db")
TABLE_NAME = "user_data"

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
            phone_number TEXT,
            nick_name TEXT,
            access_token TEXT,
            apt_key TEXT,
            villa_key   TEXT,
            sanga_key   TEXT,
            registration_date TEXT,  -- 가입일자
            cancellation_date TEXT,  -- 탈퇴일자
            recharge_sms_count INTEGER DEFAULT 0,   -- 충전문자건수(건당 100원)
            recharge_amount INTEGER DEFAULT 0,   -- 충전금액(등기부발급-건당 1000원)
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
                user_id, user_name, user_passwd, phone_number, nick_name, access_token, 
                apt_key, villa_key, sanga_key, registration_date, cancellation_date, 
                recharge_sms_count, recharge_amount,
                etc
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        cursor.execute(insert_query, (
            user_id,
            record.get("user_name") or user_id,
            record.get("user_passwd"),
            record.get("phone_number"),
            record.get("nick_name"),
            record.get("access_token"),
            record.get("apt_key"),
            record.get("villa_key"),
            record.get("sanga_key"),
            record.get("registration_date") or datetime.datetime.now().strftime("%Y-%m-%d"),
            record.get("cancellation_date"),
            record.get("recharge_sms_count") if record.get("recharge_sms_count") is not None else 0,
            record.get("recharge_amount") if record.get("recharge_amount") is not None else 0,
            record.get("etc")
        ))
        conn.commit()
        print(f"user_id {user_id} 값의 레코드가 성공적으로 삽입되었습니다.")
    else:
        print(f"user_id {user_id} 는 이미 존재합니다. 삽입을 건너뜁니다.")

    conn.close()


def user_update_record(record):
    """
    단일 레코드를 user_id를 기준으로 업데이트합니다.
    user_id가 존재하지 않을 경우 업데이트를 건너뜁니다.

    파라미터:
        record (dict): {
            "user_id": str,
            "user_name": str,
            "user_passwd": str,
            "phone_number": str,
            "nick_name": str,
            "access_token": str,
            "apt_key": str,
            "villa_key": str,
            "sanga_key": str,
            "registration_date": str,
            "cancellation_date": str,
            "recharge_sms_count": int,
            "recharge_amount": float,
            "etc": str
        }
    """
    # 테이블이 없으면 생성
    #user_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    user_id = record.get("user_id")
    # 존재 여부 확인
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()[0]

    if exists == 0:
        print(f"user_id {user_id} 는 존재하지 않습니다. 업데이트를 건너뜁니다.")
    else:
        update_query = f"""
            UPDATE {TABLE_NAME}
               SET user_name            = ?,
                   user_passwd          = ?,
                   phone_number         = ?,
                   nick_name            = ?,
                   access_token         = ?,
                   apt_key              = ?,
                   villa_key            = ?,
                   sanga_key            = ?,
                   registration_date    = ?,
                   cancellation_date    = ?,
                   recharge_sms_count   = ?,
                   recharge_amount      = ?,
                   etc                  = ?
             WHERE user_id = ?
        """
        cursor.execute(update_query, (
            record.get("user_name"),
            record.get("user_passwd"),
            record.get("phone_number"),
            record.get("nick_name"),
            record.get("access_token"),
            record.get("apt_key"),
            record.get("villa_key"),
            record.get("sanga_key"),
            record.get("registration_date"),
            record.get("cancellation_date"),
            record.get("recharge_sms_count"),
            record.get("recharge_amount"),
            record.get("etc"),
            user_id
        ))
        conn.commit()
        print(f"user_id {user_id} 레코드를 성공적으로 업데이트했습니다.")

    conn.close()

# 삭제
def user_delete_record(user_id):
    """
    user_id를 기준으로 레코드를 삭제합니다.
    존재하지 않을 경우 삭제를 건너뜁니다.

    파라미터:
        user_id (str): 삭제할 사용자 ID
    """
    # 테이블이 없으면 생성
    #user_create_table()

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    # 삭제 실행
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    if cursor.rowcount == 0:
        print(f"user_id {user_id} 는 존재하지 않습니다. 삭제를 건너뜁니다.")
    else:
        conn.commit()
        print(f"user_id {user_id} 레코드를 성공적으로 삭제했습니다.")

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


def verify_user(user_id: str, password: str) -> bool:
    """
    SQLite에 저장된 user_data 테이블을 조회해서
    user_id, password 쌍이 유효한지 확인합니다.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_passwd FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    stored_pass = row[0]
    # 단순 비교; 필요시 해시 비교 로직으로 교체
    return stored_pass == password
