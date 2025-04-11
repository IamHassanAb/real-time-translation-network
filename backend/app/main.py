from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from services.language_detection import language_detection
from services.translation import translation_service
from services.processmessage import process_message
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
            print(message)
            response = await process_message.perform(message)
            print(response)
            
            
            await websocket.send_text(f"Message received in room {room_id}: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    translation_service.consume()
    process_message.consume()
    uvicorn.run(app, host="0.0.0.0", port=8000)
