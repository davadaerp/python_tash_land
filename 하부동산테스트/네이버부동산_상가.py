import requests
import csv
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import webbrowser

cookies = {
    '_ga': 'GA1.1.1084468181.1734915860',
    'NAC': 'bLinBcgL5eHAA',
    '_fwb': '92EW36MJWoMlKDFNRGVTar.1734916083966',
    'NNB': 'P3BVN6YZW5UGO',
    'landHomeFlashUseYn': 'Y',
    'nhn.realestate.article.rlet_type_cd': 'Z02',
    'page_uid': 'i33ygsqptbNsse1dgqZssssstQC-503024',
    'NACT': '1',
    'nid_inf': '175862896',
    'NID_AUT': 'ygKx/8S35QHdbpFvrSj6Ain0juNAFljR+cLAR9Xnk1ITOoT1SOkvRSxgY4GqlFk1',
    'NID_JKL': 'fBQoOPU3NBnyLC3PSsnyOMWne/GV1pCjtpoL/9zUcMA=',
    'NID_SES': 'AAABonCFzQxM5vkiE54OMdyMPbSrToEm9aTkHKImD1LkHzoK0N0MZFhf9oSp2Bb7vsW689gWf1In0Rt24iwlKHdtigcGIsJV7vd6iqk3uXwD46j8sNDbImEQD+zz4c8uO1mIpFKAcSKCx1wawnUp74WxJv3ZugmAhOuSmXUaE82g7bxQ7lnKzz0xZdt0NBUyiX6mkNxAFKvIECrIJlq3FeXkzJnLL2G1oDIQZp6h/Vyp+/lpTy6VlK4DHdIll8UXoh525cy/YVWmkzCXd0hklcleD/5va5YYj2eSN/rlSVz/YlvXUtZR4BAZBwU9RNpFVY9BnbvLNgZ56L7rwFm8CEW5TYwWd3+LMytkJp+1zXx2lyqRmNHloosAuT1MoRgWjf8CQkEQhl7wKzlU5CdcEfOVOqvNQalo2MRRJu8AcnG39BDNEvDAp5eVQwCSEWE1N7YcaqF1BKEn1vQjSB8IVwsR8VvNFKYMdSZ25jhmwz95JIVnaON1nqHR/1xWOohG4dx+VPp8m0wRpmNBpfzcl07o9G6p9a4C0nPIbGh37LwgOLiJhkCONpSHtzOPJ5UJEUNp4A==',
    '_ga_451MFZ9CFM': 'GS1.1.1736498640.8.0.1736498642.0.0.0',
    'REALESTATE': 'Fri%20Jan%2010%202025%2017%3A44%3A02%20GMT%2B0900%20(Korean%20Standard%20Time)',
    'BUC': 'DKN0WiwVKe4qzAXKCI07Dr9GJz7Gpi1vd5NL1wCoAWw=',
}

headers = {
    'accept': '*/*',
    'accept-language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IlJFQUxFU1RBVEUiLCJpYXQiOjE3MzY0OTg2NDIsImV4cCI6MTczNjUwOTQ0Mn0.g37w29EO_D45o3PXXHvTCtXMOJe6d50Q1zGwW1S_WoA',
    'cache-control': 'no-cache',
    'referer': 'https://new.land.naver.com/offices?ms=37.497624,127.107268,17&a=SG:SMS&e=RETAIL&articleNo=2464180374',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
}

# 데이터를 가져오는 함수
def get_articles(page_number, trade_type_code="", realtor_name=""):
    url = (
        f'https://new.land.naver.com/api/articles?cortarNo=1171010700&order=prcDesc'
        f'&realEstateType=SG%3ASMS&tradeType={trade_type_code}&tag=%3A%3A%3A%3A%3A%3A%3A%3A'
        f'&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000'
        f'&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears'
        f'&minHouseHoldCount&maxHouseHoldCount&showArticle=false'
        f'&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost'
        f'&priceType=RETAIL&directions=&page={page_number}&articleState'
    )
    response = requests.get(url, cookies=cookies, headers=headers)

    if response.status_code != 200:
        print(f"요청 실패: 상태 코드 {response.status_code}")
        print(f"응답 내용: {response.text}")
        return []

    try:
        articles = response.json().get("articleList", [])
        if realtor_name:  # 중개사명 필터링
            articles = [article for article in articles if realtor_name in article.get("realtorName", "")]
        return articles
    except ValueError as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"응답 내용: {response.text}")
        return []


