import streamlit as st
import requests
import pandas as pd

# 부동산 데이터 수집 함수
def fetch_real_estate_data(page=1):
    cookies = {
        '_ga': 'GA1.1.1084468181.1734915860',
        'NAC': 'bLinBcgL5eHAA',
        '_fwb': '92EW36MJWoMlKDFNRGVTar.1734915863389',
        'NNB': 'P3BVN6YZW5UGO',
        '_fwb': '25JZHrvoj0EGrBF5e6kEjG.1734916083966',
        'nid_inf': '157907741',
        'NID_JKL': 'JbQzkvYC5XyCgwG1UNcFPjsan0+q1opYGHjFc1EPk0Q=',
        'landHomeFlashUseYn': 'Y',
        'nhn.realestate.article.rlet_type_cd': 'Z02',
        'page_uid': 'i33ygsqptbNsse1dgqZssssstQC-503024',
        'NACT': '1',
        'SRT30': '1736435767',
        '_ga_451MFZ9CFM': 'GS1.1.1736437354.6.0.1736437359.0.0.0',
        'REALESTATE': 'Fri%20Jan%2010%202025%2000%3A43%3A52%20GMT%2B0900%20(Korean%20Standard%20Time)',
        'BUC': 'FAMDGgz8LSWG2XGLqaRFOvfHHPgrt0WbOyUnGo5esnw=',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzY0Mzc0MzIsImV4cCI6MTczNjQ0ODIzMn0.7XGA86KwOs1NgsVfGkhSvBAN82KZW5b9I8NTJ8fMgDU',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://new.land.naver.com/complexes/111515?ms=37.497624,127.107268,17&a=APT:ABYG:JGC:PRE&e=RETAIL&articleNo=2501308230',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    data_list = []
    url = f'https://new.land.naver.com/api/articles/complex/111515?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo=111515&buildingNos=&areaNos=&type=list&order=prc'

    response = requests.get(url, cookies=cookies, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for article in data.get('articleList', []):
            data_list.append({
                '번호': article.get('articleNo'),
                '아파트명': article.get('articleName'),
                '거래유형': article.get('tradeTypeName'),
                '가격': article.get('dealOrWarrantPrc'),
                '층정보': article.get('floorInfo'),
                '면적1': article.get('area1'),
                '면적2': article.get('area2'),
                '방향': article.get('direction'),
                '확인날짜': article.get('articleConfirmYmd'),
                '특징': article.get('articleFeatureDesc'),
            })
    else:
        st.error(f"{page}페이지 데이터 요청 실패: {response.status_code}")

    return data_list


# Streamlit 페이지 네이션 구현
def show_real_estate_data(page):
    data = fetch_real_estate_data(page)
    if data:
        df = pd.DataFrame(data)
        st.dataframe(df)  # Dataframe을 Streamlit에서 보여줍니다
        return df
    return None

# 페이지 관리
current_page = 1

# Streamlit UI 설정
st.title("부동산 정보 보기")

# 데이터 수집 및 페이지 이동
col1, col2 = st.columns(2)

with col1:
    if st.button("이전 페이지") and current_page > 1:
        current_page -= 1
        show_real_estate_data(current_page)

with col2:
    if st.button("다음 페이지"):
        current_page += 1
        show_real_estate_data(current_page)

# 처음에 첫 페이지 데이터 로딩
show_real_estate_data(current_page)
