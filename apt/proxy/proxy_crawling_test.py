# -*- coding: utf-8 -*-
import time
import random
import string
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ===== Smartproxy (KR 타게팅 + sticky 세션 지원) =====
BASE_USERNAME = "smart-wfightgm69_area-KR"
PASSWORD = "ahdtpddlsp69"
HOST = "proxy.smartproxy.net"
PORT = 3120

COUNTRY_KR = True  # 한국 IP 권장

def build_username(session_id: str) -> str:
    user = BASE_USERNAME
    if COUNTRY_KR:
        user += "-country-kr"
    if session_id:
        user += f"-session-{session_id}"
    return user

def make_proxies(session_id: str):
    username = build_username(session_id)
    proxy_url = f"http://{username}:{PASSWORD}@{HOST}:{PORT}"
    return {"http": proxy_url, "https": proxy_url}

# ===== UA/헤더 =====
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.72 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.185 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.72 Mobile Safari/537.36",
]

def browser_headers():
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Origin": "https://new.land.naver.com",
        "Referer": "https://new.land.naver.com/",
        "X-Requested-With": "XMLHttpRequest",
        # 필요 없으면 Authorization 제거 권장
    }

# ===== 쿠키 + 세션(재시도 내장) =====
cookies = {
    # (사용자 제공 그대로)
    '_ga': 'GA1.1.1084468181.1734915860',
    'NAC': 'bLinBcgL5eHAA',
    '_fwb': '92EW36MJWoMlKDFNRGVTar.1734916083966',
    'NNB': 'P3BVN6YZW5UGO',
    'landHomeFlashUseYn': 'Y',
    'nhn.realestate.article.rlet_type_cd': 'Z02',
    'page_uid': 'i33ygsqptbNsse1dgqZssssstQC-503024',
    'NACT': '1',
    'nid_inf': '175862896',
    'NID_AUT': 'ygKx/8S35QHdbpFvrSj6Ain0juNAFljR+cLAR9Xnk1ITOoT1SOkvRSxgY4GqlFk1',
    'NID_JKL': 'fBQoOPU3NBnyLC3PSsnyOMWne/GV1pCjtpoL/9zUcMA=',
    'NID_SES': 'AAABonCFzQxM5vkiE54OMdyMPbSrToEm9aTkHKImD1LkHzoK0N0MZFhf9oSp2Bb7vsW689gWf1In0Rt24iwlKHdtigcGIsJV7vd6iqk3uXwD46j8sNDbImEQD+zz4c8uO1mIpFKAcSKCx1wawnUp74WxJv3ZugmAhOuSmXUaE82g7bxQ7lnKzz0xZdt0NBUyiX6mkNxAFKvIECrIJlq3FeXkzJnLL2G1oDIQZp6h/Vyp+/lpTy6VlK4DHdIll8UXoh525cy/YVWmkzCXd0hklcleD/5va5YYj2eSN/rlSVz/YlvXUtZR4BAZBwU9RNpFVY9BnbvLNgZ56L7rwFm8CEW5TYwWd3+LMytkJp+1zXx2lyqRmNHloosAuT1MoRgWjf8CQkEQhl7wKzlU5CdcEfOVOqvNQalo2MRRJu8AcnG39BDNEvDAp5eVQwCSEWE1N7YcaqF1BKEn1vQjSB8IVwsR8VvNFKYMdSZ25jhmwz95JIVnaON1nqHR/1xWOohG4dx+VPp8m0wRpmNBpfzcl07o9G6p9a4C0nPIbGh37LwgOLiJhkCONpSHtzOPJ5UJEUNp4A==',
    '_ga_451MFZ9CFM': 'GS1.1.1736498640.8.0.1736498642.0.0.0',
    'REALESTATE': 'Fri%20Jan%2010%202025%2017%3A44%3A02%20GMT%2B0900%20(Korean%20Standard%20Time)',
    'BUC': 'DKN0WiwVKe4qzAXKCI07Dr9GJz7Gpi1vd5NL1wCoAWw=',
}

session = requests.Session()
session.cookies.update(cookies)

retry = Retry(
    total=2, connect=2, read=2,
    status_forcelist=(429, 502, 503, 504),
    backoff_factor=0.6,
    allowed_methods=frozenset(["GET"]),
    raise_on_status=False,
)
adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
session.mount("http://", adapter)
session.mount("https://", adapter)

