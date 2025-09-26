# api_util.py
from dataclasses import dataclass
import urllib.parse
import requests
import time
import jwt

KAKAO_REST_API_KEY = "071bad9f8f4a5d8e73f22bff8128f808"     # KAKAO_CLIENT_ID
KAKAO_CLIENT_SECRET = "bSDWyM1O8UhqyRXcFHY1g2ekkJQXeocB"
KAKAO_REDIRECT_URI = "http://127.0.0.1:5000/api/kakao/callback"
#KAKAO_REDIRECT_URI = "https://erp-dev.bacchuserp.com/api/kakao/callback"

JWT_SECRET = "bSDWyM1O8UhqyRXcFHY1g2ekkJQXeocB"
JWT_ALG = "HS256"
JWT_EXPIRES = 60 * 60 * 24 * 7  # 7일

# 아주 단순한 인메모리 세션 저장소 (실서비스: Redis/DB 권장)
TOKENS = {}  # {jti: {sub, kakao_access_token, exp}}

@dataclass
class KakaoConfig:
    # 타입 힌트는 str, 기본값은 위 상수를 그대로 사용
    rest_api_key: str = KAKAO_REST_API_KEY
    redirect_uri: str = KAKAO_REDIRECT_URI
    client_secret: str | None = KAKAO_CLIENT_SECRET
    #
    authorize_url: str = "https://kauth.kakao.com/oauth/authorize"
    token_url: str = "https://kauth.kakao.com/oauth/token"
    user_me_url: str = "https://kapi.kakao.com/v2/user/me"
    user_unlink_url: str = "https://kapi.kakao.com/v1/user/unlink"
    #
    jwt_secret: str = JWT_SECRET
    jwt_algorithm: str = JWT_ALG
    jwt_expires: int = JWT_EXPIRES  # 초 단위

class KakaoAPI:
    """Flask/DB에 의존하지 않는 카카오 OAuth 유틸"""
    def __init__(self, cfg: KakaoConfig | None = None):
        self.cfg = cfg or KakaoConfig()  # 기본값 그대로 사용 가능

    def build_authorize_url(self, state: str, scope_list: list[str] | None = None, prompt: str | None = None) -> str:
        params = {
            "response_type": "code",
            "client_id": self.cfg.rest_api_key,
            "redirect_uri": self.cfg.redirect_uri,
            "state": state,
        }
        if scope_list:
            params["scope"] = " ".join(scope_list)
        if prompt:
            params["prompt"] = prompt  # 예: "consent"
        return f"{self.cfg.authorize_url}?{urllib.parse.urlencode(params)}"

    def exchange_code_for_token(self, code: str) -> dict:
        data = {
            "grant_type": "authorization_code",
            "client_id": self.cfg.rest_api_key,
            "redirect_uri": self.cfg.redirect_uri,
            "code": code,
        }
        if self.cfg.client_secret:
            data["client_secret"] = self.cfg.client_secret
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        r = requests.post(self.cfg.token_url, data=data, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def refresh_access_token(self, refresh_token: str) -> dict:
        data = {
            "grant_type": "refresh_token",
            "client_id": self.cfg.rest_api_key,
            "refresh_token": refresh_token,
        }
        if self.cfg.client_secret:
            data["client_secret"] = self.cfg.client_secret
        headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
        r = requests.post(self.cfg.token_url, data=data, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_user_me(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get(self.cfg.user_me_url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def unlink(self, access_token: str) -> dict:
        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.post(self.cfg.user_unlink_url, headers=headers, timeout=10)
        r.raise_for_status()
        return r.json()

    def make_jwt(self,sub: str) -> str:
        iat = int(time.time())
        exp = iat + self.cfg.jwt_expires
        jti = f"{sub}-{iat}"
        payload = {"sub": sub, "iat": iat, "exp": exp, "jti": jti}
        token = jwt.encode(payload, self.cfg.jwt_secret, algorithm=self.cfg.jwt_algorithm)
        TOKENS[jti] = {"sub": sub, "exp": exp}
        return token

    def verify_jwt(self, token: str):
        try:
            payload = jwt.decode(token, self.cfg.jwt_secret, algorithms=[self.cfg.jwt_algorithm])
            jti = payload.get("jti")
            if not jti or jti not in TOKENS:
                return None
            return payload
        except Exception:
            return None
