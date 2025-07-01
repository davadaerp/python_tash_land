import os
import json
import requests
from flask import Flask, jsonify, request, redirect, render_template, url_for, make_response, abort, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

from apt.apt_db_utils import apt_read_db
from jumpo.jumpo_db_utils import jumpo_read_info_list_db
from npl.npl_db_utils import npl_read_db, query_npl_region_hierarchy
#from naver.naver_login import naver_authorization, naver_callback
#
from sanga.sanga_db_utils import sanga_read_db, sanga_read_csv, sanga_update_fav, extract_law_codes
from auction.auction_db_utils import auction_read_db, auction_read_csv
from realtor.realtor_db_utils import realtor_read_db
from master.user_db_utils import user_insert_record, user_read_db, user_create_table, user_update_record, \
    user_delete_record
#
from sms.alim_talk import alimtalk_send
from sms.purio_sms import purio_sms_send
#
from pastapt.past_apt_complete_volume_db_utils import fetch_apt_complete_volume_by_address
from pastapt.past_interest_rate_db_utils import fetch_latest_interest_rate
from pastapt.past_apt_db_utils import query_region_hierarchy, fetch_apt_detail_data, fetch_grouped_apt_data
from pastapt.past_average_annual_income_db_utils import fetch_all_income_data

# auth.py에서 토큰 관련 함수 가져오기
from common.auth import token_required, create_access_token, extract_user_info_from_token
#
from config import TEMPLATES_NAME, FORM_DIRECTORY, LEGAL_DIRECTORY, SAVE_MODE

# common/commonResponse.py에 정의된 CommonResponse와 Result를 import
from common.commonResponse import CommonResponse
from legal_docs.legal_docs_down import getIros1, requestIros1

app = Flask(__name__, template_folder=TEMPLATES_NAME)

# CORS 전체 허용
CORS(app, resources={r"/api/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization"])

# 메모리 기반의 토큰 저장소 (유저ID:토큰)
active_tokens = {}

# 아마존 로드발라서 헬스체크처리
@app.route('/q/health/ready')
def health_ready():
    return "OK", 200

# /ts/는 아마존에서 설정시 적요한 네이밍룰
@app.route("/", methods=["GET"])
@app.route("/ts/", methods=["GET"])
def loginForm():
    return render_template("login.html")

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

@app.route("/api/main")
@token_required
def main(current_user):
    return render_template("main.html")

@app.route("/api/menu", methods=["GET"])
@token_required
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

#===== 사용자(회원) 데이타 처리 =============
@app.route('/api/user/register', methods=['GET'])
def user_register_form():
    return render_template("user_register.html")

@app.route('/api/user/mypage', methods=['GET'])
def user_mypage_form():
    userId = request.args.get('user_id', '')  # 사용자 ID
    access_token = request.cookies.get('access_token')
    # 리스트 dictionary로 변환되어 넘어옴
    userInfo = user_read_db(userId)
    print(userInfo)

    return render_template("user_mypage.html", userInfo=userInfo[0])

@app.route('/api/user/dup_check', methods=['POST'])
def user_dup_check():
    data = request.get_json()
    # print(f"🔍data: {data}")
    userId = data.get("userId")
    print("📋 userId:", userId)
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

@app.route('/api/users', methods=['GET'])
def get_users_data():
    searchTitle = request.args.get('searchTitle', '')   # 중개사 타이틀
    userName = request.args.get('dangiName')           # 중개사주소

    print(f"🔍 중개사: {searchTitle}, 사용자명: {userName}")

    data = user_read_db("", userName, "")

    print(data)

    return jsonify(data)

