import requests
import xml.etree.ElementTree as ET

# API URL과 인증키 설정
url = "http://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"
service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="

# 초기 조건 설정
page_no = 1
num_of_rows = 500
all_data_retrieved = False
sequence_number = 1  # 순번 초기값

# 화면 목록 출력 (헤더)
print(
    f"{'순번':<6}{'지역 코드':<15}{'시도 코드':<10}{'시군구 코드':<15}{'읍면동 코드':<15}{'리 코드':<10}{'주민 코드':<15}{'지역 코드':<15}{'법정동 명칭':<20}{'정렬 순서':<12}{'상위 지역 코드':<15}{'하위 지역 명칭':<20}{'적용일자':<10}")
print("=" * 126)  # 구분선

while not all_data_retrieved:
    # 요청 파라미터
    params = {
        "ServiceKey": service_key,
        "type": "xml",
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "flag": "Y",
        "locatadd_nm": "서울특별시"  # 서울특별시에 해당하는 법정동 코드 목록
        # 읍명동 코드가 000 인것은 구만나옴
    }

    # API 요청
    response = requests.get(url, params=params)

    if response.status_code == 200:
        # XML 응답 파싱
        root = ET.fromstring(response.content)

        # row 데이터를 가져오기
        rows = root.findall(".//row")

        # 데이터가 없으면 종료
        if not rows:
            all_data_retrieved = True
            break

        # 데이터 출력
        for row in rows:
            print(
                f"{sequence_number:<6}"
                f"{(row.find('region_cd').text or ''):<15}"
                f"{(row.find('sido_cd').text or ''):<10}"
                f"{(row.find('sgg_cd').text or ''):<15}"
                f"{(row.find('umd_cd').text or ''):<15}"
                f"{(row.find('ri_cd').text or ''):<10}"
                f"{(row.find('locatjumin_cd').text or ''):<15}"
                f"{(row.find('locatjijuk_cd').text or ''):<15}"
                f"{(row.find('locatadd_nm').text or ''):<20}"
                f"{(row.find('locat_order').text or ''):<12}"
                f"{(row.find('locathigh_cd').text or ''):<15}"
                f"{(row.find('locallow_nm').text or ''):<20}"
                f"{(row.find('adpt_de').text or ''):<10}"
            )
            sequence_number += 1  # 순번 증가

        # 요청한 num_of_rows와 가져온 데이터 수 비교
        if len(rows) < num_of_rows:
            all_data_retrieved = True
        else:
            page_no += 1  # 다음 페이지로 넘어감

    else:
        print(f"API 요청 실패, 상태 코드: {response.status_code}")
        break
