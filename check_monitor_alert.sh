# 다바다서버 모니터링(cpu및 oracle)후 임계치 초과시 중계서버(네이버 클라우드-www.landcore.co.kr)로 알림 전송
# 한글은 인코딩 문제로 인해 영문으로만 작성, 크론에 등록해서 주기적 모니터링 처리

#!/bin/bash
export LANG=C
export LC_ALL=C

# ==========================================
# [설정 영역]
# ==========================================
CPU_THRESHOLD=90
ORACLE_THRESHOLD=3

# 한글 대신 영문 이름 사용 (인코딩 문제 방지)
RECEIVER_PHONE="admin1:01022709085,admin2:01087529302"

RELAY_SERVER_URL="http://175.106.99.143:5000/api/sms_send"

# ==========================================
# JSON 이스케이프 함수 (", \, 개행, 탭, CR 처리)
# ==========================================
json_escape() {
    printf '%s' "$1" | tr -d '\r' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/\t/\\t/g' | tr '\n' ' '
}

# ==========================================
# 1. CPU 사용량 체크 (vmstat: 구형 CentOS 호환성 높음)
# ==========================================
# vmstat 1 2 의 두번째 줄 마지막에서 두번째 컬럼 = id(idle) (wa, st 유무와 무관하게 id는 NF-1 또는 NF-2)
# CentOS5 vmstat 컬럼: ... us sy id wa st  (st 포함)
CPU_IDLE=$(vmstat 1 2 | tail -1 | awk '{print $(NF-2)}')
case "$CPU_IDLE" in
    ''|*[!0-9]*) CPU_USAGE=0 ;;
    *) CPU_USAGE=$(( 100 - CPU_IDLE )) ;;
esac

# ==========================================
# 2. Oracle 'LOCAL=NO' 접속 세션 수 체크
# ==========================================
ORACLE_COUNT=$(ps -ef | grep -i "LOCAL=NO" | grep -v grep | wc -l)
ORACLE_COUNT=$(echo $ORACLE_COUNT)   # 공백 제거

# ==========================================
# 3. 현재 상태 출력
# ==========================================
CURRENT_TIME=$(date "+%Y-%m-%d %H:%M:%S")
echo "--------------------------------------------------------"
echo "[$CURRENT_TIME] Server resource monitoring result"
echo "--------------------------------------------------------"
echo " - CPU usage      : ${CPU_USAGE}% (threshold: ${CPU_THRESHOLD}%)"
echo " - Oracle sessions: ${ORACLE_COUNT} (threshold: ${ORACLE_THRESHOLD})"
echo "--------------------------------------------------------"

# ==========================================
# 4. 알림 메시지 조합
# ==========================================
ALERT_MSG=""

if [ "$CPU_USAGE" -ge "$CPU_THRESHOLD" ]; then
    ALERT_MSG="${ALERT_MSG}[WARNING] CPU usage is ${CPU_USAGE}% (Threshold: ${CPU_THRESHOLD}%). "
fi

if [ "$ORACLE_COUNT" -ge "$ORACLE_THRESHOLD" ]; then
    ALERT_MSG="${ALERT_MSG}[WARNING] Oracle sessions: ${ORACLE_COUNT} (Threshold: ${ORACLE_THRESHOLD}). "
fi

# ==========================================
# 5. 임계치 초과 시 중계 서버로 전송
# ==========================================
if [ -n "$ALERT_MSG" ]; then
    echo "[ALERT] Threshold exceeded. Sending to relay server..."

    TITLE="[SERVER ALERT] Resource Threshold Exceeded"
    CONTENT="[$CURRENT_TIME] $ALERT_MSG"

    E_PHONE=$(json_escape "$RECEIVER_PHONE")
    E_TITLE=$(json_escape "$TITLE")
    E_CONTENT=$(json_escape "$CONTENT")

    JSON_DATA="{\"sendType\": \"naver_sms\", \"phoneNumbers\": \"${E_PHONE}\", \"title\": \"${E_TITLE}\", \"message\": \"${E_CONTENT}\"}"

    # 디버깅: 실제로 전송되는 JSON 확인
    echo "[DEBUG] JSON: $JSON_DATA"

    RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$RELAY_SERVER_URL" \
        -H "Content-Type: application/json; charset=utf-8" \
        --data-binary "$JSON_DATA")

    RESPONSE_CODE=$(echo "$RESPONSE" | tail -1)
    RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

    echo "[RESULT] HTTP code: $RESPONSE_CODE"
    echo "[RESULT] Body     : $RESPONSE_BODY"
else
    echo "[OK] All resources are within normal range."
fi
echo "========================================================"