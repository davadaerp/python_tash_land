import time
import hmac
import hashlib
import base64
import requests
import json
import mimetypes
import os

from config import UPLOAD_FOLDER_PATH

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
# --- 1) send_mms는 file_ids를 바로 받아서 전송만 담당하도록 수정 ---
def send_mms(to_number, content, subject, file_ids):
    """
    to_number: 수신번호
    content, subject: 메시지
    file_ids: upload_file()로 얻은 fileId 리스트
    """
    if not file_ids:
        print("❌ 첨부 이미지 fileId가 없습니다: MMS 전송 중단")
        return None

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
    return res

# 2) send_mms_data: 전송 대상별 성공/실패 집계 후 상태 리턴
# 2) send_mms_data에서 파일 업로드 한 번만 수행하고, file_ids만 넘기도록 수정 ---
def send_mms_data(data):
    """
    data: {
        "phoneNumbers": "홍길동:01012345678,김영희:01098765432",
        "title": "제목",
        "message": "메시지 내용",
        "imageFiles": ["sample1.jpg", "sample2.jpg"]
    }
    """
    # (기존) phoneNumbers → phone_numbers 리스트 파싱
    raw = data.get("phoneNumbers", "")
    entries = raw.split(",") if isinstance(raw, str) else raw
    phone_numbers = []
    for entry in entries:
        entry = entry.strip()
        if ":" in entry:
            _, phone = entry.split(":", 1)
        else:
            phone = entry
        phone = phone.strip().replace("-", "")
        if phone:
            phone_numbers.append(phone)

    subject     = data.get("title", "")
    content     = data.get("message", "")
    image_files = data.get("imageFiles", [])

    # 1) 여기서만 파일 업로드! → file_ids 수집
    file_ids = []
    for filename in image_files:
        full_path = os.path.join(UPLOAD_FOLDER_PATH, filename)
        fid = upload_file(full_path)
        if fid:
            file_ids.append(fid)
    if not file_ids:
        print("❌ 첨부 이미지 업로드 실패: MMS 전송 중단")
        return {
            'status': '실패',
            'success_count': 0,
            'fail_count': len(phone_numbers),
            'failures': phone_numbers
        }

    # 2) 모든 수신번호로 send_mms 호출 (파일 업로드는 안 함)
    successes = []
    failures  = []
    for to in phone_numbers:
        try:
            res = send_mms(to, content, subject, file_ids)
            if res and res.status_code < 400:
                successes.append(to)
            else:
                failures.append(to)
        except Exception as e:
            print(f"❌ {to} 전송 중 예외:", e)
            failures.append(to)

    # 3) 결과 상태 결정
    if successes and not failures:
        status = '전체성공'
    elif successes and failures:
        status = '부분성공'
    else:
        status = '실패'

    return {
        'status':        status,
        'success_count': len(successes),
        'fail_count':    len(failures),
        'failures':      failures
    }

# ✅ 실행 예시
if __name__ == "__main__":
    target_number = "01022709085"

    # 1. SMS 전송
    #send_sms(target_number, "안녕하세요. SMS 테스트입니다.", msg_type='SMS')

    # 2. LMS 전송 (제목 포함)
    #send_sms(target_number, "이것은 LMS 테스트 메시지입니다. 80바이트 초과 시 자동 LMS 처리됩니다.", subject="LMS 제목", msg_type='LMS')

    # 3. MMS 전송 (이미지 포함)
    payload = {
        "phoneNumbers": ["강종철:010-2270-9085"],
        "title": "MMS 제목",
        "message": (
            "MMS 테스트입니다. 이미지 첨부 확인해주세요.\n"
            "내용이 80자 이하일 땐 SMS로, 초과하면 자동 LMS로 전환됩니다.\n"
            "감사합니다."
        ),
        "imageFiles": ["sample1.jpg", "sample2.jpg"]
    }
    send_mms_data(payload)