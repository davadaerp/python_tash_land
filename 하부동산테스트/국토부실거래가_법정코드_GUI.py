import requests
import xml.etree.ElementTree as ET
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import csv

# API URL과 인증키 설정
url = "http://apis.data.go.kr/1741000/StanReginCd/getStanReginCdList"
service_key = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="

# 초기 조건 설정
page_no = 1
num_of_rows = 500
all_data_retrieved = False
sequence_number = 1  # 순번 초기값

# tkinter 윈도우 설정
root = tk.Tk()
root.title("법정동 코드 조회")
root.geometry("1000x600")  # 화면 크기 설정
root.resizable(True, True)  # 창 크기 조정 가능

# 윈도우 중앙 배치
window_width = 1000
window_height = 600
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
position_top = int(screen_height / 2 - window_height / 2)
position_right = int(screen_width / 2 - window_width / 2)
root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# 법정동명 입력 필드 및 버튼
search_label = tk.Label(root, text="법정동명:")
search_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

search_entry = tk.Entry(root, width=40)
search_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")

search_button = tk.Button(root, text="검색", command=lambda: fetch_data(), width=10)
search_button.grid(row=0, column=2, padx=10, pady=10, sticky="w")

# 결과를 출력할 스크롤able 그리드 형식의 Treeview 사용
tree_frame = tk.Frame(root)
tree_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

tree_scroll_y = tk.Scrollbar(tree_frame, orient="vertical")
tree_scroll_x = tk.Scrollbar(tree_frame, orient="horizontal")

tree = ttk.Treeview(tree_frame, columns=("순번", "지역 코드", "시도 코드", "시군구 코드", "읍면동 코드", "리 코드", "주민 코드", "지역 코드", "법정동 명칭", "정렬 순서", "상위 지역 코드", "하위 지역 명칭", "적용일자"),
                    show="headings", yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
tree.grid(row=0, column=0, sticky="nsew")

tree_scroll_y.config(command=tree.yview)
tree_scroll_y.grid(row=0, column=1, sticky="ns")

tree_scroll_x.config(command=tree.xview)
tree_scroll_x.grid(row=1, column=0, sticky="ew")

# 열 이름 설정
tree.heading("순번", text="순번")
tree.heading("지역 코드", text="지역 코드")
tree.heading("시도 코드", text="시도 코드")
tree.heading("시군구 코드", text="시군구 코드")
tree.heading("읍면동 코드", text="읍면동 코드")
tree.heading("리 코드", text="리 코드")
tree.heading("주민 코드", text="주민 코드")
tree.heading("지역 코드", text="지역 코드")
tree.heading("법정동 명칭", text="법정동 명칭")
tree.heading("정렬 순서", text="정렬 순서")
tree.heading("상위 지역 코드", text="상위 지역 코드")
tree.heading("하위 지역 명칭", text="하위 지역 명칭")
tree.heading("적용일자", text="적용일자")

# 열 너비 자동 조정
for col in tree["columns"]:
    tree.column(col, width=100, anchor="w", stretch=tk.YES)

# 데이터 목록을 가져오는 함수
def fetch_data():
    global page_no, all_data_retrieved, sequence_number

    locatadd_nm = search_entry.get()  # 법정동명 검색어

    # 검색 조건이 비어있을 경우 경고
    if not locatadd_nm:
        messagebox.showwarning("경고", "법정동명을 입력해주세요.", icon='warning')
        return

    # 검색 결과 초기화
    for item in tree.get_children():
        tree.delete(item)

    all_data_retrieved = False
    sequence_number = 1
    total_count = 0  # 검색된 건수 초기화

    while not all_data_retrieved:
        params = {
            "ServiceKey": service_key,
            "type": "xml",
            "pageNo": str(page_no),
            "numOfRows": str(num_of_rows),
            "flag": "Y",
            "locatadd_nm": locatadd_nm  # 법정동명에 'like' 검색 조건 추가
        }

        # API 요청
        response = requests.get(url, params=params)

        if response.status_code == 200:
            root = ET.fromstring(response.content)
            rows = root.findall(".//row")

            if not rows:
                all_data_retrieved = True
                break

            for row in rows:
                locatadd = (row.find('locatadd_nm').text or "")
                if locatadd_nm in locatadd:  # 법정동명이 검색어와 일치하는 경우만 출력
                    tree.insert("", "end", values=(
                        sequence_number,
                        (row.find('region_cd').text or ''),
                        (row.find('sido_cd').text or ''),
                        (row.find('sgg_cd').text or ''),
                        (row.find('umd_cd').text or ''),
                        (row.find('ri_cd').text or ''),
                        (row.find('locatjumin_cd').text or ''),
                        (row.find('locatjijuk_cd').text or ''),
                        locatadd,
                        (row.find('locat_order').text or ''),
                        (row.find('locathigh_cd').text or ''),
                        (row.find('locallow_nm').text or ''),
                        (row.find('adpt_de').text or '')
                    ))
                    sequence_number += 1
                    total_count += 1

            # 검색 건수 업데이트
            if total_count == 0:
                messagebox.showinfo("검색 결과", "일치하는 법정동명이 없습니다.", icon='info')

            if len(rows) < num_of_rows:
                all_data_retrieved = True
            else:
                page_no += 1

        else:
            messagebox.showerror("API 요청 실패", f"상태 코드: {response.status_code}", icon='error')
            break

# CSV 저장 함수
def save_to_csv():
    # 저장 여부 확인
    result = messagebox.askyesno("저장", "저장하시겠습니까?")
    if not result:
        return

    # CSV로 저장할 데이터 추출
    data = []
    for item in tree.get_children():
        row = tree.item(item)["values"]
        data.append(row)

    # 파일 저장 대화상자
    save_path = "data.csv"
    try:
        with open(save_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["순번", "지역 코드", "시도 코드", "시군구 코드", "읍면동 코드", "리 코드", "주민 코드", "지역 코드", "법정동 명칭", "정렬 순서", "상위 지역 코드", "하위 지역 명칭", "적용일자"])
            writer.writerows(data)
        messagebox.showinfo("저장 완료", f"데이터가 {save_path}로 저장되었습니다.", icon='info')
    except Exception as e:
        messagebox.showerror("저장 실패", f"저장 중 오류가 발생했습니다: {str(e)}", icon='error')

# CSV 저장 버튼
save_button = tk.Button(root, text="CSV 저장", command=save_to_csv, width=15)
save_button.grid(row=2, column=0, padx=10, pady=10, sticky="w")

# 열 크기 자동 조정 이벤트
def on_column_double_click(event):
    item = tree.selection()
    if item:
        values = tree.item(item)["values"]
        locatadd = values[8]  # 법정동 명칭
        region_code = values[1]  # 지역 코드

        # Toplevel 메시지 박스를 중앙에 띄우기 위한 설정
        msg_box = tk.Toplevel(root)
        msg_box.title("선택된 데이터")
        msg_box.geometry("300x150")
        msg_box.resizable(False, False)

        msg_label = tk.Label(msg_box, text=f"지역 코드: {region_code}\n법정동 명칭: {locatadd}", padx=20, pady=20)
        msg_label.pack(expand=True)

        # 메시지 박스를 창 중앙에 위치
        window_width = msg_box.winfo_width()
        window_height = msg_box.winfo_height()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        msg_box.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# 데이터 그리드에서 더블 클릭 이벤트 연결
tree.bind("<Double-1>", on_column_double_click)

# 메인 윈도우 실행
root.mainloop()
