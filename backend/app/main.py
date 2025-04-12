import threading
import json
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.processmessage import process_message as process_message_service
from services.translation import translation_service  # ensure this runs as needed
from services.language_detection import language_detection  # ensure this runs as needed
import uvicorn

app = FastAPI(title="Real-Time Translation Network")

# Configure CORS (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Real-Time Translation Network API"}

@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            # Process the message (kick off the pipeline)
            await process_message_service.process(message)
            
            # Option 1: Implement a polling mechanism with timeout if you prefer...
            # Option 2: Or, subscribe to the Redis Pub/Sub channel and wait for the notification.
            # For this example, we'll assume a simple polling with asyncio.sleep:
            timeout = 1  # seconds
            elapsed = 0
            interval = 0.5
            response_string = None

            while elapsed < timeout:
                response_string = process_message_service.redis_client.get(message['id'])
                if response_string:
                    break
                await asyncio.sleep(interval)
                elapsed += interval

            if not response_string:
                await websocket.send_text("Processing timed out")
            else:
                response = json.loads(response_string)
                await websocket.send_text(json.dumps(response))
    except Exception as e:
        print(f"Error in websocket: {e}")
    finally:
        await websocket.close()

def start_translation_consumer():
    translation_service.consume()

def start_processmessage_consumer():
    process_message_service.consume()

def start_redis_subscriber():
    # Run the subscribe method in a separate thread to listen for published messages.
    process_message_service.subscribe()

if __name__ == "__main__":
    # Start background consumer threads.
    translation_thread = threading.Thread(target=start_translation_consumer, daemon=True)
    processmessage_thread = threading.Thread(target=start_processmessage_consumer, daemon=True)
    redis_subscriber_thread = threading.Thread(target=start_redis_subscriber, daemon=True)
    
    translation_thread.start()
    processmessage_thread.start()
    redis_subscriber_thread.start()

    uvicorn.run(app, host="0.0.0.0", port=8000)
