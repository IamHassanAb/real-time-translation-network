import logging
from transformers import pipeline
from langdetect import detect_langs
from core.config import settings
import pika
from typing import Dict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LanguageDetectionService:
    def __init__(self):
        logger.info("Initializing LanguageDetectionService...")
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        try:
            logger.info("Setting up RabbitMQ connection...")
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)
            logger.info("RabbitMQ setup complete.")
        except Exception as e:
            logger.error(f"Failed to set up RabbitMQ: {e}")
            raise

    def produce(self, request: Dict) -> str:
        """Perform the Language Detection Process"""
        logger.info("Starting language detection process...")
        try:
            text = request.get('text')
            source_lang = self.detect(text)
            logger.info(f"Detected language: {source_lang}")
            request['source_lang'] = source_lang
            self.publish_lang(request)
        except Exception as e:
            logger.error(f"Error during language detection process: {e}")
            raise
        finally:
            self.close()

    def detect(self, text: str) -> str:
        """Detect language using lang_detect library"""
        logger.info("Detecting language...")
        try:
            detected_lang = detect_langs(text)[0]
            logger.info(f"Language detected: {detected_lang}")
            return detected_lang
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            raise
    
    def publish_lang(self, request: Dict):
        """Queue translation request in RabbitMQ"""
        logger.info("Publishing detected language to RabbitMQ...")
        try:
            message = {
                "text": request.get('text'),
                "source_lang": request.get,
                "target_lang": request.get('target_lang'),
            }
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.TRANSLATION_QUEUE,
                body=json.dumps(message)
            )
            logger.info("Message published to RabbitMQ.")
        except Exception as e:
            logger.error(f"Failed to publish message to RabbitMQ: {e}")
            raise
    
    def close(self):
        """Close RabbitMQ connection"""
        logger.info("Closing RabbitMQ connection...")
        try:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
            raise

# Create global instance
language_detection = LanguageDetectionService()
