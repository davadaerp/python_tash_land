#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 주요 투자 법정동 코드 추출
# 충주(대소원면-지오웰), 청주(개신동,가경동,북대동), 부산, 창원, 울산(조선 or 기계), 김해, 진주, 전주, 춘천, 원주, 충북(오창-산업단지근처임, 오송), 순천

#-- 공급이 없는지역(휘파람 강의)
# 서울
# 전주-2026년이후 공급이 없다.. 가장빨리 오르고 있다
# 울산-2026년이후 공급이 없다.. 전주다음 오르고 있다
# 부산-2028년부터 공급이 없다.. 인허가도 없다.
# 대구-2026년이후 공급이 없다.. 인허가도 없다. 2027년이후 심각해짐..=> 지금시점에 전세끼고 사두면 2027년도 엄청 오를듯.
#
# 부동산 핵심지표
#1. 도시의 서열(인구수)
#2. 인구수
#3. 공급량(인허가량)
#4. 전세가비율(90%이상)
#5. PIR기준(소득대비 주택가격 비율) => 울산(남구) -> 부산(해운대구) -> 대구(수성구) : 투자금액대비 싼곳을 찾아라.(전주보다는 부산, 창원을 사야함-1빠 창원(일자리도 많음))
    # 대구는 내년(2026년 접근)
    # 부산-동래구, 해운대구, 광안대교뷰
#6. 금리(기준금리, 주택담보대출금리)
#
# 2025 최저투자지역


import re

FILENAME = '주요투자법정동코드.txt'

def extract_active_third_components(filepath):
    """
    파일을 읽어들여
    1) 총 행 수
    2) 폐지여부가 '존재'인 행만 골라
    3) fullname.split() 했을 때 3번째 요소가 '동','읍','면','가'로 끝나면
       (code, third) 리스트로 반환
    """
    # 1) 제외할 전체지역명 목록 (시·도 / 시·군·구 단위)
    EXCLUDE_NAMES = {
        "서울특별시",
        "경기도",
        # "부산광역시",
        # "대구광역시",
        "인천광역시",
        "광주광역시",
        "대전광역시",
        # "울산광역시",
        "세종특별자치시",
        # "강원특별자치도",
        # "충청북도",
        # "충청남도",
        # "전북특별자치도",
        # "전라남도",
        # "경상북도"
        # "경상남도",
        # "제주특별자치도"
    }

    pattern = re.compile(r'.+(동|읍|면|리|가)$')
    extracted = []
    total = 0
    exist_count = 0
    abolished_count = 0

    with open(filepath, encoding='utf-8') as f:
        header = f.readline()  # 헤더 스킵
        for line in f:
            line = line.strip()
            if not line:
                continue
            total += 1
            parts = line.split('\t')
            if len(parts) != 3:
                continue
            code, fullname, status = parts

            if status == '존재':
                exist_count += 1
            elif status == '폐지':
                abolished_count += 1

            if status != '존재':
                continue

            # 4) 제외지역명 필터 (fullname이 특정 시·도 이름으로 시작하면 제외)
            if any(fullname.startswith(ex) for ex in EXCLUDE_NAMES):
                continue

            print(code, fullname, status)

            # '존재'인 경우에만 마지막 토큰 검사
            name_tokens = fullname.split()
            if not name_tokens:
                continue
            last = name_tokens[-1]
            #print(last)
            if pattern.match(last):
                extracted.append((last, code, line))

    return total, exist_count, abolished_count, extracted

if __name__ == '__main__':
    total, exist_cnt, abolished_cnt, results = extract_active_third_components(FILENAME)

    # 추출된 (code, third) 출력
    # for umdNm, cortarNo, line in results:
    #     print(f"{umdNm}\t{cortarNo}\t{line}")

    # 통계 정보
    print()
    print(f"총 행 수        : {total}")
    print(f"존재 건수       : {exist_cnt}")
    print(f"폐지 건수       : {abolished_cnt}")
