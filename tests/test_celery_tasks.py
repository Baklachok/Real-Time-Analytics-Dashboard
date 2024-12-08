import json
import pytest
from unittest.mock import patch, MagicMock

import redis

from apps.authentication.tasks import process_kafka_event


@pytest.fixture
def mock_redis(mocker):
    """Fixture для мокирования Redis."""
    return mocker.patch("apps.authentication.tasks.r")


@pytest.fixture
def mock_logger(mocker):
    """Fixture для мокирования логгера."""
    return mocker.patch("apps.authentication.tasks.logger")


def test_process_kafka_event_user_registration(mock_redis, mock_logger):
    event_data = json.dumps({"event_type": "user_registration", "username": "test_user"})
    process_kafka_event(event_data)

    # Проверяем, что Redis вызван с правильным ключом
    mock_redis.incr.assert_called_once_with("user_registration_count")
    # Проверяем, что логгер зафиксировал сообщение
    mock_logger.info.assert_any_call("Incremented user_registration_count")


def test_process_kafka_event_user_login(mock_redis, mock_logger):
    event_data = json.dumps({"event_type": "user_login", "username": "test_user"})
    process_kafka_event(event_data)

    mock_redis.incr.assert_called_once_with("user_login_count:test_user")
    mock_logger.info.assert_any_call("Incremented user_login_count for test_user")


def test_process_kafka_event_user_logout(mock_redis, mock_logger):
    event_data = json.dumps({"event_type": "user_logout", "username": "test_user"})
    process_kafka_event(event_data)

    mock_redis.incr.assert_called_once_with("user_logout_count:test_user")
    mock_logger.info.assert_any_call("Incremented user_logout_count for test_user")


def test_process_kafka_event_invalid_data(mock_redis, mock_logger):
    event_data = json.dumps({"event_type": "unknown_event", "username": "test_user"})
    process_kafka_event(event_data)

    # Redis не должен вызываться для неизвестного типа события
    mock_redis.incr.assert_not_called()
    mock_logger.error.assert_called_once_with("Invalid event data")


def test_process_kafka_event_redis_error(mock_redis, mock_logger):
    # Настраиваем Redis так, чтобы он выбрасывал ошибку подключения
    mock_redis.incr.side_effect = redis.ConnectionError("Connection error")
    event_data = json.dumps({"event_type": "user_registration", "username": "test_user"})

    process_kafka_event(event_data)

    # Проверяем, что логгер зафиксировал ошибку
    mock_logger.error.assert_called_once_with("Redis connection error: Connection error")


def test_process_kafka_event_json_decode_error(mock_redis, mock_logger):
    event_data = "invalid_json"

    process_kafka_event(event_data)

    # Проверяем, что Redis не вызывался
    mock_redis.incr.assert_not_called()
    # Проверяем, что логгер зафиксировал ошибку парсинга JSON
    mock_logger.error.assert_called_once_with("Failed to parse event data: Expecting value: line 1 column 1 (char 0)")
