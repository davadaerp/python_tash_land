#!/bin/bash

# ==========================================================
# 1. 설정 구간
# ==========================================================
BASE_DIR="/home/ubuntu/tash"
TARGET_DATA_DIRS=(
    "$BASE_DIR/auction"
    "$BASE_DIR/crawling"
    "$BASE_DIR/master"
    "$BASE_DIR/npl"
    "$BASE_DIR/pastapt"
    "$BASE_DIR/pubdata"
    "$BASE_DIR/realtor"
)

BACKUP_ROOT="$BASE_DIR/dbbackup"
DATE=$(date +%Y-%m-%d)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d) # 어제 날짜 계산 (Ubuntu/Linux 기준)

echo "🚀 멀티 디렉토리 안전 백업 프로세스를 시작합니다..."
[ ! -d "$BACKUP_ROOT" ] && mkdir -p "$BACKUP_ROOT"

# 2. 루프를 돌며 각 디렉토리 처리
for TARGET_DIR in "${TARGET_DATA_DIRS[@]}"; do

	# 디렉토리 존재 여부 확인
    if [ ! -d "$TARGET_DIR" ]; then
        echo "⚠️  경고: '$TARGET_DIR' 디렉토리가 존재하지 않아 건너뜜."
        continue
    fi

	# 디렉토리명 추출 (예: ./landcore -> landcore)
    DIR_NAME=$(basename "$TARGET_DIR")
    SAVE_PATH="$BACKUP_ROOT/$DIR_NAME"
    echo "📂 [$DIR_NAME] 처리 중..."
    [ ! -d "$SAVE_PATH" ] && mkdir -p "$SAVE_PATH"

    # ----------------------------------------------------------
    # 2. [수정] 오늘과 어제 날짜 파일 제외하고 모두 삭제
    # ----------------------------------------------------------
    # 해당 폴더 내의 .db 파일들 중 오늘($DATE)과 어제($YESTERDAY) 문자열이 없는 파일 삭제
    # xargs를 사용하여 안전하게 삭제 처리
    find "$SAVE_PATH" -name "*.db" -type f ! -name "*$DATE.db" ! -name "*$YESTERDAY.db" -delete

    # ----------------------------------------------------------
    # 3. [개선] SQLite 안전 백업 (disk I/O error 방지)
    # ----------------------------------------------------------
    found_count=0
    for file in "$TARGET_DIR"/*.db; do
        if [ -f "$file" ]; then
            pure_filename=$(basename "$file" .db)
            TARGET_FILE="$SAVE_PATH/${pure_filename}_${DATE}.db"
            
            # 단순 cp 대신 sqlite3 전용 백업 명령 사용 (추천)
            # sqlite3가 설치되어 있지 않다면 cp "$file" "$TARGET_FILE" 로 대체 가능
            if command -v sqlite3 >/dev/null 2>&1; then
                sqlite3 "$file" ".timeout 30000" ".backup '$TARGET_FILE'"
            else
                cp "$file" "$TARGET_FILE"
            fi
            
            found_count=$((found_count + 1))
        fi
    done

    if [ $found_count -gt 0 ]; then
        echo "   ✅ $found_count 개의 파일 안전 백업 및 정리 완료 (오늘/어제 데이터 유지)"
    else
        echo "   ℹ️  백업할 .db 파일이 없습니다."
    fi
done

echo "=========================================="
echo "🎉 모든 백업 및 데이터 정리가 종료되었습니다."