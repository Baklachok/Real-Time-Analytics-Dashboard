import json
from unittest.mock import patch
import redis
from Authentication.tasks import process_kafka_event
from rest_framework.test import APITestCase


class CeleryTaskTests(APITestCase):
    def _generate_event(self, event_type, username):
        """Создает событие в формате JSON."""
        return json.dumps({"event_type": event_type, "username": username})

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_process_event_task(self, mock_kafka_send):
        """Тест: базовая обработка события."""
        event = self._generate_event("test_event", "testuser")
        process_kafka_event(event)

        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "test_event", "username": "testuser"}'
        )

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_missing_event_type_or_username(self, mock_kafka_send):
        """Тест: обработка события с отсутствующими обязательными полями."""
        invalid_events = [
            self._generate_event("", "testuser"),
            self._generate_event("user_registration", "")
        ]
        for invalid_event in invalid_events:
            process_kafka_event(invalid_event)
            mock_kafka_send.assert_not_called()

    @patch('Authentication.tasks.send_event_to_kafka')
    @patch('Authentication.tasks.r.incr', side_effect=redis.ConnectionError("Redis is down"))
    def test_redis_connection_error(self, mock_redis_incr, mock_kafka_send):
        """Тест: обработка ошибки подключения к Redis."""
        event = self._generate_event("user_registration", "testuser")
        process_kafka_event(event)

        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "user_registration", "username": "testuser"}'
        )
        mock_redis_incr.assert_called_once_with("user_registration_count")

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_json_decode_error(self, mock_kafka_send):
        """Тест: обработка некорректного JSON."""
        invalid_event = "INVALID_JSON_STRING"
        process_kafka_event(invalid_event)

        mock_kafka_send.assert_not_called()

    def _test_event_with_metric(self, mock_redis_incr, mock_kafka_send, event_type, username, metric_key):
        """Общий метод для тестов с обновлением метрик."""
        event = json.dumps({"event_type": event_type, "username": username})
        process_kafka_event(event)

        # Проверяем отправку сообщения в Kafka
        mock_kafka_send.assert_called_once_with(
            "user-events",
            json.dumps({"event_type": event_type, "username": username})
        )

        # Проверяем обновление метрик в Redis
        mock_redis_incr.assert_called_once_with(metric_key)

    def test_user_registration_event(self):
        """Тест: обработка события регистрации пользователя."""
        with patch('Authentication.tasks.send_event_to_kafka') as mock_kafka_send, \
                patch('Authentication.tasks.r.incr') as mock_redis_incr:
            self._test_event_with_metric(
                mock_redis_incr, mock_kafka_send,
                "user_registration", "testuser",
                "user_registration_count"
            )

    def test_user_login_event(self):
        """Тест: обработка события входа пользователя."""
        with patch('Authentication.tasks.send_event_to_kafka') as mock_kafka_send, \
                patch('Authentication.tasks.r.incr') as mock_redis_incr:
            self._test_event_with_metric(
                mock_redis_incr, mock_kafka_send,
                "user_login", "testuser",
                "user_login_count:testuser"
            )

    def test_user_logout_event(self):
        """Тест: обработка события выхода пользователя."""
        with patch('Authentication.tasks.send_event_to_kafka') as mock_kafka_send, \
                patch('Authentication.tasks.r.incr') as mock_redis_incr:
            self._test_event_with_metric(
                mock_redis_incr, mock_kafka_send,
                "user_logout", "testuser",
                "user_logout_count:testuser"
            )

    @patch('Authentication.tasks.send_event_to_kafka', side_effect=Exception("Kafka error"))
    def test_general_exception(self, mock_kafka_send):
        """Тест: обработка общего исключения."""
        event = self._generate_event("test_event", "testuser")
        process_kafka_event(event)

        mock_kafka_send.assert_called_once()
