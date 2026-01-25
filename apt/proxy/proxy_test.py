import requests
import time

# Smartproxy 접속 정보
username = "smart-wfightgm69"
password = "ahdtpddlsp69"
host = "proxy.smartproxy.net"
port = "3120"

proxy_url = f"http://{username}:{password}@{host}:{port}"

proxies = {
    "http": proxy_url,
    "https": proxy_url,
}

# 테스트용 URL (현재 IP 확인)
url = "https://api.ipify.org?format=json"

for i in range(10):  # 5번 테스트
    try:
        resp = requests.get(url, proxies=proxies, timeout=10)
        resp.raise_for_status()
        print(f"{i+1}번째 IP:", resp.json()["ip"])
    except requests.exceptions.RequestException as e:
        print("에러 발생:", e)
    time.sleep(1)  # 호출 간격 (짧으면 같은 IP가 나올 수도 있음)
