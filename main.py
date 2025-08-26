from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🤗 Hugging Face Settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    print("⚠️ HF_API_TOKEN tidak ditemukan! AI tidak akan jalan.")

MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 503:
            return "🤖 Genesis sedang memuat model... Coba sebentar lagi."
        result = response.json()
        if isinstance(result, list):
            return result[0].get("generated_text", "")
        return result.get("generated_text", "")
    except Exception as e:
        return f"🤖 Maaf, terjadi error: {str(e)}"

# Daftar koneksi aktif
active_connections = []

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    # Konteks percakapan
    conversation = "You are Genesis, a friendly and helpful AI assistant. Keep answers short and warm."

    try:
        while True:
            data = await websocket.receive_text()

            # Tambahkan ke konteks
            conversation += f"\nUser: {data}"

            # Jika user panggil "genesis", AI merespons
            if "genesis" in data.lower():
                prompt = conversation + "\nAssistant:"
                response_text = query({
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 128,
                        "temperature": 0.7,
                        "return_full_text": False
                    }
                })
                ai_response = response_text.strip()
                final_msg = f"Genesis: {ai_response}"
                conversation += f"\nAssistant: {ai_response}"

                # Kirim ke semua
                for conn in active_connections:
                    await conn.send_text(final_msg)
            else:
                # Broadcast pesan user
                user_msg = f"User {client_id}: {data}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}