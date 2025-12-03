# -*- coding: utf-8 -*-
"""
무료 프록시 회전 + 헬스체크 + 백오프 + UA/헤더 랜덤화 샘플
- 무료 프록시 후보를 수집(여기서는 예시 URL / 파일) 후 살아있는 프록시만 선별
- 403/429/캡차 시 자동 백오프하고 다른 프록시로 회전
- requests[socks] 설치 시 SOCKS5도 사용 가능 (선택)
"""
import time
import random
import requests

# 1) 최신 브라우저 기반 UA들 (원하시면 이전에 만든 10개 리스트를 그대로 붙여 넣어 사용하세요)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.72 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.185 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.72 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.72 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.72 Safari/537.36 Edg/127.0.2651.74",
]

def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://new.land.naver.com/",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Connection": "keep-alive",
    }

# 2) 무료 프록시 후보 수집 (예시)
#    - plaintext로 "IP:PORT" 형태를 주는 공개 리스트 URL들이 흔합니다.
#    - 네트워크/출처 품질에 따라 변동이 심하므로, 실제로는 여러 소스를 쓰세요.
FREE_PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=https&timeout=5000",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    # "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/https.txt",
    # "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    # "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    # "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    # "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
    # "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    # "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
]

def load_proxies_from_sources(sources, timeout=8):
    proxies = set()
    for url in sources:
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            for line in r.text.splitlines():
                line = line.strip()
                if not line or ":" not in line:
                    continue
                # 기본적으로 HTTP 프록시 가정. HTTPS도 동일하게 쓰지만 무료는 품질이 낮음.
                proxies.add(f"http://{line}")
        except Exception:
            continue
    return list(proxies)

def load_proxies_from_file(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            v = line.strip()
            if not v:
                continue
            # 파일에도 "IP:PORT" 형태로 저장되어 있다고 가정
            if "://" not in v:
                v = "http://" + v
            out.append(v)
    return out

# 3) 프록시 헬스체크 (간단)
def proxy_ok(proxy_url, timeout=9):
    p = {"http": proxy_url, "https": proxy_url}
    try:
        r = requests.get("https://httpbin.org/ip", headers=get_headers(), proxies=p, timeout=timeout)
        if r.status_code != 200:
            return False
        r2 = requests.get("https://new.land.naver.com", headers=get_headers(), proxies=p, timeout=timeout)
        return r2.status_code == 200
    except Exception:
        return False

def build_proxy_pool(candidates, max_pool=10):
    random.shuffle(candidates)
    pool = []
    for proxy in candidates:
        if len(pool) >= max_pool:
            break
        if proxy_ok(proxy):
            pool.append(proxy)
    return pool

# 4) 회전 + 백오프 GET
def robust_get(url, proxy_pool, max_retry=6, timeout=15):
    """
    - 403/429/캡차 감지 시 증가형 백오프 후 다른 프록시로 회전
    - 네트워크 에러도 프록시 교체
    """
    last_exc = None
    for attempt in range(max_retry):
        if not proxy_pool:
            raise RuntimeError("사용 가능한 프록시 풀이 비었습니다.")
        proxy_url = random.choice(proxy_pool)
        proxies = {"http": proxy_url, "https": proxy_url}
        try:
            r = requests.get(url, headers=get_headers(), proxies=proxies, timeout=timeout)
            txt = r.text.lower() if r.text else ""
            if r.status_code in (403, 429) or "too_many_requests" in txt or "captcha" in txt:
                # 해당 프록시에 쿨다운
                wait = random.uniform(6, 18) * (attempt + 1)
                print(f"[{attempt+1}/{max_retry}] 차단 신호 감지 → {wait:.1f}s 대기, 프록시 회전")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except Exception as e:
            last_exc = e
            # 프록시 품질 불안정 → 짧게 대기 후 회전
            time.sleep(random.uniform(1.5, 4.0))
            continue
    raise RuntimeError(f"무료 프록시 회전으로도 실패: {last_exc}")

if __name__ == "__main__":
    # A) 소스에서 수집 (실사용 시 FREE_PROXY_SOURCES 채우세요)
    candidates = load_proxies_from_sources(FREE_PROXY_SOURCES)

    # B) 또는 파일에서 로딩 (예: proxies.txt에 한 줄당 'IP:PORT' 저장)
    # candidates = load_proxies_from_file("proxies.txt")

    if not candidates:
        # 데모용: 직접 임시로 몇 개 넣어 테스트 (실사용은 본인 리스트로 교체)
        # pip install "requests[socks]"
        candidates = [
            "http://103.123.25.56:8080",
            "http://203.189.88.156:80",
            "http://51.159.0.236:3128",
            #필요시 SOCKS5 (requests[socks] 설치)
            "socks5h://127.0.0.1:9050",
        ]

    print(f"후보 프록시 수집: {len(candidates)}개")

    proxy_pool = build_proxy_pool(candidates, max_pool=25)
    print(f"활성 프록시 풀 구성: {len(proxy_pool)}개")

    if not proxy_pool:
        raise SystemExit("활성 프록시가 없습니다. 소스/파일을 갱신하세요.")

    # 네이버 부동산 비공식 API 호출 예시 (page 루프 + 슬로틀링)
    cortarNo = "4113510300"  # 예: 경기도 성남시 분당구 정자동 일대(샘플). 실제로는 원하는 코드 사용
    for page in range(1, 6):
        url = (
            "https://new.land.naver.com/api/articles"
            f"?cortarNo={cortarNo}&order=rank&realEstateType=APT:PRE&priceType=RETAIL&page={page}"
        )
        # 기본 슬로틀링(랜덤)
        time.sleep(random.uniform(1.6, 3.6))
        try:
            resp = robust_get(url, proxy_pool, max_retry=7, timeout=18)
            data = resp.json()
            article_cnt = len(data.get("articleList", [])) if isinstance(data, dict) else 0
            print(f"page {page}: {article_cnt}건, isMoreData={data.get('isMoreData', False)}")
        except Exception as e:
            print(f"page {page} 실패: {e}")
