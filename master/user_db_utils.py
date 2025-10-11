import os
import sqlite3
import datetime

from config import MASTER_DB_PATH

# 공통 변수 설정
DB_FILENAME = os.path.join(MASTER_DB_PATH, "tash_data.db")
TABLE_NAME = "user_data"

def _now_iso():
    # UTC 기준 ISO-8601 문자열 (YYYY-MM-DD HH:MM:SS)
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def user_create_table():
    """
    사용자 정보를 저장하는 테이블을 생성합니다.
    필드: 기존 + kakao_id, email, nick_name, profile_image, created_at, updated_at,
          access_token, refresh_token, token_expires_at
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            user_id TEXT PRIMARY KEY,   -- 차후 kakao_id로 대체 가능
            user_name TEXT,
            user_passwd TEXT,
            phone_number TEXT,
            apt_key TEXT,
            villa_key TEXT,
            sanga_key TEXT,
            registration_date TEXT,   -- 가입일자(카카오)
            cancellation_date TEXT,   -- 탈퇴일자
            recharge_sms_count INTEGER DEFAULT 0,   -- 충전문자건수(건당 100원)
            recharge_amount INTEGER DEFAULT 0,      -- 충전금액(등기부발급-건당 1000원)
            recharge_request_date TEXT,  -- 충전요청일자
            recharge_request_sms_count INTEGER DEFAULT 0, -- 충전요청문자건수(건당 100원)
            recharge_status TEXT DEFAULT 'canceled',     -- 충전상태 (active, canceled 등) : 차후 관리자 페이지에서 on/off 처리용
            subscription_start_date TEXT, -- 구독시작일자
            subscription_end_date TEXT,   -- 구독종료일자
            subscription_month INTEGER DEFAULT 1,    -- 구독월수(1, 3, 6, 12개월)
            subscription_payment  INTEGER DEFAULT 0, -- 구독결제금액(1개월: 3만원, 3개월: 5만원, 6개월: 7만원, 12개월: 10만원)
            subscription_status TEXT DEFAULT 'canceled',     -- 구독상태 (active, canceled 등) : 차후 관리자 페이지에서 on/off 처리용
            etc TEXT,
            -- 신규 스키마 (모두 TEXT)
            kakao_id TEXT,
            email TEXT,
            nick_name TEXT,
            profile_image TEXT,
            created_at TEXT,
            updated_at TEXT,
            access_token TEXT,
            refresh_token TEXT,
            token_expires_at TEXT
        )
    """)
    # kakao_id 인덱스
    cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_kakao_id ON {TABLE_NAME}(kakao_id)")
    conn.commit()
    conn.close()

def user_insert_record(record):
    """
    단일 레코드 삽입 (스키마에 맞춰 전체 컬럼 입력).
    created_at/updated_at은 미지정 시 자동 세팅.
    """
    user_create_table()  # 테이블 없으면 생성

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    user_id = record.get("user_id")
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]


    if count == 0:
        created_at = record.get("created_at") or _now_iso()
        updated_at = record.get("updated_at") or created_at

        insert_query = f"""
            INSERT INTO {TABLE_NAME} (
                user_id, user_name, user_passwd, phone_number,
                apt_key, villa_key, sanga_key,
                registration_date, cancellation_date,
                recharge_sms_count, recharge_amount,recharge_request_date, recharge_request_sms_count, recharge_status, etc,
                kakao_id, email, nick_name, profile_image,
                created_at, updated_at,
                access_token, refresh_token, token_expires_at
            ) VALUES (?,?,?,?, 
                      ?,?,?,
                      ?,?,
                      ?,?,?,?,?,
                      ?,
                      ?,?,?,?,
                      ?,?,
                      ?,?,?)
        """
        cursor.execute(insert_query, (
            user_id,
            record.get("user_name") or user_id,
            record.get("user_passwd"),
            record.get("phone_number"),

            record.get("apt_key"),
            record.get("villa_key"),
            record.get("sanga_key"),

            created_at,
            record.get("cancellation_date"),

            record.get("recharge_sms_count") if record.get("recharge_sms_count") is not None else 0,
            record.get("recharge_amount") if record.get("recharge_amount") is not None else 0,
            record.get("recharge_request_date"),
            record.get("recharge_request_sms_count") if record.get("recharge_request_sms_count") is not None else 0,
            record.get("recharge_status") or "",

            record.get("etc"),

            record.get("kakao_id"),
            record.get("email"),
            record.get("nick_name"),
            record.get("profile_image"),

            created_at,
            updated_at,

            record.get("access_token"),
            record.get("refresh_token"),
            record.get("token_expires_at"),
        ))
        conn.commit()
        print(f"user_id {user_id} 값의 레코드가 성공적으로 삽입되었습니다.")
    else:
        print(f"user_id {user_id} 는 이미 존재합니다. 삽입을 건너뜁니다.")

    conn.close()

