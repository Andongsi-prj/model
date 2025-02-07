import json
import pymysql
from kafka import KafkaConsumer
import time
import threading
from threading import Event


KAFKA_BROKER = '192.168.0.163:9092'
KAFKA_TOPIC_log = "logs"

stop_event = Event()


def get_db_connection():
    """SQL 설정"""
    return pymysql.connect(
        host='192.168.0.163',
        user='manufacture_user',
        password='andong1234',
        db='manufacture',
        charset='utf8mb4'
    )


def save_to_db(data):
    """Kafka 데이터를 SQL에 저장"""
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = "INSERT INTO log_info (plt_number, log_time, ctgr) VALUES (%s, %s, %s)"
            cursor.execute(query, (data['pltNumber'], data['timestamp'], data['message']))
            conn.commit()
        print(f"Data saved to DB: {data['pltNumber']}")
    except Exception as e:
        print(f"Error saving data to DB: {e}")
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()


def consume_messages():
    """Kafka 메시지 소비 및 DB 저장"""
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC_log,
            bootstrap_servers=[KAFKA_BROKER],
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            group_id='kafak_to_db_group',
            value_deserializer=lambda x: json.loads(x.decode('utf-8'))
        )

        print("Kafka Consumer started...")
        for message in consumer:
            if stop_event.is_set():
                break
            data = message.value
            save_to_db(data)

    except Exception as e:
        print(f"Consumer error: {e}. Reconnecting in 5 seconds...")
        time.sleep(5)  # 재연결 대기


def start_consumer():
    """Kafka Consumer 스레드 시작"""
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()
    print("Kafka Consumer thread running...")


if __name__ == "__main__":
    try:
        start_consumer()
        while not stop_event.is_set():
            time.sleep(1)  # 무한 대기를 적절한 sleep으로 유지
    except KeyboardInterrupt:
        print("Shutting down consumer...")
        stop_event.set()
        time.sleep(1)  # 종료 신호가 처리되도록 대기
