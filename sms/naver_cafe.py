import os

# 네이버 접속id(wfight66/몽셍이69)
# 카페글쓰기
# https://www.neonet.co.kr/novo-rebank/view/market_price/PastMarketPriceDetail.neo?lcode=14&mcode=690&sname=%C8%AD%BA%CF%B5%BF&complex_cd=A1012009&pyung_cd=1
#
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time

# 폼로그인처리
def login(driver):
    try:
        # 아이디 입력 필드 대기 및 입력
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        username_field.clear()
        username_field.send_keys("wfight")

        # 비밀번호 입력 필드 대기 및 입력
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "pw"))
        )
        password_field.send_keys("ahdtpddl#$_0")

        # 로그인 버튼 대기 및 클릭
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "log.login"))
        )
        login_button.click()

        print("로그인 시도 완료.")
    except Exception as e:
        print("로그인 오류:", e)


# 위 시.군.구코드(mcode)를 자기고서 읍.면.동을 가져오기
def write_cafe_review(driver, title, content, tags):
    try:
        driver.get("https://cafe.naver.com/ca-fe/cafes/31155887/menus/18/articles/write?boardType=L")
        #driver.implicitly_wait(1)
        wait = WebDriverWait(driver, 10)

        # 제목 입력
        title_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "textarea_input")))
        title_input.clear()
        title_input.send_keys(title)
        print("제목 입력 완료")

        # 내용 입력: 에디터 iframe 내부 접근
        # step 1: 에디터 영역 클릭
        content_editable_span = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "se-placeholder"))
        )
        content_editable_span.click()

        # step 2: 본문 영역 span 옆 실제 <p> 혹은 contentEditable div 자동 포커스 됨
        # 자동 생성된 빈 단락에 본문 입력
        body_p = driver.find_element(By.CSS_SELECTOR, "p.se-text-paragraph")
        body_p.click()
        body_p.send_keys(content)
        print("본문 입력 완료")

        # 태그 입력
        tag_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tag_input_box input.tag_input"))
        )
        for tag in tags.split("#"):
            if tag.strip():
                tag_input.send_keys(f"#{tag.strip()}")
                tag_input.send_keys(Keys.ENTER)
        print("태그 입력 완료")


    except Exception as e:
        print("카페 글쓰기 자동화 오류:", e)



def main():

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    try:
        driver.get("https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/")
        driver.implicitly_wait(1)
        #=====
        login(driver)
        time.sleep(100)

        # 분석시작처리
        write_cafe_review(
            driver,
            title="상가투자 스터디 후기",
            content="오늘도 알차게 배웠습니다. 임장도 곧 나가보려구요!",
            tags="#후기#상가#투자"
        )

    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()