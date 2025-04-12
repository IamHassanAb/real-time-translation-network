import logging
import pika.exceptions
from transformers import pipeline
# from langdetect import detect_langs, DetectorFactory
from langid.langid import LanguageIdentifier, model
from utils.utils import utility_service
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
            self.channel.queue_declare(queue=settings.DETECTION_QUEUE)
            logger.info("RabbitMQ setup complete.")
        except Exception as e:
            logger.error(f"Failed to set up RabbitMQ: {e}")
            raise

    async def process(self, request: Dict):
        """Perform the Language Detection Process"""
        logger.info("Starting language detection process...")
        try:
            text = request.get('text')
            source_lang = self.detect(text)
            # logger.info(f"Detected language: {source_lang}")
            request['source_lang'] = source_lang
            self.publish_lang(request)
            # self.close()
        except Exception as e:
            logger.error(f"Error during language detection process: {e}")
            raise

    def detect(self, text: str) -> str:
        """Detect language using lang_detect library"""
        logger.info("Detecting language...")
        try:
            # DetectorFactory.seed = 0
            # detected_lang = detect_langs(text)[0]
            # parsed_lang = utility_service.extract_lang(str(detected_lang))
            # logger.info(f"Language detected: {parsed_lang}")
            identifier = LanguageIdentifier.from_modelstring(model, norm_probs=True)
            # identifier.classify("This is a test")
            parsed_lang, confidence = identifier.classify(text.lower())
            logger.info(f"Language detected: {parsed_lang} with confidence {confidence}")
            # ('en', 0.9999999909903544) #sample answer
            return parsed_lang
        except Exception as e:
            logger.error(f"Error detecting language: {e}")
            raise
    
    def publish_lang(self, request: Dict):
        """Queue translation request in RabbitMQ"""
        logger.info("Publishing detected language to RabbitMQ...")
        try:
            logger.info(f"Publish Request: {request}")

            message = {
                "id": request.get('id'),
                "text": request.get('text'),
                "source_lang": request.get('source_lang'),
                "target_lang": request.get('target_lang'),
            }
            try:

                self.channel.basic_publish(
                    exchange='',
                    routing_key=settings.DETECTION_QUEUE,
                    body=json.dumps(message)
                )
                logger.info("Message published to Detection Queue.")
            except pika.exceptions.AMQPError as e:
                logger.error(f"Failed to publish message to RabbitMQ: {e}")
                raise
                # self.channel.basic_publish(
                #     exchange='',
                #     routing_key=settings.DETECTION_QUEUE,
                #     body=json.dumps(message)
                # )
                # logger.info("Message published to RabbitMQ after reconnection.")

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
