import subprocess
import schedule
import time


def batch_task():
    print("Batch processing started...")
    # 처리 로직
    script_name = "네이버부동산_PARAM.py"

    # 현재 스케줄된 시간을 arg1으로 사용
    pgno = str(schedule.get_jobs()[0].next_run.second)  # 스케줄 시간(초 단위) 추출, 페이지번호
    arg2 = "62"  # 지역코드

    subprocess.run(["python", script_name, pgno, arg2])

    print("Batch processing completed.")


# 매 5초마다 실행
schedule.every(5).seconds.do(batch_task)

while True:
    schedule.run_pending()
    time.sleep(1)
