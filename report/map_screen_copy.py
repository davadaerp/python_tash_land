from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from PIL import Image
import pyautogui

# 크롬 브라우저 설정
options = webdriver.ChromeOptions()
options.add_argument('--start-maximized')
options.add_argument('--disable-infobars')
options.add_argument('--disable-extensions')

driver = webdriver.Chrome(options=options)

# 네이버 부동산 지도 페이지 열기
url = "https://m.land.naver.com/near/article/2515675552?poi=SCHOOLPOI"
driver.get(url)

# 페이지가 로딩될 시간 대기
time.sleep(6)

# 화면 전체 캡처 후 특정 위치 잘라내기
# ===== 여기를 직접 좌표 맞춰서 수정하세요 =====
x = 350     # 왼쪽 시작 지점
y = 200     # 위쪽 시작 지점
width = 700 # 캡처할 가로 길이
height = 500 # 캡처할 세로 길이
# ============================================

screenshot = pyautogui.screenshot()
cropped = screenshot.crop((x, y, x + width, y + height))
cropped.save("map_capture.png")

print("✅ 지도 이미지 저장 완료: map_capture.png")

driver.quit()
