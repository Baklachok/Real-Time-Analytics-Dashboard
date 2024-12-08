import unittest
from unittest.mock import patch, MagicMock
from apps.authentication.kafka_consumer import consume_events

class TestKafkaConsumer(unittest.TestCase):

    @patch("apps.authentication.kafka_consumer.Consumer")
    @patch("apps.authentication.kafka_consumer.process_kafka_event")
    def test_consume_valid_message(self, mock_process_kafka_event, mock_consumer):
        mock_message = MagicMock()
        mock_message.value.return_value = b'{"event_id": "123", "event_type": "user_login", "username": "test_user"}'
        mock_message.error.return_value = None

        mock_consumer_instance = MagicMock()
        mock_consumer_instance.poll.side_effect = [mock_message, None]
        mock_consumer.return_value = mock_consumer_instance

        consume_events(max_iterations=1)

        mock_process_kafka_event.delay.assert_called_once_with(
            '{"event_id": "123", "event_type": "user_login", "username": "test_user"}'
        )

    @patch("apps.authentication.kafka_consumer.Consumer")
    def test_consume_no_message(self, mock_consumer):
        # Мокаем Consumer.poll, чтобы он возвращал None (нет сообщений)
        mock_consumer_instance = MagicMock()
        mock_consumer_instance.poll.return_value = None
        mock_consumer.return_value = mock_consumer_instance

        # Запускаем тестируемую функцию
        with patch("apps.authentication.kafka_consumer.logger") as mock_logger:
            consume_events(max_iterations=1)

        # Проверяем, что логгер зафиксировал отсутствие сообщений
        mock_logger.info.assert_any_call("No message received.")

    @patch("apps.authentication.kafka_consumer.Consumer")
    def test_consume_message_with_error(self, mock_consumer):
        # Мокаем сообщение с ошибкой
        mock_message = MagicMock()
        mock_message.error.return_value = "Test Error"

        # Мокаем Consumer.poll
        mock_consumer_instance = MagicMock()
        mock_consumer_instance.poll.return_value = mock_message
        mock_consumer.return_value = mock_consumer_instance

        # Запускаем тестируемую функцию
        with patch("apps.authentication.kafka_consumer.logger") as mock_logger:
            consume_events(max_iterations=1)

        # Проверяем, что логгер зафиксировал ошибку
        mock_logger.error.assert_any_call("Consumer error: Test Error")
