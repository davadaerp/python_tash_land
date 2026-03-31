#!/bin/zsh

# --- 설정 구간: 여기서 파일 리스트를 관리하세요 ---
SOURCE_DIR="landcore"
BUILD_DIR="landcore_ext"
ZIP_NAME="landcore_ext.zip"

# 1. login 디렉토리에서 복사할 파일들
LOGIN_FILES=("popup.js" "popup_kakao.js" "popup.html" "popup_kakao.html")

# 2. panel 디렉토리에서 복사할 파일들
PANEL_FILES=("panel.css" "panel.js" "panel.html")

# 3. tools 디렉토리에서 복사할 파일들
TOOLS_FILES=("guide.html" "memo.js" "memo.html")

# 4. 루트 디렉토리에서 복사할 파일들
ROOT_FILES=("manifest.json" "landcore.js" "landcore_panel.js" "background.js" "config.json")

# 5. 이 중 "난독화"를 적용할 파일명 (확장자 포함)
OBFUSCATE_LIST=("popup.js" "popup_kakao.js" "landcore.js" "landcore_panel.js" "memo.js")

# --------------------------------------------

echo "🚀 맞춤형 배포 프로세스를 시작합니다..."

# 초기화
rm -rf $BUILD_DIR
rm -f $ZIP_NAME
mkdir -p $BUILD_DIR/login
mkdir -p $BUILD_DIR/sidepanel
mkdir -p $BUILD_DIR/tools
mkdir -p $BUILD_DIR/img
mkdir -p $BUILD_DIR/libs

# A. 일반 디렉토리(img, libs) 전체 복사
echo "📁 img, libs 디렉토리 복사 중..."
cp -R $SOURCE_DIR/img/ $BUILD_DIR/img/ 2>/dev/null
cp -R $SOURCE_DIR/libs/ $BUILD_DIR/libs/ 2>/dev/null

# B. login 디렉토리 파일 처리
echo "🔒 login 디렉토리 선택 파일 처리 중..."
for target in "${LOGIN_FILES[@]}"; do
    src_path="$SOURCE_DIR/login/$target"
    dist_path="$BUILD_DIR/login/$target"

    if [[ -f "$src_path" ]]; then
        if [[ "${OBFUSCATE_LIST[*]}" =~ "$target" ]]; then
            javascript-obfuscator "$src_path" --output "$dist_path"
            echo "   [난독화] $target"
        else
            cp "$src_path" "$dist_path"
            echo "   [일반복사] $target"
        fi
    fi
done

# C. sidepanel 디렉토리 파일 처리
echo "🔒 sidepanel 디렉토리 선택 파일 처리 중..."
for target in "${PANEL_FILES[@]}"; do
    src_path="$SOURCE_DIR/sidepanel/$target"
    dist_path="$BUILD_DIR/sidepanel/$target"

    if [[ -f "$src_path" ]]; then
        if [[ "${OBFUSCATE_LIST[*]}" =~ "$target" ]]; then
            javascript-obfuscator "$src_path" --output "$dist_path"
            echo "   [난독화] $target"
        else
            cp "$src_path" "$dist_path"
            echo "   [일반복사] $target"
        fi
    fi
done

# D. tools 디렉토리 파일 처리
echo "🔒 tools 디렉토리 선택 파일 처리 중..."
for target in "${TOOLS_FILES[@]}"; do
    src_path="$SOURCE_DIR/tools/$target"
    dist_path="$BUILD_DIR/tools/$target"

    if [[ -f "$src_path" ]]; then
        if [[ "${OBFUSCATE_LIST[*]}" =~ "$target" ]]; then
            javascript-obfuscator "$src_path" --output "$dist_path"
            echo "   [난독화] $target"
        else
            cp "$src_path" "$dist_path"
            echo "   [일반복사] $target"
        fi
    fi
done

# D. 루트 디렉토리 파일 처리
echo "📄 루트 디렉토리 선택 파일 처리 중..."
for target in "${ROOT_FILES[@]}"; do
    src_path="$SOURCE_DIR/$target"
    dist_path="$BUILD_DIR/$target"

    if [[ -f "$src_path" ]]; then
        if [[ "${OBFUSCATE_LIST[*]}" =~ "$target" ]]; then
            javascript-obfuscator "$src_path" --output "$dist_path"
            echo "   [난독화] $target"
        else
            cp "$src_path" "$dist_path"
            echo "   [일반복사] $target"
        fi
    fi
done

# D. 압축
echo "📦 배포 파일 압축 중..."
zip -r $ZIP_NAME $BUILD_DIR > /dev/null

echo "✅ 모든 작업이 완료되었습니다: $ZIP_NAME"