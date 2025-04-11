import logging
from transformers import pipeline
from core.config import settings
import pika
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TranslationService:
    def __init__(self):
        self.models = {}
        self.request = {}
        self.setup_rabbitmq()
        logger.info("TranslationService initialized.")
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        try:
            self.connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            # Create Connection to Translation Queue
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)
            logger.info("RabbitMQ connection and channel setup completed.")
        except Exception as e:
            logger.error(f"Error setting up RabbitMQ: {e}")
            raise

    def get_model(self, source_lang: str = settings.DEFAULT_SOURCE_LANG, target_lang: str = settings.DEFAULT_TARGET_LANG):
        """Get or create translation model for language pair"""
        model_key = f"{source_lang}-{target_lang}"
        if model_key not in self.models:
            model_name = settings.HUGGINGFACE_MODEL.format(
                src=source_lang,
                tgt=target_lang
            )
            logger.info(f"Loading model for {model_key}: {model_name}")
            self.models[model_key] = pipeline(
                "translation",
                model=model_name
            )
        return self.models[model_key]
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using HuggingFace model"""
        if source_lang == target_lang:
            logger.info("Source and target languages are the same. Returning original text.")
            return text
            
        logger.info(f"Translating text from {source_lang} to {target_lang}.")
        model = self.get_model(source_lang, target_lang)
        result = model(text)
        translation = result[0]['translation_text']
        logger.info(f"Translation completed: {translation}")
        return translation
    
    def publish_translation(self, text: str, source_lang: str, target_lang: str):
        """Queue translation request in RabbitMQ"""
        message = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.TRANSLATION_QUEUE,
                body=json.dumps(message)
            )
            logger.info("Translation request published to RabbitMQ.")
        except Exception as e:
            logger.error(f"Error publishing translation request: {e}")
            raise

    def produce(self):
        try:
            logger.info("Producing translation request.")
            self.request['translation_text'] = self.translate(**self.request)
            self.publish_translation(**self.request)
        except Exception as e:
            logger.error(f"Error in produce method: {e}")
        finally:
            self.close()

    def consume(self):
        def callback(ch, method, properties, body):
            try:
                self.request = json.loads(body)
                logger.info(f"Received message: {self.request}")
            except Exception as e:
                logger.error(f"Error processing received message: {e}")

        try:
            logger.info("Starting to consume messages.")
            self.channel.basic_consume(queue=settings.DETECTION_QUEUE, on_message_callback=callback, auto_ack=True)
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error in consume method: {e}")
        finally:
            self.close()

    def close(self):
        """Close RabbitMQ connection"""
        try:
            self.connection.close()
            logger.info("RabbitMQ connection closed.")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")

# Create global instance
translation_service = TranslationService()
