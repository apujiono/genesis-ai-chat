from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Daftar koneksi WebSocket aktif
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
            data = await websocket.receive_text()
            
            # 💬 Broadcast ke semua user (termasuk pengirim)
            message = f"User {client_id}: {data}"
            for connection in active_connections:
                await connection.send_text(message)
                
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        print(f"Error: {e}")

# 🔁 Health check (untuk cek aplikasi jalan)
@app.get("/health")
def health():
    return {"status": "ok"}