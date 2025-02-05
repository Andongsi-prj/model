import base64
from flask import Blueprint, request, jsonify
from kafka import KafkaConsumer
import json
import threading

images_route = Blueprint('images_route', __name__)

# Kafka Consumer 설정
consumer = KafkaConsumer(
    'test_topic',  # Topic 이름
    bootstrap_servers=['192.168.0.163:9092'],  # Kafka 브로커 주소
    auto_offset_reset='earliest',  # 처음부터 메시지 읽기
    enable_auto_commit=True,  # 자동 오프셋 커밋
    group_id='image_consumer_group',  # Consumer 그룹 ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # JSON 역직렬화
)

# Kafka에서 받은 이미지를 저장할 리스트
received_images = []

def consume_kafka_messages():
    """Kafka 메시지 소비 및 이미지 데이터 저장"""
    global received_images
    for message in consumer:
        data = message.value  # 메시지 값 (JSON)
        plt_number = data.get('plt_number')
        encoded_image = data.get('encoded_image')
        if encoded_image:
            print(f"Received Image ID: {plt_number}")
            # Base64 인코딩된 이미지를 리스트에 추가
            received_images.append({
                "plt_number": plt_number,
                "encoded_image": f"data:image/png;base64,{encoded_image}"
            })

# Kafka Consumer를 별도의 스레드에서 실행
threading.Thread(target=consume_kafka_messages, daemon=True).start()

@images_route.route("/", methods=['POST'])
def get_images():
    """Kafka에서 받은 이미지를 POST 요청으로 반환"""
    if not received_images:
        return jsonify({"message": "No images available yet."}), 404

    # 요청에서 필요한 이미지 ID를 확인 (옵션)
    requested_id = request.json.get("plt_number") if request.json else None

    if requested_id:
        # 특정 ID의 이미지를 반환
        for image in received_images:
            if image["plt_number"] == requested_id:
                return jsonify(image), 200

        return jsonify({"message": "Image not found."}), 404

    # 요청된 ID가 없으면 가장 최근 이미지를 반환
    return jsonify(received_images[-1]), 200
