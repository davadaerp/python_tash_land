import json
import os

TXT_FILE = "법정동코드.txt"
OUTPUT_FILE = "region_codes.json"


def get_short_name(full_name):
    """
    시도 축약명 생성
    """
    if full_name.endswith("특별자치도"):
        return full_name[:-5]
    if full_name.endswith("특별자치시"):
        return full_name[:-5]
    if full_name.endswith("광역시"):
        return full_name[:-3]
    if full_name.endswith("특별시"):
        return full_name[:-3]
    if full_name.endswith("도") and len(full_name) == 4:
        return full_name[0] + full_name[2]
    return full_name


def load_entries(path):
    entries = []
    with open(path, encoding="utf-8") as f:
        next(f)  # 헤더 스킵
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) != 3:
                continue
            code, name, status = parts
            if status == "존재":
                entries.append((code, name))
    return entries


def build_structure(entries):
    provinces = {}
    # 시도
    for code, name in entries:
        if code.endswith("00000000"):
            pkey = code[:2]
            provinces[pkey] = {
                "시도 코드": int(pkey),
                "시도 이름": f"{get_short_name(name)},{name}",
                "시군구": []
            }
    # 시군구
    for code, name in entries:
        pkey = code[:2]
        if pkey in provinces and code[2:5] != "000" and set(code[5:]) == {"0"}:
            city_code = int(code[:5])
            prov_full = provinces[pkey]["시도 이름"].split(",",1)[1]
            city_name = name.replace(f"{prov_full} ", "")
            provinces[pkey]["시군구"].append({
                "시군구 코드": city_code,
                "시군구 이름": city_name
            })
    # 정렬
    result = []
    for pkey in sorted(provinces.keys(), key=lambda x: int(x)):
        prov = provinces[pkey]
        prov["시군구"] = sorted(prov["시군구"], key=lambda x: x["시군구 코드"])
        result.append(prov)
    return result


def write_json_inline_cities(structured, out_path):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write('[\n')
        for i, prov in enumerate(structured):
            f.write('  {\n')
            f.write(f'    "시도 코드": {prov["시도 코드"]},\n')
            f.write(f'    "시도 이름": "{prov["시도 이름"]}\",\n')
            f.write('    "시군구": [\n')
            cities = prov["시군구"]
            for j, city in enumerate(cities):
                line = json.dumps(city, ensure_ascii=False)
                comma = ',' if j < len(cities) - 1 else ''
                f.write(f'      {line}{comma}\n')
            f.write('    ]\n')
            closing = '},' if i < len(structured) - 1 else '}'
            f.write(f'  {closing}\n')
        f.write(']\n')



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


def main():
    base = os.path.dirname(__file__)
    entries = load_entries(os.path.join(base, TXT_FILE))
    #
    structured = build_structure(entries)
    write_json_inline_cities(structured, os.path.join(base, OUTPUT_FILE))
    print(f"✅ '{OUTPUT_FILE}' 생성 완료 ({len(structured)}개 시도)")

    # 주소분석
    auction_file = "auction_data.csv"  # 경매 데이터 파일
    region_file = "region_codes.json"  # 법정코드 JSON 파일
    process_auction_data(auction_file, region_file)

if __name__ == "__main__":
    main()
