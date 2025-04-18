import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import requests
import xmltodict
import csv
from datetime import datetime

# API URL
url = "http://apis.data.go.kr/1613000/RTMSDataSvcNrgTrade/getRTMSDataSvcNrgTrade"

# 현재 연도 가져오기
current_year = datetime.now().year

# UI 중앙 배치 함수
def center_window(window):
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# 커스텀 메시지 박스
def custom_message_box(root, message, box_type="info", on_confirm=None):
    box = tk.Toplevel(root)
    box.title("알림")
    box.geometry("300x150")
    center_window(box)

    tk.Label(box, text=message, wraplength=280, pady=20).pack()
    button_frame = tk.Frame(box)
    button_frame.pack(pady=10)

    if box_type == "confirm":
        tk.Button(button_frame, text="저장", command=lambda: [box.destroy(), on_confirm()]).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="취소", command=box.destroy).pack(side=tk.RIGHT, padx=5)
    else:
        tk.Button(button_frame, text="확인", command=box.destroy).pack()

    box.transient(root)
    box.grab_set()
    root.wait_window(box)

# 데이터 저장 함수
def save_to_csv():
    if not current_data:
        custom_message_box(root, "저장할 데이터가 없습니다.", "info")
        return

    def save():
        selected_dong = dong_entry.get().strip()  # 읍면동 필드값 가져오기
        selected_year = deal_year_combobox.get()
        selected_building_area = building_area_entry.get().strip()  # 건물면적 필드값 가져오기
        # 읍면동명이 공백이 아니면 파일명에 추가
        file_name = f"real_estate_data_{selected_year}_{selected_dong}_{selected_building_area}.csv" if selected_dong else f"real_estate_data_{selected_year}.csv"

        with open(file_name, mode="w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file)
            writer.writerow(columns)
            for item in current_data:
                writer.writerow(item)
        custom_message_box(root, f"데이터가 {file_name}에 저장되었습니다.", "info")

    custom_message_box(root, "데이터를 CSV 파일로 저장하시겠습니까?", "confirm", save)

# API 데이터 가져오기
def get_data():
    global current_data
    selected_address = address_entry.get()
    selected_year = deal_year_combobox.get()
    selected_dong = dong_entry.get().strip()
    selected_building_area = building_area_entry.get().strip()

    if not selected_address:
        custom_message_box(root, "주소(법정동 코드)를 입력해주세요.", "info")
        return

    current_data = []
    tree.delete(*tree.get_children())  # 화면 목록 초기화

    # 1월부터 12월까지 데이터 가져오기
    for month in range(1, 13):
        deal_ymd = f"{selected_year}{str(month).zfill(2)}"
        params = {
            "serviceKey": "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==",
            "LAWD_CD": selected_address,
            "DEAL_YMD": deal_ymd,
            "pageNo": page_no.get(),
            "numOfRows": 30,  # 페이지당 화면 출력 건수 수정
        }

        try:
            response = requests.get(url, params=params, verify=False)
            response.raise_for_status()
            response_dict = xmltodict.parse(response.text)
            items = response_dict.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not items:
                continue

            if isinstance(items, dict):
                items = [items]

            # 동 검색 필터 적용
            if selected_dong:
                items = [item for item in items if selected_dong in item.get('umdNm', '')]

            # 건물면적 검색 조건 적용
            if selected_building_area:
                try:
                    selected_building_area_float = float(selected_building_area)  # 사용자가 입력한 면적
                except ValueError:
                    custom_message_box(root, "건물평수는 숫자로 입력해 주세요.", "info")
                    return
                selected_building_area_pyung = int(selected_building_area_float)  # 평수로 변환

                # 건물면적 비교 조건 적용
                items = [item for item in items if item.get('buildingAr', '') and int(float(item.get('buildingAr', 0)) / 3.3) == selected_building_area_pyung]

            for item in items:  # 순번은 화면에 나타나는 순서대로
                # 건물면적을 3.3으로 나누어 평수로 계산
                building_area = item.get('buildingAr', '')
                try:
                    building_area_float = float(building_area) / 3.3  # 3.3으로 나누기
                    building_area_in_pyung = int(building_area_float)  # 소수점 제외하여 평수로 표시
                except ValueError:
                    building_area_in_pyung = building_area  # 면적값이 없거나 잘못된 경우 원래 값 표시

                # 거래일자 결합
                deal_date = f"{item.get('dealYear', '')}-{str(item.get('dealMonth', '')).zfill(2)}-{str(item.get('dealDay', '')).zfill(2)}"

                row = [
                    len(current_data) + 1,  # 현재 데이터 리스트의 길이를 사용하여 순번 부여
                    selected_address,  # 주소(법정동 코드) 화면 목록에 표시
                    item.get('dealYear', ''),
                    item.get('dealMonth', ''),
                    item.get('dealDay', ''),
                    deal_date,  # 거래일자 추가
                    item.get('buildYear', ''),
                    building_area,  # 건물면적만 표시
                    building_area_in_pyung,  # 건물평수
                    item.get('buildingType', ''),
                    item.get('buildingUse', ''),
                    item.get('buyerGbn', ''),
                    item.get('dealAmount', ''),
                    item.get('estateAgentSggNm', ''),
                    item.get('jibun', ''),
                    item.get('landUse', ''),
                    item.get('plottageAr', ''),
                    item.get('sggNm', ''),
                    item.get('umdNm', ''),
                ]
                current_data.append(row)
                tree.insert("", "end", values=row)

            # 거래일자 기준으로 정렬
            current_data.sort(key=lambda x: datetime.strptime(x[5], "%Y-%m-%d") if x[5] else datetime.max)

            update_page_navigation()
        except Exception as e:
            custom_message_box(root, f"데이터 처리 중 오류가 발생했습니다: {e}", "error")

# 페이지 네비게이션 업데이트
def update_page_navigation():
    total_pages = (len(current_data) // 30) + (1 if len(current_data) % 30 > 0 else 0)  # 페이지당 화면 출력 건수 수정
    page_no.set(1)
    page_label.config(text=f"페이지: {page_no.get()} / {total_pages}")

# 페이지 전환 함수
def prev_page():
    if page_no.get() > 1:
        page_no.set(page_no.get() - 1)
        get_data()

def next_page():
    total_pages = (len(current_data) // 30) + (1 if len(current_data) % 30 > 0 else 0)  # 페이지당 화면 출력 건수 수정
    if page_no.get() < total_pages:
        page_no.set(page_no.get() + 1)
        get_data()

# 메인 창 생성
root = tk.Tk()
root.title("부동산 거래 정보 조회")
root.geometry("1280x600")
center_window(root)

# 검색 조건 프레임
search_frame = tk.Frame(root)
search_frame.pack(pady=10, fill=tk.X)

address_label = tk.Label(search_frame, text="주소 (법정동 코드):")
address_label.pack(side=tk.LEFT, padx=5)
address_entry = tk.Entry(search_frame, width=10)
address_entry.insert(0, "11110")
address_entry.pack(side=tk.LEFT, padx=5)

deal_year_label = tk.Label(search_frame, text="거래년도:")
deal_year_label.pack(side=tk.LEFT, padx=5)
deal_year_combobox = ttk.Combobox(search_frame, state="readonly",
                                  values=[str(year) for year in range(current_year, current_year - 10, -1)], width=5)
deal_year_combobox.set(str(current_year))
deal_year_combobox.pack(side=tk.LEFT, padx=5)

dong_label = tk.Label(search_frame, text="동 검색:")
dong_label.pack(side=tk.LEFT, padx=5)
dong_entry = tk.Entry(search_frame, width=10)
dong_entry.pack(side=tk.LEFT, padx=5)

building_area_label = tk.Label(search_frame, text="건물평수:")  # '평'으로 변경
building_area_label.pack(side=tk.LEFT, padx=5)
building_area_entry = tk.Entry(search_frame, width=5)
building_area_entry.insert(0, "0")
building_area_entry.pack(side=tk.LEFT, padx=5)

# 엔터 키로 검색 실행
dong_entry.bind("<Return>", lambda event: get_data())

search_button = tk.Button(search_frame, text="검색", command=get_data)
search_button.pack(side=tk.LEFT, padx=5)

# 결과 목록 프레임
tree_frame = tk.Frame(root)
tree_frame.pack(fill=tk.BOTH, expand=True)

columns = ['순번', '법정동 코드', '거래년도', '거래월', '거래일', '거래일자', '건축년도', '건물면적', '건물평수', '건물종류', '건물용도', '매수구분', '거래금액', '부동산업소명', '지번', '토지이용', '대지면적',
           '시군구명', '읍면동명']
tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

scrollbar = tk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")
tree.configure(yscrollcommand=scrollbar.set)

# 페이지 네비게이션 프레임
page_frame = tk.Frame(root)
page_frame.pack(fill=tk.X, pady=5)

page_no = tk.IntVar(value=1)
page_label = tk.Label(page_frame, text=f"페이지: {page_no.get()}")
page_label.pack(side=tk.RIGHT, padx=10)

prev_button = tk.Button(page_frame, text="이전", command=prev_page)
prev_button.pack(side=tk.LEFT, padx=5)

next_button = tk.Button(page_frame, text="다음", command=next_page)
next_button.pack(side=tk.LEFT, padx=5)

save_button = tk.Button(page_frame, text="저장", command=save_to_csv)
save_button.pack(side=tk.LEFT, padx=5)

# 순번 연계 위한 초기 값 설정
current_data = []
root.mainloop()
