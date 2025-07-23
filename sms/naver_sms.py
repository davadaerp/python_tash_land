import time
import hmac
import hashlib
import base64
import requests
import json
import mimetypes
import os

# SENS 설정값
access_key = "fTenshdXfuN0XHRCm2yH"
secret_key = "JA1QHVo1O47VRcv20r93DE4GeT2E5FVrc1GarqZ3"
service_id = "ncp:sms:kr:298535262510:bacchus"
sender_number = "0234459085"
api_host = "https://sens.apigw.ntruss.com"

# 서명 생성
def make_signature(uri, timestamp, access_key, secret_key):
    message = f"POST {uri}\n{timestamp}\n{access_key}"
    message = message.encode("utf-8")
    secret = secret_key.encode("utf-8")
    signature = hmac.new(secret, message, hashlib.sha256).digest()
    return base64.b64encode(signature).decode()

# 파일 업로드 후 fileId 반환
# 차후 파일업로드전에 5m크기파일 필터링및 jpg,jpeg 확장자 체크요망
def upload_file(file_path):
    if not os.path.isfile(file_path):
        print(f"🚫 파일이 존재하지 않음: {file_path}")
        return None

    with open(file_path, "rb") as f:
        file_body = base64.b64encode(f.read()).decode("utf-8")

    file_name = os.path.basename(file_path)
    uri = f"/sms/v2/services/{service_id}/files"
    url = f"{api_host}{uri}"
    timestamp = str(int(time.time() * 1000))
    signature = make_signature(uri, timestamp, access_key, secret_key)

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature,
    }

    body = {
        "fileName": file_name,
        "fileBody": file_body
    }

    res = requests.post(url, headers=headers, data=json.dumps(body))
    if res.status_code == 200:
        file_id = res.json().get("fileId")
        print(f"✅ 파일 업로드 성공: {file_name} → fileId = {file_id}")
        return file_id
    else:
        print(f"❌ 파일 업로드 실패: {res.status_code}, {res.text}")
        return None


# SMS 또는 LMS 전송
def send_sms(to_number, content, subject=None, msg_type='SMS'):
    uri = f"/sms/v2/services/{service_id}/messages"
    url = f"{api_host}{uri}"
    timestamp = str(int(time.time() * 1000))
    signature = make_signature(uri, timestamp, access_key, secret_key)

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature,
    }

    body = {
        "type": msg_type,
        "contentType": "COMM",
        "countryCode": "82",
        "from": sender_number,
        "subject": subject if subject else "",
        "content": content,
        "messages": [
            {
                "to": to_number,
                "subject": subject if subject else "",
                "content": content
            }
        ]
    }

    res = requests.post(url, headers=headers, data=json.dumps(body))
    print(f"📤 [{msg_type}] Status Code:", res.status_code)
    try:
        print("📨 Response:", res.json())
    except Exception as e:
        print("⚠️ 응답 파싱 오류:", e)


# MMS 전송
def send_mms(to_number, content, subject, image_paths):
    # Step 1. 파일 업로드 → fileId 수집
    file_ids = []
    for file_path in image_paths:
        fid = upload_file(file_path)
        if fid:
            file_ids.append(fid)

    if not file_ids:
        print("❌ 첨부 이미지 업로드 실패: MMS 전송 중단")
        return

    # Step 2. 메시지 전송
    uri = f"/sms/v2/services/{service_id}/messages"
    url = f"{api_host}{uri}"
    timestamp = str(int(time.time() * 1000))
    signature = make_signature(uri, timestamp, access_key, secret_key)

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "x-ncp-apigw-timestamp": timestamp,
        "x-ncp-iam-access-key": access_key,
        "x-ncp-apigw-signature-v2": signature,
    }

    body = {
        "type": "MMS",
        "contentType": "COMM",
        "countryCode": "82",
        "from": sender_number,
        "subject": subject,
        "content": content,
        "messages": [
            {
                "to": to_number,
                "subject": subject,
                "content": content
            }
        ],
        "files": [{"fileId": fid} for fid in file_ids]
    }

    res = requests.post(url, headers=headers, data=json.dumps(body))
    print("📤 [MMS] Status Code:", res.status_code)
    try:
        print("📨 Response:", res.json())
    except Exception as e:
        print("⚠️ 응답 파싱 오류:", e)


# ✅ 실행 예시
if __name__ == "__main__":
    target_number = "01022709085"

    # 1. SMS 전송
    #send_sms(target_number, "안녕하세요. SMS 테스트입니다.", msg_type='SMS')

    # 2. LMS 전송 (제목 포함)
    #send_sms(target_number, "이것은 LMS 테스트 메시지입니다. 80바이트 초과 시 자동 LMS 처리됩니다.", subject="LMS 제목", msg_type='LMS')

    # 3. MMS 전송 (이미지 포함)
    image_files = ["sample1.jpg", "sample2.jpg"]  # 실제 존재하는 파일로 교체
    send_mms(target_number, "MMS 테스트입니다. 이미지 첨부 확인해주세요.그리고 메시지 내용(content)은 80자 이하로 유지해야 SMS로 전송됩니다. 초과 시는 LMS 또는 MMS로 타입을 변경해야 합니다.\n연락처는 010-2270-9085로 해주세요.\n감사합니다.\n잘부탁드립니다.", "MMS 제목", image_files)
