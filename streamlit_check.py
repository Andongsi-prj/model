import streamlit as st
import requests
import base64
from PIL import Image
from io import BytesIO

# FastAPI 서버 URL 설정
FASTAPI_URL = "http://192.168.0.163:8000/predict/"

# Streamlit 앱 시작
st.title("YOLOv8 객체 탐지")
st.write("이미지를 업로드하면 객체 탐지 결과를 확인할 수 있습니다.")

# 이미지 업로드 위젯
uploaded_file = st.file_uploader("이미지를 업로드하세요", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 업로드된 파일을 Base64로 변환
    with st.spinner("이미지를 처리 중입니다..."):
        image_bytes = uploaded_file.read()
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # FastAPI로 요청 보내기
        response = requests.post(FASTAPI_URL, json={"image_base64": base64_image})

    if response.status_code == 200:
        # FastAPI에서 반환된 JSON 데이터 처리
        result = response.json()
        
        # Annotated image 처리
        annotated_image_base64 = result["annotated_image"]
        annotated_image_bytes = base64.b64decode(annotated_image_base64)
        annotated_image = Image.open(BytesIO(annotated_image_bytes))
        
        # Predictions 데이터 처리
        predictions = result["predictions"]

        # Annotated image 표시
        st.image(annotated_image, caption="탐지 결과", use_container_width=True)

        # Predictions 정보 표시
        st.subheader("탐지된 객체 정보")
        for prediction in predictions:
            label = prediction["label"]
            confidence = prediction["confidence"]
            bbox = prediction["bbox"]
            st.write(f"클래스: {label}, 신뢰도: {confidence:.2f}%, 바운딩 박스: {bbox}")
    else:
        st.error(f"FastAPI 오류: {response.status_code}, {response.text}")
