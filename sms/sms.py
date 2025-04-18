
from flask import jsonify


def sms_send(data):

    print(data)

    if (data == ""):
        return jsonify({'error': '로그인아이디/패스워드를 확인해주세요.'}), 400
        #return jsonify({'error': '뿌리오 충전금액을 확인해주세요.'}), 400

    return jsonify({'error': '로그인아이디/패스워드를 확인해주세요'}), 401

    # try:
    #     # Base64 디코딩하여 "username:password" 형태 복원
    #     decoded = base64.b64decode(credential).decode("utf-8")
    #     userid, password = decoded.split(":", 1)
    #     print("create_access_token:", userid, password)
    # except Exception as e:
    #     return jsonify({'error': 'Invalid credential format'}), 400
    #
    # # 사용자 인증
    # if userid in USER_CREDENTIALS and USER_CREDENTIALS[userid] == password:
    #     access_token = generate_token(userid, expiration_hours=1)
    #     return jsonify({'access_token': access_token, 'expires_in': 3600, 'userid': userid, })
    # else:
    #     return jsonify({'error': 'Invalid userid or password'}), 401
