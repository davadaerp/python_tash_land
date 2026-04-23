from flask import Blueprint, render_template, request, redirect, jsonify, url_for

from .trial_db_utils import (
    trial_create_table,
    trial_insert_single,
    trial_select_by_email_or_phone,
)

from .review_db_utils import (
    DEFAULT_PAGE_SIZE,
    review_create_table,
    review_read_list,
    review_select_single,
    review_insert_single,
    review_update_single,
    review_delete_single,
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
}

ADMIN_HOSTS = {
    "admin.landcore.co.kr",
}


def is_landing_host():
    host = (request.host or "").lower().split(":")[0]
    print("DEBUG host:", host)
    return host in LANDING_HOSTS

def is_admin_host():
    host = (request.host or "").lower().split(":")[0]
    return host in ADMIN_HOSTS

@landing_bp.route("/", methods=["GET"])
def landing_index():
    if not is_landing_host():
        return render_template("login.html")
    return render_template("landing/index.html")

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

    return jsonify({
        "result": "Success",
        "message": "무료체험 요청이 접수되었습니다.",
        "item": item
    })

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

        if not writer or not title or not content:
            return jsonify({
                "result": "Fail",
                "message": "작성자, 제목, 내용은 필수입니다."
            }), 400

        item = review_insert_single(writer, title, rating, content)

        if not item:
            return jsonify({
                "result": "Fail",
                "message": "후기 등록 중 오류가 발생했습니다."
            }), 500

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