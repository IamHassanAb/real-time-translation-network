from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.language_detection import language_detection
from services.translation import translation_service
from services.processmessage import process_message
import threading
# from .core.config import settings
import json

app = FastAPI(title="Real-Time Translation Network")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
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
            print(data)
            # TODO: Process message and send translation
            message = json.loads(data)
            # print(message)
            language_detection.process(message)
            # translated_text = translation_service.translate(
            #     text=original_text,
            #     source_lang=source_lang,
            #     target_lang=target_lang
            # )
            # print(response)
            
            
            await websocket.send_text(f"Message received in room {room_id}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

def start_translation_consumer():
    translation_service.consume()

# def start_process_message_consumer():
#     process_message.consume()


if __name__ == "__main__":
    import uvicorn

    translation_thread = threading.Thread(target=start_translation_consumer, daemon=True)
    # process_message_thread = threading.Thread(target=start_process_message_consumer, daemon=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
