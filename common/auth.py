import datetime
import jwt
import base64
from functools import wraps
from flask import request, jsonify

from config import SECRET_KEY
from master.user_db_utils import verify_user


# Auth Header를 이용한 처리
def token_header_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        print('======token_required=====')
        print(request.headers)
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            print(auth_header)
            parts = auth_header.split()
            if len(parts) == 2 and parts[0] == 'Bearer':
                token = parts[1]
        if not token:
            # 필요한 시점에 loginForm을 import
            from tash_service_app import loginForm
            return loginForm()
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['userid']
        except jwt.ExpiredSignatureError:
            from tash_service_app import loginForm
            return loginForm()
        except jwt.InvalidTokenError:
            from tash_service_app import loginForm
            return loginForm()
        return f(current_user, *args, **kwargs)
    return decorated


# 쿠키를 이용한 토큰처리
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 쿠키에서 access_token 추출
        token = request.cookies.get("access_token")
        print("Cookie access_token:", token)
        if not token:
            # 필요한 시점에 loginForm을 import
            from tash_service_app import loginForm
            return loginForm()
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = data['userid']
        except jwt.ExpiredSignatureError:
            from tash_service_app import loginForm
            return loginForm()
        except jwt.InvalidTokenError:
            from tash_service_app import loginForm
            return loginForm()
        return f(current_user, *args, **kwargs)
    return decorated

# 쿠키를 이용한 토큰처리
def kakao_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 쿠키에서 access_token 추출
        token = request.cookies.get("access_token")
        print("Cookie access_token:", token)
        if not token:
            # 필요한 시점에 loginForm을 import
            from tash_service_app import loginForm
            return loginForm()

        current_user = 'kakao'

        return f(current_user, *args, **kwargs)
    return decorated

def create_access_token():
    """
    클라이언트가 /api/token에 POST 요청을 보내면,
    JSON 데이터에서 credential (base64 인코딩된 "username:password"),
    grant_type, client_id, client_secret 정보를 읽어 사용자 인증 후 토큰을 발행합니다.
    """
    data = request.get_json()
    print("create_access_token() Received data:", data)
    if not data or 'credential' not in data:
        return jsonify({
            'result': 'Fail',
            'errcode': 401,
            'message': 'Missing credentials'
        })

    credential = data.get("credential")
    grant_type = data.get("grant_type")
    client_id = data.get("client_id")
    client_secret = data.get("client_secret")

    # 클라이언트 정보 검증 (예제에서는 고정값 사용)
    if client_id != 'dp' or client_secret != '7987f7cb05cb1992':
        return jsonify({
            'result': 'Fail',
            'errcode': 401,
            'message': 'Invalid client credentials'
        })

    try:
        # Base64 디코딩하여 "username:password" 형태 복원
        decoded = base64.b64decode(credential).decode("utf-8")
        userid, password = decoded.split(":", 1)
    except Exception as e:
        return jsonify({
            'result': 'Fail',
            'errcode': 400,
            'message': 'Invalid credential format'
        })

    # 4) 사용자 인증
    if not verify_user(userid, password):
        print("create_access_token verify_user failed:", userid, password)
        return jsonify({
            'result': 'Fail',
            'errcode': 401,
            'message': 'Invalid userid or password'
        })

    # 5) 성공: 토큰 발급
    access_token = generate_token(userid, expiration_hours=1)
    return jsonify({
        'result':       'Success',
        'errcode':      200,
        'message':      'Token created successfully',
        'access_token': access_token,
        'expires_in':   3600,
        'userid':       userid
    })


def generate_token(userid, expiration_hours=1):
    """
    주어진 userid로 JWT 토큰을 생성합니다.
    토큰 유효시간은 기본 1시간입니다.
    """
    expiration_time = datetime.datetime.utcnow() + datetime.timedelta(hours=expiration_hours)
    token = jwt.encode(
        {'userid': userid, 'exp': expiration_time},
        SECRET_KEY,
        algorithm="HS256"
    )
    return token

def extract_user_info_from_token(access_token):
    """
    주어진 access_token에서 userid와 토큰 만료시간(exptime)을 추출합니다.
    """
    try:
        decoded_payload = jwt.decode(access_token, SECRET_KEY, algorithms=["HS256"])
        userid = decoded_payload.get("userid")
        exptime = decoded_payload.get("exp")
        errmsg = "Success"
        return userid, exptime, errmsg
    except jwt.ExpiredSignatureError:
        errmsg = "Token has expired."
        print("Error: Token has expired.")
    except jwt.InvalidTokenError as e:
        errmsg = "Invalid token."
        print("Error: Invalid token.", str(e))
    return None, None, errmsg