#===== 아파트 데이타 처리 =============
@app.route('/api/apt', methods=['GET'])
def get_apt_data():
    lawdCd = request.args.get('lawdCd', '')
    umdNm = request.args.get('umdNm', '')
    trade_type = request.args.get('trade_type', '')
    sale_year = request.args.get('saleYear', '')
    category = request.args.get('category')
    dangiName = request.args.get('dangiName')

    print(f"🔍 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 📅 매물 연도: {sale_year}, 🏠 카테고리: {category},")

    data = apt_read_db(lawdCd, umdNm, trade_type, sale_year, category, dangiName)

    return jsonify(data)

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

    if SAVE_MODE == "sqlite":
        data = sanga_read_db(lawdCd, umdNm, trade_type, sale_year, category, dangiName)
    else:
        data = sanga_read_csv(lawdCd, umdNm, trade_type, sale_year, category, dangiName)

    return jsonify(data)

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
    main_category = request.args.get('mainCategory', '')
    #category = request.args.get('category')
    dangiName = request.args.get('dangiName', '')

    print(
        f"DB - 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 매각 년치: {year_range}, 메인 카테고리: {main_category}")

    categories = []
    if main_category != '':
        categories = category_mappings[main_category]

    # if main_category in ["아파트", "빌라", "근린상가", "다가구"]:
    #     if not category:
    #         categories = category_mappings[main_category]
    #     else:
    #         categories = [c for c in category_mappings[main_category] if c in category]

    print(f"DB - 법정동코드: {lawdCd}, 법정동명: {umdNm}, 단지명: {dangiName}, 매각 년치: {year_range}, 메인 카테고리: {main_category}, 필터 카테고리: {categories}")

    # 데이타 저장
    if SAVE_MODE == "csv":
        data = auction_read_csv(lawdCd, umdNm, year_range, categories, dangiName)
    elif SAVE_MODE == "sqlite":
        data = auction_read_db(lawdCd, umdNm, year_range, categories, dangiName)
    else:
        print("알 수 없는 저장 방식입니다. SAVE_MODE 값을 'csv' 또는 'sqlite'로 설정해주세요.")

    return jsonify(data)


#===== realtor 데이타 처리 =============
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
    data = npl_read_db(lawdCd, region, sggNm, umdNm, categories, opposabilityStatus, persionalStatus, auctionApplicant)

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
    # 빌라 국토부 실거래(내부 확장툴 접근)
    if menu == 'villa_real_deal':
        return render_template("extool_villa_real_deal.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
    # 상가 국토부 실거래(내부 확장툴 접근)
    if menu == 'sanga_real_deal':
        return render_template("extool_sanga_real_deal.html", law_cd=law_cd, lawName=lawName, umdNm=umdNm, api_key=api_key)
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
    else :
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
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# # 업로드 폴더가 없으면 생성
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
            # 안전한 파일 이름 생성
            filename = secure_filename(file.filename)
            # 고유한 파일 이름을 위해 타임스탬프 추가
            unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.{filename}"
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

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

    if len(saved_files) == 0:
        return jsonify({'success': False, 'message': 'No valid files uploaded'}), 400

    return jsonify({
        'success': True,
        'message': 'Files uploaded successfully',
        'file_count': len(saved_files),
        'files': saved_files
    })

@app.route('/api/form_down', methods=['GET'])
def form_download():
    # 쿼리 파라미터 form 값을 확인
    form_type = request.args.get('form')

    if form_type == 'contents':
        filename = '명도확인서.docx'
    elif form_type == 'yieldcalc':
        filename = '수익율계산.xls'
    elif form_type == 'checklist':
        filename = '투자체크리스트.xls'
    else:
        # 잘못된 파라미터면 404 에러
        abort(404)

    try:
        print(form_type, filename)
        # 파일을 첨부파일로 전송 (다운로드 처리)
        return send_from_directory(FORM_DIRECTORY, filename, as_attachment=True)
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
    results = fetch_apt_detail_data(apt_id)
    print(apt_id, region)
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

        # 값 추가
        item["month_income"] = month_income
        item["year_income"] = year_income
        item["pir"] = pir

    # print(json.dumps(results, ensure_ascii=False, indent=2))
    #
    results.sort(key=lambda x: x["month"])  # 또는 int(x["month"][:4]) 도 가능

    return render_template("pastdata_pop_pir.html",
                                    apt_data=results,
                                    last_interest_rate=last_interest_rate,
                                    apt_complete_volumes=apt_complete_volumes)

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



if __name__ == '__main__':
    #app.run(host='0.0.0.0', port=5002)
    # app.run(host='0.0.0.0', port=8081)
    app.run(host='localhost', port=8080, debug=True)
