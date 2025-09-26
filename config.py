# config.py
import os

BASE_PATH = "/Users/wfight/IdeaProjects/PythonProject/Auction"
#BASE_PATH = "/home/ubuntu/tash"

# 환경변수 SANGA_DB_PATH가 설정되어 있으면 사용하고, 없으면 기본 경로를 사용
MASTER_DB_PATH = os.environ.get("MASTER_DB_PATH", BASE_PATH + "/master")
APT_BASE_PATH = os.environ.get("APT_BASE_PATH", BASE_PATH + "/apt")
SANGA_BASE_PATH = os.environ.get("SANGA_DB_PATH", BASE_PATH + "/sanga")
AUCTION_DB_PATH = os.environ.get("AUCTION_DB_PATH", BASE_PATH + "/auction")
PUBLIC_BASE_PATH = os.environ.get("PUBLIC_BASE_PATH", BASE_PATH + "/pubdata")
#
NPL_DB_PATH = os.environ.get("AUCTION_DB_PATH", BASE_PATH + "/npl")
REALTOR_DB_PATH = os.environ.get("REALTOR_DB_PATH", BASE_PATH + "/realtor")
JUMPO_BASE_PATH = os.environ.get("JUMPO_BASE_PATH", BASE_PATH + "/jumpo")
#
PAST_APT_BASE_PATH = os.environ.get("PAST_APT_BASE_PATH", BASE_PATH + "/pastapt")
#
UPLOAD_FOLDER_PATH = os.environ.get("UPLOAD_FOLDER", BASE_PATH + "/uploads")

# SANGA_BASE_PATH 디렉토리 경로라면 마지막에 os.sep (예: '/')를 추가하여 안전하게 사용
if not MASTER_DB_PATH.endswith(os.sep):
    MASTER_DB_PATH += os.sep

if not APT_BASE_PATH.endswith(os.sep):
    APT_BASE_PATH += os.sep

if not SANGA_BASE_PATH.endswith(os.sep):
    SANGA_BASE_PATH += os.sep

if not NPL_DB_PATH.endswith(os.sep):
    NPL_DB_PATH += os.sep

if not AUCTION_DB_PATH.endswith(os.sep):
    AUCTION_DB_PATH += os.sep

if not JUMPO_BASE_PATH.endswith(os.sep):
    JUMPO_BASE_PATH += os.sep

if not SANGA_BASE_PATH.endswith(os.sep):
    SANGA_BASE_PATH += os.sep

if not PAST_APT_BASE_PATH.endswith(os.sep):
    PAST_APT_BASE_PATH += os.sep

# 파일 업로드 설정
if not UPLOAD_FOLDER_PATH.endswith(os.sep):
    UPLOAD_FOLDER_PATH += os.sep

TEMPLATES_NAME = "templates"

# 파일들이 위치한 디렉터리 경로 (예: 'downloads' 폴더)
FORM_DIRECTORY = 'forms'

# 법적서류(등기부등본) 다운로드 파일들이 위치한 디렉터리 경로
LEGAL_DIRECTORY = 'legal_docs'

# 저장 방식 선택: "csv" 또는 "sqlite"
SAVE_MODE = "sqlite"  # 원하는 방식으로 변경 가능 (예: "csv")

# JWT 서명에 사용할 비밀키
SECRET_KEY = '7987f7cb05cb1992'