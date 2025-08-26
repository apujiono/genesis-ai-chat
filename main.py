from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from transformers import pipeline
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🧠 Load model ringan
generator = None
print("🚀 Memuat model distilgpt2...")

try:
    generator = pipeline("text-generation", model="distilgpt2", max_new_tokens=64, device=-1)
    print("✅ Model siap!")
except Exception as e:
    print(f"❌ Gagal muat model: {e}")

# 🧠 Memory percakapan
user_memory = {}

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/")
async def chat_page(request: Request):
    # (bisa tambah validasi username nanti)
    return templates.TemplateResponse("index.html", {"request": request})

# Daftar koneksi
active_connections = []

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    if client_id not in user_memory:
        user_memory[client_id] = "User: Halo\nGenesis: Hai! Aku Genesis, siap membantu."

    try:
        while True:
            user_input = await websocket.receive_text()

            if "genesis" in user_input.lower() and generator:
                context = user_memory[client_id]
                prompt = f"{context}\nUser: {user_input}\nGenesis:"

                try:
                    result = generator(prompt, max_length=120, num_return_sequences=1)[0]['generated_text']
                    if "Genesis:" in result:
                        ai_text = result.split("Genesis:")[1].strip()
                    else:
                        ai_text = result.strip()
                    response = ai_text.split(". ")[0] + "."

                    # Update memory
                    user_memory[client_id] = f"{context}\nUser: {user_input}\nGenesis: {response}"

                    ai_msg = f"Genesis: {response}"
                    for conn in active_connections:
                        await conn.send_text(ai_msg)
                except Exception as e:
                    await websocket.send_text("🤖 Maaf, sedang berpikir ulang.")
            else:
                user_msg = f"{client_id}: {user_input}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print("Error:", e)