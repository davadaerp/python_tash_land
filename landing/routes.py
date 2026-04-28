from flask import Blueprint, render_template, request, redirect, jsonify, url_for
from datetime import timedelta, datetime
from master.user_db_utils import user_read_db, user_update_exist_record
from sms.naver_alim_talk import alimtalk_send
from sms.naver_sms import send_sms
from .trial_db_utils import (
    trial_create_table,
    trial_insert_single,
    trial_select_by_email_or_phone,
    trial_read_list,
    trial_approve_single,
    trial_select_single,
    trial_ensure_schema,
    trial_delete_single,
)

from .review_db_utils import (
    DEFAULT_PAGE_SIZE,
    review_create_table,
    review_read_list,
    review_select_single,
    review_insert_single,
    review_update_single,
    review_delete_single,
    review_password_match,
)

landing_bp = Blueprint(
    "landing",
    __name__,
)

LANDING_HOSTS = {
    "landcore.co.kr",
    "www.landcore.co.kr",
    "new.landcore.co.kr",
    "127.0.0.1",
    "localhost",
}

ADMIN_HOSTS = {
    "admin.landcore.co.kr",
    "127.0.0.1",
}

def is_landing_host():
    host = (request.host or "").lower().split(":")[0]
    print("DEBUG host:", host)
    return host in LANDING_HOSTS

def is_admin_host():
    host = (request.host or "").lower().split(":")[0]
    return host in ADMIN_HOSTS

@landing_bp.route("/about", methods=["GET"])
def landing_about():
    if not is_landing_host():
        return redirect("/ts/")
    return render_template("landing/about.html")

@landing_bp.route("/trial", methods=["GET"])
def landing_trial():
    if not is_landing_host():
        return redirect("/ts/")
    trial_create_table()
    return render_template("landing/trial.html")

@landing_bp.route("/pricing", methods=["GET"])
def landing_pricing():
    if not is_landing_host():
        return redirect("/ts/")
    return render_template("landing/pricing.html")

@landing_bp.route("/reviews", methods=["GET"])
def landing_reviews():
    if not is_landing_host():
        return redirect("/ts/")
    review_create_table()
    return render_template("landing/reviews.html")

# 무료체험 폰인증
@landing_bp.route('/api/trial/phone_auth', methods=['POST'])
def trial_phone_auth():
    data = request.get_json(silent=True) or {}

    phone_number = str(data.get("phoneNumber", "")).strip()
    auth_number = str(data.get("authNumber", "")).strip()

    if not phone_number:
        return jsonify({
            "result": "Fail",
            "message": "휴대폰 번호가 없습니다."
        }), 400

    if not auth_number:
        return jsonify({
            "result": "Fail",
            "message": "인증번호가 없습니다."
        }), 400

    title = "무료체험 전화번호 인증"
    message = "\n무료체험 인증번호는 " + auth_number + " 입니다."

    result = send_sms(phone_number, message, title, msg_type='SMS')

    # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
    if result.status_code == 202:
        return jsonify({
            "result": "Success",
            "message": "인증번호가 발송되었습니다."
        }), 200
    else:
        return jsonify({
            "result": "Fail",
            "message": "인증번호 발송에 실패하였습니다."
        }), 500

# 무료체험 저장외
@landing_bp.route("/api/trial/crud", methods=["POST"])
def trial_crud():
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).strip().lower()

    if action != "create":
        return jsonify({
            "result": "Fail",
            "message": "지원하지 않는 action 입니다."
        }), 400

    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip()
    phone = str(payload.get("phone", "")).strip()
    category = str(payload.get("category", "")).strip()
    memo = str(payload.get("memo", "")).strip()
    privacy_agree = str(payload.get("privacy_agree", "N")).strip().upper()

    if not name:
        return jsonify({
            "result": "Fail",
            "message": "이름은 필수입니다."
        }), 400

    if not email:
        return jsonify({
            "result": "Fail",
            "message": "이메일은 필수입니다."
        }), 400

    if not phone:
        return jsonify({
            "result": "Fail",
            "message": "전화번호는 필수입니다."
        }), 400

    if privacy_agree != "Y":
        return jsonify({
            "result": "Fail",
            "message": "개인정보 수집 및 이용에 동의해야 신청할 수 있습니다."
        }), 400

    # 무료체험여부 체크
    existing_trial = trial_select_by_email_or_phone(email, phone)
    if existing_trial:
        return jsonify({
            "result": "Fail",
            "message": "무료체험은 1번만 가능합니다."
        }), 400

    item = trial_insert_single(
        name=name,
        email=email,
        phone=phone,
        category=category,
        memo=memo,
        privacy_agree=privacy_agree
    )

    if not item:
        return jsonify({
            "result": "Fail",
            "message": "무료체험 요청 저장 중 오류가 발생했습니다."
        }), 500

    # =========================
    # 무료체험 저장 성공 후 관리자 알림톡/SMS 전송
    # =========================
    admin_send_ok, admin_send_message = send_trial_created_admin_alimtalk(item)
    print("trial_crud() 무료체험요청 관리자 알림톡 결과:", admin_send_ok, admin_send_message)

    return jsonify({
        "result": "Success",
        "message": "무료체험 요청이 접수되었습니다.",
        "item": item
    })

