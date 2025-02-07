import os
import requests
import sys

# 슬랙 API 토큰, 업로드할 채널 ID, 스레드 ts (스레드에 게시할 경우)를 환경에 맞게 설정하세요.
slack_token = "xoxb-8327137432257-8408801187235-HnctqtlymIumAPG3ccqqBRN3"
channel_id = "C089X7RJE0Y"
thread_ts = ""  # 스레드에 게시하지 않으려면 빈 문자열로 두세요.

# 전송할 이미지 파일의 경로
img_src = os.path.abspath('C:/Users/gh159/Desktop/project/model/frontend-CJOI-4-shs/defect_image.png')

# 기본 headers: JSON 타입과 Authorization 헤더 지정
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {slack_token}'
}

# 이미지 파일 읽기
try:
    with open(img_src, 'rb') as f:
        content = f.read()
except FileNotFoundError:
    print("파일을 찾을 수 없습니다:", img_src)
    sys.exit(1)

# 1. Slack의 files.getUploadURLExternal API를 호출해 업로드 URL과 file_id 받아오기
data = {
    "filename": "error.png",
    "length": len(content)  # 파일 크기 (바이트 단위)
}
# getUploadURLExternal은 application/x-www-form-urlencoded 타입을 사용합니다.
headers['Content-Type'] = 'application/x-www-form-urlencoded'
get_url_response = requests.post(
    url="https://slack.com/api/files.getUploadURLExternal",
    headers=headers,
    data=data
)
get_url_result = get_url_response.json()

if not get_url_result.get("ok", False):
    print("업로드 URL을 받지 못했습니다:", get_url_result)
    sys.exit(1)

# 응답에서 file_id와 업로드 URL 추출
file_id_info = {
    "file_id": get_url_result.get('file_id'),
    "upload_url": get_url_result.get('upload_url')
}

if not file_id_info.get("upload_url"):
    print("업로드 URL이 응답에 없습니다.")
    sys.exit(1)

# 2. 두 번째 요청: 추출한 upload_url로 실제 파일 전송
upload_response = requests.post(
    url=file_id_info.get('upload_url'),
    files={'file': content}
)
if upload_response.status_code != 200:
    print("파일 업로드에 실패했습니다:", upload_response.text)
    sys.exit(1)

# 3. 업로드 완료를 알리기 위해 files.completeUploadExternal API 호출
attachment = {
    "files": [{
        "id": file_id_info.get('file_id'),
        "title": "error.png"
    }],
    "channel_id": channel_id
}
if thread_ts:
    attachment["thread_ts"] = thread_ts

headers['Content-Type'] = 'application/json; charset=utf-8'
complete_response = requests.post(
    url="https://slack.com/api/files.completeUploadExternal",
    headers=headers,
    json=attachment
)
complete_result = complete_response.json()

if complete_result.get("ok"):
    print("이미지가 성공적으로 슬랙 채널에 업로드되었습니다!")
else:
    print("이미지 업로드에 실패했습니다:", complete_result)
