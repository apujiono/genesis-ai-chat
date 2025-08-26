from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🤗 Hugging Face Settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    raise ValueError("HF_API_TOKEN tidak ditemukan! Harap set di environment variable.")

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

@app.get("/health")
def health():
    return {"status": "ok"}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        if isinstance(result, list):
            return result[0].get("generated_text", "Maaf, tidak ada respons.")
        return result.get("generated_text", "Maaf, saya tidak mengerti.")
    except Exception as e:
        return f"[Error AI] {str(e)}"

# WebSockets: Chat antar user
active_connections = []

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    conversation_history = "You are Genesis, a helpful and friendly AI assistant."

    try:
        while True:
            user_input = await websocket.receive_text()

            # Tambahkan input user ke percakapan
            conversation_history += f"\nUser: {user_input}"

            # Jika user panggil "genesis", AI merespons
            if "genesis" in user_input.lower():
                prompt = conversation_history + "\nAssistant:"

                response_text = query({
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 150,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                })

                ai_response = response_text.strip()
                full_msg = f"Genesis: {ai_response}"
                conversation_history += f"\nAssistant: {ai_response}"

                # Kirim ke semua user
                for conn in active_connections:
                    await conn.send_text(full_msg)

            else:
                # Broadcast pesan user
                user_msg = f"User {client_id}: {user_input}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)