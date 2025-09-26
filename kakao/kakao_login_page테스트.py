# main.py
import os
import secrets
from datetime import datetime, timedelta

import requests
from flask import Flask, session, redirect, request, url_for, jsonify, make_response

from sqlalchemy import create_engine, Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker

# === 카카오 유틸 임포트 ===
from kakao_api_utils import KakaoAPI

# 필요시 scope를 None으로 두고 최소 동작 확인
DEFAULT_SCOPE = None  # 예: ["profile_nickname", "profile_image"]

# === KakaoAPI 인스턴스화 ===
kakao = KakaoAPI()

# === Flask & DB 설정 ===
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))
app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

engine = create_engine("sqlite:///users.db", echo=False, future=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    provider = Column(String(20), default="kakao", nullable=False)
    kakao_id = Column(String(64), nullable=False)
    email = Column(String(255))
    nickname = Column(String(255))
    profile_image = Column(String(512))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    access_token = Column(String(2048))
    refresh_token = Column(String(2048))
    token_expires_at = Column(DateTime)
    __table_args__ = (UniqueConstraint("provider", "kakao_id", name="uq_provider_kakaoid"),)

Base.metadata.create_all(engine)

def db():
    return SessionLocal()

# === Routes ===
@app.route("/")
def index():
    user = None
    if "user_id" in session:
        with db() as s:
            user = s.get(User, session["user_id"])
    if user:
        return f"""
        <h2>로그인됨</h2>
        <p><b>{user.nickname}</b> ({user.email or '이메일 없음'})</p>
        <img src="{user.profile_image or ''}" alt="profile" style="height:60px"/>
        <div style="margin-top:12px">
            <a href="/me">/me (JSON)</a> |
            <a href="/logout">로그아웃(앱 세션만)</a> |
            <a href="/unlink" onclick="return confirm('서비스 연결을 해제할까요?')">연결 해제</a>
        </div>
        """
    else:
        return f"""
        <h2>카카오톡 간편가입 데모</h2>
        <a href="/api/kakao/login" style="
            display:inline-block;padding:10px 16px;background:#FEE500;border-radius:8px;
            color:#000;text-decoration:none;font-weight:700">카카오로 시작하기</a>
        <p style="margin-top:12px;font-size:13px;color:#666">
            최초 로그인 시 동의 화면이 표시됩니다.
        </p>
        """

@app.route("/api/kakao/login")
def kakao_login():
    state = secrets.token_urlsafe(16)
    session["oauth_state"] = state
    auth_url = kakao.build_authorize_url(state, DEFAULT_SCOPE)
    print("== kakao_login() kakao_auth_url:", auth_url)
    return redirect(auth_url)

@app.route("/api/kakao/callback")
def kakao_callback():
    # CSRF 방지
    state = request.args.get("state")
    if not state or state != session.get("oauth_state"):
        return make_response("잘못된 state 값입니다.", 400)

    code = request.args.get("code")
    if not code:
        error = request.args.get("error_description") or request.args.get("error") or "인가 코드를 찾을 수 없습니다."
        return make_response(f"카카오 인가 실패: {error}", 400)

    print("== kakao_callback() code:", code)

    # 1) 코드 → 토큰 (유틸 사용)
    token = kakao.exchange_code_for_token(code)
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    expires_in = token.get("expires_in")

    # 2) 사용자 정보 (유틸 사용)
    me = kakao.get_user_me(access_token)
    kakao_id = str(me.get("id"))
    kakao_account = me.get("kakao_account", {}) or {}
    needs_email = kakao_account.get("email_needs_agreement") is True
    email = kakao_account.get("email")
    profile = kakao_account.get("profile") or {}
    nickname = profile.get("nickname")
    profile_img = profile.get("profile_image_url")

    # (옵션) 이메일 추가동의 유도 로직
    if needs_email and not email:
        session["oauth_state"] = secrets.token_urlsafe(16)
        auth_url = kakao.build_authorize_url(session["oauth_state"], ["account_email"], prompt="consent")
        return redirect(auth_url)

    # 3) 회원 저장/업데이트 (DB 작업은 main에서)
    with db() as s:
        user = s.query(User).filter_by(provider="kakao", kakao_id=kakao_id).one_or_none()
        now = datetime.utcnow()
        expires_at = (now + timedelta(seconds=expires_in)) if expires_in else None

        if user is None:
            user = User(
                provider="kakao",
                kakao_id=kakao_id,
                email=email,
                nickname=nickname or f"user_{kakao_id[-6:]}",
                profile_image=profile_img,
                access_token=access_token,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                created_at=now,
                updated_at=now,
            )
            s.add(user)
            s.commit()
        else:
            user.email = email or user.email
            user.nickname = nickname or user.nickname
            user.profile_image = profile_img or user.profile_image
            user.access_token = access_token
            if refresh_token:
                user.refresh_token = refresh_token
            user.token_expires_at = expires_at
            user.updated_at = now
            s.commit()

        session["user_id"] = user.id

    return redirect(url_for("index"))

@app.route("/me")
def me():
    if "user_id" not in session:
        return jsonify({"authenticated": False})
    with db() as s:
        user = s.get(User, session["user_id"])
        return jsonify({
            "authenticated": True,
            "provider": user.provider,
            "kakao_id": user.kakao_id,
            "email": user.email,
            "nickname": user.nickname,
            "profile_image": user.profile_image,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat(),
        })

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/unlink")
def unlink():
    if "user_id" not in session:
        return redirect(url_for("index"))
    with db() as s:
        user = s.get(User, session["user_id"])
        try:
            kakao.unlink(user.access_token)  # 유틸 사용
        except Exception as e:
            return make_response(f"연결 해제 실패: {e}", 400)

        user.access_token = None
        user.refresh_token = None
        s.commit()
        session.clear()
        return redirect(url_for("index"))

if __name__ == "__main__":
    # 개발용 실행
    app.run(host="127.0.0.1", port=5000, debug=True)
