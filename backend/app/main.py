import os
import json
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.endpoints import upload, analysis, video
from .core.config import settings


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, paper_id: str, websocket: WebSocket):
        await websocket.accept()
        # If there's already a connection for this paper, close it first
        if paper_id in self.active_connections:
            try:
                old_ws = self.active_connections[paper_id]
                await old_ws.close()
            except:
                pass
        self.active_connections[paper_id] = websocket
        print(f"ConnectionManager: Connected paper {paper_id}, total connections: {len(self.active_connections)}")

    def disconnect(self, paper_id: str):
        if paper_id in self.active_connections:
            del self.active_connections[paper_id]
            print(f"ConnectionManager: Disconnected paper {paper_id}, remaining connections: {len(self.active_connections)}")

    async def send_log(self, paper_id: str, message: str):
        if paper_id in self.active_connections:
            try:
                ws = self.active_connections[paper_id]
                await ws.send_text(message)
            except Exception as e:
                print(f"Error sending log to {paper_id}: {e}")
                # Don't remove connection on error - let it retry


app = FastAPI()

# CORS middleware
# For development, allow all origins. In production, use specific origins from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

manager = ConnectionManager()
video.manager = manager


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {"status": "healthy"}


@app.websocket("/ws/papers/{paper_id}/logs")
async def websocket_endpoint(websocket: WebSocket, paper_id: str):
    await manager.connect(paper_id, websocket)
    print(f"WebSocket connected for paper {paper_id}")
    try:
        # Send initial connection message
        await websocket.send_text(json.dumps({"type": "connected", "message": "Connected to logs"}))
        
        # Keep connection alive - just wait for disconnection
        # Don't require client to send messages, just keep the connection open
        # The manager will send logs as they come in from the agent
        while True:
            try:
                # Wait for client disconnect or a message (but don't require messages)
                # Use a long timeout so we can keep the connection open
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
                # If client sends "ping", respond with "pong"
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except asyncio.TimeoutError:
                # Connection is still alive, just send a keepalive and continue
                try:
                    await websocket.send_text(json.dumps({"type": "keepalive"}))
                except Exception as e:
                    print(f"Error sending keepalive, connection likely closed: {e}")
                    break
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for paper {paper_id}")
                break
    except Exception as e:
        print(f"WebSocket error for paper {paper_id}: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.disconnect(paper_id)
        print(f"WebSocket cleaned up for paper {paper_id}")


# --- THIS IS THE DEFINITIVE PATHING FIX ---
# Mount the 'videos' directory at the top level of the API.
videos_dir = Path("videos")
os.makedirs(videos_dir, exist_ok=True)
app.mount("/api/videos", StaticFiles(directory=videos_dir), name="videos")

app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(video.router, prefix="/api", tags=["video"])
