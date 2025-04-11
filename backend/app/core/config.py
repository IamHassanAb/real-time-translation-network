from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Real-Time Translation Network"
    
    # WebSocket Settings
    WS_PING_INTERVAL: int = 20
    WS_PING_TIMEOUT: int = 20
    
    # Translation Settings
    SUPPORTED_LANGUAGES: List[str] = ["en", "es", "fr"]
    DEFAULT_SOURCE_LANG: str = "en"
    DEFAULT_TARGET_LANG: str = "es"
    
    # RabbitMQ Settings
    RABBITMQ_URL: str = "5672://localhost"
    TRANSLATION_QUEUE: str = "translation_queue"
    DETECTION_QUEUE: str = "detection_queue"
    # RESPONSE_QUEUE: str = "response_queue"
    
    # HuggingFace Settings
    HUGGINGFACE_MODEL: str = "Helsinki-NLP/opus-mt-{src}-{tgt}"

    # Languages Currently Supported
    # AVAILABLE_LANGUAGES = {"en-fr", "en-de", "en-ar", "ar-en", "de-en", "fr-en"}
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
