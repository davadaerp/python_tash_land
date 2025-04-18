import requests
import tkinter as tk
from tkinter import ttk, messagebox

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

# 부동산 데이터 수집 함수
def fetch_real_estate_data(page=1):
    cookies = {
        '_ga': 'GA1.1.1084468181.1734915860',
        'NAC': 'bLinBcgL5eHAA',
        '_fwb': '92EW36MJWoMlKDFNRGVTar.1734915863389',
        'NNB': 'P3BVN6YZW5UGO',
        '_fwb': '25JZHrvoj0EGrBF5e6kEjG.1734916083966',
        'nid_inf': '157907741',
        'NID_JKL': 'JbQzkvYC5XyCgwG1UNcFPjsan0+q1opYGHjFc1EPk0Q=',
        'landHomeFlashUseYn': 'Y',
        'nhn.realestate.article.rlet_type_cd': 'Z02',
        'page_uid': 'i33ygsqptbNsse1dgqZssssstQC-503024',
        'NACT': '1',
        'SRT30': '1736435767',
        '_ga_451MFZ9CFM': 'GS1.1.1736437354.6.0.1736437359.0.0.0',
        'REALESTATE': 'Fri%20Jan%2010%202025%2000%3A43%3A52%20GMT%2B0900%20(Korean%20Standard%20Time)',
        'BUC': 'FAMDGgz8LSWG2XGLqaRFOvfHHPgrt0WbOyUnGo5esnw=',
    }

    headers = {
        'accept': '*/*',
        'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzY0Mzc0MzIsImV4cCI6MTczNjQ0ODIzMn0.7XGA86KwOs1NgsVfGkhSvBAN82KZW5b9I8NTJ8fMgDU',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'referer': 'https://new.land.naver.com/complexes/111515?ms=37.497624,127.107268,17&a=APT:ABYG:JGC:PRE&e=RETAIL&articleNo=2501308230',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
    }

    data_list = []
    url = f'https://new.land.naver.com/api/articles/complex/111515?realEstateType=APT%3AABYG%3AJGC%3APRE&tradeType=A1&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&complexNo=111515&buildingNos=&areaNos=&type=list&order=prc'

    response = requests.get(url, cookies=cookies, headers=headers)

    if response.status_code == 200:
        data = response.json()
        for article in data.get('articleList', []):
            data_list.append({
                '번호': article.get('articleNo'),
                '아파트명': article.get('articleName'),
                '거래유형': article.get('tradeTypeName'),
                '가격': article.get('dealOrWarrantPrc'),
                '층정보': article.get('floorInfo'),
                '면적1': article.get('area1'),
                '면적2': article.get('area2'),
                '방향': article.get('direction'),
                '확인날짜': article.get('articleConfirmYmd'),
                '특징': article.get('articleFeatureDesc'),
            })
    else:
        messagebox.showerror("에러", f"{page}페이지 데이터 요청 실패: {response.status_code}")

    return data_list


# 페이지 관리
current_page = 1

# 부동산 데이터 수집 함수
def show_real_estate_data(page):
    global current_page
    data = fetch_real_estate_data(page)
    if data:
        # 테이블 초기화 후 새 데이터 추가
        for row in tree.get_children():
            tree.delete(row)
        for row in data:
            tree.insert("", "end", values=list(row.values()))
        messagebox.showinfo("완료", f"부동산 데이터 수집 완료! (페이지 {page})")
        current_page = page

# 이전 페이지
def previous_page():
    if current_page > 1:
        show_real_estate_data(current_page - 1)

# 다음 페이지
def next_page():
    show_real_estate_data(current_page + 1)


# Tkinter GUI 설정
root = tk.Tk()
root.title("부동산 정보 보기")
root.geometry("1000x600")

# 테이블 설정
columns = ['번호', '아파트명', '거래유형', '가격', '층정보', '면적1', '면적2', '방향', '확인날짜', '특징']
tree = ttk.Treeview(root, columns=columns, show='headings')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center", width=100)

tree.pack(fill=tk.BOTH, expand=True)

# 버튼 추가
btn_fetch = tk.Button(root, text="부동산 데이터 수집", command=lambda: show_real_estate_data(current_page))
btn_fetch.pack(pady=10)

# 이전 페이지 버튼
btn_previous = tk.Button(root, text="이전 페이지", command=previous_page)
btn_previous.pack(side=tk.LEFT, padx=10, pady=10)

# 다음 페이지 버튼
btn_next = tk.Button(root, text="다음 페이지", command=next_page)
btn_next.pack(side=tk.RIGHT, padx=10, pady=10)

# GUI 실행
root.mainloop()
