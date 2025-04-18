import json
from datetime import datetime
import requests
import time
import hmac
import hashlib
import base64

# 알림톡 전송처리
def alimtalk_send(data):
    # JSON 문자열을 파싱하여 각 속성을 변수에 할당
    userid = data["userid"]
    userpswd = data["userpswd"]
    title = data["title"]
    message = data["message"]
    phone_numbers = data["phoneNumbers"]

    # 번호를 쉼표로 분리하고 하이픈 제거
    phone_list = [phone.strip().replace("-", "") for phone in phone_numbers.split(",")]

    # [설정값]
    service_id = "ncp:kkobizmsg:kr:2985352:bacchus"
    url = f"https://sens.apigw.ntruss.com/alimtalk/v2/services/{service_id}/messages"
    access_key = "fTenshdXfuN0XHRCm2yH"  # 본인 키로 교체
    secret_key = "JA1QHVo1O47VRcv20r93DE4GeT2E5FVrc1GarqZ3"  # 본인 키로 교체

    # 현재 타임스탬프 (밀리초 단위)
    timestamp = str(int(time.time() * 1000))
    method = "POST"
    uri = f"/alimtalk/v2/services/{service_id}/messages"

    # 서명 생성
    signature_message = f"{method} {uri}\n{timestamp}\n{access_key}"
    signature = base64.b64encode(
        hmac.new(secret_key.encode('utf-8'), signature_message.encode('utf-8'), digestmod=hashlib.sha256).digest()
    ).decode('utf-8')

    # 헤더 설정
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature
    }

    # 메시지 본문 생성
    servie_date = datetime.now().strftime("%Y-%m-%d")
    item_name = title   #"부동사매도의뢰"
    item_spec = message

    # 메시지 리스트 구성
    messages = []
    for entry in phone_list:
        # entry 형식: "이름:전화번호"
        name, phone_number = entry.split(":", 1)
        # 알림톡 0002 탬플릿 구조임.
        content_template = (
            f"안녀하세요. {name}님\n"
            f"물건 {item_name} 요청합니다.\n"
            f"{item_spec}\n"
            f"잘 부탁드립니다.\n\n감사합니다."
        )
        messages.append({
            "countryCode": "82",
            "to": phone_number,
            "content": content_template
            # 첨부 파일 ID 리스트
            #"imageIdList": [file_id]
        })

    # 페이로드 구성
    payload = {
        "plusFriendId": "@davada",
        "templateCode": "0002",
        "messages": messages
    }

    # POST 요청 전송
    response = requests.post(url, headers=headers, json=payload)

    # 응답 상태 및 결과 출력
    print("Sending to phones:", phone_list)
    print("Response Code:", response.status_code)
    try:
        print("Response Body:", response.json())
    except Exception as e:
        print("응답 처리 중 오류 발생:", e)


if __name__ == "__main__":
    # JSON 샘플 데이터
    json_data = '''{
          "userid": "logphone",
          "userpswd": "ekqkek#$0",
          "title": "다바다 서비스이용건",
          "message": "부동산매매의뢰합니다.\\n1:주소:강북구 수유동 100-1번지\\n2.년식:2018년식\\n3.20평\\n4.방수:방3-욕실2\\n5.위치:4층\\n6.매매금액:2.5억\\n7.연락번호:01022709085\\n",
          "phone_numbers": "010-2270-9085,010-8379-9085"
        }'''
    alimtalk_send(json.loads(json_data))
