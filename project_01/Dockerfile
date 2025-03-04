# 베이스 이미지로 Python 사용
FROM python:3.8-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 종속성 설치 (OpenCV 및 기타 라이브러리에 필요)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# YOLO 모델 파일 복사
COPY yolov11l_pipe.pt .

# 애플리케이션 코드 복사
COPY main.py .

# Uvicorn 실행 명령어 설정
CMD ["uvicorn", "main:main", "--host", "0.0.0.0", "--port", "8001"]
