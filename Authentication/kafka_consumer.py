import logging
import os

from confluent_kafka import Consumer
from dotenv import load_dotenv

from Authentication.tasks import process_kafka_event

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
    logger.info("Consumer created.")

    try:
        consumer.subscribe(['user-events'])
        logger.info("Consumer subscribed to topics.")


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

            logger.info(f"Message received: {message.value().decode('utf-8')}")
            process_kafka_event.delay(message.value().decode('utf-8'))
    finally:
        logger.info("Closing consumer.")
        consumer.close()

