from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import io
from PIL import Image
import cv2
import numpy as np
from ultralytics import YOLO
import traceback
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 인스턴스 생성
main = FastAPI()

# YOLOv8 모델 로드
model = YOLO("best.pt")
labels = model.names  # YOLO 모델에서 클래스 이름 가져오기

# 입력 데이터 스키마 정의
class ImageData(BaseModel):
    image_base64: str

# base64 문자열을 OpenCV 이미지로 변환하는 함수
def decode_base64_to_image(base64_str: str) -> np.ndarray:
    try:
        image_data = base64.b64decode(base64_str)
        pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

# OpenCV 이미지를 base64 문자열로 변환하는 함수
def encode_image_to_base64(image: np.ndarray) -> str:
    _, buffer = cv2.imencode('.jpg', image)
    return base64.b64encode(buffer).decode("utf-8")

# 바운딩 박스를 그리는 함수
def draw_bounding_boxes(frame: np.ndarray, results, confidence_threshold=50):
    frame_with_boxes = frame.copy()
    detected_objects = results[0].boxes

    for box in detected_objects:
        confidence = float(box.conf[0]) * 100
        if confidence < confidence_threshold:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        class_id = int(box.cls[0])
        class_label = labels.get(class_id, "Unknown")

        color = (0, 255, 0) if class_label == 'Normal' else (0, 0, 255)
        cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), color, 2)
    return frame_with_boxes

@main.post("/predict/")
async def predict(data: ImageData):
    try:
        # Step 1: Base64 디코딩 및 이미지 전처리
        frame = decode_base64_to_image(data.image_base64)

        # Step 2: YOLO 추론 수행 (신뢰도 임계값 통일)
        results = model(frame, conf=0.7)

        # Step 3: 바운딩 박스 그리기
        frame_with_boxes = draw_bounding_boxes(frame, results)

        # Step 4: 바운딩 박스가 그려진 이미지를 Base64로 인코딩
        annotated_image_base64 = encode_image_to_base64(frame_with_boxes)

        # Step 5: 예측된 라벨과 신뢰도 추출
        predictions = []
        for box in results[0].boxes:
            confidence = float(box.conf[0]) * 100
            if confidence < 70:  # 신뢰도 필터링 통일
                continue

            class_id = int(box.cls[0])
            predictions.append({
                "label": labels.get(class_id, "Unknown"),
                "confidence": confidence,
                "bbox": [int(coord) for coord in box.xyxy[0].tolist()]
            })

        return {
            "annotated_image": annotated_image_base64,
            "predictions": predictions,
        }
    except Exception as e:
        error_message = f"Error: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_message)

main.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000"],  # Flask 도메인 명시
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)