# ===== 외부 IP 확인(동일 세션ID 프록시로) =====
IP_ENDPOINTS = [
    "https://api.ipify.org?format=json",
    "https://httpbin.org/ip",
    "https://ifconfig.me/ip",
    "https://ipapi.co/ip",
]
def fetch_exit_ip(session_id, timeout=10):
    for ep in IP_ENDPOINTS:
        try:
            r = session.get(ep, headers=browser_headers(),
                            proxies=make_proxies(session_id),
                            timeout=timeout, verify=True)
            r.raise_for_status()
            ct = r.headers.get("Content-Type", "")
            if "application/json" in ct:
                j = r.json()
                if "ip" in j: return j["ip"]
                if "origin" in j: return j["origin"].split(",")[0].strip()
            else:
                ip = (r.text or "").strip()
                if ip: return ip
        except Exception:
            continue
    return None

# ===== 워밍업→API (동일 IP), 429면 Retry-After 준수 + 세션ID 교체 =====
def warmup_then_get_json(url, session_id, timeout=22, max_retry=5):
    last_err = None
    for attempt in range(1, max_retry + 1):
        try:
            # (1) 홈 워밍업
            session.get("https://new.land.naver.com/",
                        headers=browser_headers(),
                        proxies=make_proxies(session_id),
                        timeout=timeout, verify=True)

            # (2) API 호출 (약간의 변형 파라미터로 캐싱/탐지 완화)
            salt = random.randint(100000, 999999)
            call_url = f"{url}&_ts={int(time.time())}&_={salt}"

            r = session.get(call_url, headers=browser_headers(),
                            proxies=make_proxies(session_id),
                            timeout=timeout, verify=True)

            if r.status_code == 429:
                ra = r.headers.get("Retry-After")
                wait = float(ra) if (ra and ra.isdigit()) else random.uniform(12, 24)
                print(f"429 감지 → {wait:.1f}s 대기 (attempt {attempt}/{max_retry})")
                time.sleep(wait)
                # 429 후에는 다른 IP로 교체
                session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                continue

            txt = (r.text or "").lower()
            if r.status_code in (403,) or "captcha" in txt or "too_many_requests" in txt:
                wait = random.uniform(20, 40)
                print(f"{r.status_code}/차단문구 감지 → {wait:.1f}s 대기 (attempt {attempt}/{max_retry})")
                time.sleep(wait)
                session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
                continue

            r.raise_for_status()
            return r.json()

        except Exception as e:
            last_err = e
            # 네트워크/프록시 불안정 → 짧게 대기 후 동일/새 세션 혼합 시도
            time.sleep(random.uniform(3, 6))
            # 실패 누적 시 IP 교체
            if attempt >= 2:
                session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    raise last_err

# ===== 실행 =====
if __name__ == "__main__":
    cortarNo = "4113510300"  # 예시
    last_call_ts = 0.0

    for page in range(1, 6):
        # (A) 6–12초 랜덤 슬로틀링(보수적으로)
        now = time.monotonic()
        elapsed = now - last_call_ts
        base_wait = random.uniform(6.0, 12.0)
        if elapsed < base_wait:
            time.sleep(base_wait - elapsed)

        # (B) 이번 회차용 sticky 세션ID 생성(워밍업/API 동일 IP)
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

        used_ip = fetch_exit_ip(session_id) or "UNKNOWN"

        url = (
            "http://new.land.naver.com/api/articles"
            f"?cortarNo={cortarNo}&order=rank&realEstateType=APT:PRE&priceType=RETAIL&page={page}"
        )

        # url = (
        #     "https://m.land.naver.com/cluster/clusterList"
        #     "?view=atcl"
        #     f"&cortarNo={cortarNo}"
        #     "&rletTpCd=SG"
        #     "&tradTpCd=A1"
        #     "&pCortarNo="
        #     "&addon=COMPLEX"
        #     "&isOnlyIsale=false"
        # )

        try:
            data = warmup_then_get_json(url, session_id, timeout=22, max_retry=5)
            article_cnt = len(data.get("articleList", [])) if isinstance(data, dict) else 0
            print(f"[page {page}] IP={used_ip} | 건수={article_cnt} | isMoreData={data.get('isMoreData', False)}")
        except Exception as e:
            print(f"[page {page}] IP={used_ip} | 실패: {e}")

        last_call_ts = time.monotonic()
