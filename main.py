from fastapi import FastAPI, Request, WebSocket
from fastapi.templating import Jinja2Templates
import requests
import os

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ✅ Gunakan model yang selalu bisa diakses
MODEL_NAME = "gpt2"
HF_API_TOKEN = os.getenv("HF_API_TOKEN", "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
API_URL = f"https://api-inference.huggingface.co/models/{MODEL_NAME}"
headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

def query(payload):
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            return f"❌ Error {response.status_code}: {response.text}"
        result = response.json()
        print("Raw:", result)
        return result[0].get("generated_text", "") if isinstance(result, list) else result.get("generated_text", "")
    except Exception as e:
        return f"Error: {str(e)}"

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

            if "genesis" in user_input.lower():
                prompt = f"User: {user_input}\nGenesis:"

                response_text = query({
                    "inputs": prompt,
                    "parameters": {
                        "max_new_tokens": 64,
                        "temperature": 0.8,
                        "return_full_text": False
                    }
                })

                # Bersihkan respons
                if "Genesis:" in response_text:
                    response_text = response_text.split("Genesis:")[1]
                clean = response_text.split(". ")[0] + "."
                clean = clean.strip()

                ai_msg = f"Genesis: {clean}"
                for conn in active_connections:
                    await conn.send_text(ai_msg)
            else:
                user_msg = f"User {client_id}: {user_input}"
                for conn in active_connections:
                    await conn.send_text(user_msg)

    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)