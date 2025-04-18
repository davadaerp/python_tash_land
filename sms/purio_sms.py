from flask import jsonify
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# 폼로그인 처리
def login(driver, userid, userpswd):
    try:
        # 아이디 입력 필드 로딩 대기 (HTML 코드 상 name 속성은 "userId")
        username_field = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.NAME, "userId"))
        )
        # 비밀번호 입력 필드 (HTML 코드 상 name 속성은 "userPwd")
        password_field = driver.find_element(By.NAME, "userPwd")

        # 로그인 정보 입력
        username_field.clear()
        username_field.send_keys(userid)
        password_field.clear()
        password_field.send_keys(userpswd)

        # 로그인 버튼 클릭 (HTML 코드 상 id는 "btnLogin")
        submit_button = driver.find_element(By.ID, "btnLogin")
        submit_button.click()

        # 정상 처리 출력
        print("로그인 시도 완료.")

        return 'Success'
    except Exception as e:
        # 에러 발생 시 JSON 형태로 에러 코드 및 메시지 출력
        error_response = {'error': '로그인아이디/패스워드를 확인해주세요' + str(e)}
        print(json.dumps(error_response, ensure_ascii=False))
        return 'Failed'

def click_change_next_button(driver):
    try:
        # "다음에 변경하기" 버튼 로딩 대기 및 클릭
        change_next_button = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "btnChangeNext"))
        )
        change_next_button.click()

        print("'다음에 변경하기' 버튼 클릭 완료.")
    except Exception as e:
        print("'다음에 변경하기' 버튼 처리 중 오류 발생:", e)


def get_user_cash_amount(driver):
    try:
        # 금액 요소 로딩 대기
        cash_element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "txt_userCashAmt"))
        )

        # 텍스트 추출 (콤마 제거 후 숫자로 변환)
        cash_text = cash_element.text.replace(",", "")
        cash_amount = int(cash_text)

        print(f"현재 보유 금액: {cash_amount:,}원")
        return cash_amount

    except Exception as e:
        print("금액 정보 조회 중 오류 발생:", e)
        return None

# 제목과 메시지처리
def fill_message_fields(driver, title, message):
    try:
        # 제목 입력 필드 로딩 대기 후 값 입력
        subject_field = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "ip_sendSubject"))
        )
        subject_field.clear()
        subject_field.send_keys(title)

        # 메시지 텍스트에리어 로딩 대기 후 값 입력
        message_textarea = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "ip_sendMessage"))
        )
        message_textarea.clear()
        message_textarea.send_keys(message)

        print("제목과 메시지 내용 입력 완료.")
    except Exception as e:
        print("입력 오류:", e)

# 발송번호 목록채우기
def add_phone_numbers(driver, phone_numbers):
    try:
        # 1. 'list_contacts' 텍스트에 전화번호 입력 (각 번호는 엔터키로 구분)
        list_contacts = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "list_contacts"))
        )
        list_contacts.clear()
        # 전화번호 문자열을 줄바꿈(\n) 기준으로 분리하여 각각 입력하고 Shift+Enter를 전송합니다.
        lines = phone_numbers.split(",")
        for i, line in enumerate(lines):
            list_contacts.send_keys(line)
            # 마지막 줄이 아니라면 Shift+Enter를 입력해 줄바꿈 효과를 냅니다.
            if i < len(lines) - 1:
                list_contacts.send_keys(Keys.SHIFT, Keys.ENTER)
        time.sleep(1)

        # 만약 이전 작업에서 모달창이 이미 열려 있다면, 먼저 닫아줍니다.
        try:
            modal_confirm = WebDriverWait(driver, 1).until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[@class='jconfirm-holder']//div[@class='jconfirm-buttons']//button[text()='확인']"
                ))
            )
            modal_confirm.click()
            # 모달이 닫힐 때까지 기다림
            WebDriverWait(driver, 5).until(
                EC.invisibility_of_element_located((By.XPATH, "//div[@class='jconfirm-holder']"))
            )
        except Exception:
            pass

        # 2. 'addReceiver' 버튼 클릭하여 번호 추가 처리
        add_receiver_button = WebDriverWait(driver, 1).until(
            EC.element_to_be_clickable((By.ID, "addReceiver"))
        )
        add_receiver_button.click()

        print("전화번호 입력 및 추가 완료.")

        # 3. 메시지 박스가 뜨면, 그 안의 '확인' 버튼을 찾아 클릭
        # 메시지 박스 내부에 있는 버튼 중 텍스트에 '확인'이 포함된 버튼을 선택합니다.
        # addReceiver 클릭 후 모달이 나타난다면, 확인 버튼을 클릭해서 닫아줍니다.
        modal_confirm = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//div[@class='jconfirm-holder']//div[@class='jconfirm-buttons']//button[text()='확인']"
            ))
        )
        modal_confirm.click()
        print("메시지 박스의 확인 버튼 클릭 완료.")

    except Exception as e:
        print("전화번호 추가 중 오류:", e)

