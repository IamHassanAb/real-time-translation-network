from transformers import pipeline
from ..core.config import settings
import pika
import json

class TranslationService:
    def __init__(self):
        self.models = {}
        self.request = {}
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        # Create Connection to Translation Queue
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)

        # Create connection to Detection Queue 
        # self.detection_channel = self.connection.channel()
        # self.detection_channel.queue_declare(queue=settings.DETECTION_QUEUE)
    
    def get_model(self, source_lang: str = settings.DEFAULT_SOURCE_LANG, target_lang: str = settings.DEFAULT_TARGET_LANG):
        """Get or create translation model for language pair"""
        model_key = f"{source_lang}-{target_lang}"
        if model_key not in self.models:
            model_name = settings.HUGGINGFACE_MODEL.format(
                src=source_lang,
                tgt=target_lang
            )
            self.models[model_key] = pipeline(
                "translation",
                model=model_name
            )
        return self.models[model_key]
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using HuggingFace model"""
        if source_lang == target_lang:
            return text
            
        model = self.get_model(source_lang, target_lang)
        result = model(text)
        return result[0]['translation_text']
    
    def publish_translation(self, text: str, source_lang: str, target_lang: str):
        """Queue translation request in RabbitMQ"""
        message = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang
        }
        self.channel.basic_publish(
            exchange='',
            routing_key=settings.TRANSLATION_QUEUE,
            body=json.dumps(message)
        )
        print(" [X] Sent 'Translation Request'")

    def produce(self):
        self.request['translation_text'] = self.translate(**self.request)
        self.publish_translation(**self.request)
        self.close()

    
    def consume(self):
        def callback(ch, method, properties, body):
            self.request = body
            print(f" [x] Received detected {self.request}")

        self.channel.basic_consume(queue=settings.DETECTION_QUEUE, on_message_callback=callback, auto_ack=True)

        print(' [*] Waiting for messages.')
        self.channel.start_consuming()

    
    def close(self):
        """Close RabbitMQ connection"""
        self.connection.close()

# Create global instance
translation_service = TranslationService()
