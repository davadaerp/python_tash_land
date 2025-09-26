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


def main():
    base = os.path.dirname(__file__)
    entries = load_entries(os.path.join(base, TXT_FILE))
    #
    structured = build_structure(entries)
    write_json_inline_cities(structured, os.path.join(base, OUTPUT_FILE))
    print(f"✅ '{OUTPUT_FILE}' 생성 완료 ({len(structured)}개 시도)")


if __name__ == "__main__":
    main()
