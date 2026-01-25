#!/bin/bash

# ==========================================================
# 1. 설정 구간: 백업할 디렉토리 목록 및 상세 설명
# ==========================================================
# 각 디렉토리의 성격:
# - auction  : 법원 경매 물건 정보 및 입찰 데이터 저장
# - crawling : 네이버 부동산, 아실 등 외부 사이트 수집 스크립트 및 임시 데이터(법정동코드목록 존재함)
#              클라이언트에서 수집한 아파트및 상가데이타 저장
# - master   : 시스템 운영에 필요한 기본 코드성 데이터 및 마스터 DB
# - npl      : 부실채권(Non Performing Loan) 관련 분석 데이터
# - pastapt  : 아파트 과거 실거래가 및 히스토리 기록 데이터
# - pubdata  : 공공데이터포털 등에서 수집한 공공 API 결과물
# - realtor  : 공인중개사 정보 및 매물 등록 회원 관련 데이터

# 기본 작업 디렉토리 상수 설정
BASE_DIR="."
#BASE_DIR="/home/ubuntu/tash"

# 각 디렉토리의 성격 (상대 경로 대신 BASE_DIR 결합):
TARGET_DATA_DIRS=(
    "$BASE_DIR/auction"
    "$BASE_DIR/crawling"
    "$BASE_DIR/master"
    "$BASE_DIR/npl"
    "$BASE_DIR/pastapt"
    "$BASE_DIR/pubdata"
    "$BASE_DIR/realtor"
)

# BACKUP_ROOT: 모든 백업이 모일 최상위 디렉토리
BACKUP_ROOT="$BASE_DIR/dbbackup"

# DATE: 파일명에 사용할 날짜 (YYYY-MM-DD)
DATE=$(date +%Y-%m-%d)

# ----------------------------------------------------------
echo "🚀 멀티 디렉토리 DB 백업 프로세스를 시작합니다..."

# 백업 루트 디렉토리 생성
[ ! -d "$BACKUP_ROOT" ] && mkdir -p "$BACKUP_ROOT"

# 2. 루프를 돌며 각 디렉토리 처리
for TARGET_DIR in "${TARGET_DATA_DIRS[@]}"; do

    # 디렉토리 존재 여부 확인
    if [ ! -d "$TARGET_DIR" ]; then
        echo "⚠️  경고: '$TARGET_DIR' 디렉토리가 존재하지 않아 건너뜁니다."
        continue
    fi

    # 디렉토리명 추출 (예: ./landcore -> landcore)
    DIR_NAME=$(basename "$TARGET_DIR")
    SAVE_PATH="$BACKUP_ROOT/$DIR_NAME"

    echo "📂 [$DIR_NAME] 처리 중..."

    # 해당 디렉토리용 백업 폴더 생성
    [ ! -d "$SAVE_PATH" ] && mkdir -p "$SAVE_PATH"

    # 3. 해당 폴더 내 3일 지난 백업 파일 삭제
    find "$SAVE_PATH" -name "*.db" -type f -mtime +3 -exec rm -f {} \;

    # 4. .db 파일 찾아 복사 및 이름 변경
    found_count=0
    # 해당 디렉토리 바로 아래의 .db 파일만 대상 (하위까지 찾으려면 -maxdepth 제거)
    for file in "$TARGET_DIR"/*.db; do
        if [ -f "$file" ]; then
            pure_filename=$(basename "$file" .db)
            # 결과 예: dbbackup/apt/apt_data_2025-01-24.db
            cp "$file" "$SAVE_PATH/${pure_filename}_${DATE}.db"
            found_count=$((found_count + 1))
        fi
    done

    if [ $found_count -gt 0 ]; then
        echo "   ✅ $found_count 개의 파일 백업 완료"
    else
        echo "   ℹ️  백업할 .db 파일이 없습니다."
    fi

done

echo "=========================================="
echo "🎉 모든 백업 작업이 종료되었습니다."