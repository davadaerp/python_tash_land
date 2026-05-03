import os
import gc
import time
import subprocess
from pathlib import Path

# ==============================
# 설정값
# ==============================
DIR_CONFIGS = {
    "/Users/wfight/Downloads/경매/교육동영상/상가투자/상남자": 0.12,
    "/Users/wfight/Downloads/경매/교육동영상/상가투자/보보스상가": 0.11,
    "/Users/wfight/Downloads/경매/교육동영상/상가투자/보보스토지": 0.11,
    "/Users/wfight/Downloads/경매/교육동영상/상가투자/지역예측": 0.11,
    "/Users/wfight/Downloads/경매/교육동영상/특수물건": 0.11,
}

OUTPUT_DIR_NAME = "converted_mp4"
OUTPUT_SUFFIX = "_compressed"
MIN_FILE_SIZE_MB = 500
RECURSIVE_SEARCH = True

FFPROBE_PATH = "/opt/homebrew/bin/ffprobe"
FFMPEG_PATH = "/opt/homebrew/bin/ffmpeg"


def bytes_to_mb(size_bytes):
    return round(size_bytes / (1024 * 1024), 2)


def bytes_to_gb(size_bytes):
    return round(size_bytes / (1024 * 1024 * 1024), 2)


def cleanup_memory():
    collected = gc.collect()
    print(f"[MEMORY] gc.collect() 완료 - 정리 객체 수: {collected}")


def ensure_output_dir(base_dir: str) -> str:
    output_dir = os.path.join(base_dir, OUTPUT_DIR_NAME)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def is_target_file(filepath: str) -> bool:
    if not filepath.lower().endswith(".mp4"):
        return False
    if not os.path.isfile(filepath):
        return False

    min_size_bytes = MIN_FILE_SIZE_MB * 1024 * 1024
    return os.path.getsize(filepath) > min_size_bytes


def get_video_info(filepath):
    cmd = [
        FFPROBE_PATH,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,bit_rate",
        "-of", "default=noprint_wrappers=1",
        filepath
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe 실행 실패:\n{result.stderr}")

    info = {}
    for line in result.stdout.split("\n"):
        if "=" in line:
            key, val = line.split("=", 1)
            info[key.strip()] = val.strip()

    file_size = os.path.getsize(filepath)

    return {
        "width": int(info.get("width", 0)),
        "height": int(info.get("height", 0)),
        "bitrate": int(info.get("bit_rate", 0)) if info.get("bit_rate") else None,
        "size": file_size
    }


def build_output_path(input_path: str, root_dir: str) -> str:
    root_dir = os.path.abspath(root_dir)
    input_path = os.path.abspath(input_path)

    output_root = ensure_output_dir(root_dir)

    relative_parent = os.path.relpath(os.path.dirname(input_path), root_dir)
    if relative_parent == ".":
        target_dir = output_root
    else:
        target_dir = os.path.join(output_root, relative_parent)
        os.makedirs(target_dir, exist_ok=True)

    base_name = os.path.basename(input_path)
    stem, ext = os.path.splitext(base_name)
    output_filename = f"{stem}{OUTPUT_SUFFIX}{ext}"
    return os.path.join(target_dir, output_filename)


def compress_video(input_path: str, root_dir: str, target_ratio: float):
    info = None
    result = None
    output_path = None

    try:
        info = get_video_info(input_path)

        print("\n" + "=" * 70)
        print(f"파일: {input_path}")
        print(f"해상도: {info['width']}x{info['height']}")
        print(f"원본 용량: {bytes_to_mb(info['size'])} MB ({bytes_to_gb(info['size'])} GB)")
        print(f"적용 압축율: {target_ratio}")

        if info["bitrate"] and info["bitrate"] > 0:
            target_bitrate = int(info["bitrate"] * target_ratio)
        else:
            target_bitrate = 800000

        print(f"목표 비트레이트: {target_bitrate}")

        output_path = build_output_path(input_path, root_dir)

        if os.path.exists(output_path):
            print("\n[SKIP] 이미 압축 파일 존재")
            print(f"원본: {input_path}")
            print(f"출력: {output_path}")
            return

        print(f"출력 파일: {output_path}")

        cmd = [
            FFMPEG_PATH,
            "-i", input_path,
            "-b:v", str(target_bitrate),
            "-bufsize", str(target_bitrate),
            "-vf", "scale=min(1280\\,iw):-2",
            "-c:a", "aac",
            "-b:a", "96k",
            "-y",
            output_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print("압축 실패")
            print(result.stderr)
            return

        if not os.path.exists(output_path):
            print("압축 실패: 출력 파일이 생성되지 않았습니다.")
            return

        new_size = os.path.getsize(output_path)

        print(f"압축 완료: {output_path}")
        print(f"압축 용량: {bytes_to_mb(new_size)} MB ({bytes_to_gb(new_size)} GB)")
        print(f"압축 비율: {round(new_size / info['size'], 4)}")

    except Exception as e:
        print(f"처리 실패: {input_path}")
        print(f"에러: {e}")

    finally:
        del info
        del result
        del output_path
        cleanup_memory()
        time.sleep(1)


def iter_target_files(root_dir: str):
    if RECURSIVE_SEARCH:
        for current_root, _, files in os.walk(root_dir):
            if OUTPUT_DIR_NAME in Path(current_root).parts:
                continue

            for file_name in files:
                full_path = os.path.join(current_root, file_name)
                if is_target_file(full_path):
                    yield full_path
    else:
        for file_name in os.listdir(root_dir):
            full_path = os.path.join(root_dir, file_name)
            if is_target_file(full_path):
                yield full_path


def main():
    for input_dir, target_ratio in DIR_CONFIGS.items():
        if not os.path.isdir(input_dir):
            print(f"\n디렉토리 없음: {input_dir}")
            continue

        print("\n" + "#" * 80)
        print(f"대상 디렉토리 시작: {input_dir}")
        print(f"디렉토리 압축율: {target_ratio}")

        file_list = list(iter_target_files(input_dir))
        file_list.sort()

        found = False
        for file_path in file_list:
            found = True
            compress_video(file_path, input_dir, target_ratio)

        if not found:
            print("조건에 맞는 500MB 초과 mp4 파일이 없습니다.")


if __name__ == "__main__":
    main()