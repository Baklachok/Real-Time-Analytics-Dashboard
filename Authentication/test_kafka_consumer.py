import logging
import unittest
from unittest.mock import MagicMock, patch

from Authentication.kafka_consumer import consume_events


logger = logging.getLogger(__name__)

class KafkaConsumerTests(unittest.TestCase):
    @patch("Authentication.kafka_consumer.Consumer")
    @patch("Authentication.kafka_consumer.logger")
    def test_consumer_handles_no_messages(self, MockLogger, MockConsumer):
        """Тест обработки ситуации без сообщений."""
        # Создаем мок-объект Consumer
        mock_consumer = MagicMock()
        logger.debug(f"MockConsumer: {mock_consumer}")
        logger.debug(f"Poll calls: {mock_consumer.poll.mock_calls}")
        mock_consumer.poll.return_value = None  # Симулируем отсутствие сообщений
        logger.debug(f"MockConsumer: {mock_consumer}")
        logger.debug(f"Poll calls: {mock_consumer.poll.mock_calls}")
        MockConsumer.return_value = mock_consumer

        def should_stop_after_poll():
            # Завершаем цикл после первого вызова poll
            yield False
            yield True

        should_stop_gen = should_stop_after_poll()

        def should_stop():
            return next(should_stop_gen)

        # Вызываем тестируемую функцию
        consume_events(should_stop=should_stop)

        # Проверяем, что poll был вызван хотя бы один раз
        mock_consumer.poll.assert_called_once()
        logger.debug(f"MockConsumer: {mock_consumer}")
        logger.debug(f"Poll calls: {mock_consumer.poll.mock_calls}")

    @patch("Authentication.kafka_consumer.Consumer")
    @patch("Authentication.kafka_consumer.logger")
    @patch("Authentication.kafka_consumer.process_kafka_event")
    def test_consumer_process_message(self, MockProcessKafkaEvent, MockLogger, MockConsumer):
        """Тест на обработку сообщений."""
        mock_consumer = MagicMock()
        mock_message = MagicMock()
        mock_message.value.return_value = b'{"event_type": "test_event", "username": "test_user"}'
        mock_message.error.return_value = None
        mock_consumer.poll.side_effect = [mock_message, None]
        MockConsumer.return_value = mock_consumer

        def should_stop_after_poll():
            # Завершаем цикл после первого вызова poll
            yield False
            yield True

        should_stop_gen = should_stop_after_poll()

        def should_stop():
            return next(should_stop_gen)

        logger.debug(f">>> MockConsumer setup: {MockConsumer}")
        logger.debug(f">>> Mocked poll side effect:{mock_consumer.poll.side_effect}")

        # Вызываем функцию
        consume_events(should_stop=should_stop)

        # Проверяем вызовы
        logger.debug(f">>> Checking poll call count:{mock_consumer.poll.call_count}")
        logger.debug(f">>> Checking process_kafka_event call count:{MockProcessKafkaEvent.delay.call_count}")
        mock_consumer.poll.assert_called_once()
        MockProcessKafkaEvent.delay.assert_called_once_with('{"event_type": "test_event", "username": "test_user"}')

    @patch("Authentication.kafka_consumer.Consumer")
    @patch("Authentication.kafka_consumer.logger")
    def test_consumer_closes_on_exit(self, MockLogger, MockConsumer):
        """Тест на закрытие Consumer при завершении."""
        mock_consumer = MagicMock()
        MockConsumer.return_value = mock_consumer

        def should_stop_after_poll():
            # Завершаем цикл после первого вызова poll
            yield False
            yield True

        should_stop_gen = should_stop_after_poll()

        def should_stop():
            return next(should_stop_gen)

        consume_events(should_stop=should_stop)

        mock_consumer.close.assert_called_once()
