from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from transformers import pipeline
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# 🧠 Load AI Genesis (offline)
print("🚀 Memuat model AI Genesis (gpt2)...")
generator = pipeline("text-generation", model="gpt2", max_new_tokens=64)

# Daftar koneksi WebSocket
active_connections = []

@app.get("/")
async def get_chat_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            user_input = await websocket.receive_text()

            # Jika user panggil "genesis", AI merespons
            if "genesis" in user_input.lower():
                # Format prompt
                prompt = f"User: {user_input}\nGenesis:"
                
                # Generate respons
                try:
                    response = generator(prompt, max_length=128, num_return_sequences=1)[0]['generated_text']
                    
                    # Ambil bagian setelah "Genesis:"
                    if "Genesis:" in response:
                        ai_text = response.split("Genesis:")[1].strip()
                    else:
                        ai_text = response.strip()

                    # Potong kalimat pertama saja
                    final_response = ai_text.split(". ")[0] + "."
                    
                    ai_msg = f"Genesis: {final_response}"
                    
                    # Kirim ke semua user
                    for conn in active_connections:
                        await conn.send_text(ai_msg)
                        
                except Exception as e:
                    await websocket.send_text("🤖 Maaf, AI sedang sibuk.")
                    print("Error generation:", e)
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