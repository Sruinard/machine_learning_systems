from fastapi import FastAPI
from fastapi import FastAPI, WebSocket
import requests

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        # retrieve single review from api:
        response = requests.get("http://0.0.0.0:8080/reviews/b19a7789-ec44-4ff2-876b-1ef30da21a3d")
        review_content = response.json()["content"]
        await websocket.send_text(f"Message text was: {review_content}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)