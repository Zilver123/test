from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import asyncio
from typing import List, Optional
from agent import main as agent_main
import os
from pathlib import Path

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Create videos directory if it doesn't exist
videos_dir = Path("videos")
videos_dir.mkdir(exist_ok=True)

# Mount the videos directory
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# Store active WebSocket connections
active_connections: List[WebSocket] = []

class GenerateRequest(BaseModel):
    url: str
    prompt: str

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("[DEBUG] New WebSocket connection request")
    try:
        await websocket.accept()
        print("[DEBUG] WebSocket connection accepted")
        active_connections.append(websocket)
        
        # Send initial connection success message
        await websocket.send_json({
            "type": "connection_status",
            "status": "connected"
        })
        
        while True:
            try:
                data = await websocket.receive_text()
                print(f"[DEBUG] Received WebSocket message: {data}")
                # Handle any incoming WebSocket messages here
            except json.JSONDecodeError:
                print("[DEBUG] Invalid JSON received")
                continue
            except WebSocketDisconnect:
                print("[DEBUG] WebSocket disconnected")
                if websocket in active_connections:
                    active_connections.remove(websocket)
                break
    except Exception as e:
        print(f"[DEBUG] WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/generate")
async def generate_video(request: GenerateRequest):
    try:
        # Get the first active WebSocket connection
        websocket = active_connections[0] if active_connections else None
        
        if not websocket:
            raise HTTPException(status_code=400, detail="No active WebSocket connection")
        
        # Call the agent's main function
        result = await agent_main(
            url=request.url,
            user_prompt=request.prompt,
            websocket=websocket
        )
        
        if isinstance(result, dict) and "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
            
        return JSONResponse(content=result)
    except Exception as e:
        print(f"[ERROR] Error in generate endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.options("/generate")
async def options_generate():
    return JSONResponse(content={})

@app.get("/")
async def root():
    return {"message": "Marketing Video Generator API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 