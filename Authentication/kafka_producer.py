import logging
import os
from confluent_kafka import Producer
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

producer_config = {
    'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
}

producer = Producer(producer_config)

def send_event_to_kafka(topic, message):
    logger.info(f"Attempting to send message to Kafka: {message}")
    try:
        producer.produce(topic, value=message)
        producer.flush()  # Обязательно для гарантии доставки
        logger.info(f"Message sent to Kafka topic '{topic}'")
    except Exception as e:
        print(f"Error sending message to Kafka: {e}")
