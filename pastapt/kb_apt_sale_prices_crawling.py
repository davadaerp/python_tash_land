# kb부동산 주간별 매매시세(https://data.kbland.kr/kbstats/wmh?tIdx=HT01&tsIdx=weekAptSalePriceInx)
import requests
from collections import defaultdict

# 1) 요청할 URL과 헤더 (Bearer 토큰) 설정
url = (
    "https://data-api.kbland.kr/bfmstat/weekMnthlyHuseTrnd/"
    "priceIndexOnlyWeekAptExcel?"
    "매매전세코드=01&기간=1&매물종별구분="
    '{"98":"주택종합","01":"아파트","09":"단독","08":"연립"}'
)
headers = {
    "Authorization": "Bearer E/xLe2/6NAhwEQVkfP8cR2IAF2jrVGAakAgNpM/YVcCbENkWJk2aIVRC9wYdeezsvUgcN60kaf02G0zez7h53inEDb+uti+0THgQ30IgloxW/4GvHOD7ywLh2nZixZXNph3rr09VVxA4s63I0ABMbyYTDYG4RtVIgKVTCHDbtMLib5i603INZ+x3gbK15gN2a/Bm4snP2qOf0l0cLV/A3kg0Mw4pCzEOE+gxp2/izI8XAPUS2MIbwzgFGvWUKwqMDc5If+xRCMLUI7kxZWXJd30d5J4qfBpbYJonKnW617d8j0ttExXOFJ0GgkznflJwFOtVesYptveJbjoH4IXLwg=="
}

# 2) API 콜
resp = requests.get(url, headers=headers)
resp.raise_for_status()
payload = resp.json()

# 3) 원본 리스트
regions = payload["dataBody"]["data"]["데이터리스트"]

# 4) 지역명 → entry 맵
region_map = {r["지역명"]: r for r in regions}

# 5) 최상위지역명 기준으로 그룹핑
grouped = defaultdict(list)
for r in regions:
    grouped[r["최상위지역명"]].append(r["지역명"])

# 6) 출력에서 제외할 최상위그룹
skip_groups = {
    "전국",
    "서울특별시",
    "수도권",
    "6개광역시",
    "5개광역시",
    "기타지방"
}

# 7) 출력에서 제외할 ‘구’(gu) 목록
skip_gus = {
    "부산", "대구", "인천", "광주", "대전", "울산",
    "경기", "충북", "충남", "전남", "경북", "경남",
    "제주", "강원", "전북", "강북14개구", "강남11개구"
}

# 8) 각 그룹별로 (그룹명, 구) 조합을 찍고, 날짜·값을 출력
for top_region, gu_list in grouped.items():
    if top_region in skip_groups:
        continue

    for gu in gu_list:
        # gu 자체가 skip 목록에 있으면 건너뛴다
        if gu in skip_gus:
            continue

        entry = region_map.get(gu)
        if not entry:
            continue

        # 강북/강남 그룹은 서울특별시로 표시
        region_label = "서울특별시" if top_region in {"강북14개구", "강남11개구"} else top_region

        for point in entry["dataList"]:
            date  = point["기준날짜"]
            value = point["데이터"]
            print(f"{region_label}, {gu}, {date}, {value}")