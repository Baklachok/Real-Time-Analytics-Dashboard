import json
from unittest.mock import patch

import redis

from Authentication.tasks import process_kafka_event

from rest_framework.test import APITestCase


class CeleryTaskTests(APITestCase):
    @patch('Authentication.tasks.send_event_to_kafka')
    def test_process_event_task(self, mock_kafka_send):
        """Тест задачи Celery"""
        event = json.dumps({"event_type": "test_event", "username": "testuser"})  # Передаем строку JSON
        process_kafka_event(event)

        # Проверяем вызов send_event_to_kafka с правильными аргументами
        mock_kafka_send.assert_called_once_with(
            "user-events",  # Убедитесь, что тема соответствует вашему коду
            '{"event_type": "test_event", "username": "testuser"}'
        )

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_missing_event_type_or_username(self, mock_kafka_send):
        """Тест: обработка события с отсутствующими данными"""
        invalid_event = json.dumps({"event_type": "", "username": "testuser"})
        process_kafka_event(invalid_event)

        # Проверяем, что Kafka не вызывается
        mock_kafka_send.assert_not_called()

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_missing_username(self, mock_kafka_send):
        """Тест: обработка события с отсутствующим username"""
        invalid_event = json.dumps({"event_type": "user_registration"})
        process_kafka_event(invalid_event)

        # Проверяем, что Kafka не вызывается
        mock_kafka_send.assert_not_called()

    @patch('Authentication.tasks.send_event_to_kafka')
    @patch('Authentication.tasks.r.incr', side_effect=redis.ConnectionError("Redis is down"))
    def test_redis_connection_error(self, mock_redis_incr, mock_kafka_send):
        """Тест: ошибка подключения к Redis"""
        event = json.dumps({"event_type": "user_registration", "username": "testuser"})
        process_kafka_event(event)

        # Проверяем, что сообщение отправлено в Kafka
        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "user_registration", "username": "testuser"}'
        )

        # Проверяем, что Redis попытался обновить метрику
        mock_redis_incr.assert_called_once_with("user_registration_count")

    @patch('Authentication.tasks.send_event_to_kafka')
    def test_json_decode_error(self, mock_kafka_send):
        """Тест: обработка некорректного JSON"""
        invalid_event = "INVALID_JSON_STRING"
        process_kafka_event(invalid_event)

        # Проверяем, что Kafka не вызывается
        mock_kafka_send.assert_not_called()

    @patch('Authentication.tasks.send_event_to_kafka')
    @patch('Authentication.tasks.r.incr')
    def test_user_registration_event(self, mock_redis_incr, mock_kafka_send):
        """Тест: обработка события регистрации пользователя"""
        event = json.dumps({"event_type": "user_registration", "username": "testuser"})
        process_kafka_event(event)

        # Проверяем, что сообщение отправлено в Kafka
        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "user_registration", "username": "testuser"}'
        )

        # Проверяем, что Redis обновил метрику регистрации
        mock_redis_incr.assert_called_once_with("user_registration_count")

    @patch('Authentication.tasks.send_event_to_kafka')
    @patch('Authentication.tasks.r.incr')
    def test_user_login_event(self, mock_redis_incr, mock_kafka_send):
        """Тест: обработка события входа пользователя"""
        event = json.dumps({"event_type": "user_login", "username": "testuser"})
        process_kafka_event(event)

        # Проверяем, что сообщение отправлено в Kafka
        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "user_login", "username": "testuser"}'
        )

        # Проверяем, что Redis обновил метрику входа
        mock_redis_incr.assert_called_once_with("user_login_count:testuser")

    @patch('Authentication.tasks.send_event_to_kafka')
    @patch('Authentication.tasks.r.incr')
    def test_user_logout_event(self, mock_redis_incr, mock_kafka_send):
        """Тест: обработка события выхода пользователя"""
        event = json.dumps({"event_type": "user_logout", "username": "testuser"})
        process_kafka_event(event)

        # Проверяем, что сообщение отправлено в Kafka
        mock_kafka_send.assert_called_once_with(
            "user-events",
            '{"event_type": "user_logout", "username": "testuser"}'
        )

        # Проверяем, что Redis обновил метрику выхода
        mock_redis_incr.assert_called_once_with("user_logout_count:testuser")

    @patch('Authentication.tasks.send_event_to_kafka', side_effect=Exception("Kafka error"))
    def test_general_exception(self, mock_kafka_send):
        """Тест: общий Exception"""
        event = json.dumps({"event_type": "test_event", "username": "testuser"})
        process_kafka_event(event)

        # Проверяем, что Kafka вызывался и выбросил ошибку
        mock_kafka_send.assert_called_once()
