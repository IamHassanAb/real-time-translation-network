import logging
# from transformers import pipeline
import requests
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
            model_name = settings.HUGGINGFACE_MODEL_URL.format(
                src=source_lang,
                tgt=target_lang
            )
            logger.info(f"Loading model for {model_key}: {model_name}")
            
            self.models[model_key] = model_name
        return self.models[model_key]
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using HuggingFace model"""
        if source_lang == target_lang:
            logger.info("Source and target languages are the same. Returning original text.")
            return text
            
        logger.info(f"Translating text from {source_lang} to {target_lang}.")
        model_url = self.get_model(source_lang, target_lang)
        result = requests.post(
            model_url,
            headers={"Authorization": f"Bearer {settings.HUGGINGFACE_TOKEN}"},
            json={"inputs": text}
        )
        # result = model(text)
        translation = result[0]['translation_text']
        logger.info(f"Translation completed: {translation}")
        return translation
    
    def publish_translation(self):
        """Queue translation request in RabbitMQ"""
        message = {
            "id": self.request.get('id'),
            "text": self.request.get('text'),
            "translation_text": self.request.get('translation_text'),
            "source_lang": self.request.get('source_lang'),
            "target_lang": self.request.get('target_lang'),
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
            self.publish_translation()
        except Exception as e:
            logger.error(f"Error in produce method: {e}")

    def consume(self):
        logger.info("Starting to consume messages from RabbitMQ...")
        def callback(ch, method, properties, body):
            try:
                if body is None:
                    logger.error("Received an empty message (body is None).")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    return
                
                # Decode body from bytes and parse as JSON
                message = json.loads(body.decode())
                logger.info(f"Received message from RabbitMQ: {message}")
                
                # Save the message as a dict so we can use it with keyword arguments
                self.request = message
                
                # Log the message keys to verify required data is present
                logger.info(f"Message keys: {list(self.request.keys())}")
                
                # Process the message: perform the translation and publish the response
                self.produce()
            except Exception as e:
                logger.error(f"Error processing received message: {e}")
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)


        try:
            logger.info("TranslationService is consuming messages...")
            self.channel.basic_consume(queue=settings.DETECTION_QUEUE, 
                                       on_message_callback=callback)
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