# CSV로 저장하는 함수
def save_articles_to_csv(page_number, articles):
    with open('real_estate_articles_with_page.csv', 'a', newline='', encoding='utf-8') as file:
        fieldnames = [
            "pageNumber(페이지번호)", "articleNo(기사번호)", "articleName(기사명)", "realEstateTypeName(부동산유형)",
            "tradeTypeName(거래유형)", "dealOrWarrantPrc(가격)", "area1(면적1)", "area2(면적2)",
            "direction(방향)", "realtorName(중개사명)", "cpName(업체명)", "cpPcArticleUrl(기사URL)"
        ]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if page_number == 1:
            writer.writeheader()
        for article in articles:
            writer.writerow({
                "pageNumber(페이지번호)": page_number,
                "articleNo(기사번호)": article.get("articleNo"),
                "articleName(기사명)": article.get("articleName"),
                "realEstateTypeName(부동산유형)": article.get("realEstateTypeName"),
                "tradeTypeName(거래유형)": article.get("tradeTypeName"),
                "dealOrWarrantPrc(가격)": article.get("dealOrWarrantPrc"),
                "area1(면적1)": article.get("area1"),
                "area2(면적2)": article.get("area2"),
                "direction(방향)": article.get("direction"),
                "realtorName(중개사명)": article.get("realtorName"),
                "cpName(업체명)": article.get("cpName"),
                "cpPcArticleUrl(기사URL)": article.get("cpPcArticleUrl")
            })


class RealEstateApp:
    def __init__(self, root):
        self.page_number = 1
        self.items_per_page = 20
        self.root = root
        self.trade_type = ""
        self.root.title("부동산 데이터 검색")

        # 화면 크기 및 위치 설정
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = 1000
        window_height = 600
        position_top = int(screen_height / 2 - window_height / 2)
        position_right = int(screen_width / 2 - window_width / 2)
        self.root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

        # 상단 검색창 프레임
        self.top_frame = tk.Frame(self.root)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        self.search_label = tk.Label(self.top_frame, text="중개사명 검색:")
        self.search_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_entry = tk.Entry(self.top_frame)
        self.search_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.trade_type_label = tk.Label(self.top_frame, text="거래유형:")
        self.trade_type_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.trade_type_combobox = ttk.Combobox(self.top_frame, values=["전체", "매매", "월세"], state="readonly")
        self.trade_type_combobox.current(0)
        self.trade_type_combobox.pack(side=tk.LEFT, padx=5, pady=5)

        self.search_button = tk.Button(self.top_frame, text="검색", command=self.search_realtor)
        self.search_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Treeview 설정
        self.tree = ttk.Treeview(self.root, columns=(
            "articleNo", "articleName", "realEstateTypeName", "tradeTypeName", "dealOrWarrantPrc",
            "area1", "area2", "direction", "realtorName", "cpName", "cpPcArticleUrl"), show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", stretch=tk.YES)

        # 페이지 버튼
        self.previous_button = tk.Button(self.root, text="이전", command=self.previous_page)
        self.previous_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.next_button = tk.Button(self.root, text="다음", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.save_button = tk.Button(self.root, text="CSV 저장", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=10, pady=5)

        self.page_frame = tk.Frame(self.root)
        self.page_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

        self.page_label = tk.Label(self.page_frame, text=f"현재 페이지: {self.page_number}")
        self.page_label.pack(side=tk.RIGHT)

        self.tree.bind("<Double-1>", self.open_url)

        self.fetch_data()

    def fetch_data(self):
        trade_type_map = {"전체": "", "매매": "A1", "월세": "B1"}
        trade_type_code = trade_type_map.get(self.trade_type_combobox.get(), "")
        realtor_name = self.search_entry.get().strip()
        articles = get_articles(self.page_number, trade_type_code, realtor_name)
        self.update_treeview(articles)
        self.update_buttons()

    def update_treeview(self, articles):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for article in articles[:self.items_per_page]:
            self.tree.insert("", "end", values=(
                article.get("articleNo"), article.get("articleName"), article.get("realEstateTypeName"),
                article.get("tradeTypeName"), article.get("dealOrWarrantPrc"), article.get("area1"),
                article.get("area2"), article.get("direction"), article.get("realtorName"),
                article.get("cpName"), article.get("cpPcArticleUrl")
            ))

    def search_realtor(self):
        self.page_number = 1
        self.fetch_data()

    def update_buttons(self):
        self.page_label.config(text=f"현재 페이지: {self.page_number}")

    def previous_page(self):
        if self.page_number > 1:
            self.page_number -= 1
            self.fetch_data()

    def next_page(self):
        self.page_number += 1
        self.fetch_data()

    def save_data(self):
        articles = get_articles(self.page_number)
        save_articles_to_csv(self.page_number, articles)
        messagebox.showinfo("정보", "데이터가 CSV 파일로 저장되었습니다.")

    def open_url(self, event):
        item = self.tree.selection()[0]
        article_url = self.tree.item(item, "values")[-1]
        webbrowser.open(article_url)


if __name__ == "__main__":
    root = tk.Tk()
    app = RealEstateApp(root)
    root.mainloop()