# 전송번호 업데이트
def update_sender_number(driver, new_number):
    try:
        # 1. hidden input인 sendCallerNumber의 value 업데이트
        sender_input = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "sendCallerNumber"))
        )
        driver.execute_script("arguments[0].value = arguments[1];", sender_input, new_number)

        # 2. p 태그인 sendCallerText의 텍스트 업데이트 (포맷은 필요에 따라 변경 가능)
        sender_text = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.ID, "sendCallerText"))
        )
        # 만약 하이픈 포맷을 유지하고 싶다면, new_number를 적절히 포맷해서 넣어주세요.
        driver.execute_script("arguments[0].innerText = arguments[1];", sender_text, new_number)

        # 3. 라디오 버튼(sender_num)도 찾아서 value 속성을 업데이트
        sender_radio = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='sender_num']"))
        )
        driver.execute_script("arguments[0].setAttribute('value', arguments[1]);", sender_radio, new_number)

        # 4. data-caller-phone 속성이 있는 card_list 요소 업데이트 (sendCallerList 내의 card_list)
        card_list = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#sendCallerList .card_list"))
        )
        driver.execute_script("arguments[0].setAttribute('data-caller-phone', arguments[1]);", card_list, new_number)

        print("발신번호가 업데이트되었습니다:", new_number)
    except Exception as e:
        print("발신번호 업데이트 중 오류 발생:", e)


def open_attachment_popup(driver):
    try:
        # CSS 선택자로 해당 div 요소를 찾습니다.
        attachment_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".item_img.btn_photo_sub_add.last.target"))
        )
        attachment_button.click()
        print("첨부파일 팝업이 열렸습니다.")
    except Exception as e:
        print("첨부파일 팝업 열기 중 오류 발생:", e)

def click_send_request(driver):
    try:
        # 'btn_sendRequest' 버튼이 클릭 가능할 때까지 대기 후 클릭
        send_request_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "btn_sendRequest"))
        )
        send_request_button.click()
        print("발송하기 버튼 클릭 완료.")
        time.sleep(2)

        # 2. 모달 내에서 'sendConfirmOk' 버튼 클릭
        # send_confirm_ok = WebDriverWait(driver, 3).until(
        #     EC.element_to_be_clickable((By.ID, "sendConfirmOk"))
        # )
        # send_confirm_ok.click()
        print("발송 확인 버튼 클릭 완료.")

    except Exception as e:
        print("발송하기 버튼 클릭 중 오류:", e)


def purio_sms_send(data):

    # JSON 문자열을 파싱하여 각 속성을 변수에 할당
    userid = data["userid"]
    userpswd = data["userpswd"]
    title = data["title"]
    message = data["message"]
    phone_numbers = data["phoneNumbers"]

    # 크롬드라이버 화면없이 동작하게 처리하는 방법(배치개념에 적용)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    # 필요에 따라 추가 옵션 설정: --no-sandbox, --disable-dev-shm-usage 등

    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Chrome()
    try:
        driver.get("https://www.ppurio.com")
        driver.implicitly_wait(1)

        #=====
        result = login(driver,userid, userpswd)
        print(result)
        if result == 'Failed':
            return jsonify({'error': '로그인아이디/패스워드를 확인해주세요'}), 400
        time.sleep(3)

        # 다음단계 진입
        click_change_next_button(driver)
        time.sleep(2)

        # 충전캐시금액 구하기
        cash_amount = get_user_cash_amount(driver)
        if cash_amount > 0:
            print(f"보유 금액: {cash_amount:,}원 - 사이트로 이동합니다.")
            driver.get("https://www.ppurio.com/send/sms/gn/view")
        else:
            return jsonify({'error': '잔액이 부족합니다 (0원)'}), 401
        time.sleep(1)

        # 제목과 메시지처리
        fill_message_fields(driver, title, message)
        time.sleep(1)

        # 첨부파일 추가하기
        # open_attachment_popup(driver)
        # time.sleep(3)

        # 발송번호 목록채우기
        print(phone_numbers)
        add_phone_numbers(driver, phone_numbers)
        time.sleep(3)

        # 전송번호 업데이트
        # new_number = "010-2270-9085"
        # update_sender_number(driver, new_number)

        # 발송하기
        click_send_request(driver)
        time.sleep(30)
        #
    except Exception as e:
        print("오류 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    # JSON 샘플 데이터
    json_data = '''{
          "userid": "logphone",
          "userpswd": "ekqkek#$0",
          "title": "다바다 서비스이용건",
          "message": "안녕하세요. 다바다입니다.\\n제발 월 서비스 요금을 납부해주세요.\\n추신: 오늘 프라이드 제가 씁니다. ",
          "phone_numbers": "010-4866-9085,010-8379-9085"
        }'''

    # "message": "안녕하세요. 이번달 다바다 서비스이용금액이 미납되었습니다.\\n확인하시구 납부부탁합니다.\\n추신: 오늘프라이드 제가씁니다.",
    # "phonelists": "010-2270-9085\\n010-4866-9085\\n010-8379-9085"

    purio_sms_send(json.loads(json_data))