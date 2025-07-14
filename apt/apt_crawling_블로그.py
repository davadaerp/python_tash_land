# playWright툴이용한 검색처리(실시간검색적용등)
https://www.youtube.com/watch?v=RhOLFm3XG8Y


https://www.youtube.com/watch?v=xht7-LwT9Ro

https://tech-archive.com/29

아래는 네이버 부동산에서 서울시에서 매매가 9억 미만인 아파트 정보를 크롤링하는 코드입니다.


-- 네이버부동산 api작성한 깃허브 https://github.com/jissp/naver-land-crawler
https://velog.io/@dev-lop/%ED%86%A0%EC%9D%B4%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8-%EB%84%A4%EC%9D%B4%EB%B2%84-%EB%B6%80%EB%8F%99%EC%82%B0-%ED%81%AC%EB%A1%A4%EB%9F%AC

import time
import random
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json

# 쿠키 정보 (필요에 따라 수정)
cookies = {
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

# 여러 User-Agent 문자열 목록
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/114.0.1823.67',
    'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0'
]


# 기본 헤더 템플릿 (매 요청마다 User-Agent를 무작위 선택)
BASE_HEADERS = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzY0OTg2NDIsImV4cCI6MTczNjUwOTQ0Mn0.g37w29EO_D45o3PXXHvTCtXMOJe6d50Q1zGwW1S_WoA',
    'cache-control': 'no-cache',
    'referer': 'https://new.land.naver.com/offices?ms=37.497624,127.107268,17&a=SG:SMS&e=RETAIL&articleNo=2464180374',
}


# 세션 생성 및 기본 설정
session = requests.Session()
session.cookies.update(cookies)

def get_random_headers():
    headers = BASE_HEADERS.copy()
    headers['User-Agent'] = random.choice(USER_AGENTS)
    return headers

def crawl_naver_real_estate():
    # 네이버 부동산 URL 설정
    url = "https://new.land.naver.com/complexes?ms=37.563485,126.980018,17&a=APT:ABYG:JGC&e=RETAIL"

    # HTTP 요청 보내고 응답 받기
    headers = get_random_headers()
    #response = session.get(url, headers=headers)
    response = requests.get(url, headers=headers)

    # 응답의 HTML을 BeautifulSoup으로 파싱
    soup = BeautifulSoup(response.text, 'html.parser')

    # 아파트 정보 추출
    apt_list = soup.select('.item_title')

    # 결과 출력
    for apt in apt_list:
        apt_name = apt.text.strip()
        print(apt_name)

# 메인 함수
def main():
    print("서울시 매매가 9억 미만 아파트 목록:")
    crawl_naver_real_estate()

if __name__ == "__main__":
    main()





https://cocoabba.tistory.com/58

전체 요청 절차는 아래와 같다.
 1. 모바일 네이버 부동산 사이트에서 검색어(지역명) 입력 : https://m.land.naver.com/search/result/검색어

import requests
from bs4 import BeautifulSoup
import json

keyword = "원하는 지역명"
url = "https://m.land.naver.com/search/result/{}".format(keyword)
res = requests.get(url)
res.raise_for_status()

soup = (str)(BeautifulSoup(res.text, "lxml"))


 2. 응답 메시지 내에서 필요 데이터 추출 및 요청 데이터 구성: lat, lon, z, cortarNo, rletTpCds, tradTpCds

#응답 메시지 속에서 원하는 데이터 얻기
#  filter: {
#             lat: '37.550985',
#             lon: '126.849534',
#             z: '12',
#             cortarNo: '1150000000',
#             cortarNm: '강서구',
#             rletTpCds: '*',
#             tradTpCds: 'A1:B1:B2'
#         },

value = soup.split("filter: {")[1].split("}")[0].replace(" ","").replace("'","")

lat = value.split("lat:")[1].split(",")[0]
lon = value.split("lon:")[1].split(",")[0]
z = value.split("z:")[1].split(",")[0]
cortarNo = value.split("cortarNo:")[1].split(",")[0]
rletTpCds = value.split("rletTpCds:")[1].split(",")[0]
tradTpCds = value.split("tradTpCds:")[1].split()[0]

# lat - btm : 37.550985 - 37.4331698 = 0.1178152
# top - lat : 37.6686142 - 37.550985 = 0.1176292
lat_margin = 0.118

# lon - lft : 126.849534 - 126.7389841 = 0.1105499
# rgt - lon : 126.9600839 - 126.849534 = 0.1105499
lon_margin = 0.111

btm=float(lat)-lat_margin
lft=float(lon)-lon_margin
top=float(lat)+lat_margin
rgt=float(lon)+lon_margin

# 최초 요청 시 디폴트 값으로 설정되어 있으나, 원하는 값으로 구성
rletTpCds="SG" #상가
tradTpCds="A1:B1:B2" #매매/전세/월세 매물 확인

응답메시지 속에 필요한 데이터인 filter: {} 값을 파싱하여 다음 요청에 필요한 각 필드 데이터를 추출하였다.
검색 시, 조건에 해당하는 rletTpCds (상가 구분), tradTpCds (거래 유형) 에 대해서도 응답 메시지 내 데이터를 통해 아래와 같이 디테일한 정보를 확인 할 수 있다.
최초 요청 메시지에서 각 속성값 확인 가능

_tradTpCd = [{tagCd: 'A1', uiTagNm: '매매'},
             {tagCd: 'B1', uiTagNm: '전세'},
             {tagCd: 'B2', uiTagNm: '월세'},
             {tagCd: 'B3', uiTagNm: '단기임대'}];
