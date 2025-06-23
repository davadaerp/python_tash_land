# 연동사이트: https://apick.app/my_page
# 회원id: wfightgm69@gmail.com
# 패스워드: 몽셍이ap_0
# 연동api-key: 15663652ebe058a17b8114f00d5b7c1b
#
import requests

API_KEY = '15663652ebe058a17b8114f00d5b7c1b'

def getIros1(address, type, save_path):
    result = requestIros1(address, type)
    if not result:
        return "요청 실패 (네트워크 오류)"

    if 'data' not in result:
        return f"API 오류: {result.get('message', '알 수 없는 오류')}"

    data = result['data']

    if data.get('result') == 1:
        ic_id = data.get('ic_id')
        success = requestIrosDownload1(ic_id, save_path)
        return None if success else "파일 다운로드 실패"
    else:
        return data.get('error', '알 수 없는 오류')


def requestIros1(address, type):
    url = 'https://apick.app/rest/iros/1'
    headers = { 'CL_AUTH_KEY': API_KEY }
    data = { 'address': address, 'type': type }

    try:
        response = requests.post(url, headers=headers, data=data)
        print("응답내용:", response.text)  # 디버깅용
        return response.json()
    except Exception as e:
        print("요청 예외:", e)
        return False


def requestIrosDownload1(ic_id, save_path):
    # 요청 URL
    url = 'https://apick.app/rest/iros_download/1'

    # 헤더 설정
    headers = {
        'CL_AUTH_KEY': API_KEY,  # API 키 입력
    }

    # form-data 형식으로 파일 전송
    data = {
        'ic_id': ic_id
    }

    try:
        # POST 요청
        response = requests.post(url, headers=headers, data=data)
        if response.status_code != 200: return False

        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except:
        return False

# err = getIros1('경기도 김포시 운양동 반도유보라6차 903동 403호', '건물', '아파트.pdf')
# if (err):
#     print("발급실패 :", err)
# else:
#     print("발급성공")