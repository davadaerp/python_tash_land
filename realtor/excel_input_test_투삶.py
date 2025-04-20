import os
import re
import pandas as pd
from realtor_db_utils import realtor_insert_or_update_record
from config import REALTOR_DB_PATH

# Excel 파일 경로 지정
EXCEL_FILENAME = os.path.join(REALTOR_DB_PATH, "대출상담사_투삶.xlsx")

# 모든 시트를 DataFrame 딕셔너리로 읽기 (키: 시트명, 값: DataFrame)
sheets_dict = pd.read_excel(EXCEL_FILENAME, sheet_name=None)

# 각 시트별로 처리
for sheet_name, df in sheets_dict.items():
    print(f"--- 시트: {sheet_name} ---")

    # 필수 컬럼 확인
    required_cols = {'지역', '담당자', '전화번호'}
    if not required_cols.issubset(df.columns):
        print(f"'{sheet_name}' 시트에 {required_cols - set(df.columns)} 컬럼이 없습니다.")
        continue

    for idx, row in df.iterrows():
        # 엑셀 데이터 추출
        raw_region = row['지역']
        region = str(raw_region).strip() if pd.notna(raw_region) and str(raw_region).strip() else "기타"
        #
        role        = str(row.get('구분', '')).strip()      # 예: "대출상담사"
        company     = str(row.get('회사', '')).strip()
        if company == 'nan':
            company = '';

        # raw_name: 원본 문자열 (예: "송지희\n팀장")
        raw_name = str(row['담당자'])

        # 1) 줄바꿈(\n, \r) 및 탭 제거
        no_whitespace = raw_name.replace('\n', '') \
            .replace('\r', '') \
            .replace('\t', '')

        # 2) 한글, 영문, 숫자, 공백 외 모든 문자는 제거
        name = re.sub(r'[^가-힣A-Za-z0-9 ]', '', no_whitespace).strip()

        raw_phone   = str(row['전화번호']).strip()
        # 1) 숫자만 남기기
        digits = re.sub(r'\D', '', raw_phone)

        # 2) '010' 으로 시작하지 않거나 길이가 11이 아니면 건너뛰기
        if not (digits.startswith('010') and len(digits) == 11):
            print(f"유효하지 않은 휴대폰 번호 '{raw_phone}' — 건너뜁니다.")
            continue

        # 3) '010-XXXX-XXXX' 형태로 포맷
        mobile = f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

        # mem_no: 1부터 시작하여 3자리 문자열로 포맷팅
        mem_no = str(idx + 1).zfill(3)

        # DB에 저장할 레코드 생성
        record = {
            "mem_no":        mem_no,
            "title":         role or "대출상담",  # 구분 컬럼이 비어있으면 기본값
            "representative": name,
            "address1":      region,
            "address2":      company,
            "landline_phone": "",
            "mobile_phone":  mobile,
            "sel_type":      "loaner"
        }
        print(record)

        # DB에 삽입 (중복 검사 포함)
        realtor_insert_or_update_record(record)

    print()
