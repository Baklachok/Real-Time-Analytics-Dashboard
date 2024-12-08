import logging
import os

from confluent_kafka import Consumer
from dotenv import load_dotenv

from apps.authentication.tasks import process_kafka_event

load_dotenv()
logger = logging.getLogger(__name__)

def consume_events(max_iterations=None):
    logger.info(f"Kafka bootstrap servers: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')}")
    consumer_config = {
        'bootstrap.servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'group.id': 'django-group',
        'auto.offset.reset': 'earliest',
    }
    consumer = Consumer(consumer_config)
    logger.info("Attempting to connect to Kafka and subscribe to topics.")
    try:
        consumer.subscribe(['user-events'])
    except Exception as e:
        logger.error(f"Failed to subscribe to Kafka topic: {e}")

    iteration = 0
    try:
        while True:
            if max_iterations is not None and iteration >= max_iterations:
                logger.info("Reached max iterations. Exiting consume loop.")
                break
            iteration += 1
            logger.info("Kafka consumer is consuming messages.")
            message = consumer.poll(5.0)
            if message is None:
                logger.info("No message received.")
                continue
            if message.error():
                logger.error(f"Consumer error: {message.error()}")
                continue

            logger.info(f"Message received from Kafka: {message.value().decode('utf-8')}")
            process_kafka_event.delay(message.value().decode('utf-8'))
    finally:
        logger.info("Closing consumer.")
        consumer.close()

