import requests
import csv
import sys

# 요청에 사용할 cookies와 headers
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

# 명령줄 인자 처리
if len(sys.argv) > 1:
    try:
        page = int(sys.argv[1])
    except ValueError:
        print("페이지 번호는 정수여야 합니다. 기본값으로 1을 사용합니다.")
        page = 1
else:
    page = 1
    print("페이지 번호가 제공되지 않아 기본값으로 1을 사용합니다.")

if len(sys.argv) > 2:
    try:
        area1 = int(sys.argv[2])
    except ValueError:
        print("area1 값은 정수여야 합니다. 기본값으로 62를 사용합니다.")
        area1 = 62
else:
    area1 = 62
    print("area1 값이 제공되지 않아 기본값으로 62를 사용합니다.")

# CSV 파일 설정 (페이지 번호와 area1 포함)
csv_file = f'real_estate_data_page_{page}_area_{area1}.csv'
fieldnames = ['page', 'articleNo', 'articleName', 'tradeTypeName', 'dealOrWarrantPrc', 'floorInfo', 'area1', 'area2',
              'direction', 'articleConfirmYmd', 'articleFeatureDesc']

# 데이터 수집 및 저장
with open(csv_file, mode='w', encoding='utf-8-sig', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    url = f'https://new.land.naver.com/api/articles/complex/111515?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin={area1}&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo=111515&buildingNos=&areaNos=&type=list&order=prc'

    response = requests.get(url, cookies=cookies, headers=headers)

    # 데이터 확인 및 저장
    if response.status_code == 200:
        data = response.json()
        for article in data.get('articleList', []):
            writer.writerow({
                'page': page,  # 페이지 번호 추가
                'articleNo': article.get('articleNo'),
                'articleName': article.get('articleName'),
                'tradeTypeName': article.get('tradeTypeName'),
                'dealOrWarrantPrc': article.get('dealOrWarrantPrc'),
                'floorInfo': article.get('floorInfo'),
                'area1': article.get('area1'),
                'area2': article.get('area2'),
                'direction': article.get('direction'),
                'articleConfirmYmd': article.get('articleConfirmYmd'),
                'articleFeatureDesc': article.get('articleFeatureDesc'),
            })
        print(f"페이지 {page}와 area1={area1} 데이터가 {csv_file}에 저장되었습니다.")
    else:
        print(f"페이지 {page} 요청 실패: {response.status_code}")

print(f"모든 데이터가 {csv_file} 파일에 저장되었습니다.")
