
# 유튜브 비공개 영상 다운로드 스크립트
#
# 브라우저에서 로그인한 상태의 YouTube 쿠키를 추출해야 합니다.
# 크롬에서 Get cookies.txt extension을 설치
# 해당 유튜브 비디오 페이지 열고 쿠키 저장
# cookies.txt로 저장
#
# pip install yt-dlp
# brew install ffmpeg

import os
import shutil
import subprocess
import yt_dlp

# optional: imageio-ffmpeg fallback
try:
    from imageio_ffmpeg import get_ffmpeg_exe
except ImportError:
    get_ffmpeg_exe = None


def find_ffmpeg():
    # 1) 시스템 설치된 ffmpeg
    ff = shutil.which('ffmpeg')
    if ff:
        return ff
    # 2) imageio-ffmpeg fallback
    if get_ffmpeg_exe:
        try:
            return get_ffmpeg_exe()
        except Exception:
            pass
    raise EnvironmentError(
        "ffmpeg 실행 파일을 찾을 수 없습니다.\n"
        "– macOS: brew install ffmpeg\n"
        "– Ubuntu/Debian: sudo apt install ffmpeg\n"
        "– Windows: https://ffmpeg.org/download.html 에서 설치 후 PATH에 추가\n"
    )


def download_video(url, save_path='./', cookies='cookies.txt'):
    ydl_opts = {
        #'format': 'best[ext=mp4][height<=720][vcodec^=avc1][acodec^=mp4a]',
        'format': 'best[ext=mp4][height<=1024][vcodec^=avc1][acodec^=mp4a]',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'cookiefile': cookies  # ← 쿠키파일로 인증
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def download_audio(url, save_path='./', cookies='cookies.txt', bitrate='192'):
    """
    1) yt-dlp 로 오디오(bestaudio) 다운로드 (.m4a/.webm 등)
    2) ffmpeg subprocess 로 mp3로 변환
    3) 중간파일 삭제
    """
    os.makedirs(save_path, exist_ok=True)
    ffmpeg_bin = find_ffmpeg()

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{save_path}/%(title)s.%(ext)s',
        'cookiefile': cookies,
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # info 뽑아서 파일명 준비
        info = ydl.extract_info(url, download=False)
        in_path = ydl.prepare_filename(info)
        # 실제 다운로드
        ydl.download([url])

    # mp3 출력경로
    base, _ = os.path.splitext(in_path)
    out_path = f'{base}.mp3'

    # ffmpeg 로 변환
    subprocess.run([
        ffmpeg_bin,
        '-y',            # overwrite
        '-i', in_path,   # input
        '-vn',           # video 없애고
        '-acodec', 'libmp3lame',
        '-ab', f'{bitrate}k',
        out_path
    ], check=True)

    # 중간 오디오 파일 제거
    os.remove(in_path)
    print(f"✅ saved MP3: {out_path}")

if __name__ == '__main__':

    # 다운로드 디렉터리 생성
    #os.makedirs('./downloads', exist_ok=True)

    # 예시: 인증이 필요한 비공개 영상일 때 cookies.txt 를 사용
    # 예시 URL (비공개일 경우, 접근 권한 있어야 함)
    #video_url = 'https://www.youtube.com/watch?v=tS19kK46Pmo'
    #video_url = 'https://www.youtube.com/watch?v=t-AHPemYAps'
    # 썸머릴레이-아파트 투자: https://www.youtube.com/watch?v=EnwryePl9E4
    # 썸머릴레이-공장 투자: https://www.youtube.com/watch?v=rVcqpAvNun4
    # 썸머릴레이-스카 투자: https://www.youtube.com/watch?v=HispvLz4OBo
    # 썸머릴레이-오피스 투자: https://youtu.be/c3IVy4cI_X0
    video_url = 'https://youtu.be/c3IVy4cI_X0'
    # 1) 동영상 다운로드
    download_video(video_url, save_path='./', cookies='cookies.txt')

    # 2) 오디오만 MP3로 추출
    #download_audio(video_url, save_path='./', cookies='cookies.txt', bitrate='192')