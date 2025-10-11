#
# ✅ 멀티프로세스(동시접속) 추천 운영 방법: gunicorn + Flask
# gunicorn은 Python WSGI HTTP 서버로, 멀티 프로세스/멀티 스레드를 활용해 동시에 여러 요청을 처리할 수 있습니다.
# 1. gunicorn 설치
# pip install gunicorn
#
# gunicorn app:app --workers 4 --bind 0.0.0.0:8080
# app:app → 첫 번째 app은 파일명 (app.py), 두 번째 app은 Flask 인스턴스 변수
# #
# --workers 4 → 4개 프로세스로 실행
# --bind → 접속 포트 지정
#
import os
import json
import time

import requests
import secrets
from flask import Flask, jsonify, request, redirect, render_template, url_for, make_response, abort, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path

# 상가및 아파트 크롤링데이타(예전PC)
from apt.apt_db_utils import apt_read_db, get_jeonse_min_max
from sanga.sanga_db_utils import sanga_update_fav, extract_law_codes
#
# 상가및 아파트 크롤링데이타(신규서버)
from crawling.apt_mobile_db_utils import apt_read_db as apt_mobile_read_db, get_jeonse_min_max as get_jeonse_min_max_mobile
from crawling.sanga_mobile_db_utils import sanga_read_db as sanga_mobile_read_db
from crawling.crawl_lawd_codes_db_utils import search_crawl_lawd_codes, insert_crawl_lawd_code, \
    delete_crawl_lawd_code_by_id, get_crawl_lawd_code_by_cd_type
from crawling.lawd_code_db_utils import search_lawd_by_name
#
from jumpo.jumpo_db_utils import jumpo_read_info_list_db
from npl.npl_db_utils import npl_read_db, query_npl_region_hierarchy
from pubdata.public_land_db_search import run_sanga, sanga_items_to_json, run_villa, villa_items_to_json, run_apt, \
    apt_items_to_json
from pubdata.public_land_lawd_code_db_utils import get_lawd_by_code
#from naver.naver_login import naver_authorization, naver_callback
#
from auction.auction_db_utils import auction_read_db
from realtor.realtor_db_utils import realtor_read_db
from master.user_db_utils import user_insert_record, user_read_db, user_create_table, user_update_record, \
    user_delete_record, user_cancel_record, user_update_exist_record
#
from sms.naver_alim_talk import alimtalk_send
from sms.naver_sms import send_mms_data, send_sms
from sms.purio_sms import purio_sms_send
#
from pastapt.past_apt_complete_volume_db_utils import fetch_apt_complete_volume_by_address
from pastapt.past_interest_rate_db_utils import fetch_latest_interest_rate
from pastapt.past_apt_db_utils import query_region_hierarchy, fetch_apt_detail_data, fetch_grouped_apt_data, \
    fetch_apt_by_name_and_size
from pastapt.past_average_annual_income_db_utils import fetch_all_income_data
from pastapt.kb_apt_sale_price_index_db_utils import fetch_latest_sale_index_by_address
# 국토부공공데이타 가져오기
from pubdata.public_population_stats import get_population_rows, prev_month_yyyymm

# auth.py에서 토큰 관련 함수 가져오기
from common.auth import create_access_token, extract_user_info_from_token, kakao_token_required
#
from config import TEMPLATES_NAME, FORM_DIRECTORY, LEGAL_DIRECTORY, UPLOAD_FOLDER_PATH

# common/commonResponse.py에 정의된 CommonResponse와 Result를 import
from legal_docs.legal_docs_down import getIros1

app = Flask(__name__, template_folder=TEMPLATES_NAME)

# CORS 전체 허용
CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

# 메모리 기반의 토큰 저장소 (유저ID:토큰)
active_tokens = {}

APT_KEY = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
VILLA_KEY = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="
SANGA_KEY = "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA=="

# 아마존 로드발라서 헬스체크처리
@app.route('/q/health/ready')
def health_ready():
    return "OK", 200

# /ts/는 아마존에서 설정시 적요한 네이밍룰
@app.route("/", methods=["GET"])
@app.route("/ts/", methods=["GET"])
def loginForm():
    #return render_template("login.html")
    return render_template("login_kakao.html")

@app.route("/api/token", methods=["POST"])
def token_create():

    # 1) create_access_token 호출
    resp = create_access_token()

    # 2) JSON 파싱
    payload = json.loads(resp.get_data(as_text=True))
    print('/api/token:', payload)

    # 3) 실패인 경우, 400
    if payload.get("result") == "Fail":
        # errcode 를 HTTP status 로 사용
        #return jsonify(data), payload.get("errcode", 400)
        return jsonify(payload)

    # 4) 성공인 경우, 키 추가
    payload.setdefault("apt_key",   "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==")
    payload.setdefault("villa_key", "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==")
    payload.setdefault("sanga_key", "B2BtWbuZVFz/EJoLsrDa6corOwSR4SsGwjBKzK2WJQ3JVwRMIUoXOGY3BHXrxZq78nP+ECsW5wB4TEwbgxS2PA==")

    # 5) user_id와 access_token을 메모리에 저장 (중복 방지)
    #access_token = payload.get('access_token')

    # user_id 추출 및 토큰을 메모리저장(중복방지)
    # user_id = data.get("user_id")
    # access_token = data.get("access_token")
    # active_tokens[user_id] = access_token

    # 5) 최종 응답, 200
    return jsonify(payload)

@app.route("/api/login_token", methods=["GET"])
def login_token():
    # 아래 access_token에서 username(id)와 패스워드를 얻어 사용자정보를 리턴해준다.
    auth_header = request.headers.get("Authorization")
    access_token = ""
    if auth_header:
        # 헤더 값은 "Bearer <토큰>" 형태이므로 분리
        parts = auth_header.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            access_token = parts[1]
    print('login_token:', access_token)

    # 토큰 정합성 체크
    userid, exptime, errmsg = extract_user_info_from_token(access_token)
    if errmsg == 'Success':
        print("User ID:", userid)
        print("Exptime:", exptime)
        print("login_token() Success to extract master info from token.")

        # 차후에 중복로그인 체크 => 토큰 유효성 & 중복 로그인 확인
        # if active_tokens.get(userid) != access_token:
        #     result = "Failed"
        #     errmsg = '다른 세션에서 로그인되었습니다.'

        # 로그인 성공 시 리다이렉트 URL을 JSON으로 반환
        #return jsonify(CommonResponse.success(data, "로그인 성공").to_dict())
        return jsonify({"result": "Success", "errmag": errmsg})
    else:
        print("login_token() Failed to extract master info from token.")
        return jsonify({"result": "Failed", "errmag": errmsg})
        #return jsonify(CommonResponse.fail("400", "login_token() Failed:" + errmsg).to_dict())

@app.route("/api/logout", methods=["GET"])
def logout():
    # 토큰 제거
    token = request.cookies.get("access_token")
    userid, exptime, errmsg = extract_user_info_from_token(token)
    print('logout', userid, token)
    if errmsg == 'Success':
        active_tokens.pop(userid, None)
    #
    # 리다이렉트 응답 생성
    response = make_response(redirect(url_for("loginForm")))

    # access_token 쿠키 삭제 (클라이언트 브라우저에 명시적으로 삭제 지시)
    response.set_cookie('access_token', '', expires=0, path='/')

    return response


# # 카카오 로그인 관련
from kakao.kakao_client import kakao, TOKENS  # 재수출된 TOKENS 사용
from common.auth import kakao_extool_auth_required

# 필요시 scope를 None으로 두고 최소 동작 확인
DEFAULT_SCOPE = None  # 예: ["profile_nickname", "profile_image"]

@app.route("/api/kakao/login")
def kakao_login():
    #
    user_create_table()  # 테이블 없으면 생성
    #
    state = secrets.token_urlsafe(16)
    # session["oauth_state"] = state
    auth_url = kakao.build_authorize_url(state, DEFAULT_SCOPE)
    print("== kakao_login() kakao_auth_url:", auth_url)
    return redirect(auth_url)

