import requests, ssl, time, random
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# ===== Smartproxy 접속 정보 =====
USERNAME = "smart-wfightgm69"
PASSWORD = "ahdtpddlsp69"
HOST = "proxy.smartproxy.net"
PORT = "3120"

PROXY_URL = f"http://{USERNAME}:{PASSWORD}@{HOST}:{PORT}"

def make_proxies():
    return {"http": PROXY_URL, "https": PROXY_URL}

# ===== TLSv1.2 + 안정화 어댑터 =====
class TLS12HttpAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        # 일부 사이트가 TLS1.2를 강하게 요구하거나 특정 cipher만 허용
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        # (선택) cipher 튜닝 - 필요시만 사용
        # ctx.set_ciphers("ECDHE+AESGCM:!ECDSA:!aNULL:!eNULL")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        # 프록시 연결에도 동일한 TLS 설정 적용
        kwargs.setdefault("ssl_context", ssl.create_default_context())
        return super().proxy_manager_for(*args, **kwargs)

# ===== 세션 구성 =====
def make_session():
    s = requests.Session()
    # 리트라이(SSL 실패/일시 차단/리셋 등 대응)
    retries = Retry(
        total=5,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS"]
    )
    adapter = TLS12HttpAdapter(max_retries=retries, pool_maxsize=10, pool_block=True)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s

# ===== User-Agent 로테이션 =====
USER_AGENTS = [
    # 최신 크롬 계열 UA 몇 개
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

# ===== 크롤링 대상 (네이버 뉴스 메인) =====
URL = "https://news.naver.com/"

def crawl_naver_news_headlines():
    sess = make_session()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "close",       # 연결을 매 요청 종료해 서버/프록시와 keep-alive 충돌 방지
        "Referer": "https://www.naver.com/",
    }
    r = sess.get(
        URL,
        headers=headers,
        proxies=make_proxies(),
        timeout=15,
        allow_redirects=True,
        verify=True  # 시스템/가상환경에 certifi 최신 설치 권장: pip install -U certifi
    )
    r.raise_for_status()
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(r.text, "html.parser")

    # 메인 영역에서 기사 타이틀 후보들 추출 (페이지 구조 바뀌면 셀렉터만 바꾸면 됨)
    sel_list = [
        "div.cjs_t",                   # 많이 쓰이는 영역
        "div.sa_text_strong",          # 일부 카드형
        "a.cluster_text_headline",     # 클러스터
    ]
    texts = []
    for sel in sel_list:
        for el in soup.select(sel):
            t = el.get_text(strip=True)
            if t and t not in texts:
                texts.append(t)

    print("=== 네이버 뉴스 헤드라인 상위 10 ===")
    for i, t in enumerate(texts[:10], 1):
        print(f"{i}. {t}")

if __name__ == "__main__":
    for i in range(3):
        print(f"\n[{i+1}] 크롤링 시도")
        try:
            crawl_naver_news_headlines()
        except Exception as e:
            print("에러 발생:", repr(e))
        time.sleep(2)
