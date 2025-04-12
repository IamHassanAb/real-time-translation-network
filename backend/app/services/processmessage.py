import logging
import time
import json
import redis
import pika
from typing import Dict
import asyncio
from core.config import settings
from services.language_detection import language_detection
from services.translation import translation_service

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProcessMessageService:
    def __init__(self) -> None:
        self.request = {}
        logger.info("Initializing ProcessMessageService")
        self.setup_rabbitmq()
        self.setup_redis()
    
    def setup_rabbitmq(self):
        """Setup RabbitMQ connection and channel."""
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

    def setup_redis(self):
        """Setup Redis connection."""
        try:
            logger.info("Setting up Redis connection")
            pool = redis.ConnectionPool(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB
            )
            self.redis_client = redis.Redis(connection_pool=pool)
            logger.info("Redis setup completed")
        except Exception as e:
            logger.error(f"Failed to setup Redis: {e}")
            raise
    
    async def process(self, request: Dict):
        """
        Perform the message processing.
        Here the language_detection service is called, which (in your flow) eventually triggers translation.
        """
        logger.info("Starting message processing")
        try:
            # Assign a unique ID based on the current time (or use another unique method)
            request['id'] = round(time.time())
            # Kick off language detection (which triggers the further pipeline)
            await language_detection.process(request)
        except Exception as e:
            logger.error(f"Error during message processing: {e}")
            raise

    def store(self, request: Dict) -> str:
        """
        Store the translation request in Redis and publish a notification for subscribers.
        :param request: The translation request to store
        :return: The request ID
        """
        try:
            logger.info("Storing translation request in Redis")
            request_id = request.get('id')
            # Serialize the request into JSON so it can be stored and retrieved properly.
            serialized_request = json.dumps(request)
            self.redis_client.set(request_id, serialized_request)
            logger.info(f"Stored request with ID: {request_id} and data: {serialized_request}")
            
            # Publish a message to notify subscribers that this request has been processed.
            self.redis_client.publish('translation_channel', request_id)
            logger.info(f"Published message to 'translation_channel' with ID: {request_id}")
            
            return request_id
        except Exception as e:
            logger.error(f"Error storing request in Redis: {e}")
            raise

    def consume(self):
        """
        Consume messages from the RabbitMQ translation queue.
        When a message is received from translation, it is stored in Redis.
        """
        def callback(ch, method, properties, body):
            logger.info(f"Received message from translation queue: {body}")
            try:
                # Assuming the body is a JSON-encoded string
                request_data = json.loads(body.decode())
            except Exception as e:
                logger.error(f"Error decoding message: {e}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Store the final processed request in Redis and publish a notification.
            self.store(request_data)
            logger.info("Message processing and storage completed")
            ch.basic_ack(delivery_tag=method.delivery_tag)

        try:
            logger.info("Starting to consume messages from the RabbitMQ translation queue")
            # Note: Using auto_ack=False to ensure messages are acknowledged after processing.
            self.channel.basic_consume(queue=settings.TRANSLATION_QUEUE, on_message_callback=callback, auto_ack=False)
            logger.info("Waiting for messages...")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error during message consumption: {e}")
            raise

    def subscribe(self):
        """
        Subscribe to the Redis Pub/Sub channel ('translation_channel') to receive notifications in real time.
        This can be run in a separate thread or integrated into your asynchronous workflow.
        """
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe('translation_channel')
        logger.info("Subscribed to 'translation_channel'")
        for message in pubsub.listen():
            if message['type'] == 'message':
                request_id = message['data'].decode()
                logger.info(f"Received published message for request ID: {request_id}")
                # Optionally, fetch the stored data from Redis.
                data = self.redis_client.get(request_id)
                if data:
                    logger.info(f"Retrieved data for {request_id}: {data.decode()}")
                else:
                    logger.warning(f"No data found for request ID: {request_id}")

# Initialize an instance of your process message service.
process_message = ProcessMessageService()
