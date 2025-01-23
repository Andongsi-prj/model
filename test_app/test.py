from flask import Flask, Response, jsonify, render_template
import cv2
import serial
import time
import numpy as np
import os

from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import load_img, img_to_array

# Flask 앱 생성
app = Flask(__name__)

# 아두이노 시리얼 포트 설정 (예: COM3 또는 /dev/ttyUSB0)
try:
    arduino = serial.Serial(port='COM5', baudrate=9600, timeout=1)
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    arduino = None

# AI 모델 로드 (정상/불량 분류 모델)
model = load_model('test_app/models/cnn_model.keras')

# 웹캠 초기화
camera_index = 1  # 카메라 인덱스 (필요 시 변경)
cap = cv2.VideoCapture(camera_index)

# 스크린샷 저장 경로
screenshot_dir = "test_app/static"
os.makedirs(screenshot_dir, exist_ok=True)  # 디렉토리가 없으면 생성

# 상태 저장 (전역 변수)
current_status = {"status": "No object detected", "confidence": "0.00%", "screenshot_url": ""}

# 프레임 스킵 설정 (예: 3프레임마다 처리)
frame_skip = 3


def preprocess_image(image_path, target_size=(258, 258)):
    """이미지를 로드하고 전처리하여 모델 입력 형식으로 변환"""
    img = load_img(image_path, color_mode='rgb', target_size=target_size)
    img_array = img_to_array(img) / 255.0  # 정규화 (0~1)
    return np.expand_dims(img_array, axis=0)  # 배치 차원 추가


def clean_up_screenshots(directory, max_files=10):
    """
    디렉토리에서 스크린샷 파일이 max_files 개수를 초과하면 오래된 파일부터 삭제합니다.
    :param directory: 디렉토리 경로
    :param max_files: 최대 허용 파일 개수
    """
    try:
        files = [
            (f, os.path.getmtime(os.path.join(directory, f)))
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
        ]
        files.sort(key=lambda x: x[1])  # 수정 시간 기준 정렬

        while len(files) > max_files:
            oldest_file = files.pop(0)[0]
            file_path = os.path.join(directory, oldest_file)
            try:
                os.remove(file_path)
                print(f"Deleted old screenshot: {file_path}")
            except Exception as e:
                print(f"Error deleting file {file_path}: {e}")

    except Exception as e:
        print(f"Error during cleanup: {e}")


def process_frame(frame):
    """모델 추론 및 상태 업데이트"""
    global current_status

    try:
        timestamp = int(time.time())
        new_screenshot_path = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")  # PNG 형식으로 저장

        cv2.imwrite(new_screenshot_path, frame)  # 스크린샷 저장

        clean_up_screenshots(screenshot_dir, max_files=10)  # 오래된 스크린샷 정리

        img_array = preprocess_image(new_screenshot_path)  # 이미지 전처리
        prediction = model.predict(img_array)              # 모델 추론

        labels = {0: '불량', 1: '정상'}                     # 클래스 라벨 정의
        class_idx = np.argmax(prediction)                  # 가장 높은 확률의 클래스 반환
        class_label = labels[class_idx]                    # 클래스 인덱스를 라벨로 변환
        confidence = prediction[0][class_idx] * 100         # Confidence 계산

        current_status["status"] = class_label             # 상태 업데이트
        current_status["confidence"] = f"{confidence:.2f}%"
        current_status["screenshot_url"] = f"/static/screenshot_{timestamp}.png"

    except Exception as e:
        print(f"Error processing frame: {e}")
        current_status["status"] = "Error"
        current_status["confidence"] = "N/A"
        current_status["screenshot_url"] = ""


def generate_frames():
    """실시간 카메라 프레임 스트리밍"""
    global cap

    frame_count = 0

    while True:
        try:
            success, frame = cap.read()
            if not success:
                print("Failed to read frame from camera. Reinitializing...")
                cap.release()
                cap = cv2.VideoCapture(camera_index)
                time.sleep(1)
                continue

            frame_count += 1

            if frame_count % frame_skip == 0 and arduino is not None:
                try:
                    arduino.write(b"READ\n")
                    time.sleep(0.1)
                    data = arduino.readline().decode('utf-8').strip()

                    if data == "DETECTED":
                        process_frame(frame)

                except Exception as e:
                    print(f"Error reading from Arduino: {e}")

            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

        except Exception as e:
            print(f"Error in video stream: {e}")
            continue


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/get_status', methods=['GET'])
def get_status():
    return jsonify(current_status)


if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5000)
    finally:
        if cap.isOpened():
            cap.release()
