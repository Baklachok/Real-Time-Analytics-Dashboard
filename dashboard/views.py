import logging
import redis
from rest_framework.views import APIView
from rest_framework.response import Response

logger = logging.getLogger(__name__)
r = redis.StrictRedis(host='redis', port=6379, db=0)


class AnalyticsView(APIView):
    def get(self, request):
        try:
            # Получаем метрики из Redis
            user_registration_count = r.get("user_registration_count")
            logger.debug(f"Fetched user_registration_count: {user_registration_count}")
            user_registration_count = int(user_registration_count.decode('utf-8')) if user_registration_count else 0
            logger.debug(f"Decoded user_registration_count: {user_registration_count}")

            user_login_counts = {}
            user_logout_counts = {}

            # Получаем все ключи логинов
            logger.debug(f"Fetched login keys: {r.keys("user_login_count:*")}")
            for key in r.keys("user_login_count:*"):
                logger.debug(f"Retrieved key: {key}, Value: {r.get(key)}")
                username = key.decode('utf-8').split(":")[-1]
                logger.debug(f"Processing login key: {key.decode('utf-8')}, value: {r.get(key)}")
                user_login_counts[username] = int(r.get(key).decode('utf-8') or 0)

            # Получаем все ключи логаутов
            logger.debug(f"Fetched logout keys: {r.keys("user_logout_count:*")}")
            for key in r.keys("user_logout_count:*"):
                logger.debug(f"Retrieved key: {key}, Value: {r.get(key)}")
                username = key.decode('utf-8').split(":")[-1]
                logger.debug(f"Processing login key: {key.decode('utf-8')}, value: {r.get(key)}")
                user_logout_counts[username] = int(r.get(key).decode('utf-8') or 0)

            data = {
                "user_registration_count": user_registration_count,
                "user_login_counts": user_login_counts,
                "user_logout_counts": user_logout_counts,
            }
            logger.debug(f"Final analytics data: {data}")

            return Response(data, status=200)

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return Response({"error": "Failed to connect to Redis"}, status=500)
        except Exception as e:
            logger.error(f"Failed to retrieve analytics: {e}")
            return Response({"error": "Failed to retrieve analytics"}, status=500)
