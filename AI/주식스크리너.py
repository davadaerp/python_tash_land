import time
import json
import math
import datetime as dt
from typing import List, Dict, Any
from io import StringIO

import requests
import pandas as pd
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36"
}

# ====== 유틸 ======
# 주식 스크리너 설계
# 1. 분석 조건
# 업종 사이클: 성장기 → 가점
# 분기 매출 성장률: 전년 동기 대비 +10% 이상 → 가점
# 영업이익률: 5% 이상 + 개선 추세 → 가점
# PER: 업종 평균 이하 → 가점
# PBR: 1 이하 → 가점
# 외국인 지분율 변화: 최근 3개월↑ → 가점
# 기관 지분율 변화: 최근 3개월↑ → 가점
# 거래량: 평소 대비 2배↑ + 주가 상승 → 가점
# 리스크 점검: 부채비율 > 200% 또는 적자 2분기 이상 → 감점

def yyyymmdd(d: dt.date) -> str:
    return d.strftime("%Y%m%d")

def safe_float(v, default=math.nan):
    try:
        if v is None: return default
        if isinstance(v, (int, float)): return float(v)
        s = str(v).replace(",", "").replace("%", "").strip()
        return float(s) if s not in ("", "-", "N/A") else default
    except Exception:
        return default

# ====== 시세(가격/거래량) – 네이버 시세 JSON ======
def fetch_price_history_naver(symbol: str, start: str, end: str, timeframe="day") -> pd.DataFrame:
    url = (
        "https://api.finance.naver.com/siseJson.naver"
        f"?symbol={symbol}&requestType=1&startTime={start}&endTime={end}&timeframe={timeframe}"
    )
    res = requests.get(url, headers=HEADERS, timeout=10)
    txt = res.text.strip().replace("'", '"')
    data = json.loads(txt)

    header = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=header)
    df["날짜"] = pd.to_datetime(df["날짜"])
    for col in ["종가", "시가", "고가", "저가", "거래량"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.dropna(subset=["종가"]).reset_index(drop=True)

# ====== PER/PBR & 업종 평균 & 외국인보유비중 – 네이버 종목 메인 파싱 ======
def fetch_per_pbr_naver(symbol: str) -> Dict[str, float]:
    """
    반환:
      PER, PBR, 업종PER, 업종PBR, 외국인보유비중(%)
    """
    url = f"https://finance.naver.com/item/main.nhn?code={symbol}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    soup = BeautifulSoup(res.text, "lxml")
    text = soup.get_text(" ", strip=True)

    import re

    def find_nearby_number(keyword: str) -> float:
        idx = text.find(keyword)
        if idx == -1:
            return math.nan
        window = text[max(0, idx - 80): idx + 80]
        nums = re.findall(r"[-+]?\d*\.\d+|\d+", window)
        return safe_float(nums[-1]) if nums else math.nan

    # 종목 지표
    per = find_nearby_number("PER")
    pbr = find_nearby_number("PBR")

    # 동일업종 지표 (네이버에 '동일업종 PER', '동일업종 PBR' 표기 존재)
    ind_per = find_nearby_number("동일업종 PER")
    ind_pbr = find_nearby_number("동일업종 PBR")

    # 외국인 보유비중 (네이버 종목 메인에 '외국인 보유비중' 표기 존재)
    fr_ratio = find_nearby_number("외국인 보유비중")

    return {
        "PER": per,
        "PBR": pbr,
        "업종PER": ind_per,
        "업종PBR": ind_pbr,
        "외국인보유비중": fr_ratio
    }

# ====== 투자자별 매매 동향 – 네이버 ‘외국인/기관’ 표 ======
def fetch_investor_flow_naver(symbol: str, lookback_days=20) -> Dict[str, Any]:
    url = f"https://finance.naver.com/item/frgn.naver?code={symbol}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    dfs = pd.read_html(StringIO(res.text))  # ✅ FutureWarning 해결

    flow = None
    for df in dfs:
        if {"날짜", "개인", "외국인", "기관"}.issubset(set(df.columns)):
            flow = df.copy()
            break

    result = {"외국인순매수합": math.nan, "기관순매수합": math.nan, "최근일자": None}
    if flow is None or flow.empty:
        return result

    for col in ["개인", "외국인", "기관"]:
        flow[col] = pd.to_numeric(flow[col].astype(str).str.replace(",", "", regex=False), errors="coerce")
    flow["날짜"] = pd.to_datetime(flow["날짜"], errors="coerce")
    flow = flow.dropna(subset=["날짜"]).sort_values("날짜").tail(lookback_days)

    result["외국인순매수합"] = float(flow["외국인"].sum())
    result["기관순매수합"] = float(flow["기관"].sum())
    result["최근일자"] = flow["날짜"].max().date().isoformat() if not flow.empty else None
    return result

# ====== 분기 재무 – FnGuide ======
def fetch_quarter_sales_op_fnguide(symbol: str) -> pd.DataFrame:
    gicode = f"A{symbol}"
    url = f"https://comp.fnguide.com/SVO3/ASP/SVD_Main.asp?gicode={gicode}"
    res = requests.get(url, headers=HEADERS, timeout=10)
    res.raise_for_status()

    dfs = pd.read_html(StringIO(res.text), header=0)  # ✅ FutureWarning 해결
    q = None
    for df in dfs:
        if "매출액" in df.columns and "영업이익" in df.columns:
            q = df.copy()
            break

    if q is None:
        return pd.DataFrame()

    q = q[q.iloc[:, 0].astype(str).str.contains("매출액|영업이익", regex=True)]
    q = q.set_index(q.columns[0])
    q.columns = [str(c) for c in q.columns]
    q = q.applymap(lambda x: safe_float(x, default=math.nan))
    return q

def compute_quarter_growth(q_df: pd.DataFrame) -> Dict[str, Any]:
    result = {"분기매출증가율_yoy": math.nan, "영업이익률": math.nan}
    if q_df.empty:
        return result
    cols = list(q_df.columns)
    if len(cols) >= 5:
        latest, prev_y = cols[-1], cols[-5]
        sales_latest = safe_float(q_df.loc["매출액", latest])
        sales_prev_y = safe_float(q_df.loc["매출액", prev_y])
        if not math.isnan(sales_latest) and not math.isnan(sales_prev_y) and sales_prev_y != 0:
            result["분기매출증가율_yoy"] = (sales_latest / sales_prev_y - 1) * 100.0
    if len(cols) >= 1:
        latest = cols[-1]
        op = safe_float(q_df.loc["영업이익", latest])
        sales = safe_float(q_df.loc["매출액", latest])
        if not math.isnan(op) and not math.isnan(sales) and sales != 0:
            result["영업이익률"] = (op / sales) * 100.0
    return result

# ====== (옵션) KRX 외국인 지분율 훅 ======
def fetch_foreign_ownership_krx(symbol: str, trade_date: str | None = None) -> float:
    """
    ⚠️ 안내:
      KRX 데이터포털 JSON은 세션/OTP(또는 폼 토큰) 기반이라
      단순 GET만으로는 차단되는 경우가 많습니다.
      - 표준 패턴: OTP 발급 → OTP로 JSON/엑셀 요청
      - 또는 bld + form-data를 특정 Referer/쿠키와 함께 POST
    이 함수는 그런 환경을 고려해 훅(hook)만 제공하며,
    연결 준비 전에는 math.nan을 반환합니다.

    연동 준비 후 이 자리에서:
    1) 세션 생성(쿠키)
    2) OTP 발급 엔드포인트 호출
    3) JSON/엑셀 엔드포인트에 OTP/폼데이터로 요청
    4) 외국인지분율(보유비중, %) 파싱 후 반환
    """
    # TODO: KRX 세션/OTP 연동 후 구현
    return math.nan

# ====== 스코어링 ======
GROWTH_INDUSTRIES = {"반도체", "2차전지", "AI", "바이오", "인터넷", "소프트웨어", "클라우드"}

def score_row(row: Dict[str, Any]) -> Dict[str, Any]:
    score = 0
    notes = []

    # 업종 성장성
    if row.get("업종") in GROWTH_INDUSTRIES:
        score += 2; notes.append("업종 성장성 +2")

    # 매출 YoY
    yoy = safe_float(row.get("분기매출증가율_yoy"))
    if not math.isnan(yoy) and yoy >= 10:
        score += 2; notes.append("분기 매출 YoY ≥10% +2")

    # 영업이익률
    o_margin = safe_float(row.get("영업이익률"))
    if not math.isnan(o_margin):
        if o_margin >= 5: score += 1; notes.append("영업이익률 ≥5% +1")
        if o_margin >= 10: score += 1; notes.append("영업이익률 ≥10% +1")

    # PER/PBR 절대치
    per = safe_float(row.get("PER"))
    pbr = safe_float(row.get("PBR"))
    if not math.isnan(per) and per <= 12:
        score += 1; notes.append("PER ≤ 12 +1")
    if not math.isnan(pbr) and pbr <= 1:
        score += 1; notes.append("PBR ≤ 1 +1")

    # 🔥 업종 대비 밸류에이션
    ind_per = safe_float(row.get("업종PER"))
    ind_pbr = safe_float(row.get("업종PBR"))
    if not math.isnan(per) and not math.isnan(ind_per) and per <= ind_per * 0.9:
        score += 1; notes.append("업종대비 PER 10% 이상 저평가 +1")
    if not math.isnan(pbr) and not math.isnan(ind_pbr) and pbr <= ind_pbr * 0.9:
        score += 1; notes.append("업종대비 PBR 10% 이상 저평가 +1")

    # 외국인/기관 수급
    fg = safe_float(row.get("외국인순매수합"))
    ig = safe_float(row.get("기관순매수합"))
    if not math.isnan(fg) and fg > 0:
        score += 1; notes.append("최근 외국인 순매수 +1")
    if not math.isnan(ig) and ig > 0:
        score += 1; notes.append("최근 기관 순매수 +1")

    # 외국인 보유비중(지분율) – 참고 가점(선택)
    fr = safe_float(row.get("외국인보유비중"))
    if not math.isnan(fr) and fr >= 30:
        score += 1; notes.append("외국인 보유비중 ≥30% +1")

    # 리스크: 고PER + 매출감소
    if (not math.isnan(per) and per >= 50) and (not math.isnan(yoy) and yoy < 0):
        score -= 2; notes.append("고PER + 매출감소 -2")

    decision = "매수" if score >= 8 else ("관망" if score >= 5 else "매도")
    return {"점수": score, "투자판단": decision, "판단근거": "; ".join(notes)}

# ====== 메인 파이프라인 ======
def screen_symbols(symbols: List[Dict[str, str]]) -> pd.DataFrame:
    today = dt.date.today()
    start = yyyymmdd(today - dt.timedelta(days=365))
    end = yyyymmdd(today)

    results = []
    for item in symbols:
        code = item["종목코드"]
        name = item.get("종목명", code)
        industry = item.get("업종", "")

        # 1) 가격/거래량
        try:
            px = fetch_price_history_naver(code, start, end, timeframe="day")
        except Exception:
            px = pd.DataFrame()

        vol_growth = math.nan
        if not px.empty and len(px) >= 40:
            last20 = px.tail(20)["거래량"].mean()
            prev20 = px.tail(40).head(20)["거래량"].mean()
            if prev20 and not math.isnan(prev20) and prev20 != 0:
                vol_growth = (last20 / prev20 - 1) * 100.0

        # 2) PER/PBR + 업종 평균 + 외국인보유비중(네이버)
        try:
            val = fetch_per_pbr_naver(code)
        except Exception:
            val = {"PER": math.nan, "PBR": math.nan, "업종PER": math.nan, "업종PBR": math.nan, "외국인보유비중": math.nan}

        # 3) 수급(외인/기관 순매수)
        try:
            flow = fetch_investor_flow_naver(code, lookback_days=20)
        except Exception:
            flow = {"외국인순매수합": math.nan, "기관순매수합": math.nan, "최근일자": None}

        # 4) 분기 재무
        try:
            qtbl = fetch_quarter_sales_op_fnguide(code)
            qcalc = compute_quarter_growth(qtbl)
        except Exception:
            qcalc = {"분기매출증가율_yoy": math.nan, "영업이익률": math.nan}

        # 5) (옵션) KRX 외국인 지분율 시도 → 실패시 네이버 값 사용
        fr_krx = fetch_foreign_ownership_krx(code)  # 현재는 nan 반환(훅)
        foreign_ratio = fr_krx if not math.isnan(fr_krx) else val.get("외국인보유비중")

        row = {
            "종목코드": code, "종목명": name, "업종": industry,
            "PER": val.get("PER"), "PBR": val.get("PBR"),
            "업종PER": val.get("업종PER"), "업종PBR": val.get("업종PBR"),
            "외국인보유비중": foreign_ratio,  # % 단위
            "외국인순매수합": flow.get("외국인순매수합"),
            "기관순매수합": flow.get("기관순매수합"),
            "수급최신일": flow.get("최근일자"),
            "분기매출증가율_yoy": qcalc.get("분기매출증가율_yoy"),
            "영업이익률": qcalc.get("영업이익률"),
            "20일거래량증가율": vol_growth,
        }

        row.update(score_row(row))
        results.append(row)
        time.sleep(0.6)  # 과호출 방지

    df = pd.DataFrame(results)
    df = df.sort_values(["투자판단", "점수", "분기매출증가율_yoy"], ascending=[True, False, False])
    return df

if __name__ == "__main__":
    symbols = [
        {"종목코드": "005930", "종목명": "삼성전자", "업종": "반도체"},
        {"종목코드": "000660", "종목명": "SK하이닉스", "업종": "반도체"},
        {"종목코드": "035720", "종목명": "카카오", "업종": "인터넷"},
        {"종목코드": "051910", "종목명": "LG화학", "업종": "2차전지"},
    ]

    df = screen_symbols(symbols)
    cols = ["종목코드","종목명","업종","점수","투자판단","판단근거",
            "PER","업종PER","PBR","업종PBR",
            "외국인보유비중","외국인순매수합","기관순매수합","수급최신일",
            "분기매출증가율_yoy","영업이익률","20일거래량증가율"]
    print(df[cols].to_string(index=False))

    out = f"stock_screening_result_{dt.date.today().isoformat()}.xlsx"
    df[cols].to_excel(out, index=False)
    print(f"\n📁 저장: {out}")