# 무료체험 저장 성공 후 관리자 알림톡/SMS 전송
def send_trial_created_admin_alimtalk(item):
    """
    무료체험 요청 저장 성공 시 관리자 알림톡/SMS 발송
    """
    if not item:
        return False, "무료체험 요청 데이터가 없습니다."

    name = str(item.get("name", "")).strip()
    email = str(item.get("email", "")).strip()
    phone = str(item.get("phone", "")).strip()
    category = str(item.get("category", "")).strip()

    to = "01022709085"
    title = "무료체험"  # 물건 (무료처험) 요청합니다.
    message = (
        f"\n{name}님이 무료체험요청을 하였습니다.\n"
        f"구분: {category or '-'}\n"
        f"전화번호: {phone}\n"
        f"이메일: {email}\n"
        f"관리자페이지에서 확인 바랍니다."
    )

    data = {
        "userid": phone or email or "trial",
        "userpswd": "0000",
        "phoneNumbers": "관리자:" + to,
        "title": title,
        "message": message
    }

    print("send_trial_created_admin_alimtalk() 무료체험요청 관리자 알림톡 발송:", data)

    try:
        mms_result = alimtalk_send(data)

        if mms_result.status_code == 202:
            print("send_trial_created_admin_alimtalk() 관리자 알림톡 성공")
            return True, message

        print("send_trial_created_admin_alimtalk() 관리자 알림톡 실패:", mms_result.status_code)
        return False, "관리자 알림톡 발송 실패"

    except Exception as e:
        print("send_trial_created_admin_alimtalk() 예외 발생:", e)
        return False, str(e)


#=======================================
@landing_bp.route("/api/reviews/list", methods=["GET"])
def reviews_list():
    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", DEFAULT_PAGE_SIZE, type=int)
    data = review_read_list(page, page_size)
    return jsonify(data)