@app.get("/api/kakao/callback")
def kakao_auth_callback():
    code = request.args.get("code")
    if not code:
        error = request.args.get("error_description") or request.args.get("error") or "인가 코드를 찾을 수 없습니다."
        return jsonify({"result": "Fail", "message": error}), 400

    print("== kakao_callback() code:", code)

    # 1) 코드 → 토큰
    try:
        token = kakao.exchange_code_for_token(code)  # ← 여기서 403이면 위에서 print로 상세 로그 남음
        access_token = token.get("access_token")
        refresh_token = token.get("refresh_token")
        expires_in = token.get("expires_in")
    except Exception as e:
        return make_response(_error_bridge_html(f"토큰 교환 실패: {e}"), 400)

    # 2) 사용자 정보
    me = kakao.get_user_me(access_token)
    kakao_id = str(me.get("id"))
    user_id = kakao_id
    kakao_account = me.get("kakao_account", {}) or {}
    email = kakao_account.get("email")
    profile = kakao_account.get("profile") or {}
    nickname = profile.get("nickname")
    profile_img = profile.get("profile_image_url")

    # (옵션) 이메일 추가동의 유도 로직
    # if needs_email and not email:
    #     session["oauth_state"] = secrets.token_urlsafe(16)
    #     auth_url = kakao.build_authorize_url(session["oauth_state"], ["account_email"], prompt="consent")
    #     return redirect(auth_url)

    # 2) DB에서 user_id로 사용자 조회
    rows = user_read_db(user_id=kakao_id)
    sms_count = rows[0].get("recharge_sms_count", 0) if rows else 0
    if not rows:
        print("user not found. insert new user.")
        user_insert_record({
            "user_id": kakao_id,
            "kakao_id": kakao_id,
            "user_name": nickname,
            "email": email,
            "nick_name": nickname,
            "profile_image": profile_img,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": str(datetime.utcnow() + timedelta(seconds=expires_in))
        })
    else:
        print("user found. update user info.")
        # 3) DB 저장/갱신 처리 (예: user_update_record 또는 insert)
        user_update_exist_record({
            "user_id": kakao_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_expires_at": str(datetime.utcnow() + timedelta(seconds=expires_in)),
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        })

    print("== kakao_callback() 사용자 정보:", {
        "kakao_id": kakao_id,
        "email": email,
        "nickname": nickname,
        "profile_img": profile_img,
        "sms_count": sms_count,
    })

    # 우리 서비스용 JWT 발급(user_id 기반)
    app_token = kakao.make_jwt(user_id)

    # 확장프로그램 팝업으로 토큰/프로필 전달 (postMessage)
    # 보안 고려: origin 체크는 확장 프로그램에서 수행
    html = f"""
<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8"><title>로그인 완료</title></head>
<body>
<script>
  try {{
    window.opener && window.opener.postMessage({{
        type: "kakao_login_success",
        token: {repr(app_token)},
        nickname: {repr(nickname)},
        sms_count: {sms_count},
        apt_key: {repr(APT_KEY)},
        villa_key: {repr(VILLA_KEY)},
        sanga_key: {repr(SANGA_KEY)}
    }}, "*");
  }} catch (e) {{}}
  window.close();
</script>
로그인 처리 중...
</body>
</html>
"""
    resp = make_response(html)
    resp.headers["Content-Security-Policy"] = "default-src 'none'; script-src 'unsafe-inline';"
    return resp

def _error_bridge_html(msg: str) -> str:
    return f"""<!doctype html><meta charset="utf-8">
<title>로그인 실패</title>
<div style="font-family:system-ui;padding:24px">
  <h2>로그인 처리 중 오류</h2>
  <pre style="white-space:pre-wrap">{msg}</pre>
  <button onclick="location.href='/'">메인으로</button>
</div>
"""

