import requests
import xmltodict
import csv
import datetime

# 2024년으로 설정
search_year = 2024

# 변경된 URL
url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"

# 요청 파라미터 설정
lawd_cd = "11110"  # 예시 법정동 코드
params = {
    "serviceKey": "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==",
    "LAWD_CD": lawd_cd,  # 검색 조건으로 법정동 코드
    "DEAL_YMD": f"{search_year}01",  # 기본값으로 2024년 1월을 설정
    "pageNo": 1,
    "numOfRows": 50
}

# 전체 데이터를 저장할 리스트
all_items = []

# 월별로 검색 요청을 보내기 위해 반복
for month in range(1, 13):  # 1월부터 12월까지
    month_str = f"{month:02d}"  # 월을 2자리 형식으로 만들어서 (01, 02, ..., 12)
    params["DEAL_YMD"] = f"{search_year}{month_str}"  # 각 월에 대해 DEAL_YMD를 업데이트

    # API 요청
    response = requests.get(url, params=params, verify=False)

    # 응답 코드가 200이면 정상 처리
    if response.status_code == 200:
        try:
            # XML 응답을 JSON으로 변환
            response_dict = xmltodict.parse(response.text)

            # response, body, items, item 각 단계에서 None 체크 후 접근
            response_data = response_dict.get('response', {})
            body = response_data.get('body', {})
            items = body.get('items', {})

            # 'items'이 없거나 비어 있는 경우 처리
            if not items or not isinstance(items, dict) or 'item' not in items:
                print(f"{search_year}년 {month_str}월: 검색된 데이터가 없습니다.")
            else:
                items = items['item']
                # 거래년, 거래월, 거래일을 기준으로 소트
                items_sorted = sorted(items, key=lambda x: (x.get('dealYear', ''), x.get('dealMonth', ''), x.get('dealDay', '')))

                # 전체 항목에 추가
                all_items.extend(items_sorted)

                # 필터링된 항목을 화면에 출력
                print(f"{'순번':<8}{'주소(법정코드)':<14}{'거래년도(dealYear)':<10}{'거래월(dealMonth)':<10}{'거래일(dealDay)':<10}{'건축년도(buildYear)':<14}{'건물면적(buildingAr)':<14}{'건물종류(buildingType)':<14}{'건물용도(buildingUse)':<22}{'매수구분(buyerGbn)':<14}{'거래금액(dealAmount)':<14}{'부동산업소명(estateAgentSggNm)':<22}{'지번(jibun)':<14}{'토지이용(landUse)':<14}{'대지면적(plottageAr)':<14}{'시군구명(sggNm)':<14}{'읍면동명(umdNm)':<14}")
                print("=" * 200)

                # 항목 출력
                for index, item in enumerate(items_sorted, 1):
                    # None 값에 대해 빈 문자열로 대체
                    print(f"{str(index):<8}"  # 순번
                          f"{lawd_cd:<14}"  # 주소(법정코드) - 검색 조건 값
                          f"{str(item.get('dealYear', '') or ''):<10}"
                          f"{str(item.get('dealMonth', '') or ''):<10}"
                          f"{str(item.get('dealDay', '') or ''):<10}"
                          f"{str(item.get('buildYear', '') or ''):<14}"
                          f"{str(item.get('buildingAr', '') or ''):<14}"
                          f"{str(item.get('buildingType', '') or ''):<14}"
                          f"{str(item.get('buildingUse', '') or ''):<22}"
                          f"{str(item.get('buyerGbn', '') or ''):<14}"
                          f"{str(item.get('dealAmount', '') or ''):<14}"
                          f"{str(item.get('estateAgentSggNm', '') or ''):<22}"
                          f"{str(item.get('jibun', '') or ''):<14}"
                          f"{str(item.get('landUse', '') or ''):<14}"
                          f"{str(item.get('plottageAr', '') or ''):<14}"
                          f"{str(item.get('sggNm', '') or ''):<14}"
                          f"{str(item.get('umdNm', '') or ''):<14}")

        except Exception as e:
            print(f"{search_year}년 {month_str}월: XML 파싱 오류: {e}")
    else:
        print(f"{search_year}년 {month_str}월: API 요청 실패: {response.status_code}, 응답 내용: {response.text}")

# CSV 파일로 출력 (전체 데이터)
csv_filename = f"filtered_apartment_deals_{search_year}.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    # CSV 파일의 헤더 작성
    writer.writerow(
        ['순번', '주소(법정코드)', '거래년도(dealYear)', '거래월(dealMonth)', '거래일(dealDay)', '건축년도(buildYear)', '건물면적(buildingAr)',
         '건물종류(buildingType)', '건물용도(buildingUse)', '매수구분(buyerGbn)', '거래금액(dealAmount)', '부동산업소명(estateAgentSggNm)',
         '지번(jibun)', '토지이용(landUse)', '대지면적(plottageAr)', '시군구명(sggNm)', '읍면동명(umdNm)'])

    # 필터링된 데이터 저장
    for index, item in enumerate(all_items, 1):
        writer.writerow([
            str(index),  # 순번
            lawd_cd,  # 주소(법정코드) - 검색 조건 값
            item.get('dealYear', ''),
            item.get('dealMonth', ''),
            item.get('dealDay', ''),
            item.get('buildYear', ''),
            item.get('buildingAr', ''),
            item.get('buildingType', ''),
            item.get('buildingUse', ''),
            item.get('buyerGbn', ''),
            item.get('dealAmount', ''),
            item.get('estateAgentSggNm', ''),
            item.get('jibun', ''),
            item.get('landUse', ''),
            item.get('plottageAr', ''),
            item.get('sggNm', ''),
            item.get('umdNm', '')
        ])

print(f"{search_year}년: CSV 파일로 출력되었습니다: {csv_filename}")
