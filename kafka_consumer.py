from kafka import KafkaConsumer
import json
import base64

# Kafka Consumer 설정
consumer = KafkaConsumer(
    'test_topic',  # Producer가 데이터를 보낸 Topic 이름
    bootstrap_servers=['192.168.0.163:9092'],  # Kafka 브로커 주소
    auto_offset_reset='earliest',  # 처음부터 메시지를 읽음
    enable_auto_commit=True,  # 자동으로 오프셋 커밋
    group_id='image_consumer_group',  # Consumer 그룹 ID
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))  # JSON 역직렬화
)

print("Kafka Consumer 시작")

# 메시지 수신 및 처리
for message in consumer:
    try:
        data = message.value  # 메시지 값 (JSON)
        plt_number = data['plt_number']  # 메시지에서 plt_number 추출
        encoded_image = data['encoded_image']  # Base64로 인코딩된 이미지 데이터 추출

        # 이미지 디코딩
        image_data = base64.b64decode(encoded_image)
        
        # 처리 결과 출력 (예: plt_number와 이미지 크기 출력)
        print(f"Received Image ID: {plt_number}, Image Size: {len(image_data)} bytes")
        
        # 추가 처리 로직을 여기에 작성 가능 (예: 파일 저장, 데이터베이스 저장 등)
    
    except Exception as e:
        print(f"Error processing message: {e}")
