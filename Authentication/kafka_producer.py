# Функция для создания Kafka Producer
import os

from confluent_kafka import Producer


def get_kafka_producer():
    config = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'client.id': os.getenv('KAFKA_CLIENT_ID', 'django-app')
    }
    return Producer(config)

# Отправка события в Kafka
def send_event_to_kafka(topic, event):
    producer = get_kafka_producer()
    try:
        producer.produce(topic, event)
        producer.flush()  # Обеспечиваем доставку сообщений
    except Exception as e:
        print(f"Failed to send event to Kafka: {e}")