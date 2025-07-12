'''
pip install python-telegram-bot==13.15
v13.x에서는 bot.send_message()가 동기 메서드로 동작합니다

1. TELEGRAM_TOKEN 얻기
1.1. BotFather로 새 봇 생성
Telegram 앱에서 @BotFather를 검색해 채팅을 시작합니다.
core.telegram.org

/newbot 명령어를 입력하고 봇 이름(Name)과 사용자 이름(Username, 반드시 고유)을 차례로 설정합니다.
siteguarding.com

생성이 완료되면 BotFather가 API 토큰(예: 123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ)을 메시지로 제공합니다.
core.telegram.org

1.2. 기존 봇 토큰 조회
이미 생성한 봇의 토큰이 필요할 경우, BotFather에 /mybots 또는 /token 명령을 보내고 목록에서 봇을 선택하면 토큰을 다시 확인할 수 있습니다.
support.bolddesk.com

2. CHAT_ID 얻기
2.1. getUpdates API 활용
봇 토큰을 이용해 봇에게 임의의 메시지를 전송합니다.

브라우저나 HTTP 클라이언트에서 다음 URL 호출:
https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
gist.github.com

반환된 JSON의 result[0].message.chat.id(개인 대화) 또는 result[0].channel_post.chat.id(채널 게시물)에서 숫자 값을 확인합니다.
gist.github.com

1. 봇을 “공개” 상태로 만들기
BotFather 대화창에서

/mybots → [당신의 봇 선택] → Edit Bot → Group Privacy → Disable
를 통해 그룹·개인채팅 모두에서 메시지를 주고받을 수 있도록 설정하고, “Bot Username”이 @YourBotUsername 형태로 공용 링크가 되도록 합니다.

2. 사용자에게 봇 링크 공유하기
https://t.me/YourBotUsername
사용자는 이 링크를 클릭한 뒤, 채팅창에서 /start 명령을 눌러야만 봇과의 1:1 대화를 시작할 수 있습니다.

중요: 텔레그램 보안 정책상, 사용자가 직접 봇에게 /start를 보내지 않으면 봇이 사용자를 임의로 호출할 수 없습니다.
'''

import os
import time
import urllib
import feedparser
import requests
import schedule
import sqlite3
from datetime import datetime, timedelta
from telegram import Bot

# 환경 변수 또는 직접 입력
# 봇이름: news, user: @TashLandBot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8049755307:AAEEX_SU191jFYW3WEv3LtAaeiQsBtlYeQI")
CHAT_ID         = os.getenv("TELEGRAM_CHAT_ID", "8076112825")

# 청주,충주,울산,구미,춘천,원주,
queries = ["충주산업단지", "청주sk하이닉스", "울산ai센터", "삼성구미AI센터", "2차전지,관세", "충주,청주,울산,구미 아파트미분양 or 미분양"]
# 키워드를 OR 연산자로 연결하고 URL 인코딩
query_string = urllib.parse.quote_plus(" OR ".join(queries))
RSS_URL = (
    "https://news.google.com/rss/search?"
    f"q={query_string}&hl=ko&gl=KR&ceid=KR:ko"
)

# HTTP 요청 시 브라우저 User-Agent 헤더 지정
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

# DB(또는 파일) 초기화
DB_PATH = "processed.db"
conn    = sqlite3.connect(DB_PATH)
cur     = conn.cursor()
# msg 컬럼을 추가하여 메시지 내용도 저장
cur.execute("""
    CREATE TABLE IF NOT EXISTS processed (
        id   TEXT PRIMARY KEY,
        msg  TEXT,
        ts   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

SEARCH_DAY = 30  # 검색 기간(일 단위)

def fetch_and_notify():
    print("실행시간:", datetime.now())

    # 1) RSS XML을 HTTP 헤더와 함께 가져오기
    response = requests.get(RSS_URL, headers=HEADERS)
    response.raise_for_status()

    # 2) feedparser로 문자열 파싱
    feed = feedparser.parse(response.text)
    if not feed.entries:
        print("No entries found in the feed.")
        return
    #
    bot  = Bot(token=TELEGRAM_TOKEN)

    # 1) 아직 처리되지 않은 항목만 필터링
    new_entries = []
    now = datetime.now()
    one_month_ago = now - timedelta(days=SEARCH_DAY)

    for entry in feed.entries:
        uid = entry.id if 'id' in entry else entry.link
        # published_parsed 가 없는 경우 건너뜀
        if not entry.get('published_parsed'):
            continue
        published_dt = datetime(*entry.published_parsed[:6])
        # 30일 이내 자료만 필터링
        if published_dt < one_month_ago:
            continue
        # 이미 처리된 항목인지 확인
        cur.execute("SELECT 1 FROM processed WHERE id=?", (uid,))
        if not cur.fetchone():
            new_entries.append((uid, entry))

    if not new_entries:
        print("No new items.")
        return

    # 2) 최신 순으로 정렬(원래 feed.entries가 최신 우선이지만, 안전하게 정렬)
    #    published_parsed: time.struct_time
    new_entries.sort(
        key=lambda x: x[1].published_parsed,
        reverse=True
    )

    # 3) 상위 5개만 전송
    for uid, entry in new_entries[:5]:
        title     = entry.title
        link      = entry.link
        #published = entry.get("published", "Unknown date")
        # 기존에 published_dt는 이렇게 생성됩니다.
        published_dt = datetime(*entry.published_parsed[:6])
        formatted_date = published_dt.strftime("%Y-%m-%d")
        msg = (
            f"📰 <b><a href=\"{link}\">{title}</a></b>\n"
            f"{formatted_date}"
        )
        print(title, formatted_date)
        bot.send_message(
            chat_id=CHAT_ID,
            text=msg,
            parse_mode="HTML"
        )
        # 4) 전송한 항목 DB에 기록
        # 메시지와 함께 id를 DB에 저장
        cur.execute(
            "INSERT INTO processed(id, msg) VALUES(?, ?)",
            (uid, msg)
        )
        conn.commit()
        time.sleep(1)  # 연속 전송 시 과부하 방지

def main():
    # 매시간 00분마다 실행, 20분
    #schedule.every().hour.at(":00").do(fetch_and_notify)
    [schedule.every().hour.at(f":{minute:02d}").do(fetch_and_notify) for minute in (00, 30, 35, 40, 51, 55)]
    print("Agent started. Waiting for schedule...")

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()
