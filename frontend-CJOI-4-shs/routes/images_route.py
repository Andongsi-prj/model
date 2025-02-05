from flask import Blueprint, jsonify
from kafka import KafkaConsumer
import json, time
from queue import Queue
import threading

images_route = Blueprint('images_route', __name__)

# Kafka Consumer 설정
consumer = KafkaConsumer(
    'test11_topic',  # Topic 이름 (프로듀서와 동일한 토픽 사용)
    bootstrap_servers=['192.168.0.163:9092'],  # Kafka 브로커 주소
    auto_offset_reset='earliest',  # 처음부터 메시지 읽기
    enable_auto_commit=True,  # 자동 오프셋 커밋
    group_id='image_consumer_group',  # Consumer 그룹 ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # JSON 역직렬화
)

# 메시지를 저장할 큐 생성 (FIFO)
message_queue = Queue()

# Kafka 메시지를 소비하는 함수 (별도 스레드에서 실행)
def consume_kafka_messages():
    for message in consumer:
        data = message.value  # 메시지 값 (JSON)
        plt_number = data.get('plt_number')
        encoded_image = data.get('encoded_image')
        if encoded_image:
            # 메시지를 큐에 저장
            message_queue.put({
                "plt_number": plt_number,
                "encoded_image": f"data:image/png;base64,{encoded_image}"
            })

# Kafka Consumer를 별도의 스레드에서 실행
threading.Thread(target=consume_kafka_messages, daemon=True).start()

@images_route.route('/', methods=['POST'])
def get_images():
    """큐에서 메시지를 하나씩 가져와 JSON으로 반환"""
    if message_queue.empty():
        return jsonify({'message': 'No images available yet.'}), 404

    # 큐에서 메시지 가져오기 (FIFO 순서)
    next_message = message_queue.get()
    return jsonify(next_message), 200
