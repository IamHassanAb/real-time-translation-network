import logging
from core.config import settings
from services.language_detection import language_detection
from services.translation import translation_service
import pika
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProcessMessageService:

    def __init__(self) -> None:
        self.request = {}
        logger.info("Initializing ProcessMessageService")
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        try:
            logger.info("Setting up RabbitMQ connection")
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)
            logger.info("RabbitMQ setup completed")
        except Exception as e:
            logger.error(f"Failed to setup RabbitMQ: {e}")
            raise

    async def perform(self, request: Dict) -> str:
        """
        Simulate processing a message.
        """
        try:
            logger.info(f"Performing processing for text: {request}")
            language_detection.produce(request)
            logger.info("Language detection completed")
            translation_service.produce()
            logger.info("Translation completed")
            logger.info("Processing completed")
            return self.request
        except Exception as e:
            logger.error(f"Error during message processing: {e}")
            raise
    
    def consume(self):
        """Consume Translation Message """
        def callback(ch, method, properties, body):
            logger.info(f"Received message: {body}")
            self.request = body
            logger.info("Message processing done")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            logger.info("Starting to consume messages")
            self.channel.basic_consume(queue=settings.TRANSLATION_QUEUE, on_message_callback=callback, auto_ack=True)
            logger.info("Waiting for messages")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            raise


process_message = ProcessMessageService()