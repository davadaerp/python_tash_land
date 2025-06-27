#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re

FILENAME = '법정동코드.txt'

def extract_active_third_components(filepath):
    """
    파일을 읽어들여
    1) 총 행 수
    2) 폐지여부가 '존재'인 행만 골라
    3) fullname.split() 했을 때 3번째 요소가 '동','읍','면','가'로 끝나면
       (code, third) 리스트로 반환
    """
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

            # '존재'인 경우에만 마지막 토큰 검사
            name_tokens = fullname.split()
            if not name_tokens:
                continue
            last = name_tokens[-1]
            #print(last)
            if pattern.match(last):
                extracted.append((code, last, line))

    return total, exist_count, abolished_count, extracted

if __name__ == '__main__':
    total, exist_cnt, abolished_cnt, results = extract_active_third_components(FILENAME)

    # 추출된 (code, third) 출력
    for code, umdNm, line in results:
        print(f"{code}\t{umdNm}\t{line}")

    # 통계 정보
    print()
    print(f"총 행 수        : {total}")
    print(f"존재 건수       : {exist_cnt}")
    print(f"폐지 건수       : {abolished_cnt}")
