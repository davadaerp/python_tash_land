import sqlite3
import os
from typing import Optional, Dict

# users, social_accounts
DB_PATH = os.getenv('USERS_DB_PATH', 'users.db')

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    #conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    # 사용자 테이블
    cur.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT
            )
    ''')

    # 소셜 계정 매핑
    cur.execute(f'''
            CREATE TABLE IF NOT EXISTS social_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                provider TEXT,
                provider_user_id TEXT,
                UNIQUE(provider, provider_user_id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
    ''')
    conn.commit()
    conn.close()

# 사용자 CRUD
def create_user(username: Optional[str], email: Optional[str], password_hash: Optional[str]) -> int:
    init_db()
    #
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash)
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

# 소셜 계정
def get_social_account(provider: str, provider_user_id: str) -> Optional[Dict]:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM social_accounts WHERE provider = ? AND provider_user_id = ?",
        (provider, provider_user_id)
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def create_social_account(user_id: int, provider: str, provider_user_id: str) -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO social_accounts (user_id, provider, provider_user_id) VALUES (?, ?, ?)",
        (user_id, provider, provider_user_id)
    )
    sa_id = cur.lastrowid
    conn.commit()
    conn.close()
    return sa_id