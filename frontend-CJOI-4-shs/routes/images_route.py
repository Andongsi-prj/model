from flask import Blueprint, jsonify
from kafka import KafkaConsumer
import json, time
from queue import Queue
import threading

images_route = Blueprint('images_route', __name__)

# Kafka Consumer 설정
consumer = KafkaConsumer(
    'repair_topic',  # Topic 이름 (프로듀서와 동일한 토픽 사용)
    bootstrap_servers=['192.168.0.163:9092'],  # Kafka 브로커 주소
    auto_offset_reset='earliest',  # 처음부터 메시지 읽기
    enable_auto_commit=True,  # 자동 오프셋 커밋
    group_id='image_consumer_group',  # Consumer 그룹 ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # JSON 역직렬화
)

# 메시지를 저장할 큐 생성 (FIFO)
message_queue = Queue()

def consume_kafka_messages():
    while True:
        try:
            for message in consumer:
                data = message.value
                plt_number = data.get('plt_number')
                encoded_image = data.get('encoded_image')
                print(plt_number)
                if encoded_image:
                    message_queue.put({
                        "plt_number": plt_number,
                        "encoded_image": f"data:image/png;base64,{encoded_image}"
                    })
        except Exception as e:
            print(f"Error in consumer thread: {e}")
            time.sleep(1)
        else:
            print("Kafka consumer is running and consuming messages.")


# Kafka Consumer를 별도의 스레드에서 실행
threading.Thread(target=consume_kafka_messages, daemon=True).start()

@images_route.route('/', methods=['POST'])
def get_images():
    timeout = 5  # 최대 대기 시간 (초)
    start_time = time.time()

    while message_queue.empty():
        if time.time() - start_time > timeout:
            return jsonify({'message': 'No images available yet.'}), 404
        time.sleep(0.1)  # 잠시 대기

    next_message = message_queue.get()
    return jsonify(next_message), 200