@app.get("/api/kakao/logout")
def kakao_auth_logout():
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        access_token = auth.split(" ", 1)[1]
        payload = kakao.verify_jwt(access_token)
        user_id = payload["sub"]  # user_id는 kakao_id와 동일하게 설정됨
        if payload:
            jti = payload.get("jti")
            if jti in TOKENS:
                del TOKENS[jti]

        #==============================================
        # 사용자 삭제
        print("== unlink() user_id:", user_id)
        print("== unlink() access_token:", access_token)

        # 3) Kakao Unlink 시도 (토큰이 있는 경우에만)
        try:
            if access_token:
                kakao.unlink(access_token)  # KakaoAPI 유틸 사용
        except Exception as e:
            # 언링크 실패 시 에러 반환
            return make_response(f"연결 해제 실패: {e}", 400)

        # 4) 해당 user_id 토큰 필드 초기화 및 updated_at 갱신
        user_update_exist_record({
            "user_id": user_id,
            "kakao_id": user_id,
            "access_token": "",
            "refresh_token": "",
            "token_expires_at": "",
            "updated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        })

    return jsonify({"result": "ok"})

@app.get("/api/kakao/me")
@kakao_extool_auth_required
def api_me(user_id):
    # auth = request.headers.get("Authorization", "")
    # if not auth.startswith("Bearer "):
    #     return jsonify({"error": "unauthorized"}), 401
    # token = auth.split(" ", 1)[1]
    # payload = kakao.verify_jwt(token)
    # if not payload:
    #     return jsonify({"error": "unauthorized"}), 401
    #
    # user_id = payload["sub"]    # user_id는 kakao_id와 동일하게 설정됨
    print("== api_me() user_id:", user_id)
    # 닉네임/문자건수는 실제론 DB에서 조회
    # 여기서는 간단히 유저아이디 기반으로 예시값 구성
    # 2) DB에서 user_id로 사용자 조회
    rows = user_read_db(user_id=user_id)
    if not rows:
        return jsonify({"error": "사용자가 존재하지 않습니다."}), 401
    #print(rows)
    #
    nick_name = rows[0].get("nick_name")
    sms_count = rows[0].get("recharge_sms_count", 0) if rows else 0
    #  구독상태 (active, canceled 등) : 차후 관리자 페이지에서 on/off 처리용
    plan_name = "0개월"
    plan_date = '0일남음'
    # 구독상태 체크(request-요청, active-구독, cancelled-구독취소)
    subscription_status = rows[0].get("subscription_status", 'cancelled') if rows else 'cancelled'
    is_subscribed = subscription_status
    if subscription_status == 'active' or subscription_status == 'request':
        #is_subscribed = "active"
        subscription_start_date = rows[0].get("subscription_start_date", "")
        subscription_end_date = rows[0].get("subscription_end_date", "")
        plan_name = f"{rows[0].get('subscription_month', 1)}개월"
        #
        # 날짜 포맷: "2025-09-30 07:54:28"
        fmt = "%Y-%m-%d %H:%M:%S"
        try:
            start_date = datetime.strptime(subscription_start_date, fmt).date()
            end_date = datetime.strptime(subscription_end_date, fmt).date()

            # 남은 날짜 계산
            remaining_days = (end_date - start_date).days
            if remaining_days < 0:
                remaining_days = 0

            plan_date = f"{remaining_days}일남음"
        except Exception as e:
            # 날짜 파싱 실패 시 기본값
            plan_date = "0일남음"
    else:
        plan_name = "미구독"
        plan_date = "0일"
    #
    # 문자충전상태 체크
    is_recharged = rows[0].get("recharge_status", 'active') if rows else 'active'
    # if is_recharged != 'active':
    #     sms_count = 0

    print(is_subscribed , plan_name, plan_date, is_recharged, sms_count)

    return jsonify({
        "nickname": nick_name,
        "is_subscribed": is_subscribed,
        "is_recharged": is_recharged,
        "plan_name": plan_name,
        "plan_date": plan_date,
        "sms_count": sms_count, "apt_key": APT_KEY, "villa_key": VILLA_KEY, "sanga_key": SANGA_KEY
    })

# ===== 메인 페이지 및 메뉴 =====
@app.route("/api/main")
#@token_required
@kakao_token_required
def main(current_user):
    return render_template("main.html")

@app.route("/api/menu", methods=["GET"])
#@token_required
@kakao_token_required
def menu(current_user):
    menu = request.args.get("menu", "")
    print(menu)
    if menu == 'user':
        return render_template("user_search.html")
    if menu == 'apt':
        return render_template("realdata_apt.html")
    if menu == 'villa':
        return render_template("realdata_villa.html")
    if menu == 'sanga':
        return render_template("realdata_sanga.html")
    if menu == 'apt_search':
        return render_template("crawling_apt_search.html")
    if menu == 'sanga_search':
        return render_template("crawling_sanga_search.html")
    if menu == 'auction':
        return render_template("crawling_auction_search.html")
    if menu == 'npl':
        return render_template("crawling_npl_search.html")
    if menu == 'realtor':
        return render_template("crawling_realtor_search.html")
    if menu == 'realtor_pop':
        return render_template("crawling_realtor_message_pop.html")
    if menu == 'jumpo':
        return render_template("crawling_jumpo_search.html")
    if menu == 'sanga_profit':
        return render_template("profit_sanga_sheet.html")
    if menu == 'general_profit':
        return render_template("profit_general_sheet.html")
    if menu == 'api_key':
        #type = request.args.get("type", "")
        return render_template("realdata_pop_key.html")
    if menu == 'past_apt':
        return render_template("pastdata_apt.html")
    # 마이페이지, 구독, 문자충전
    if menu == 'mypage':
        return render_template("extool_user_mypage.html")
    if menu == 'subscribe':
        return render_template("extool_user_subscribe.html")
    if menu == 'recharge':
        return render_template("extool_user_recharge.html")

#===== 사용자(회원) 데이타 처리 =============
@app.route('/api/user/register', methods=['GET'])
def user_register_form():
    return render_template("user_register.html")

# 사용자 구독인증
@app.route('/api/user/subscribe_auth', methods=['POST'])
@kakao_extool_auth_required
def user_subscribe_auth(user_id):
    print(f"user_subscribe_auth user_id: {user_id}")
    data = request.get_json()
    phone_number = data.get("phoneNumber")
    auth_number = data.get("authNumber")

    # 메니저에게 카톡으로 구독처리여부 SMS 전송요망
    to = phone_number
    title = "문자 인증번호"
    message = "\n문자 인증번호는 " + auth_number + " 입니다."
    result = send_sms(to, message, title, msg_type='SMS')
    # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
    if result.status_code == 202:
        return jsonify({"result": "Success", "message": "인증번호가 발송되었습니다."}), 200
    else:
        return jsonify({"result": "Fail", "message": "인증번호 발송에 실패하였습니다."}), 500

# 사용자 구독정보 저장(구독시작일, 종료일, 구독상태 등)
@app.route('/api/user/subscribe', methods=['POST'])
@kakao_extool_auth_required
def user_subscribe(user_id):
    data = request.get_json()
    # #print(f"🔍data: {data}")
    print(f"user_subscribe user_id: {user_id}")
    subscription_month = data.get("plan")
    phone_number = data.get("phoneNumber") or ''
    print("📋 subscription_month:", subscription_month, "phone_number:", phone_number)

    # 오늘 일시 (YYYY-MM-DD HH:MM:SS)
    subscription_start_date = datetime.now()

    # 종료일 = 시작일 + plan 개월
    try:
        months = int(subscription_month)
    except (TypeError, ValueError):
        months = 0  # plan 값이 잘못 들어왔을 때 fallback

    # 구독 종료일 계산
    subscription_end_date = subscription_start_date + relativedelta(months=months)

    # DB 저장용 포맷 문자열
    start_str = subscription_start_date.strftime("%Y-%m-%d %H:%M:%S")
    end_str = subscription_end_date.strftime("%Y-%m-%d %H:%M:%S")

    print("user found. update user info.")
    userInfo = user_read_db(user_id)
    user_name = userInfo[0].get("user_name")
    if not userInfo:
        return jsonify({"error": "사용자가 존재하지 않습니다."}), 401

    # 메니저에게 카톡으로 구독처리여부 알림톡/SMS 전송요망
    to = "01022709085"
    title = subscription_month + "개월 구독"
    message = "\n" + user_name + "님이 " + subscription_month + "개월 구독요청하였습니다. 관리자페이지에서 승인처리바랍니다."
    data = {
        "userid": user_id,
        "userpswd": "0000",
        "phoneNumbers": "관리자:" + to,
        "title": title,
        "message": message
    }
    print("user_subscribe() 구독요청 알림톡 발송:", data)
    mms_result = alimtalk_send(data)
    #print(f"user_subscribe() Response Code: {mms_result.status_code}, "f"user_subscribe() 구독요청 알림톡 결과: {mms_result.json()}")
    # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
    if mms_result.status_code == 202:
        #
        user_update_exist_record({
            "user_id": user_id,
            "phone_number": phone_number,
            "subscription_start_date": start_str,
            "subscription_end_date": end_str,
            "subscription_month": months,
            "subscription_status": "request"  # 관리자 승인 대기 상태(request:구독요청,active:구독,cancelled:구독취소)
        })
        print("user_subscribe() 구독요청 알림톡 성공")
    else:
        print("user_subscribe() 구독요청 알림톡 실패:")
    #
    # 메니저에게 카톡으로 구독처리여부 SMS 전송요망
    # mms_result = send_sms(to, message, title, msg_type='SMS')
    #
    return jsonify(data), 200

# 사용자 구독요청 승인처리(관리자 전용)
@app.route('/api/user/subscribe_approval', methods=['POST'])
def user_subscribe_approval():
    data = request.get_json()
    print(f"🔍data: {data}")
    user_id = data.get("user_id")
    approval_status = data.get("subscribe_status", "cancelled")  # Y/N
    subscription_month = data.get("subscription_month", 1)
    print("📋 user_id:", user_id, "approval:", approval_status)

    # if approval != "Y":
    #     return jsonify({"result": "Fail", "message": "승인여부가 Y가 아닙니다."}), 400

    user_update_exist_record({
        "user_id": user_id,
        "subscription_month": subscription_month,
        "subscription_status": approval_status   # 관리자 승인 대기 상태(request:구독요청,active:구독,cancelled:구독취소)
    })

    return jsonify({"success": "구독승인되었습니다."}), 200


# 사용자 구독정보 체크(구독기간 만료 등)
@app.route('/api/user/subscribe_check', methods=['POST'])
@kakao_extool_auth_required
def user_subscribe_check(user_id):
    print(f"user_subscribe_check user_id: {user_id}")
    # 2) DB에서 user_id로 사용자 조회
    rows = user_read_db(user_id=user_id)
    if not rows:
        return jsonify({"error": "사용자가 존재하지 않습니다."}), 401
    #
    #print(rows)
    #
    subscription_status = rows[0].get("subscription_status")
    print("subscription_status:", subscription_status)
    if subscription_status != "active":
        rtn_data = {
            'result': 'Fail',
            'message': '구독(갱신)후 사용바랍니다.'
        }
    else:
        rtn_data = {
            'result': 'Success',
            'message': '구독완료되었습니다.'
        }

    return jsonify(rtn_data), 200


# 사용자 문자및 등기비용 충전처리
@app.route('/api/user/sms_recharge', methods=['POST'])
@kakao_extool_auth_required
def user_sms_recharge(user_id):
    data = request.get_json()
    #print(f"🔍data: {data}")
    recharge_cnt = data.get("recharge")
    print("recharge_cnt:", recharge_cnt)

    # 메니저에게 카톡으로 문자충전요청 알림톡/SMS 전송요망
    userInfo = user_read_db(user_id)
    user_name = userInfo[0].get("user_name")
    if not userInfo:
        return jsonify({"error": "사용자가 존재하지 않습니다."}), 401

    # 메니저에게 카톡으로 구독처리여부 알림톡/SMS 전송요망
    to = "01022709085"
    title = recharge_cnt + "건 충전"
    message = "\n" + user_name + "님이 문자 " + recharge_cnt + "건 충전요청하였습니다. 관리자페이지에서 승인처리바랍니다."
    data = {
        "userid": user_id,
        "userpswd": "0000",
        "phoneNumbers": "관리자:" + to,
        "title": title,
        "message": message
    }
    print("user_subscribe() 문자충전요청 알림톡 발송:", data)
    mms_result = alimtalk_send(data)
    #print(f"user_subscribe() Response Code: {mms_result.status_code}, "f"user_subscribe() 구독요청 알림톡 결과: {mms_result.json()}")
    # 응답 상태 및 결과 출력(202: 성공, 4xx, 5xx: 실패)
    if mms_result.status_code == 202:
        #
        user_update_exist_record({
            "user_id": user_id,
            "recharge_request_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recharge_request_sms_count": recharge_cnt,
            "recharge_status": "request"  # 관리자 승인 대기 상태(request:충전요청,active:충전)
        })
        print("user_sms_recharge() 충전요청 알림톡 성공")
    else:
        print("user_sms_recharge() 충전요청 알림톡 실패:")
    #
    return jsonify(data), 200

# 사용자 문자충전 승인처리(관리자 전용)
@app.route('/api/user/recharge_approval', methods=['POST'])
def user_recharge_approval():
    data = request.get_json()
    print(f"🔍data: {data}")
    user_id = data.get("user_id")
    approval_status = data.get("recharge_status", "cancelled")  # Y/N
    approval_sms_count = data.get("approval_sms_count", 1)      # 기존충전건수 + 요청충전건수
    print("📋 user_id:", user_id, "approval:", approval_status, "approval_sms_count:", approval_sms_count)

    # if approval != "Y":
    #     return jsonify({"result": "Fail", "message": "승인여부가 Y가 아닙니다."}), 400

    user_update_exist_record({
        "user_id": user_id,
        "recharge_sms_count": approval_sms_count,
        "recharge_request_sms_count": 0,    # 충전요청건수 초기화
        "recharge_status": approval_status   # 관리자 승인 대기 상태(request:구독요청,active:구독,cancelled:구독취소)
    })

    # 차후 충전요청자에게 충전완료 알림톡/SMS 전송요망
    ##

    return jsonify({"success": "충전승인되었습니다."}), 200

#============== 확장툴 마이페이지 ====================
# 마이페이지 회원정보 조회
@app.route('/api/user/mypage/member', methods=['POST'])
@kakao_extool_auth_required
def user_member(user_id):
    # user_id는 데코레이터에서 추출되어 주입됨
    print(f"user_member user_id: {user_id}")

    # 리스트 dictionary로 변환되어 넘어옴
    userInfo = user_read_db(user_id)
    #print(userInfo)
    if not userInfo:
        return jsonify({"error": "사용자 정보를 찾을 수 없습니다."}), 404

    data = userInfo[0]  # DB에서 첫 번째 사용자 데이터만 사용

    # 1. subscription_month 값 가공 + 구독금액 매핑
    payment_map = {
        1: "5만원",
        6: "7만원",
        12: "10만원"
    }

    # 1. subscription_month 값 가공
    #    DB에 숫자로 들어온다고 가정 (1, 3, 6 등)
    if "subscription_month" in data:
        try:
            month_val = int(data["subscription_month"])
            # "개월" 표시
            data["subscription_month"] = f"{month_val}개월"
            # 구독금액 자동 설정
            data["subscription_payment"] = payment_map.get(month_val, data.get("subscription_payment", "—"))
        except (ValueError, TypeError):
            # 숫자가 아니거나 None인 경우 그대로 둠
            pass

    # 2. subscription_status 값 가공
    if data.get("subscription_status") == "active":
        data["subscription_status"] = "구독"
    else:
        data["subscription_status"] = "—"

    return jsonify(data)

#==========================================================
# 사용자 아이디 중복체크
@app.route('/api/user/dup_check', methods=['POST'])
def user_dup_check():
    data = request.get_json()
    # print(f"🔍data: {data}")
    userId = data.get("userId")
    print("📋 userId:", userId)

    # 테이블 보장
    #user_create_table()

    # 사용자 중복검색
    result = user_read_db(userId)
    print(result)
    if result:
        rtn_data = {
            'result': 'Fail',
            'message': ''
        }
    else:
        rtn_data = {
            'result': 'Success',
            'message': ''
        }
    print(rtn_data)

    return jsonify(rtn_data)

# 사용자 회원가입/수정/삭제/조회처리
@app.route('/api/user/crud', methods=['POST'])
def user_register_crud():
    data = request.get_json()
    print(f"🔍 /api/user/crud data: {data}")
    mode = data.get("mode")

    try:
        # 테이블 보장
        user_create_table()

        if mode == "C":
            # record 전체를 딕셔너리로 전달
            user_insert_record(data)
            rtn_message = "신규 입력이 완료되었습니다."

        elif mode == "U":
            user_update_record(data)
            rtn_message = "수정이 완료되었습니다."

        elif mode == "D":
            user_id = data.get("user_id")
            if not user_id:
                raise ValueError("삭제할 user_id가 없습니다.")
            user_delete_record(user_id)
            rtn_message = "삭제가 완료되었습니다."

        else:  # mode가 'R'이거나 지정되지 않은 경우 조회
            results = user_read_db(
                user_id=data.get("user_id", ""),
                userName=data.get("user_name", ""),
                nickName=data.get("nick_name", "")
            )
            return jsonify({
                "result": "Success",
                "message": "조회가 완료되었습니다.",
                "data": results
            })

        return jsonify({
            "result": "Success",
            "message": rtn_message
        })

    except Exception as e:
        # 오류 발생 시 status를 Fail로 반환
        return jsonify({
            "result": "Fail",
            "message": str(e)
        }), 500

# 사용자 회원가입 탈퇴처리
@app.route('/api/user/cancel', methods=['POST'])
def user_register_cancel():
    data = request.get_json()
    print(f"🔍 /api/user/cancel data: {data}")
    user_id = data.get("user_id")
    reason = data.get("reaseon")
    try:
        user_cancel_record(user_id, reason)

        return jsonify({
            "result": "Success",
            "message": "탈퇴가 완료되었습니다."
        })

    except Exception as e:
        # 오류 발생 시 status를 Fail로 반환
        return jsonify({
            "result": "Fail",
            "message": str(e)
        }), 500

@app.route('/api/users', methods=['GET'])
def get_users_data():
    searchTitle = request.args.get('searchTitle', '')   # 중개사 타이틀
    userName = request.args.get('dangiName')           # 중개사주소

    print(f"🔍 중개사: {searchTitle}, 사용자명: {userName}")

    data = user_read_db("", userName, "")

    print(data)

    return jsonify(data)

#==== 크롤링db에 법정동코드 테이를 목록가져오기 autocomplete용(국토부대체) ========
@app.route('/api/lawdcd/autocomplete')
def get_lawdcds_data():
    # 질의 파라미터
    q = request.args.get('locatadd_nm', '').strip()
    limit = request.args.get('limit', '').strip()
    try:
        limit = int(limit) if limit else 30   # 기본 30
    except ValueError:
        limit = 30

    # 로그
    print(f"🔍 법정동코드 검색어: {q}, limit={limit}")

    # 빈 검색어는 빈 리스트 반환
    if not q:
        return jsonify({"items": [], "count": 0})

    # DB 조회 (이미 구현해 두신 함수)
    results = search_lawd_by_name(q, limit=limit)  # List[{"lawd_cd","lawd_name"}]
    print(results)

    # JS에서 쓰던 키로 매핑하여 반환
    payload = {
        "items": [
            {
                "region_cd":  r["lawd_cd"],   # 기존 JS의 region_cd
                "locatadd_nm": r["lawd_name"] # 기존 JS의 locatadd_nm
            }
            for r in results
        ],
        "count": len(results)
    }
    return jsonify(payload)


#===== 네이버 아파트 매물 데이타 처리 =============
@app.route('/api/apt', methods=['GET'])
def get_apt_data():
    lawdCd = request.args.get('lawdCd', '')
    umdNm = request.args.get('umdNm', '')
    trade_type = request.args.get('trade_type', '')
    sale_year = request.args.get('saleYear', '')
    category = request.args.get('category')
    dangiName = request.args.get('dangiName')

    print(f"🔍 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 📅 매물 연도: {sale_year}, 🏠 카테고리: {category},")

    # data = apt_read_db(lawdCd, umdNm, trade_type, sale_year, category, dangiName)
    data = apt_mobile_read_db(lawdCd, umdNm, sale_year, category, dangiName)
    # 2) 매매 항목마다 전세 max/min 호출해서 필드 추가
    for item in data:
        if item.get("trade_type") == "매매":
            # 3) 전세 max/min 가격을 가져옴
            jm = get_jeonse_min_max_mobile(
                lawdCd       = item.get("lawdCd", ""),
                umdNm        = item.get("umdNm", ""),
                article_name = item.get("article_name", ""),
                area1        = item.get("area1", "")
            )
            max_price = float(jm["max_price"])
            min_price = float(jm["min_price"])
            #print(f"🔍 {item.get('article_name', '')} - max_price: {max_price}, min_price: {min_price}")
            #print(f"{item.get('article_name', '')},{jm.get('max_price', '')},{jm.get('min_price', '')}")
            #
            item["jeonseMaxPrice"] = jm["max_price"]
            item["jeonseMinPrice"] = jm["min_price"]
            if max_price != 0 and min_price != 0:
                item["jeonseAvgPrice"] = (max_price + min_price) / 2
            else:
                item["jeonseAvgPrice"] = 0

    return jsonify(data)

#===== 아파트 데이타 처리(국토부실거래 검색) =============
@app.route('/api/apt/land_data', methods=['GET'])
def get_apt_land_data():

    # 종로구, 읍면동(창신동,숭인동, 종로1가, 인사동 등)
    lawd_cd = request.args.get('lawd_cd', '11110')
    # 법정동코드 테이블에서 조회(public_data.db lawd_code 테이블)
    res = get_lawd_by_code(lawd_cd + "00000")  # 법정동명(서울특별시 종로구)
    lawd_nm = res["lawd_name"]  # 서울특별시 종로구
    #lawd_nm = request.args.get('lawd_nm', '서울시')
    umd_nm = request.args.get('umd_nm', '창신동')
    #
    apt_nm = request.args.get('apt_nm', '')  # 단지명(선택)

    print(f"🔍 법정동코드: {lawd_cd}, 법정동명: {lawd_nm}, 읍면동명: {umd_nm}")

    print("\n########## 아파트 ##########")
    all_items = run_apt(lawd_cd, lawd_nm, umd_nm, apt_nm, verify=False)
    #
    # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    json_records = apt_items_to_json(all_items, lawd_cd)
    #print(json.dumps(json_records, ensure_ascii=False, indent=2))
    #
    print(f"\n[총 누적 건수: {len(all_items)}\n")

    return json_records

#===== 과거 아파트 실거래가 데이타 처리(부동산원데이타) =============
@app.route('/api/apt/pir_apt', methods=['GET'])
def get_apt_pir_data():
    apt_name = request.args.get('apt_name', '')
    size = request.args.get('size', '')

    print(f"🔍 아파트명: {apt_name}, 평형(크기): {size}")

    # past_apt에서 데이타를 가져옴
    data = fetch_apt_by_name_and_size(apt_name, size)
    print(data)
    if not data:
        return jsonify({"result": "Fail", "message": "해당 아파트의 시세 정보가 없습니다."})

    return jsonify(data)

# 인구 통계 데이타 처리
@app.route('/api/apt/population', methods=['GET'])
def get_public_population():
    """
    쿼리 파라미터:
      - stdg_cd:  법정동코드(시/군/구 등)       예) 4311000000
      - srch_fr_ym: 조회시작년월(YYYYMM)       예) 202507
      - srch_to_ym: 조회종료년월(YYYYMM)       예) 202507
      - lv: 1(광역시)/2(시군구)/3(읍면동)      예) 3
      - prefer_db: 'true'|'false' (기본 true)
      - service_key: 공공데이터포털 키(옵션; 미제공 시 환경변수/기본값 사용)
    응답:
      { "source": "DB|API", "count": n, "items": [...] }
    """

    print(request.args)

    # 기본 파라미터(없으면 이 값으로)
    # STDG_CD_DEFAULT = "4311000000"  # 법정동코드-청주시(4311000000)
    # SRCH_SGG_NM = "청주시"  # 시군구명 (선택, 빈 문자열이면 전체)
    SRCH_FR_YM_DEFAULT = prev_month_yyyymm()
    SRCH_TO_YM_DEFAULT = prev_month_yyyymm()
    #LV_DEFAULT = "3"  # 1:광역시, 2:시군구, 3:읍면동

    # 1) 파라미터 수집 (대소문자/스네이크-카멜 혼용 대응)
    stdg_cd    = request.args.get('stdg_cd')    or request.args.get('stdgCd')
    sgg_nm    = request.args.get('sgg_nm')    or request.args.get('sggNm')
    srch_fr_ym = request.args.get('srch_fr_ym') or request.args.get('srchFrYm')  or SRCH_FR_YM_DEFAULT
    srch_to_ym = request.args.get('srch_to_ym') or request.args.get('srchToYm')  or SRCH_TO_YM_DEFAULT
    lv         = request.args.get('lv')

    # 최신 시그니처(서비스키 받는 버전)
    rows_for_display, rows_source = get_population_rows(
        stdg_cd=stdg_cd,
        sgg_nm=sgg_nm,
        srch_fr_ym=srch_fr_ym,
        srch_to_ym=srch_to_ym,
        lv=lv,
        prefer_db=True,
    )

    # 합계 대상 필드
    NUM_FIELDS = [
        "totNmprCnt", "maleNmprCnt", "femlNmprCnt",
        "male0AgeNmprCnt", "male10AgeNmprCnt", "male20AgeNmprCnt", "male30AgeNmprCnt", "male40AgeNmprCnt",
        "male50AgeNmprCnt", "male60AgeNmprCnt", "male70AgeNmprCnt", "male80AgeNmprCnt", "male90AgeNmprCnt",
        "male100AgeNmprCnt",
        "feml0AgeNmprCnt", "feml10AgeNmprCnt", "feml20AgeNmprCnt", "feml30AgeNmprCnt", "feml40AgeNmprCnt",
        "feml50AgeNmprCnt", "feml60AgeNmprCnt", "feml70AgeNmprCnt", "feml80AgeNmprCnt", "feml90AgeNmprCnt",
        "feml100AgeNmprCnt",
    ]

    def _as_int(v):
        try:
            if v in (None, "", "null", "None"):
                return 0
            return int(str(v).replace(",", ""))
        except Exception:
            return 0

    display_rows = len(rows_for_display or [])

    # ── 청주시( sggNm 가 '청주시' 로 시작 ) 집계 대상 선택
    rows = rows_for_display or []
    cheongju_rows = [r for r in rows if str(r.get("sggNm", "")).startswith("청주시")]
    target_rows = cheongju_rows if cheongju_rows else rows  # 없으면 전체 합계

    # ── 합계 계산
    sums = {f: 0 for f in NUM_FIELDS}
    for r in target_rows:
        for f in NUM_FIELDS:
            sums[f] += _as_int(r.get(f, 0))

    tot_population = sums.get("totNmprCnt", 0)  # 총인구 합계

    # 로그(콘솔)
    print(f"\n=== Normalized items (all {display_rows}) — source: {rows_source} ===")
    #preview = (rows_for_display or [])[:2]
    # print(json.dumps(preview, ensure_ascii=False, indent=2))
    print(f"집계 기준: {'청주시' if cheongju_rows else '전체'} / tot_population={tot_population:,}")
    print(f"\n총 {display_rows}건 출력 (source: {rows_source})")

    # 3) 응답 JSON
    return jsonify({
        "source": rows_source,
        "count": display_rows,
        "sums": sums,  # ✅ 요구사항 1: 각 필드별 총합(청주시 기준)
        "items": rows_for_display or []
    }), 200


#===== 빌라 데이타 처리(국토부실거래 검색) =============
@app.route('/api/villa/land_data', methods=['GET'])
def get_villa_land_data():

    # 종로구, 읍면동(창신동,숭인동, 종로1가, 인사동 등)
    lawd_cd = request.args.get('lawd_cd', '11110')
    # 법정동코드 테이블에서 조회(public_data.db lawd_code 테이블)
    res = get_lawd_by_code(lawd_cd + "00000")  # 법정동명(서울특별시 종로구)
    lawd_nm = res["lawd_name"]  # 서울특별시 종로구
    #lawd_nm = request.args.get('lawd_nm', '서울시')
    umd_nm = request.args.get('umd_nm', '창신동')

    print(f"🔍 법정동코드: {lawd_cd}, 법정동명: {lawd_nm}, 읍면동명: {umd_nm}")

    print("\n########## 빌라(연립/다세대) ##########")
    all_items = run_villa(lawd_cd, lawd_nm, umd_nm, verify=False)
    #
    # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    json_records = villa_items_to_json(all_items, lawd_cd)
    print(json.dumps(json_records, ensure_ascii=False, indent=2))
    #
    print(f"\n[총 누적 건수: {len(all_items)}\n")

    return json_records

#===== 상가 데이타 처리 =============
@app.route('/api/sanga', methods=['GET'])
def get_sanga_data():
    lawdCd = request.args.get('lawdCd', '')
    umdNm = request.args.get('umdNm', '')
    trade_type = request.args.get('trade_type', '')
    sale_year = request.args.get('saleYear', '')
    category = request.args.get('category')
    dangiName = request.args.get('dangiName')

    print(f"🔍 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 📅 매물 연도: {sale_year}, 🏠 카테고리: {category},")

    # 기존 PC크롤링 데이타 가져오기
    #data = sanga_read_db(lawdCd, umdNm, trade_type, sale_year, category, dangiName)
    # 신규 모바일크롤링 데이타 가져오기
    data = sanga_mobile_read_db(lawdCd, umdNm, trade_type, sale_year, category, dangiName)
    #print(json.dumps(data, ensure_ascii=False, indent=2))

    return jsonify(data)

#===== 상가 국토부실거래 검색
@app.route('/api/sanga/land_data', methods=['GET'])
def get_sanga_land_data():

    # 종로구, 읍면동(창신동,숭인동, 종로1가, 인사동 등)
    lawd_cd = request.args.get('lawd_cd', '11110')
    # 법정동코드 테이블에서 조회(public_data.db lawd_code 테이블)
    res = get_lawd_by_code(lawd_cd + "00000")  # 법정동명(서울특별시 종로구)
    lawd_nm = res["lawd_name"]  # 서울특별시 종로구
    #lawd_nm = request.args.get('lawd_nm', '서울시')
    umd_nm = request.args.get('umd_nm', '창신동')

    print(f"🔍 법정동코드: {lawd_cd}, 법정동명: {lawd_nm}, 읍면동명: {umd_nm}")

    # # 1) DB 초기화(테이블 생성)
    # init_sanga_db()

    print("\n########## SANGA (비주거) ##########")
    all_items = run_sanga(lawd_cd, lawd_nm, umd_nm, verify=False)
    #
    # (1) all_items를 JSON 타입(리스트[딕셔너리])으로 변환하여
    json_records = sanga_items_to_json(all_items, lawd_cd)
    #print(json.dumps(json_records, ensure_ascii=False, indent=2))
    #
    print(f"\n[총 누적 건수: {len(all_items)}\n")

    return json_records

@app.route('/api/sanga/fav', methods=['PUT'])
def update_fav():
    data = request.get_json()
    print(f"🔍data: {data}")
    article_no = data.get("article_no")
    fav = data.get("fav")

    result = sanga_update_fav(article_no, fav)

    return jsonify(result)

#===== 경매 데이타 처리 =============
category_mappings = {
    "아파트": ["아파트"],
    "빌라": ["연립주택", "도시형생활주택", "다세대주택", "단독주택", "오피스텔(주거)"],
    "다가구": ["다가구주택", "상가주택"],
    "상업용외": ["근린상가", "근린생활시설", "오피스텔(상업)", "공장", "지식산업센터", "숙박시설", "의료시설", "목욕탕", "종교시설", "창고시설"]
}

@app.route('/api/auction/categories', methods=['GET'])
def get_auction_categories():
    # "빌라"와 "근린상가"의 맨 앞에 "전체" 추가
    categoryOptions = {
        key: (["전체"] + values if key in ["빌라", "근린상가"] else values)
        for key, values in category_mappings.items()
    }
    json_data = json.dumps(categoryOptions, ensure_ascii=False, indent=4)
    print(json_data)
    return json_data

@app.route('/api/auction', methods=['GET'])
def get_auction_data():
    # SQLite DB(auction_data.db)를 참조하여 데이터 읽기
    lawdCd = request.args.get('lawdCd', '')
    umdNm = request.args.get('umdNm', '')
    year_range = request.args.get('yearRange', '')
    # 차후 NPL에서 호출방식과  상가검색및 확장상가 검색에서 호출하는 방식 재조정 요망(상업용외,  그냥 근린상가와 근린생활시설 만 경우)
    main_category = request.args.get('mainCategory', '')
    #category = request.args.get('category')
    dangiName = request.args.get('dangiName', '')

    # print(
    #     f"DB - 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 매각 년치: {year_range}, 메인 카테고리: {main_category}")

    categories = []
    if main_category != '':
        if (main_category == "근린상가"):
            # 상가검색에서 근린상가 선택시
            categories = ["근린상가", "근린생활시설"]
        else:
            categories = category_mappings[main_category]

    print(f"DB - 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 매각 년치: {year_range}, 메인 카테고리: {main_category}, 필터 카테고리: {categories}")

    # 데이타 가져오기
    data = auction_read_db(lawdCd, umdNm, year_range, categories, dangiName)
    print(data)

    return jsonify(data)


#===== realtor(중개사) 데이타 처리 =============
@app.route('/api/realtor', methods=['GET'])
def get_realtordata():
    lawdCd = request.args.get('lawdCd', '')
    selType = request.args.get('selType', '')
    searchTitle = request.args.get('searchTitle', '')   # 중개사 타이틀
    dangiName = request.args.get('dangiName')           # 중개사주소

    print(f"🔍 법정동코드: {lawdCd}, 중개사: {searchTitle}, 중개사주소: {dangiName}")

    data = realtor_read_db(lawdCd, selType, searchTitle, dangiName)

    print(data)

    return jsonify(data)

MAP_API_KEY = "644F5AF8-9BF1-39DE-A097-22CACA23352F"
@app.route('/api/geocode')
def geocode():
    addr = request.args.get('address','')
    params = {
        "service":"address",
        "request":"getcoord",
        "format":"json",
        "crs":"epsg:4326",
        "type":"parcel",
        "address":addr,
        "key":MAP_API_KEY
    }
    r = requests.get("https://api.vworld.kr/req/address", params=params, timeout=5)
    data = r.json()
    return jsonify(data)


#===== NPL(부실채권투자) 데이타 처리 =============
@app.route('/api/npl/categories', methods=['GET'])
def get_npl_categories():
    # 바로 JSON으로 응답
    return jsonify(category_mappings)

@app.route('/api/npl/region_categories', methods=['GET'])
def get_npl_region_categories():
    #
    category = request.args.get('category', '') # 지역(region), 시군구명(sggNm)
    sel_code = request.args.get('sel_code', '')
    parent_sel_code = request.args.get('parent_sel_code', '')

    print('category: ' + category, sel_code, parent_sel_code)

    json_data = query_npl_region_hierarchy(category, sel_code, parent_sel_code)
    print("Region query 결과:")
    print(json.dumps(json_data, ensure_ascii=False, indent=2))

    return json_data

@app.route('/api/npl', methods=['GET'])
def get_npl_data():
    # SQLite DB(auction_data.db)를 참조하여 데이터 읽기
    lawdCd = request.args.get('lawdCd', '')
    region = request.args.get('region', '')
    sggNm = request.args.get('sggNm', '')
    umdNm = request.args.get('umdNm', '')
    mainCategory = request.args.get('mainCategory', '')
    subCategory = request.args.get('subCategory', '')
    opposabilityStatus = request.args.get('opposabilityStatus')           # 임차권포함여부: 전체(all), 포함(Y), 안함(N)
    persionalStatus = request.args.get('persionalStatus')           # 임차권포함여부: 전체(all), 포함(Y), 안함(N)
    auctionApplicant = request.args.get('auctionApplicant', '')           # 경매신청자
    buildingPy = request.args.get('buildingPy', '')           # 건물평수

    if region == '전체':
        region = ''
    if sggNm == '전체':
        sggNm = ''
    if umdNm == '전체':
        umdNm = ''
    if opposabilityStatus == 'all':
        opposabilityStatus = ''

    print(
        f"DB - 법정동코드: {lawdCd}, 지역명: {region}, 시군구명: {sggNm}, 법정동명: {umdNm},  경매신청자: {auctionApplicant},  메인 카테고리: {mainCategory}, 서브 카테고리: {subCategory}, 임차권여부: {opposabilityStatus}")

    categories = []
    if mainCategory == '' and subCategory == '':
        categories = ''
    elif mainCategory != '' and subCategory == '':
        categories = category_mappings[mainCategory]
    else:
        # subCategory 단일값을 배열 형태로
        categories = [subCategory]

    # 데이타 읽기
    data = npl_read_db(lawdCd, region, sggNm, umdNm, categories, opposabilityStatus, persionalStatus, auctionApplicant, buildingPy)

    return jsonify(data)


#===== 점포 데이타 처리 =============
@app.route('/api/jumpo', methods=['GET'])
def get_jumpo_data():
    region = request.args.get('region', '')     # 지역(서울,경기..)
    section = request.args.get('section', '')   # 휴게음식점,
    upjong = request.args.get('upjong')         # 카페,음식점
    umdNm = request.args.get('umdNm', '')       # 읍면동명

    print(f"🔍 지역: {region},  섹션(분류): {section}, 업종: {upjong}, 법정동명: {umdNm}, ")

    data = jumpo_read_info_list_db(region, section, upjong, umdNm)

    return jsonify(data)


#== 네이버확장툴 접근
@app.route("/api/ext_tool/main", methods=["GET"])
def ext_tool_main():
    return render_template("extool_main_popup.html")

@app.route("/api/ext_tool", methods=["GET"])
# @token_required
def ext_tool():
    menu = request.args.get("menu", "")
    print(menu)

    # 시도 매핑 딕셔너리
    region_map = {
        "서울시": "서울특별시",
        "부산시": "부산특별시",
        "대구시": "대구광역시",
        "인천시": "인천광역시",
        "광주시": "광주광역시",
        "대전시": "대전광역시",
        "세종시": "세종특별자치시",
        "울산시": "울산광역시",
        "경기도": "경기도",
        "강원도": "강원특별자치도",
        "충청북도": "충청북도",
        "충청남도": "충청남도",
        "전라북도": "전라북도",
        "전라남도": "전라남도",
        "경상북도": "경상북도",
        "경상남도": "경상남도",
        "제주도": "제주특별자치도"
    }

    # "경기도,김포시,구래동"
    regions = request.args.get("regions", "").split(",")
    region = region_map.get(regions[0], regions[0])
    sigungu = regions[1]
    umdNm = regions[2]
    lawName = region + ' ' + sigungu + ' ' + umdNm

    # 법정동코드.txt를 읽음.. 차후 redis 메모리DB이용
    law_cd = extract_law_codes(region, sigungu, umdNm)
    print(regions)
    print(lawName, law_cd)

    #= 국토부 api_key
    api_key = request.args.get("api_key", "")
    print('api_key: ' + api_key)

    #===== 확장툴 접근
    # 아파트 국토부 실거래(내부 확장툴 접근)
    if menu == 'apt_real_deal':
        return render_template("extool_apt_real_deal.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 빌라 국토부 실거래(내부 확장툴 접근)
    if menu == 'villa_real_deal':
        return render_template("extool_villa_real_deal.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 상가 국토부 실거래(내부 확장툴 접근)
    if menu == 'sanga_real_deal':
        return render_template("extool_sanga_real_deal.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 아파트 네이버 매물 데이타 검색
    if menu == 'apt_search':
        return render_template("crawling_apt_search.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 상가 네이버 매물 데이타 검색
    if menu == 'sanga_search':
        return render_template("crawling_sanga_search.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 빌라 국토부 실거래 팝업 검색
    if menu == 'villa':
        return render_template("realdata_villa.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 아파트 국토부 실거래 팝업 검색
    if menu == 'apt':
        return render_template("realdata_apt.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # NPL 경매데이타 검색
    if menu == 'npl_search':
        return render_template("crawling_npl_search.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm)
    # 상가 수익율계산표
    if menu == 'sanga_profit':
        return render_template("profit_sanga_sheet.html")
    # 아파트,빌라 수익율계산표
    if menu == 'general_profit':
        return render_template("profit_general_sheet.html")
    if menu == 'realtor':
        return render_template("crawling_realtor_search.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm)
    if menu == 'form_down':
        return render_template("form_download.html")

@app.route("/api/ext_tool/map", methods=["GET"])
def ext_tool_map():
    return render_template("extool_map_popup.html")

@app.route('/api/sms_send', methods=['POST'])
def sms_send():
    # 제목,내용,발신전화번호목록,발신첨부파일목록
    # userid: loginId,
    # userpswd: loginPassword,
    # sendType: selectedSendType,   # kakao,sms
    # phoneNumbers: window.selectedPhoneNumbers,
    # title: messageTitle,
    # message: messageContent
    data = request.get_json()
    print(f"🔍data: {data}")
    sendType = data['sendType']
    if sendType == 'kakao':
        response_result = alimtalk_send(data)
        result = 'Success'
        errmsg = 'Success'
    elif sendType == 'naver_mms':
        # NAVER_MMS 발송 처리
        mms_result = send_mms_data(data)
        status     = mms_result['status']

        if status == '전체성공':
            result = 'Success'
            errmsg = '모든 MMS 전송에 성공했습니다.'
        elif status == '부분성공':
            result = 'PartialSuccess'
            errmsg = (
                f"{mms_result['success_count']}건 성공, "
                f"{mms_result['fail_count']}건 실패"
            )
        else:
            result = 'Failed'
            errmsg = '모두 MMS 전송에 실패했습니다.'
    else :
        # 일반문자 뿌리오 이용한 전송처리(크롬드라이버 이용)
        response_result = purio_sms_send(data)
        print(jsonify(response_result))
        # 예외 응답 처리: Response 객체가 튜플일 수 있으므로 분리
        if isinstance(response_result, tuple):
            response_data, status_code = response_result
            if status_code >= 400:
                print(f"Error sms_send: {response_data.get_json()}")
                result = 'Failed'
                errmsg = response_data.get_json().get('error')
            else:
                result = 'Success'

    # 로그인 성공 시 리다이렉트 URL을 JSON으로 반환
    #return jsonify({"result": result, "data": data, "errmsg": errmsg})
    return jsonify({"result": result, "errmsg": errmsg})

# 파일 업로드 설정
#app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}

# # 업로드 폴더가 없으면 생성
# os.makedirs(UPLOAD_FOLDER_PATH, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload_files', methods=['POST'])
def upload_files():
    # 요청에 파일이 포함되어 있는지 확인
    if 'files' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({'success': False, 'message': 'No selected files'}), 400

    saved_files = []
    for file in files:
        if file.filename == '':
            continue

        if file and allowed_file(file.filename):
            filename = file.filename
            # 1) 원본에서 확장자 추출
            ext = Path(filename).suffix.lower().lstrip('.')  # 예: 'jpg', 'jpeg', ''
            # 안전한 파일 이름 생성
            # safe = secure_filename(file.filename or "")
            print(f"파일이름: {filename}, 확장자: {ext}")
            # 고유한 파일 이름을 위해 타임스탬프 추가
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            print("unique_filename: " + unique_filename)
            save_path = os.path.join(UPLOAD_FOLDER_PATH, unique_filename)

            try:
                file.save(save_path)
                saved_files.append({
                    'original_name': filename,
                    'saved_name': unique_filename,
                    'size': os.path.getsize(save_path)
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'message': f'Error saving file {filename}: {str(e)}'
                }), 500
        #
        time.sleep(0.6)

    if len(saved_files) == 0:
        return jsonify({'success': False, 'message': 'No valid files uploaded'}), 400

    return jsonify({
        'success': True,
        'message': 'Files uploaded successfully',
        'file_count': len(saved_files),
        'files': saved_files
    })

# == 문서양식 다운로드 리스트 =============
@app.route('/api/form_list', methods=['GET'])
def form_list():
    try:
        # FORM_DIRECTORY 내 파일 목록 가져오기
        files = os.listdir(FORM_DIRECTORY)

        # 숨김파일(.DS_Store 등) 제거
        files = [f for f in files if not f.startswith('.')]

        # JSON 응답으로 리턴
        return jsonify({"files": files})
    except Exception as e:
        print("❌ Error reading FORM_DIRECTORY:", e)
        return jsonify({"error": "파일 목록을 불러올 수 없습니다."}), 500

@app.route('/api/form_down', methods=['GET'])
def form_download():
    # 쿼리 파라미터 form 값을 확인
    fileName = request.args.get('fileName')

    try:
        print(fileName)
        # 파일을 첨부파일로 전송 (다운로드 처리)
        return send_from_directory(FORM_DIRECTORY, fileName, as_attachment=True)
    except Exception as e:
        abort(404)

@app.route('/api/form_editor', methods=['GET'])
def form_editor():
    return render_template("form_editor.html")

@app.route("/api/form_editor/submit", methods=["POST"])
def form_submit():
    content = request.form.get("ir1")
    print("📋 받은 내용:", content)

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>제출 결과</title>
    </head>
    <body>
        <h2>📋 제출된 내용</h2>
        <div style="border:1px solid #ccc; padding:10px; margin-top:10px;">
            {content}
        </div>
        <hr>
        <a href="/api/form_editor">⏪ 다시 작성하기</a>
    </body>
    </html>
    """


#====== 투자가의삶님 아파트분석 ======
@app.route('/api/pastapt/categories', methods=['GET'])
def get_pastapt_categories():
    #
    category = request.args.get('category', '')
    sel_code = request.args.get('sel_code', '')
    parent_sel_code = request.args.get('parent_sel_code', '')

    json_data = query_region_hierarchy(category, sel_code, parent_sel_code)
    print("Region query 결과:")
    print(json.dumps(json_data, ensure_ascii=False, indent=2))

    return json_data

@app.route('/api/pastapt/apt_list', methods=['GET'])
def get_pastapt_apt_list():
    #
    regionNm = request.args.get('regionNm', '')
    sggNm = request.args.get('sggNm', '')
    umdNm = request.args.get('umdNm', '')
    houseCnt = request.args.get('houseCnt', '')

    results = fetch_grouped_apt_data(regionNm, sggNm, umdNm, houseCnt)
    # for row in results:
    #     print(row)

    return results

@app.route('/api/pastapt/apt_detail', methods=['GET'])
def get_pastapt_apt_detail():
    #
    apt_id = request.args.get('apt_id', '')

    results = fetch_apt_detail_data(apt_id)
    for row in results:
        print(row)

    return results

# 투자가의삶님 아파트 분석 팝업(연복리)
@app.route('/api/pastapt/interest', methods=['GET'])
def get_pastapt_apt_interest():
    #
    apt_name = request.args.get('apt_name', '')
    min_month = request.args.get('min_month', '')
    sale_rent_diff_amt = request.args.get('sale_rent_diff_amt', 0)
    print(sale_rent_diff_amt)
    #
    return render_template("pastdata_pop_interest.html", apt_name=apt_name, min_month=min_month, sale_rent_diff_amt=sale_rent_diff_amt)

@app.route('/api/pastapt/pir', methods=['GET'])
def get_pastapt_apt_pir():
    #
    apt_id = request.args.get('apt_id', '')
    region = request.args.get('region', '')
    sgg_nm = request.args.get('sgg_nm', '')
    salePrice = request.args.get('salePrice', '0')
    jeonsePrice = request.args.get('jeonsePrice', '0')
    jeonseRate = request.args.get('jeonseRate', '0')

    print(apt_id, region, sgg_nm, salePrice, jeonsePrice, jeonseRate)

    # PIR적용 아파트 상세 데이타 가져오기
    results = fetch_apt_detail_data(apt_id)
    # for row in results:
    #     print(row)
    #
    # 가장최근금리 가져오기
    last_interest_rate = fetch_latest_interest_rate()
    print("📈 최근 금리:", last_interest_rate)

    # 아파트 공급량가져오기
    address = region
    apt_complete_volumes = fetch_apt_complete_volume_by_address(address)
    print("🏢 아파트 공급량:", apt_complete_volumes)

    # 매매지수 가져오기
    last_sale_indexs = fetch_latest_sale_index_by_address(region, sgg_nm)
    last_sale_index = last_sale_indexs[0]
    print("📊 최근 매매지수:", last_sale_indexs, last_sale_index)

    # 근로자 월/년간 소득
    income_data = fetch_all_income_data()
    # for row in income_data:
    #     print(row)

    # 연도 → income_data 매핑 딕셔너리 생성
    income_map = {str(item['year']): item for item in income_data}
    #
    for item in results:
        year = item["month"][:4]
        income_info = income_map.get(year)

        if income_info:
            month_income = income_info["income"]
            year_income = income_info["year_income"]
        else:
            month_income = 0
            year_income = 0

        # sale_high 값에서 ',' 제거하고 정수로 변환
        sale_high_value = int(item["sale_high"].replace(",", ""))

        # PIR 계산 (year_income이 0이면 0 처리)
        pir = round(sale_high_value / year_income, 2) if year_income else 0

        # 값 추가 => 월수익, 년수익, PIR
        item["month_income"] = month_income
        item["year_income"] = year_income
        item["pir"] = pir

        # 매매호가,전세가, 전세율
        item["salePrice"]  = salePrice
        item["jeonsePrice"] = jeonsePrice
        item["jeonseRate"]  = jeonseRate

    # print(json.dumps(results, ensure_ascii=False, indent=2))
    #
    results.sort(key=lambda x: x["month"])  # 또는 int(x["month"][:4]) 도 가능

    return render_template("pastdata_pop_pir.html",
                                    apt_data=results,
                                    last_interest_rate=last_interest_rate,
                                    apt_complete_volumes=apt_complete_volumes,
                                    last_sale_index=last_sale_index)

@app.route('/api/pastapt/juso_popup', methods=['GET'])
def get_pastapt_juso_popup():
    #
    return render_template("pastapt_pop_juso_popup.html")

@app.route('/api/pastapt/juso_display', methods=['POST'])
def get_pastapt_juso_display():
    inputYn = request.form.get("inputYn")
    roadFullAddr = request.form.get("roadFullAddr")
    roadAddrPart1 = request.form.get("roadAddrPart1")
    roadAddrPart2 = request.form.get("roadAddrPart2")
    addrDetail = request.form.get("addrDetail")
    jibunAddr = request.form.get("jibunAddr")
    zipNo = request.form.get("zipNo")
    print("📋 받은 내용:", inputYn, zipNo)
    #
    return render_template("pastapt_pop_juso_display.html",
                           inputYn=inputYn,
                           roadFullAddr=roadFullAddr,
                           roadAddrPart1=roadAddrPart1,
                           roadAddrPart2=roadAddrPart2,
                           addrDetail=addrDetail,
                           jibunAddr=jibunAddr,
                           zipNo=zipNo)


@app.route('/api/pastapt/property/create', methods=['GET'])
def get_pastapt_property_create():
    roadFullAddr = request.args.get('roadFullAddr', '')
    print("📋 등기생성:", roadFullAddr)

    type = '건물'
    filename = roadFullAddr.strip().replace(' ', '_') + '.pdf'
    save_path = LEGAL_DIRECTORY + '/' + filename
    # 이미 생성된 파일이 있으면 바로 성공 응답
    if os.path.isfile(save_path):
        rtn_data = {
            'status': 'Success',
            'message': filename
        }
        print("파일 존재:", save_path)
        return jsonify(rtn_data)

    # 없으면 외부 API 호출하여 생성
    err = getIros1(roadFullAddr, type, save_path)
    print(err)
    if err:
        rtn_data = {
            'status': 'Fail',
            'message': err
        }
    else:
        rtn_data = {
            'status': 'Success',
            'message': filename
        }
    print(rtn_data)

    return jsonify(rtn_data)

@app.route('/api/pastapt/property/download', methods=['GET'])
def get_pastapt_property_download():
    filename = request.args.get('filename', '')
    file_path = os.path.join(LEGAL_DIRECTORY, filename)
    print("📋 다운로드:", filename)

    if not os.path.isfile(file_path):
        # 파일이 없으면 404 상태와 JSON 메시지 리턴
        return jsonify({'status': 'Fail', 'message': '파일이 존재하지 않습니다.'}), 404

    # 파일이 존재하면 첨부파일로 전송
    return send_from_directory(LEGAL_DIRECTORY, filename, as_attachment=True)

#===================================================
# 크롤링할 법정동코드 CRUD처리
# -----------------------
# 1) 목록 조회
# -----------------------
@app.get("/api/crawl_lawd_codes/admin")
def admin_lawd_codes():
    return render_template("crawling_lawd_codes_popup.html")

@app.get("/api/crawl_lawd_codes/list")
def list_lawd_codes():
    """
    쿼리파라미터:
      - trade_type: 'APT' | 'SG' (없으면 전체)
      - q: 검색어(법정동명 like)
    """
    trade_type = request.args.get("trade_type")  # 'APT', 'SG' or None
    q = request.args.get("q")
    print(f"검색어: {q}, trade_type: {trade_type}")

    json_rows = search_crawl_lawd_codes(
        lawd_cd=None,
        lawd_name=q,
        trade_type=trade_type if trade_type else None
    ) or []

    return jsonify({"items": json_rows})

# -----------------------
# 2) 저장(UPSERT)
# -----------------------
@app.post("/api/crawl_lawd_codes/insert")
def insert_lawd_code():
    """
    JSON Body:
      - lawd_cd: str (필수)
      - lawd_name: str (필수)
      - trade_type: 'APT' | 'SG' (기본 'SG')
    Header:
      - Authorization: Bearer <token>
    """
    # if not require_token():
    #     return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True) or {}
    lawd_cd = (data.get("lawd_cd") or "").strip()
    lawd_name = (data.get("lawd_name") or "").strip()
    trade_type = (data.get("trade_type") or "SG").strip().upper()
    print("법정동코드:", lawd_cd, "법정동명:", lawd_name, "trade_type:", trade_type)

    # if not lawd_cd or not lawd_name:
    #     return jsonify({"error": "법정동코드와 법정동명은 필수입니다."}), 400
    # if trade_type not in ("SG", "APT"):
    #     return jsonify({"error": "trade_type은 'SG' 또는 'APT'만 허용됩니다."}), 400

    try:
        # ✅ 저장 전에 (lawd_cd, trade_type)로 존재 여부 체크
        existing = get_crawl_lawd_code_by_cd_type(lawd_cd, trade_type)
        if existing:
            return jsonify({"error": f"법정동코드({lawd_cd})가 중복되어집니다. 확인해주세요."}), 400

        insert_crawl_lawd_code(lawd_cd, lawd_name, trade_type)
        return jsonify({"ok": True, "message": "저장(업서트) 되었습니다."})
    except Exception as e:
        return jsonify({"error": f"저장 실패: {e}"}), 500

# -----------------------
# 3) 삭제
# -----------------------
@app.delete("/api/crawl_lawd_codes/<int:record_id>")
def remove_lawd_code(record_id: int):
    """
    Header:
      - Authorization: Bearer <token>
    Path:
      - record_id: int (id로 단건 삭제)
    """
    print(f"삭제할 ID: {record_id}")
    try:
        deleted = delete_crawl_lawd_code_by_id(record_id)
        if deleted > 0:
            return jsonify({"ok": True, "deleted": deleted})
        else:
            return jsonify({"error": "대상 레코드를 찾을 수 없습니다."}), 404
    except Exception as e:
        return jsonify({"error": f"삭제 실패: {e}"}), 500


if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5002)
    # app.run(host='0.0.0.0', port=8081)
    # app.run(host='localhost', port=8080, debug=True)
    app.run(host='127.0.0.1', port=5000, debug=True)
