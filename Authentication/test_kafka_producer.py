import unittest
from unittest.mock import patch, MagicMock

from Authentication.kafka_producer import send_event_to_kafka


class KafkaProducerTests(unittest.TestCase):
    @patch('Authentication.kafka_producer.Producer')  # Указываем путь к Producer
    def test_send_event_to_kafka(self, MockProducer):
        # Создаем замоканный объект Producer
        mock_producer = MagicMock()
        MockProducer.return_value = mock_producer

        topic = "user-events"
        message = '{"event_type": "test_event", "username": "testuser"}'

        # Вызываем функцию
        send_event_to_kafka(topic, message)

        # Проверяем, что produce и flush были вызваны
        mock_producer.produce.assert_called_once_with(topic, value=message)
        mock_producer.flush.assert_called_once()

    @patch("Authentication.kafka_producer.Producer")  # Патчим класс Producer
    def test_send_event_to_kafka_success(self, MockProducer):
        """Тест на успешную отправку сообщения в Kafka."""
        # Создаем замоканный объект Producer
        mock_producer = MagicMock()
        MockProducer.return_value = mock_producer

        topic = "test-topic"
        message = '{"event_type": "test_event", "username": "test_user"}'

        # Вызываем тестируемую функцию
        send_event_to_kafka(topic, message)

        # Проверяем, что методы produce и flush были вызваны один раз
        mock_producer.produce.assert_called_once_with(topic, value=message)
        mock_producer.flush.assert_called_once()

    @patch("Authentication.kafka_producer.Producer")  # Патчим класс Producer
    @patch("Authentication.kafka_producer.logger")  # Патчим логгер
    def test_send_event_to_kafka_failure(self, MockLogger, MockProducer):
        """Тест на обработку исключений при отправке сообщения в Kafka."""
        # Создаем замоканный объект Producer, который выбрасывает исключение
        mock_producer = MagicMock()
        mock_producer.produce.side_effect = Exception("Kafka error")
        MockProducer.return_value = mock_producer

        topic = "test-topic"
        message = '{"event_type": "test_event", "username": "test_user"}'

        # Вызываем тестируемую функцию
        send_event_to_kafka(topic, message)

        # Проверяем, что logger.error был вызван с ожидаемым сообщением
        MockLogger.error.assert_called_once_with("Error sending message to Kafka: Kafka error")

    @patch("Authentication.kafka_producer.Producer")  # Патчим класс Producer
    @patch("Authentication.kafka_producer.os.getenv")  # Патчим os.getenv
    def test_send_event_to_kafka_custom_bootstrap_servers(self, MockGetenv, MockProducer):
        """Тест на проверку пользовательского значения bootstrap.servers."""
        # Подготавливаем mock для os.getenv
        MockGetenv.return_value = "custom-broker:9092"

        # Создаем замоканный объект Producer
        mock_producer = MagicMock()
        MockProducer.return_value = mock_producer

        topic = "test-topic"
        message = '{"event_type": "test_event", "username": "test_user"}'

        # Вызываем тестируемую функцию
        send_event_to_kafka(topic, message)

        # Проверяем, что Producer создавался с пользовательским bootstrap.servers
        MockProducer.assert_called_once_with({'bootstrap.servers': 'custom-broker:9092'})

        # Проверяем, что методы produce и flush были вызваны
        mock_producer.produce.assert_called_once_with(topic, value=message)
        mock_producer.flush.assert_called_once()
