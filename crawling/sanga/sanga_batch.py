import time
from datetime import datetime, timedelta
import sanga_crawling  # sanga_crawling.py 파일에 main() 함수가 정의되어 있어야 함

def wait_until_target(target_datetime):
    """현재 시각과 target_datetime 사이의 시간을 기다린 후 반환"""
    while True:
        now = datetime.now()
        if now >= target_datetime:
            break
        remaining = target_datetime - now
        print(f"대기 중... 남은 시간: {remaining}")
        time.sleep(60)  # 1분마다 확인


def main_loop(target_hour, target_minute):
    while True:
        now = datetime.now()
        # 오늘 목표 시각 계산
        next_run = datetime(now.year, now.month, now.day, target_hour, target_minute)
        # 만약 현재 시간이 이미 목표 시각보다 늦으면 내일로 설정
        if now >= next_run:
            next_run += timedelta(days=1)
        print("다음 실행 시각:", next_run)

        wait_until_target(next_run)

        print("실행 시작:", datetime.now())
        try:
            sanga_crawling.main()  # sanga_crawling.py에 정의된 main() 함수 실행
        except Exception as e:
            print("배치 작업 실행 중 오류 발생:", e)
        print("실행 종료:", datetime.now())

        # 배치 작업이 끝나면, 바로 다음 반복으로 넘어가서 다음 실행 시각을 계산함.

if __name__ == '__main__':
    # 예시: 매일 오전 2시 0분에 실행
    main_loop(9, 53)
