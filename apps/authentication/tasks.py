import json
import logging
import redis
from celery import shared_task

logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='redis', port=6379, db=0)

@shared_task
def process_kafka_event(event_data):
    try:
        logger.info(f"Received event data: {event_data}")
        event = json.loads(event_data)
        event_type = event.get("event_type")
        username = event.get("username")

        if not event_type or not username:
            raise ValueError("Invalid event data")

        # Обновление метрики в Redis
        if event_type == "user_registration":
            r.incr("user_registration_count")
            logger.info("Incremented user_registration_count")

        elif event_type == "user_login":
            r.incr(f"user_login_count:{username}")
            logger.info(f"Incremented user_login_count for {username}")

        elif event_type == "user_logout":
            r.incr(f"user_logout_count:{username}")
            logger.info(f"Incremented user_logout_count for {username}")
        else:
            # Логируем ошибку для неизвестного типа события
            logger.error("Invalid event data")
            return

    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse event data: {e}")
    except Exception as e:
        logger.error(f"Failed to process Kafka event: {e}")
