import requests
import json

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
    'referer': 'https://new.land.naver.com/complexes/8928?ms=37.497624,127.107268,17&a=APT:ABYG:JGC:PRE&e=RETAIL&articleNo=2501308230',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ' +
                  '(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
}

#지역 코드(시도/시군구/동 코드) 가져오기
def get_regions(cortarNo='0000000000'):
    """
    네이버 부동산 지역 리스트를 반환합니다.
    :param cortarNo: 10자리 지역코드 (기본값: '0000000000' = 전국)
    :return: regionList (JSON 배열), 요청 실패 시 예외 발생
    """
    url = f'https://new.land.naver.com/api/regions/list?cortarNo={cortarNo}'
    resp = requests.get(url, headers=headers, cookies=cookies)
    resp.raise_for_status()
    # 네이버 API는 UTF-8 with BOM을 자주 쓰므로 encoding 지정
    resp.encoding = 'utf-8-sig'
    data = resp.json()
    # 실제 필요한 키가 regionList니, 안전하게 꺼내서 반환
    return data.get('regionList', [])

# 특정 단지(아파트) 정보 가져오기
def get_complex_info(complex_id):
    url = f'https://new.land.naver.com/api/complexes/{complex_id}'
    resp = requests.get(url, headers=headers, cookies=cookies)
    resp.raise_for_status()
    #
    resp.encoding = 'utf-8-sig'
    return resp.json()['complexDetail']


# 네이버 부동산 지역별 매물 목록(JSON) 조회
def get_article_list(cortarNo, realEstateType='APT', tradeType='A1', page=1):
    url = 'https://new.land.naver.com/api/articles'
    params = {
        'cortarNo': cortarNo,
        'realEstateType': realEstateType,
        'tradeType': tradeType,
        'page': page,
        'sameAddressGroup': 'false'
    }
    r = requests.get(url, params=params, headers=headers, cookies=cookies)
    print("응답 코드:", r.status_code)
    print("응답 내용:", r.text)

    r.raise_for_status()  # 응답 코드가 200이 아니면 예외 발생

    json_data = r.json()
    if 'articles' not in json_data:
        raise ValueError(f"'articles' 키 없음. 실제 응답: {json_data}")

    return json_data['articles']

if __name__ == '__main__':
    # 예시: 전국(region code=0000000000) 지역을 조회
    regions = get_regions()
    print(json.dumps(regions, ensure_ascii=False, indent=2))
    #
    # 예시: LG개포자이(8928)의 단지 정보 가져오기
    detail = get_complex_info('8928')
    print(detail['pyoengNames'], detail.get('supplyArea', []))
    #
    # 예: 특정 동의 매물 20건 조회
    articles = get_article_list(cortarNo='4119011500', realEstateType='APT', tradeType='A1', page=1)
    for a in articles:
        print(a['atclNo'], a['prc'], a.get('area1'), a.get('flrInfo'))



