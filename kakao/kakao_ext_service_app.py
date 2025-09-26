# 카카오 로그인 확장프로그램 백엔드 예제
# kakao_ext popup.html에서 호출
# - JWT 발급/검증, CORS 설정, 간단한 인메모리 세션 저장
#
import time
import jwt
import requests
import secrets
from urllib.parse import urlencode
from flask import Flask, request, redirect, jsonify, make_response
from flask_cors import CORS

app = Flask(__name__)

# CORS 전체 허용
CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

# 카카오 로그인 관련
from kakao.kakao_api_utils import KakaoAPI, TOKENS   # 여기서 TOKENS 가져오기

# 필요시 scope를 None으로 두고 최소 동작 확인
DEFAULT_SCOPE = None  # 예: ["profile_nickname", "profile_image"]

# === KakaoAPI 인스턴스화 ===
kakao = KakaoAPI()

@app.get("/api/kakao/login")
def auth_login_start():
    state = secrets.token_urlsafe(16)
    # session["oauth_state"] = state
    auth_url = kakao.build_authorize_url(state, DEFAULT_SCOPE)
    print("== kakao_login() kakao_auth_url:", auth_url)
    return redirect(auth_url)

#@app.get(KAKAO_REDIRECT_PATH)
@app.get("/api/kakao/callback")
def kakao_auth_callback():
    code = request.args.get("code")
    if not code:
        error = request.args.get("error_description") or request.args.get("error") or "인가 코드를 찾을 수 없습니다."
        return jsonify({"result": "Fail", "message": error}), 400

    print("== kakao_callback() code:", code)

    # 1) 코드 → 토큰
    try:
        token = kakao.exchange_code_for_token(code)  # ← 여기서 403이면 위에서 print로 상세 로그 남음
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")
        expires_in = token.get("expires_in")
    except Exception as e:
        return make_response(_error_bridge_html(f"토큰 교환 실패: {e}"), 400)

    # 2) 사용자 정보
    me = kakao.get_user_me(access_token)
    kakao_id = str(me.get("id"))
    user_id = kakao_id
    kakao_account = me.get("kakao_account", {}) or {}
    email = kakao_account.get("email")
    profile = kakao_account.get("profile") or {}
    nickname = profile.get("nickname")
    profile_img = profile.get("profile_image_url")

    # 임의 문자건수 예시(실서비스: DB/외부API 조회)
    sms_count = 100

    # 우리 서비스용 JWT 발급(user_id 기반)
    app_token = kakao.make_jwt(user_id)

    # 확장프로그램 팝업으로 토큰/프로필 전달 (postMessage)
    # 보안 고려: origin 체크는 확장 프로그램에서 수행
    html = f"""
<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>로그인 완료</title></head>
<body>
<script>
  try {{
    window.opener && window.opener.postMessage({{
      type: "kakao_login_success",
      token: {repr(app_token)},
      nickname: {repr(nickname)},
      sms_count: {sms_count}
    }}, "*");
  }} catch (e) {{}}
  window.close();
</script>
로그인 처리 중...
</body>
</html>
"""
    resp = make_response(html)
    resp.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'unsafe-inline';"
    return resp

def _error_bridge_html(msg: str) -> str:
    return f"""<!doctype html><meta charset="utf-8">
<title>로그인 실패</title>
<div style="font-family:system-ui;padding:24px">
  <h2>로그인 처리 중 오류</h2>
  <pre style="white-space:pre-wrap">{msg}</pre>
  <button onclick="location.href='/'">메인으로</button>
</div>
"""

@app.post("/api/kakao/logout")
def kakao_auth_logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1]
        payload = kakao.verify_jwt(token)
        #user_id = payload["sub"]  # user_id는 kakao_id와 동일하게 설정됨
        if payload:
            jti = payload.get("jti")
            if jti in TOKENS:
                del TOKENS[jti]
    return jsonify({"result": "ok"})

@app.get("/api/kakao/me")
def api_me():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "unauthorized"}), 401
    token = auth.split(" ", 1)[1]
    payload = kakao.verify_jwt(token)
    if not payload:
        return jsonify({"error": "unauthorized"}), 401

    user_id = payload["sub"]    # user_id는 kakao_id와 동일하게 설정됨
    # 닉네임/문자건수는 실제론 DB에서 조회
    # 여기서는 간단히 유저아이디 기반으로 예시값 구성
    nickname = "야나르타쉬"
    sms_count = 100
    return jsonify({"nickname": nickname, "sms_count": sms_count})

@app.get("/healthz")
def health():
    return "ok"

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)
