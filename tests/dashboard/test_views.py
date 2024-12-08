import logging
from unittest import TestCase
from unittest.mock import patch

import redis
from rest_framework.test import APIClient
from rest_framework import status

logger = logging.getLogger(__name__)


class TestAnalyticsView(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.dashboard.views.r")
    def test_get_analytics_success(self, mock_redis):

        # Подготавливаем mock-данные Redis
        mock_redis.get.side_effect = lambda key: {
            "user_registration_count": b"10",
            "user_login_count:user1": b"5",
            "user_login_count:user2": b"3",
            "user_logout_count:user1": b"2",
        }.get(key.decode() if isinstance(key, bytes) else key, None)

        mock_redis.keys.side_effect = lambda pattern: {
            "user_login_count:*": [b"user_login_count:user1", b"user_login_count:user2"],
            "user_logout_count:*": [b"user_logout_count:user1"],
        }.get(pattern.decode() if isinstance(pattern, bytes) else pattern, [])

        logger.debug(f"Mock Redis GET calls: {mock_redis.get.call_args_list}")
        logger.debug(f"Mock Redis KEYS calls: {mock_redis.keys.call_args_list}")

        # Логируем используемые ключи
        logger.debug("Keys for user_login_count:*: %s", mock_redis.keys(b"user_login_count:*"))
        logger.debug("Keys for user_logout_count:*: %s", mock_redis.keys(b"user_logout_count:*"))

        # Выполняем запрос к API
        response = self.client.get('/api/dashboard/analytics/')
        logger.debug(f"Response status: {response.status_code}, data: {response.json()}")

        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем содержимое ответа
        expected_data = {
            "user_registration_count": 10,
            "user_login_counts": {"user1": 5, "user2": 3},
            "user_logout_counts": {"user1": 2},
        }
        self.assertEqual(response.json(), expected_data)

    @patch("apps.dashboard.views.r")
    def test_get_analytics_redis_connection_error(self, mock_redis):
        # Вызываем ошибку соединения Redis
        mock_redis.get.side_effect = redis.ConnectionError("Redis is down")

        # Выполняем запрос к API
        response = self.client.get('/api/dashboard/analytics/')

        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json(), {"error": "Failed to connect to Redis"})

    @patch("apps.dashboard.views.r")
    def test_get_analytics_general_error(self, mock_redis):
        # Вызываем общую ошибку
        mock_redis.get.side_effect = Exception("Unexpected error")

        # Выполняем запрос к API
        response = self.client.get('/api/dashboard/analytics/')

        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.json(), {"error": "Failed to retrieve analytics"})
