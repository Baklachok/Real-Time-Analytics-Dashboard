import json
import logging

import redis
from celery import shared_task
from django.core.cache import cache

logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='redis', port=6379, db=0)

@shared_task
def process_kafka_event(event_data):
    try:
        r.ping()
        logger.info(f"Received event data: {event_data}")
        event = json.loads(event_data)
        if not event.get("event_type") or not event.get("username"):
            raise ValueError("Invalid event data")
        event_type = event.get("event_type")
        username = event.get("username")

        if event_type == "user_registration":
            cache_key = "user_registration_count"
            cache.set(cache_key, 0, nx=True)
            cache.incr(cache_key, delta=1)
            logger.info(f"Incremented {cache_key}")

        elif event_type == "user_login":
            cache_key = f"user_login_count:{username}"
            cache.set(cache_key, 0, nx=True)
            cache.incr(cache_key, delta=1)
            logger.info(f"Incremented {cache_key}")

        elif event_type == "user_logout":
            cache_key = f"user_logout_count:{username}"
            cache.set(cache_key, 0, nx=True)
            cache.incr(cache_key, delta=1)
            logger.info(f"Incremented {cache_key}")
    except redis.ConnectionError as e:
        logger.error(f"Redis connection error: {e}")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse event data: {e}")
        return
    except Exception as e:
        logger.error(f"Failed to process Kafka event: {e}")


@shared_task
def test_task():
    print("Test task executed!")
