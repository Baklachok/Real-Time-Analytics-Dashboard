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
            user_registration_count = int(user_registration_count) if user_registration_count else 0

            user_login_counts = {}
            user_logout_counts = {}

            # Получаем все ключи логинов
            for key in r.keys("user_login_count:*"):
                username = key.decode('utf-8').split(":")[-1]
                user_login_counts[username] = int(r.get(key))

            # Получаем все ключи логаутов
            for key in r.keys("user_logout_count:*"):
                username = key.decode('utf-8').split(":")[-1]
                user_logout_counts[username] = int(r.get(key))

            data = {
                "user_registration_count": user_registration_count,
                "user_login_counts": user_login_counts,
                "user_logout_counts": user_logout_counts,
            }

            return Response(data, status=200)

        except redis.ConnectionError as e:
            logger.error(f"Redis connection error: {e}")
            return Response({"error": "Failed to connect to Redis"}, status=500)
        except Exception as e:
            logger.error(f"Failed to retrieve analytics: {e}")
            return Response({"error": "Failed to retrieve analytics"}, status=500)