_rletTpCd = [{tagCd: 'APT', uiTagNm: '아파트'}, {tagCd: 'OPST', uiTagNm: '오피스텔'}, {tagCd: 'VL', uiTagNm: '빌라'},
             {tagCd: 'ABYG', uiTagNm: '아파트분양권'}, {tagCd: 'OBYG', uiTagNm: '오피스텔분양권'}, {tagCd: 'JGC', uiTagNm: '재건축'},
             {tagCd: 'JWJT', uiTagNm: '전원주택'}, {tagCd: 'DDDGG', uiTagNm: '단독/다가구'}, {tagCd: 'SGJT', uiTagNm: '상가주택'},
             {tagCd: 'HOJT', uiTagNm: '한옥주택'}, {tagCd: 'JGB', uiTagNm: '재개발'}, {tagCd: 'OR', uiTagNm: '원룸'},
             {tagCd: 'GSW', uiTagNm: '고시원'}, {tagCd: 'SG', uiTagNm: '상가'}, {tagCd: 'SMS', uiTagNm: '사무실'},
             {tagCd: 'GJCG', uiTagNm: '공장/창고'}, {tagCd: 'GM', uiTagNm: '건물'}, {tagCd: 'TJ', uiTagNm: '토지'},
             {tagCd: 'APTHGJ', uiTagNm: '지식산업센터'}];

 3. 재구성한 URL로 상가 물건 그룹 데이터 요청 : https://m.land.naver.com/cluster/clusterList
   : 상가 물건 그룹?  앞선 포스팅에서 보았던 것처럼 상가를 처음 검색하면 매물 목록이 아니라 원형 형태의 데이터 그룹이 생기고, 각 그룹으로 접근하여, 물건 별 데이터를 확인 할 수 있다.
# clusterList?view 를 통한 그룹(단지)의 데이터를 가져온다.
remaked_URL = "https://m.land.naver.com/cluster/clusterList?view=atcl&cortarNo={}&rletTpCd={}&tradTpCd={}&z={}&lat={}&lon={}&btm={}&lft={}&top={}&rgt={}"\
     .format(cortarNo, rletTpCds, tradTpCds, z, lat, lon,btm,lft,top,rgt)

res2 = requests.get(remaked_URL)
json_str = json.loads(json.dumps(res2.json()))

응답 메시지 속 JSON 형태의 데이터를 확인해보면 JSON 의 ['data']['ARTICLE'] 값을 통해 상가 물건 그룹 데이터를 확인 할 수 있다.


 4. 각 물건 별 데이터 요청 : https://m.land.naver.com/cluster/ajax/articleList
values = json_str['data']['ARTICLE']

# 큰 원으로 구성되어 있는 전체 매물그룹(values)을 load 하여 한 그룹씩 세부 쿼리 진행
for v in values:
    lgeo = v['lgeo']
    count = v['count']
    z2 = v['z']
    lat2 = v['lat']
    lon2 = v['lon']

    len_pages = count / 20 + 1
    for idx in range(1, math.ceil(len_pages)):
        remaked_URL2 = "https://m.land.naver.com/cluster/ajax/articleList?""itemId={}&mapKey=&lgeo={}&showR0=&" \
                       "rletTpCd={}&tradTpCd={}&z={}&lat={}&""lon={}&totCnt={}&cortarNo={}&page={}" \
            .format(lgeo, lgeo, rletTpCds, tradTpCds, z2, lat2, lon2, count, cortarNo, idx)


 5. JSON 형태 데이터 파싱을 통한 원하는 데이터 추출 : Excel 형태
마지막 단계에서 articleList 요청을 통해서 각 매물 별 요청 진행 및 원하는 데이터를 얻을 수 있다.

atclNo = v['atclNo']  # 물건번호
rletTpNm = v['rletTpNm']  # 상가구분
tradTpNm = v['tradTpNm']  # 매매/전세/월세 구분
prc = v['prc']  # 가격
spc1 = v['spc1']  # 계약면적(m2) -> 평으로 계산 : * 0.3025
spc2 = v['spc2']  # 전용면적(m2) -> 평으로 계산 : * 0.3025
hanPrc = v['hanPrc']  # 보증금
rentPrc = v['rentPrc']  # 월세
flrInfo = v['flrInfo']  # 층수(물건층/전체층)
tagList = v['tagList']  # 기타 정보
rltrNm = v['rltrNm']  # 부동산
detaild_information = "https://m.land.naver.com/article/info/{}".format(atclNo)




        remaked_URL2 = "https://m.land.naver.com/cluster/ajax/articleList?""itemId={}&mapKey=&lgeo={}&showR0=&" \
                       "rletTpCd={}&tradTpCd={}&z={}&lat={}&""lon={}&totCnt={}&cortarNo={}&page={}" \
            .format(lgeo, lgeo, rletTpCds, tradTpCds, z2, lat2, lon2, count, cortarNo, idx)

        res3 = requests.get(remaked_URL2, headers=headers)
        json_str3 = json.loads(json.dumps(res3.json()))
        values3 = json_str3['body']
        for v2 in values3:
            atclNo = v2['atclNo']        # 물건번호

.....

        atclNo = v['atclNo']  # 물건번호
        rletTpNm = v['rletTpNm']  # 상가구분
        tradTpNm = v['tradTpNm']  # 매매/전세/월세 구분
        prc = v['prc']  # 가격
        spc1 = v['spc1']  # 계약면적(m2) -> 평으로 계산 : * 0.3025
        spc2 = v['spc2']  # 전용면적(m2) -> 평으로 계산 : * 0.3025
        hanPrc = v['hanPrc']  # 보증금
        rentPrc = v['rentPrc']  # 월세
        flrInfo = v['flrInfo']  # 층수(물건층/전체층)
        tagList = v['tagList']  # 기타 정보
        rltrNm = v['rltrNm']  # 부동산
        detaild_information = "https://m.land.naver.com/article/info/{}".format(atclNo)