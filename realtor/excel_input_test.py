import os
import pandas as pd
from realtor_db_utils import realtor_insert_record
from config import REALTOR_DB_PATH

# Excel 파일 경로 지정
EXCEL_FILENAME = os.path.join(REALTOR_DB_PATH, "대출상담사.xlsx")

# 모든 시트를 DataFrame 딕셔너리로 읽기 (키: 시트명, 값: DataFrame)
sheets_dict = pd.read_excel(EXCEL_FILENAME, sheet_name=None)

# 각 시트별로 처리
for sheet_name, df in sheets_dict.items():
    print(f"--- 시트(지역): {sheet_name} ---")

    # '성함'과 '연락처' 열이 있는지 확인
    if '성함' in df.columns and '연락처' in df.columns:
        for index, row in df.iterrows():
            name = row['성함']
            phone = row['연락처']
            region = sheet_name

            # Excel 행의 데이터를 기반으로 DB에 저장할 record 생성
            record = {
                # mem_no는 예시로 index 값을 3자리 문자열로 변환하여 사용합니다.
                "mem_no": str(index).zfill(3),
                # title은 기본값으로 "대출상담"을 사용합니다.
                "title": "대출상담",
                # 대표자명은 성함 컬럼의 값으로 설정합니다.
                "representative": name,
                # address1은 시트명(지역)으로 설정합니다.
                "address1": region,
                # address2와 landline_phone은 엑셀에 해당 정보가 없으므로 빈 문자열로 처리합니다.
                "address2": region,
                "landline_phone": "",
                # mobile_phone은 연락처 컬럼의 값으로 설정합니다.
                "mobile_phone": phone,
                "sel_type": "loaner"
            }
            print(record)
            # DB에 단일 레코드 삽입 (내부에서 중복 확인 후 삽입)
            realtor_insert_record(record)
    else:
        print("해당 시트에 '성함' 또는 '연락처' 열이 없습니다.")

    print()
