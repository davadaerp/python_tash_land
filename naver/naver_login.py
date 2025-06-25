import os
from flask import Flask, redirect, request, session, jsonify, render_template
from flask_cors import CORS
from requests_oauthlib import OAuth2Session
from werkzeug.security import generate_password_hash, check_password_hash

from users_db_utils import init_db, create_user, get_user_by_username, get_user_by_id, get_social_account, create_social_account

# ──────────────────────────────────────────────────────────
# 설정값
# ──────────────────────────────────────────────────────────
CLIENT_ID     = os.getenv("NAVER_CLIENT_ID", "OnuOlcjbgFntia0Xesvy")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "cAFGaeZTib")
REDIRECT_URI  = "http://localhost:8080/api/login/naver/code"  # <-- 변경된 콜백 URL
#REDIRECT_URI  = "https://erp-dev.bacchuserp.com/api/login/naver/code"  # <-- 변경된 콜백 URL

AUTH_BASE   = "https://nid.naver.com/oauth2.0/authorize"
TOKEN_URL   = "https://nid.naver.com/oauth2.0/token"
PROFILE_API = "https://openapi.naver.com/v1/nid/me"

# 아이디·별명·이메일·휴대전화
SCOPE = ["profile", "email", "phone"]

app = Flask(__name__, template_folder="../templates", static_folder="../static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change_this_secret")

# CORS 전체 허용
# CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])
CORS(app, resources={
    r"/api/login/naver*": {
        "origins": "http://localhost:8080",
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})

# 초기 DB 설정
init_db()

# Naver OAuth helper
def get_naver_oauth(state=None):
    return OAuth2Session(
        client_id=CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        state=state
    )

def get_token(code: str) -> dict:
    """
    authorization code로 access_token (및 refresh_token 등)을 가져옵니다.
    """
    oauth = get_naver_oauth()
    token = oauth.fetch_token(
        TOKEN_URL,
        client_secret=CLIENT_SECRET,
        code=code,
    )
    return token


def get_profile(token: dict) -> dict:
    """
    token을 이용해 네이버 프로필 정보를 조회합니다.
    """
    oauth = OAuth2Session(
        client_id=CLIENT_ID,
        token=token,
    )
    resp = oauth.get(PROFILE_API)
    resp.raise_for_status()
    return resp.json()

# naver 인증
def naver_authorization():
    """
    사용자에게 네이버 로그인/동의 페이지로 리다이렉트할 URL을 제공합니다.
    """
    oauth = get_naver_oauth()
    # AUTH_BASE   = "https://nid.naver.com/oauth2.0/authorize"
    auth_url, state = oauth.authorization_url(AUTH_BASE)
    # 상태를 세션에 저장
    session['oauth_state'] = state
    return auth_url

# naver callback data
def naver_callback(code):
    """
    네이버 로그인 후 콜백 처리: 토큰과 프로필을 받아와 JSON으로 반환합니다.
    """
    # 세션에 저장된 state
    state = session.get('oauth_state')
    # 1) 토큰 가져오기
    token = get_token(code)

    # 2) 프로필 전체 JSON 가져오기
    profile_json = get_profile(token)

    # 3) profile_json 내부 속성 출력
    print("===== NAVER USER PROFILE =====")
    for k, v in profile_json.items():
        print(f"{k}: {v}")
    print("================================")

    # 4) 그 중 'response'만 꺼내기
    user_info = profile_json.get('response', {})

    # 5) 개별 값 추출
    # user_id = user_info.get('id')
    # nickname = user_info.get('nickname')
    # email = user_info.get('email')
    # mobile = user_info.get('mobile')
    # mobile_e164 = user_info.get('mobile_e164')
    # real_name = user_info.get('name')
    #
    # print(f"ID            : {user_id}")
    # print(f"Nickname      : {nickname}")
    # print(f"Email         : {email}")
    # print(f"Mobile        : {mobile}")
    # print(f"Mobile (E164) : {mobile_e164}")
    # print(f"Name          : {real_name}")
    print("================================")

    # # 6) 클라이언트에 돌려줄 데이터
    # data = {
    #     'token': token,
    #     'profile': user_info
    # }
    return user_info, token

# 로컬 가입
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if get_user_by_username(data['username']):
        return jsonify({'error': '이미 존재하는 사용자명'}), 400
    pw_hash = generate_password_hash(data['password'])
    uid = create_user(data['username'], None, pw_hash)
    return jsonify({'status': 'ok', 'user_id': uid}), 201

# 로컬 로그인
@app.route('/login', methods=['POST'])
def login_local():
    data = request.json
    user = get_user_by_username(data['username'])
    if not user or not check_password_hash(user['password_hash'], data['password']):
        return jsonify({'error': '아이디 또는 비밀번호가 틀립니다.'}), 401
    session['user_id'] = user['id']
    return jsonify({'status': 'ok'})


@app.route('/api/login/check', methods=['POST'])
def login_check():
    data = request.json
    user_id = data.get('userId')

    # 사용자 조회 함수 (사용자 정의 함수로 가정)
    user = get_user_by_username(user_id)

    return jsonify({
        'is_duplicate': user is not None
    })
@app.route("/", methods=["GET"])
@app.route("/ts/", methods=["GET"])
def loginForm():
    return render_template("login.html")

@app.route("/api/register", methods=["GET"])
def registerForm():
    return render_template("login_user_register.html")

@app.route("/api/login/naver")
def index():
    auth_url = naver_authorization()
    print('/api/login/naver : ' + auth_url)
    return redirect(auth_url)

# 변경된 콜백 경로로 수정
@app.route("/api/login/naver/code")
def callback():
    """
    네이버 로그인 후 콜백 처리: 토큰과 프로필을 받아와 JSON으로 반환합니다.
    """
    code = request.args.get('code')
    if not code:
        return "Error: missing code", 400
    #
    user_info, token = naver_callback(code)

    print("===== NAVER USER PROFILE =====")
    # 5) 개별 값 추출
    user_id = user_info.get('id')
    nickname = user_info.get('nickname')
    email = user_info.get('email')
    mobile = user_info.get('mobile')
    mobile_e164 = user_info.get('mobile_e164')
    real_name = user_info.get('name')

    print(f"ID            : {user_id}")
    print(f"Nickname      : {nickname}")
    print(f"Email         : {email}")
    print(f"Mobile        : {mobile}")
    print(f"Mobile (E164) : {mobile_e164}")
    print(f"Name          : {real_name}")
    print("================================")

    naver_id = user_id
    sa = get_social_account('naver', naver_id)
    if sa:
        user = get_user_by_id(sa['user_id'])
    else:
        if session.get('user_id'):
            user = get_user_by_id(session['user_id'])
        else:
            uid = create_user(None, email, None)
            user = get_user_by_id(uid)
        create_social_account(user['id'], 'naver', naver_id)

    session['user_id'] = user['id']
    return jsonify({'status': 'ok', 'master': {'id': user['id'], 'email': user['email']}})

# 로그인 정보 조회
@app.route('/me')
def me():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'error': '로그인 필요'}), 401
    user = get_user_by_id(uid)
    return jsonify({'id': user['id'], 'username': user['username'], 'email': user['email']})

if __name__ == '__main__':
    # localhost:8080으로 실행
    app.run(host='localhost', port=8080, debug=True)
