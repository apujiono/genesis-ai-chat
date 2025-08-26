from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🤗 Hugging Face Settings
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    print("❌ ERROR: HF_API_TOKEN tidak di-set di environment!")

MODEL_NAME = "HuggingFaceH4/zephyr-7b-beta"
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"

headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 503:
            return "🤖 Model sedang loading... Tunggu 10-20 detik."
        elif response.status_code != 200:
            return f"❌ Error {response.status_code}: {response.text}"

        result = response.json()
        print("🔹 Raw Hugging Face response:", result)  # Debug log

        # Ambil teks dari hasil
        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("generated_text", "")
        elif isinstance(result, dict):
            text = result.get("generated_text", "")
        else:
            text = str(result)

        return text.strip()
    except Exception as e:
        print("🚨 Error query:", e)
        return f"🤖 Error koneksi: {str(e)}"

# Daftar koneksi aktif
active_connections = []

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    # Konteks percakapan (untuk memberi konteks ke AI)
    conversation = (
        "<|system|>\n"
        "Kamu adalah Genesis, asisten AI yang ramah, cerdas, dan membantu. "
        "Jawab dengan singkat, jelas, dan hangat.<|end|>"
    )

    try:
        while True:
            user_input = await websocket.receive_text()

            # Tambahkan ke riwayat
            conversation += f"\n<|user|>\n{user_input}<|end|>"

            # Cek: apakah user panggil "genesis"
            if "genesis" in user_input.lower():
                # Format prompt sesuai Zephyr
                prompt = conversation + "\n<|assistant|>"

                # Kirim ke Hugging Face
                response_text = query({
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 150,
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "do_sample": True,
                        "return_full_text": False
                    }
                })

                # Bersihkan output: ambil setelah <|assistant|> dan sebelum <|end|>
                if "<|assistant|>" in response_text:
                    response_text = response_text.split("<|assistant|>")[1]
                if "<|end|>" in response_text:
                    response_text = response_text.split("<|end|>")[0]
                response_text = response_text.strip()

                # Jika hasil masih kosong
                if not response_text:
                    response_text = "Maaf, aku tidak bisa merespons saat ini."

                # Format respons akhir
                ai_msg = f"Genesis: {response_text}"
                conversation += f"\n<|assistant|>\n{response_text}<|end|>"

                # Kirim ke semua user
                for conn in active_connections:
                    await conn.send_text(ai_msg)
            else:
                # Broadcast pesan user
                user_msg = f"User {client_id}: {user_input}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print("WebSocket error:", e)

@app.get("/health")
def health():
    return {"status": "ok", "ai": "ready"}