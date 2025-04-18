import json
import pandas as pd
import re


def load_json_data(filepath):
    """JSON 파일 로드"""
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def extract_region_code(address, json_data):
    """주소에서 시도 코드, 시군구 코드, 읍면동 추출"""
    for region in json_data:
        # 시도 이름을 ',' 기준으로 분리하여 리스트로 저장
        sido_names = region["시도 이름"].split(",")

        # 주소에 포함된 시도 이름 찾기
        if any(sido_name.strip() in address for sido_name in sido_names):
            sido_code = region["시도 코드"]
            sido_name = sido_names[0].strip()  # 첫 번째 시도 이름 사용

            for city in region["시군구"]:
                if city["시군구 이름"] in address:
                    sigungu_code = city["시군구 코드"]
                    sigungu_name = city["시군구 이름"]

                    match = re.search(r'([가-힣]+(읍|면|동))', address)
                    eub_myeon_dong = match.group(1) if match else None

                    return sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong

    return None, None, None, None, None


def process_auction_data(auction_file, region_file):
    """경매 데이터 처리 및 출력"""
    json_data = load_json_data(region_file)

    with open(auction_file, 'r', encoding='utf-8') as file:
        df = pd.read_csv(file)

    if '주소1' not in df.columns:
        raise ValueError("CSV 파일에 '주소1' 필드가 존재하지 않습니다.")

    print(f"{'순번':<5}{'주소1':<30}{'시도 코드':<10}{'시도 이름':<10}{'시군구 코드':<10}{'시군구 이름':<10}{'읍면동':<10}")

    for idx, row in enumerate(df.iterrows(), start=1):
        address = str(row[1]['주소1'])
        sido_code, sido_name, sigungu_code, sigungu_name, eub_myeon_dong = extract_region_code(address, json_data)

        # None 값을 빈 문자열로 변환하여 출력
        print(f"{idx:<5}"
              f"{address:<30}"
              f"{sido_code if sido_code else '':<10}"
              f"{sido_name if sido_name else '':<10}"
              f"{sigungu_code if sigungu_code else '':<10}"
              f"{sigungu_name if sigungu_name else '':<10}"
              f"{eub_myeon_dong if eub_myeon_dong else '없음':<10}")


if __name__ == "__main__":
    auction_file = "auction_data.csv"  # 경매 데이터 파일
    region_file = "region_codes.json"  # 법정코드 JSON 파일
    process_auction_data(auction_file, region_file)
