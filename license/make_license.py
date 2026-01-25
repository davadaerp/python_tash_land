import time
from datetime import datetime, timedelta, timezone
import json
import sys
import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet

# --- [추가] 안전한 로깅 설정 ---
# 이 설정은 stdout의 인코딩 문제를 방지하고 파일과 콘솔에 안전하게 출력합니다.
# 부모인 LandCore 설정을 상속받음
logger = logging.getLogger("LandCore.License")

# 랜드코어 고정 키워드(fosemzhdj)
SECRET_KEYWORD = "fosemzhdj"

def generate_fixed_key(keyword: str):
    key_bytes = hashlib.sha256(keyword.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes).decode()

    # print 대신 logger 사용
    logger.info(f"키워드: {keyword}")
    logger.info(f"생성된 Fernet 키: {fernet_key}")
    return fernet_key


def make_license(days=30):
    try:
        fixed_secret_key = generate_fixed_key(SECRET_KEYWORD)
        fernet = Fernet(fixed_secret_key.encode("utf-8"))

        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        issued_at = datetime.now(timezone.utc)
        expires_at = end_date.strftime("%Y-%m-%d")

        payload = {
            "user_id": "landcore",
            "days": days,
            "issued_at": issued_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "expires_at": expires_at
        }

        token_bytes = fernet.encrypt(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        license_token = token_bytes.decode("utf-8")

        with open("license.key", "w", encoding="utf-8") as f:
            f.write(license_token)

        logger.info(f"✅ 라이선스 발행 완료: {expires_at}까지 {days}일간 유효")
        return True
    except Exception as e:
        logger.error(f"❌ 라이선스 생성 실패: {e}")
        return False


def check_license():
    file_path = "license.key"
    if not os.path.exists(file_path):
        logger.error("🚨 [ERROR] 라이선스 파일(license.key)이 존재하지 않습니다.")
        return None

    try:
        # 특수문자 라인은 안전한 기호(-)로 대체하거나 제거 권장
        logger.info("-" * 40)
        fixed_secret_key = generate_fixed_key(SECRET_KEYWORD)
        fernet = Fernet(fixed_secret_key.encode("utf-8"))

        with open(file_path, "r", encoding="utf-8") as f:
            encrypted_token = f.read().strip()

        decrypted_data = fernet.decrypt(encrypted_token.encode("utf-8"))
        payload = json.loads(decrypted_data.decode("utf-8"))

        expire_date = datetime.strptime(payload['expires_at'], "%Y-%m-%d")
        now = datetime.now()
        remaining_delta = expire_date - now
        remaining_days = remaining_delta.days + 1

        logger.info("-" * 40)
        logger.info("📜 라이선스 인증 정보")
        logger.info(f"▶ 사용자 ID   : {payload.get('user_id')}")
        logger.info(f"▶ 발급 총일   : {payload.get('days')}일")
        logger.info(f"▶ 발급 일시   : {payload.get('issued_at')}")
        logger.info(f"▶ 만료 예정일 : {payload.get('expires_at')}")
        logger.info(f"▶ 남은 일자   : {remaining_days}")

        if remaining_days > 0:
            logger.info(f"▶ 남은 기간   : {remaining_days}일 남음")
            logger.info("-" * 40)
            logger.info("✅ 라이선스 인증 성공. 프로그램을 시작합니다.")
            payload['remaining_days'] = remaining_days
            return payload
        else:
            logger.info("-" * 40)
            logger.error(f"🚨 [ERROR] 라이선스 기간이 만료되었습니다. (만료일: {payload['expires_at']})")
            return None
    except Exception as e:
        logger.error(f"🚨 [ERROR] 라이선스 검증 실패 (변조 또는 키 불일치): {e}")
        return None


if __name__ == "__main__":
    # --- [단독 실행 시 로깅 활성화 로직 추가] ---
    # 1. 최상위 부모 로거 가져오기
    parent_logger = logging.getLogger("LandCore")
    parent_logger.setLevel(logging.INFO)

    # 2. [핵심] 기존에 등록된 모든 핸들러를 제거 (중복 출력의 근본 원인 차단)
    while parent_logger.handlers:
        parent_logger.removeHandler(parent_logger.handlers[0])

    # 3. 새로 하나만 등록
    handler = logging.StreamHandler(sys.stdout)

    # 인코딩 설정
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        except:
            pass

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    parent_logger.addHandler(handler)

    # 4. 자식 로거가 부모에게 로그를 전달하되, 부모만 출력하도록 설정
    # (이미 위에서 부모 핸들러를 정리했으므로 하나만 나옵니다)
    logger.propagate = True

    make_license(days=33)
    time.sleep(3)
    check_license()