# 사용자후기 저장외
@landing_bp.route("/api/reviews/crud", methods=["POST"])
def reviews_crud():
    payload = request.get_json(silent=True) or {}
    action = str(payload.get("action", "")).strip().lower()

    if action == "read":
        target_id = int(payload.get("id", 0) or 0)
        item = review_select_single(target_id)

        return jsonify({
            "result": "Success" if item else "Fail",
            "item": item,
            "message": "조회 완료" if item else "해당 후기를 찾을 수 없습니다."
        })

    elif action == "create":
        writer = str(payload.get("writer", "")).strip()
        title = str(payload.get("title", "")).strip()
        rating = int(payload.get("rating", 5) or 5)
        content = str(payload.get("content", "")).strip()
        password = str(payload.get("password", "")).strip()
        #
        phone_number = str(payload.get("phone", "")).strip()

        print("reviews_crud() create payload:", payload)

        if not writer or not title or not content:
            return jsonify({
                "result": "Fail",
                "message": "작성자, 제목, 내용은 필수입니다."
            }), 400

        if not password:
            return jsonify({
                "result": "Fail",
                "message": "수정/삭제용 비밀번호는 필수입니다."
            }), 400

        item = review_insert_single(writer, phone_number, title, rating, content, password)
        if not item:
            return jsonify({
                "result": "Fail",
                "message": "후기 등록 중 오류가 발생했습니다."
            }), 500

        # 후기 1번에 해당함. 구독(체험)일자 + 30일 추가함. => 리스트로 데이터를 받아옵니다.
        user_results = user_read_db(phone_number=phone_number)
        if user_results and len(user_results) > 0:
            # 3. 리스트의 첫 번째 요소(딕셔너리)를 추출합니다.
            user_info = user_results[0]

            print("reviews_crud() user_info:", user_info)

            # 4. 이제 user_info는 딕셔너리이므로 안전하게 키로 접근합니다.
            end_date_raw = user_info.get("subscription_end_date")
            if end_date_raw:
                # 날짜 변환 로직
                if isinstance(end_date_raw, datetime):
                    dt_obj = end_date_raw
                else:
                    dt_obj = datetime.strptime(str(end_date_raw), "%Y-%m-%d %H:%M:%S")

                # 15일 연산(차후 15일 체험연장 적용)
                new_end_date = dt_obj + timedelta(days=15)
                formatted_date = new_end_date.strftime("%Y-%m-%d %H:%M:%S")

                # 5. 업데이트 실행 (user_info["key"] 형식 사용)
                user_update_exist_record({
                    "user_id": user_info["user_id"],
                    "phone_number": phone_number,
                    "subscription_start_date": user_info["subscription_start_date"],
                    "subscription_end_date": formatted_date,
                    "subscription_status": "active"
                })
                print(f"구독 연장 완료: {formatted_date}")
        else:
            print("사용자 정보가 없거나 결과 리스트가 비어있습니다.")

        return jsonify({
            "result": "Success",
            "message": "후기가 등록되었습니다.",
            "item": item
        })

    elif action == "update":
        target_id = int(payload.get("id", 0) or 0)
        writer = str(payload.get("writer", "")).strip()
        title = str(payload.get("title", "")).strip()
        rating = int(payload.get("rating", 5) or 5)
        content = str(payload.get("content", "")).strip()
        password = str(payload.get("password", "")).strip()

        if not review_password_match(target_id, password):
            return jsonify({
                "result": "Fail",
                "message": "비밀번호가 일치하지 않습니다."
            }), 403

        item = review_update_single(target_id, writer, title, rating, content)

        if not item:
            return jsonify({
                "result": "Fail",
                "message": "수정할 후기를 찾을 수 없습니다."
            }), 404

        return jsonify({
            "result": "Success",
            "message": "후기가 수정되었습니다.",
            "item": item
        })

    elif action == "delete":
        target_id = int(payload.get("id", 0) or 0)
        password = str(payload.get("password", "")).strip()

        print(target_id, password)

        # 후기 비번검증
        if not review_password_match(target_id, password):
            return jsonify({
                "result": "Fail",
                "message": "비밀번호가 일치하지 않습니다."
            }), 403

        # 후기 삭제
        deleted = review_delete_single(target_id)
        if not deleted:
            return jsonify({
                "result": "Fail",
                "message": "삭제할 후기를 찾을 수 없습니다."
            }), 404

        return jsonify({
            "result": "Success",
            "message": "후기가 삭제되었습니다."
        })

    return jsonify({
        "result": "Fail",
        "message": "지원하지 않는 action 입니다."
    }), 400


#---------------------------------------------------------------
# trial admin maanger list
#---------------------------------------------------------------
@landing_bp.route("/admin/trials", methods=["GET"])
def admin_trial_list_page():

    if not (is_admin_host()):
        return redirect("/ts/")

    trial_ensure_schema()
    return render_template("landing/admin_trial_list.html")

@landing_bp.route("/api/admin/trials/list", methods=["GET"])
def admin_trial_list_api():
    if not (is_admin_host()):
        return jsonify({
            "result": "Fail",
            "message": "접근 권한이 없습니다."
        }), 403

    page = request.args.get("page", 1, type=int)
    page_size = request.args.get("page_size", 50, type=int)
    approve_status = str(request.args.get("approve_status", "")).strip().lower()

    data = trial_read_list(page=page, page_size=page_size, approve_status=approve_status)
    return jsonify(data)

@landing_bp.route("/api/admin/trials/approve", methods=["POST"])
def admin_trial_approve_api():
    if not (is_admin_host()):
        return jsonify({
            "result": "Fail",
            "message": "접근 권한이 없습니다."
        }), 403

    payload = request.get_json(silent=True) or {}
    trial_id = int(payload.get("id", 0) or 0)
    approved_message = str(payload.get("approved_message", "")).strip()

    if trial_id < 1:
        return jsonify({
            "result": "Fail",
            "message": "승인할 무료체험 ID가 올바르지 않습니다."
        }), 400

    item = trial_select_single(trial_id)
    if not item:
        return jsonify({
            "result": "Fail",
            "message": "해당 무료체험 요청을 찾을 수 없습니다."
        }), 404

    if str(item.get("approve_status", "")).lower() == "approved":
        return jsonify({
            "result": "Fail",
            "message": "이미 승인된 요청입니다.",
            "item": item
        }), 400

    updated_item = trial_approve_single(trial_id, approved_message)
    if not updated_item:
        return jsonify({
            "result": "Fail",
            "message": "승인 처리 중 오류가 발생했습니다."
        }), 500

    #sent_ok, sent_message = send_trial_approved_message_sms(updated_item)
    sent_ok, sent_message = send_trial_approved_message_alimtalk(updated_item)

    return jsonify({
        "result": "Success",
        "message": "무료체험 승인 처리가 완료되었습니다.",
        "sent": sent_ok,
        "sent_message": sent_message,
        "item": updated_item
    })

