from transformers import pipeline
from langdetect import detect_langs
from ..core.config import settings
import pika
import json

class LanguageDetectionService:
    def __init__(self):
        # self.models = {}
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)

    def produce(self, text: str) -> str:
        """Perform the Language Detection Process"""
        source_lang = self.detect(text)
        self.publish_lang(text,source_lang)
        self.close()
        

    def detect(self, text: str) -> str:
        """Detect language using lang_detect library"""
        # model = self.get_model(source_lang, target_lang)
        return detect_langs(text)[0]
    
    
    def publish_lang(self, text: str, source_lang: str):
        """Queue translation request in RabbitMQ"""
        message = {
            "text": text,
            "source_lang": source_lang
        }
        self.channel.basic_publish(
            exchange='',
            routing_key=settings.TRANSLATION_QUEUE,
            body=json.dumps(message)
        )
        print(" [X] Sent 'Detected Language'")
        
    
    def close(self):
        """Close RabbitMQ connection"""
        self.connection.close()

# Create global instance
language_detection = LanguageDetectionService()
