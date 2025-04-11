# Real-Time Language Translation Network

## Overview
This project implements a distributed system architecture that enables real-time text message translation between 2-3 languages in a chat-style interface. The system is designed to be scalable, fault-tolerant, and provide instant translations while maintaining low latency across multiple users.

## System Architecture
```
[Client Browser] ←→ [Load Balancer (Nginx)] ←→ [FastAPI Servers]
        ↑                     ↑                        ↑
        └─────────WebSocket──┴────────────────────────┘
                            ↓
                    [Translation Service]
                    (HuggingFace Models)
                            ↓
                    [Message Queue]
                    (RabbitMQ)
```

### Components
- **FastAPI Servers**: Handle WebSocket connections, manage chat sessions, and coordinate translation requests
- **Translation Service**: Utilizes HuggingFace Transformers for efficient multilingual translations
- **Load Balancer**: Nginx for distributing WebSocket connections across multiple FastAPI instances
- **Message Queue**: RabbitMQ for managing translation request queues and ensuring message delivery
- **WebSocket**: Enables real-time bidirectional communication between clients and servers

## Features
- Real-time chat with instant translations
- Support for multiple languages (2-3 language pairs)
- WebSocket-based communication for low latency
- Scalable architecture for handling multiple concurrent users
- State-of-the-art translation using HuggingFace models
- Message persistence and delivery guarantees

## Technologies Used
- **Frontend**: HTML5, CSS3, JavaScript (WebSocket API)
- **Backend**: FastAPI (Python) with WebSocket support
- **Translation**: HuggingFace Transformers
- **Message Queue**: RabbitMQ
- **Load Balancer**: Nginx
- **Monitoring**: Prometheus & Grafana

## Prerequisites
```bash
# Required software
Python 3.8+
Node.js 14+
RabbitMQ Server
Nginx
```

## Installation
1. Clone the repository
```bash
git clone [repository-url]
cd real-time-translation-network
```

2. Install dependencies
```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
```

3. Configure the environment
```bash
# Create and edit .env file
cp .env.example .env

# Configure the following:
SUPPORTED_LANGUAGES=["en", "es", "fr"]  # Example language pairs
HUGGINGFACE_MODEL="Helsinki-NLP/opus-mt-{src}-{tgt}"
RABBITMQ_URL="amqp://localhost"
```

## Running the System
### Starting Individual Components
```bash
# Start RabbitMQ
sudo service rabbitmq-server start

# Start FastAPI server
uvicorn app.main:app --reload --port 8000

# Start Nginx
sudo service nginx start
```

### Development Setup
```bash
# Run frontend development server
cd frontend
npm run dev
```

## System Design
### Data Flow
1. Client establishes WebSocket connection through Nginx load balancer
2. Messages are sent via WebSocket to FastAPI server
3. Translation requests are queued in RabbitMQ
4. HuggingFace models process translations
5. Translated messages are broadcast to relevant chat participants

### Fault Tolerance
- WebSocket connection recovery
- Message queue persistence
- Multiple FastAPI instances for redundancy
- Load balancer health checks

### Scalability
- Horizontal scaling of FastAPI servers
- RabbitMQ clustering
- Translation service load distribution
- Connection pooling

## API Documentation
### WebSocket Endpoints
```
WS /ws/chat/{room_id}
- Payload: {
    "message": "Hello, world!",
    "source_lang": "en",
    "target_lang": "es"
}
```

## Monitoring and Maintenance
- WebSocket connection metrics
- Translation latency monitoring
- Queue length and processing time
- Error rate and success metrics

## Testing
```bash
# Run backend tests
pytest

# Run WebSocket integration tests
pytest tests/integration/
```

## Contributing
[Contribution guidelines]

## License
MIT License

## Contact
[Your contact information]