# SMS전송
def send_trial_approved_message_sms(item):
    """
    무료체험 승인 완료 SMS 발송
    """
    if not item:
        return False, "대상 데이터가 없습니다."

    name = str(item.get("name", "")).strip()
    phone = str(item.get("phone", "")).strip()
    email = str(item.get("email", "")).strip()
    approved_message = str(item.get("approved_message", "")).strip()

    if not phone:
        return False, "수신자 전화번호가 없습니다."

    # 길이 80자여부 체크
    final_message = approved_message or (
        f"{name}님 무료체험 승인이 완료되었습니다.\n"
        f"랜드코어 설치 및 이용 안내는 별도로 전달드리겠습니다."
    )

    title = "무료체험 승인완료"

    print("=== 무료체험 승인 SMS 발송 ===")
    print("name:", name)
    print("phone:", phone)
    print("email:", email)
    print("title:", title)
    print("message:", final_message)

    try:
        sms_result = send_sms(phone, final_message, title, msg_type='SMS')

        # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
        if sms_result.status_code == 202:
            print("send_trial_approved_message_sms() 무료체험 승인 SMS 성공")
            return True, final_message
        else:
            print("send_trial_approved_message_sms() 무료체험 승인 SMS 실패")
            return False, "무료체험 승인 SMS 발송에 실패하였습니다."
    except Exception as e:
        print("send_trial_approved_message_sms() 예외 발생:", e)
        return False, f"무료체험 승인 SMS 발송 중 오류: {str(e)}"


# 알림톡 전송
def send_trial_approved_message_alimtalk(item):
    """
    무료체험 승인 완료 알림톡/SMS 발송
    """
    if not item:
        return False, "대상 데이터가 없습니다."

    name = str(item.get("name", "")).strip()
    phone = str(item.get("phone", "")).strip()
    email = str(item.get("email", "")).strip()
    approved_message = str(item.get("approved_message", "")).strip()

    if not phone:
        return False, "수신자 전화번호가 없습니다."

    final_message = approved_message or (
        f"\n{name}님 무료체험 승인이 완료되었습니다.\n"
        f"랜드코어 다운로드 및 설치는 아래 URL을 참조해 주세요.\n"
    )

    title = "무료체험 승인"

    data = {
        "userid": phone,                 # 기존 alimtalk_send 구조 맞춤
        "userpswd": "0000",
        "phoneNumbers": f"{name}:{phone}",
        "title": title,
        "message": final_message
    }

    print("=== 무료체험 승인 알림톡 발송 ===")
    print("name:", name)
    print("phone:", phone)
    print("email:", email)
    print("data:", data)

    try:
        mms_result = alimtalk_send(data)

        # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
        if mms_result.status_code == 202:
            print("send_trial_approved_message() 무료체험 승인 알림톡 성공")
            return True, final_message
        else:
            print("send_trial_approved_message() 무료체험 승인 알림톡 실패")
            return False, "무료체험 승인 알림톡 발송에 실패하였습니다."
    except Exception as e:
        print("send_trial_approved_message() 예외 발생:", e)
        return False, f"무료체험 승인 알림톡 발송 중 오류: {str(e)}"


@landing_bp.route("/api/admin/trials/delete", methods=["POST"])
def admin_trial_delete_api():
    if not (is_admin_host()):
        return jsonify({
            "result": "Fail",
            "message": "접근 권한이 없습니다."
        }), 403

    payload = request.get_json(silent=True) or {}
    trial_id = int(payload.get("id", 0) or 0)

    if trial_id < 1:
        return jsonify({
            "result": "Fail",
            "message": "삭제할 무료체험 ID가 올바르지 않습니다."
        }), 400

    item = trial_select_single(trial_id)
    if not item:
        return jsonify({
            "result": "Fail",
            "message": "해당 무료체험 요청을 찾을 수 없습니다."
        }), 404

    deleted = trial_delete_single(trial_id)
    if not deleted:
        return jsonify({
            "result": "Fail",
            "message": "삭제 처리 중 오류가 발생했습니다."
        }), 500

    return jsonify({
        "result": "Success",
        "message": "무료체험 요청이 삭제되었습니다."
    })