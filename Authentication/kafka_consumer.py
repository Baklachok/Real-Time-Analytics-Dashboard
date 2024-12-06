import logging
import os

from confluent_kafka import Consumer
from dotenv import load_dotenv

from Authentication.tasks import process_kafka_event

load_dotenv()
logger = logging.getLogger(__name__)

def consume_events(should_stop=lambda: False):
    logger.info("Kafka consumer starting.")
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

        while not should_stop():
            logger.info("Polling for messages.")
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

