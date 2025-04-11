
import langdetect
import translation
from ..core.config import settings
from langdetect import language_detection
from translation import translation_service
import pika
# import asyncio


class ProcessMessageService:

    def __init__(self) -> None:
        self.request = {}
        self.setup_rabbitmq()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel"""
        self.connection = pika.BlockingConnection(
            pika.URLParameters(settings.RABBITMQ_URL)
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=settings.TRANSLATION_QUEUE)


    async def perform(self,text: str) -> str:
        """
        Simulate processing a message.
        In an actual scenario, this function would:
        - Dequeue a message,
        - Run language detection,
        - Pass the message to a translation engine,
        - Return the translated message.
        """
        # Simulate processing delay (e.g., language detection and translation)
        await language_detection.produce(text)
        await translation_service.produce(text)


        # await asyncio.sleep(1)
        # For demonstration, we simply return a modified message.

        return self.request
    
    
    def consume(self):
        """Consume Translation Message """
        def callback(ch, method, properties, body):
            print(f" [x] Received {body}")
            self.request = body
            print(" [x] Done")
            ch.basic_ack(delivery_tag = method.delivery_tag)

        self.channel.basic_consume(queue=settings.TRANSLATION_QUEUE, on_message_callback=callback, auto_ack=True)
        
        print(' [*] Waiting for messages.')
        self.channel.start_consuming()



process_message = ProcessMessageService()