import requests
import csv

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

# CSV 파일로 저장
with open('real_estate_articles_with_page.csv', 'w', newline='', encoding='utf-8') as file:
    # 첫 번째 필드에 페이지 번호를 포함한 헤더 정의
    fieldnames = [
        "pageNumber(페이지번호)",  # 페이지 번호
        "articleNo(기사번호)",
        "articleName(기사명)",
        "realEstateTypeName(부동산유형)",
        "tradeTypeName(거래유형)",
        "dealOrWarrantPrc(가격)",
        "area1(면적1)",
        "area2(면적2)",
        "direction(방향)",
        "realtorName(중개사명)",
        "cpName(업체명)",
        "cpPcArticleUrl(기사URL)"
    ]

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    for page in range(1, 11):  # 1번부터 10번까지 페이지 처리
        response = requests.get(
            f'https://new.land.naver.com/api/articles?cortarNo=1171010700&order=prcDesc&realEstateType=SG%3ASMS&tradeType=&tag=%3A%3A%3A%3A%3A%3A%3A%3A&rentPriceMin=0&rentPriceMax=900000000&priceMin=0&priceMax=900000000&areaMin=0&areaMax=900000000&oldBuildYears&recentlyBuildYears&minHouseHoldCount&maxHouseHoldCount&showArticle=false&sameAddressGroup=false&minMaintenanceCost&maxMaintenanceCost&priceType=RETAIL&directions=&page={page}&articleState',
            cookies=cookies,
            headers=headers,
        )

        data = response.json()
        article_list = data.get("articleList", [])

        for article in article_list:
            # 페이지 번호를 포함하여 기록
            writer.writerow({
                "pageNumber(페이지번호)": page,
                "articleNo(기사번호)": article["articleNo"],
                "articleName(기사명)": article["articleName"],
                "realEstateTypeName(부동산유형)": article["realEstateTypeName"],
                "tradeTypeName(거래유형)": article["tradeTypeName"],
                "dealOrWarrantPrc(가격)": article["dealOrWarrantPrc"],
                "area1(면적1)": article["area1"],
                "area2(면적2)": article["area2"],
                "direction(방향)": article["direction"],
                "realtorName(중개사명)": article["realtorName"],
                "cpName(업체명)": article["cpName"],
                "cpPcArticleUrl(기사URL)": article["cpPcArticleUrl"]
            })

print("CSV 파일로 저장되었습니다.")
