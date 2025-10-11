import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import certifi
import os

# # (선택) 회사 CA 번들 환경변수 사용
# CA_BUNDLE = os.environ.get("REQUESTS_CA_BUNDLE") or certifi.where()
#
# class TLS12HttpAdapter(HTTPAdapter):
#     def init_poolmanager(self, *args, **kwargs):
#         ctx = ssl.create_default_context(cafile=CA_BUNDLE)  # ← 신뢰 번들 지정
#         if hasattr(ssl, "TLSVersion"):
#             ctx.minimum_version = ssl.TLSVersion.TLSv1_2
#             ctx.maximum_version = ssl.TLSVersion.TLSv1_2
#         kwargs["ssl_context"] = ctx
#         return super().init_poolmanager(*args, **kwargs)
#
session = requests.Session()
# session.mount("https://", TLS12HttpAdapter(max_retries=Retry(
#     total=3, backoff_factor=0.5,
#     status_forcelist=[429, 500, 502, 503, 504],
#     allowed_methods=["GET"]
# )))

#url = "https://apis.data.go.kr/1741000/stdgSexdAgePpltn/selectStdgSexdAgePpltn"
url = "http://apis.data.go.kr/1741000/stdgSexdAgePpltn/selectStdgSexdAgePpltn"
params = {
    "serviceKey": "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==",
    "stdgCd": "1111014000",
    "srchFrYm": "202507",
    "srchToYm": "202507",
    "lv": "1",
    "regSeCd": "1",
    "type": "JSON",
    "numOfRows": "100",
    "pageNo": "1",
}
headers = {"User-Agent": "Mozilla/5.0 (population-fetch/1.0)"}

#resp = session.get(url, params=params, headers=headers, timeout=20, verify=CA_BUNDLE)
resp = session.get(url, params=params, headers=headers, timeout=20, verify=False)
resp.raise_for_status()
print(resp.json())