def user_update_record(record):
    """
    단일 레코드를 user_id 기준으로 업데이트 (스키마에 맞춰 전체 컬럼 업데이트).
    updated_at은 미지정 시 자동 갱신.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    user_id = record.get("user_id")
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()[0]

    if exists == 0:
        print(f"user_id {user_id} 는 존재하지 않습니다. 업데이트를 건너뜁니다.")
    else:
        updated_at = record.get("updated_at") or _now_iso()

        update_query = f"""
            UPDATE {TABLE_NAME}
               SET user_name          = ?,
                   user_passwd        = ?,
                   phone_number       = ?,
                   apt_key            = ?,
                   villa_key          = ?,
                   sanga_key          = ?,
                   registration_date  = ?,
                   cancellation_date  = ?,
                   recharge_sms_count = ?,
                   recharge_amount    = ?,
                   recharge_request_date = ?,
                   recharge_request_sms_count = ?,
                   recharge_status    = ?,
                   etc                = ?,
                   kakao_id           = ?,
                   email              = ?,
                   nick_name          = ?,
                   profile_image      = ?,
                   created_at         = COALESCE(created_at, ?),  -- 비어있다면 초기화
                   updated_at         = ?,
                   access_token       = ?,
                   refresh_token      = ?,
                   token_expires_at   = ?
             WHERE user_id = ?
        """
        cursor.execute(update_query, (
            record.get("user_name"),
            record.get("user_passwd"),
            record.get("phone_number"),
            record.get("apt_key"),
            record.get("villa_key"),
            record.get("sanga_key"),
            record.get("registration_date"),
            record.get("cancellation_date"),
            record.get("recharge_sms_count"),
            record.get("recharge_amount"),
            record.get("recharge_request_date") or _now_iso(),
            record.get("recharge_request_sms_count"),
            record.get("recharge_status"),
            record.get("etc"),
            record.get("kakao_id"),
            record.get("email"),
            record.get("nick_name"),
            record.get("profile_image"),
            record.get("created_at") or _now_iso(),  # created_at 비어있을 때만 채움
            updated_at,
            record.get("access_token"),
            record.get("refresh_token"),
            record.get("token_expires_at"),
            user_id
        ))
        conn.commit()
        print(f"user_id {user_id} 레코드를 성공적으로 업데이트했습니다.")

    conn.close()

def user_update_exist_record(record):
    """
    record에 '있는' 컬럼만 동적으로 UPDATE.
    - 키 필드(user_id, id)는 업데이트 대상에서 제외
    - updated_at은 미지정 시 자동 갱신(_now_iso)
    """
    if record is None:
        raise ValueError("record가 필요합니다.")

    user_id = record.get("user_id")
    if not user_id:
        raise ValueError("user_id가 필요합니다.")

    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    # 존재 여부 체크
    cursor.execute(f"SELECT 1 FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    if cursor.fetchone() is None:
        print(f"user_id {user_id} 는 존재하지 않습니다. 업데이트를 건너뜁니다.")
        conn.close()
        return 0

    # 업데이트 허용 컬럼 정의 (키 필드 제외)
    KEY_FIELDS = {"user_id", "id"}
    ALL_UPDATABLE_FIELDS = {
        "user_name",
        "user_passwd",
        "phone_number",
        "apt_key",
        "villa_key",
        "sanga_key",
        "registration_date",
        "cancellation_date",
        "recharge_sms_count",
        "recharge_amount",
        "recharge_request_date",
        "recharge_request_sms_count",
        "recharge_status",
        "subscription_start_date",
        "subscription_end_date",
        "subscription_month",
        "subscription_payment",
        "subscription_status",
        "etc",
        "kakao_id",
        "email",
        "nick_name",
        "profile_image",
        "created_at",
        "updated_at",
        "access_token",
        "refresh_token",
        "token_expires_at",
    }

    # record에 '존재하는' 키만 골라서 업데이트 목록 생성 (키 필드 제외)
    fields_to_update = [
        k for k in record.keys()
        if k in ALL_UPDATABLE_FIELDS and k not in KEY_FIELDS
    ]

    # updated_at 자동 갱신(미지정 시)
    if "updated_at" not in fields_to_update:
        fields_to_update.append("updated_at")
        record["updated_at"] = _now_iso()

    if not fields_to_update:
        print("업데이트할 필드가 없습니다.")
        conn.close()
        return 0

    # 동적 UPDATE 쿼리 구성
    set_clause = ", ".join(f"{col} = ?" for col in fields_to_update)
    params = [record.get(col) for col in fields_to_update]
    params.append(user_id)  # WHERE 바인딩

    update_sql = f"UPDATE {TABLE_NAME} SET {set_clause} WHERE user_id = ?"
    cursor.execute(update_sql, params)
    conn.commit()

    rows = cursor.rowcount  # sqlite3에서는 1 또는 0이 일반적
    print(f"user_id {user_id} 레코드 업데이트 완료. 변경 필드: {', '.join(fields_to_update)} (영향 행수: {rows})")

    conn.close()
    return rows

def user_delete_record(user_id):
    """user_id 기준 삭제."""
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    if cursor.rowcount == 0:
        print(f"user_id {user_id} 는 존재하지 않습니다. 삭제를 건너뜁니다.")
    else:
        conn.commit()
        print(f"user_id {user_id} 레코드를 성공적으로 삭제했습니다.")
    conn.close()

def user_drop_table():
    """테이블 삭제."""
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
    conn.commit()
    conn.close()
    print(f"테이블 '{TABLE_NAME}' 삭제 완료.")

def user_read_db(user_id: str = "", userName: str = "", nickName: str = "", kakao_id: str = ""):
    """
    사용자 데이터 조회.
    - user_id 정확일치
    - user_name LIKE
    - nick_name LIKE
    - kakao_id 정확일치 (신규)
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
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
    if kakao_id:
        query += " AND kakao_id = ?"
        params.append(kakao_id)

    query += " LIMIT 130"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def verify_user(user_id: str, password: str) -> bool:
    """user_id / user_passwd 단순 검증."""
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT user_passwd FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    return row[0] == password

def user_cancel_record(user_id: str, reason: str):
    """
    회원 탈퇴 처리:
    - cancellation_date: 오늘(로컬) YYYY-MM-DD
    - etc: 탈퇴사유 저장
    - updated_at: 자동 갱신
    """
    conn = sqlite3.connect(DB_FILENAME)
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE user_id = ?", (user_id,))
    exists = cursor.fetchone()[0]

    if exists == 0:
        print(f"user_id {user_id} 는 존재하지 않습니다. 탈퇴를 건너뜁니다.")
    else:
        cancel_date = datetime.datetime.now().strftime("%Y-%m-%d")
        updated_at = _now_iso()
        update_query = f"""
            UPDATE {TABLE_NAME}
               SET cancellation_date = ?,
                   etc               = ?,
                   updated_at        = ?
             WHERE user_id = ?
        """
        cursor.execute(update_query, (cancel_date, reason, updated_at, user_id))
        conn.commit()
        print(f"user_id {user_id} 레코드를 탈퇴 처리했습니다. (취소일자: {cancel_date}, 사유: {reason})")

    conn.close()
