# common/kakao_client.py
from kakao.kakao_api_utils import KakaoAPI, TOKENS
# 필요 시 토큰 스토어를 KakaoAPI에 주입할 수 있으면 여기서 주입
# from common.token_client import TOKENS

# KakaoAPI 내부가 외부 스토어 주입을 지원한다면:
# kakao = KakaoAPI(token_store=TOKENS)
# 미지원이라면 단순 인스턴스만:
kakao = KakaoAPI()