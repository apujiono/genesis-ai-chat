from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🤗 Hugging Face Settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    print("⚠️ Peringatan: HF_API_TOKEN tidak di-set. AI tidak akan jalan.")

# 🔁 Gunakan model ringan agar cepat & stabil
MODEL_NAME = "microsoft/Phi-3-mini-4k-instruct"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def query(payload):
    try:
        # Tambah timeout agar tidak stuck
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Jika model sedang loading
        if response.status_code == 503:
            return "🤖 Genesis sedang mempersiapkan diri... Coba lagi sebentar."
        
        result = response.json()
        if isinstance(result, list):
            return result[0].get("generated_text", "Maaf, tidak bisa membaca respons.")
        return result.get("generated_text", "Maaf, saya tidak mengerti.")
    except Exception as e:
        return f"🤖 Maaf, Genesis sedang sibuk. Error: {str(e)}"

# WebSockets: Chat antar user + AI
active_connections = []

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    # 🧠 Simpan percakapan singkat agar AI paham konteks
    conversation = (
        "You are Genesis, a smart and friendly AI assistant. "
        "Answer in a warm, helpful, and concise way."
    )

    try:
        while True:
            user_input = await websocket.receive_text()

            # Tambahkan ke riwayat percakapan
            conversation += f"\nUser: {user_input}"

            # 🔥 Cek: apakah user panggil "genesis"
            if "genesis" in user_input.lower():
                prompt = conversation + "\nAssistant:"

                # Kirim ke Hugging Face
                response_text = query({
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 128,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "return_full_text": False
                    }
                })

                # Ambil hanya respons AI
                ai_response = response_text.strip()
                final_msg = f"Genesis: {ai_response}"
                conversation += f"\nAssistant: {ai_response}"

                # Kirim ke semua user
                for conn in active_connections:
                    await conn.send_text(final_msg)

            else:
                # Broadcast pesan user
                user_msg = f"User {client_id}: {user_input}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")

@app.get("/health")
def health():
    return {"status": "ok", "ai": "active"}