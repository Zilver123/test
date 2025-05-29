from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Set
import uvicorn
from agent import main as agent_main
from media.analyzer import MediaAnalyzer
from media.tools import merge_images_to_video_tool
import asyncio
import tempfile
import os
from pathlib import Path
from pydantic import BaseModel
import json
import logging
import traceback
from datetime import datetime

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Store recent logs in memory
recent_logs = []
MAX_LOGS = 100

class LogHandler(logging.Handler):
    def emit(self, record):
        log_entry = self.format(record)
        recent_logs.append(log_entry)
        if len(recent_logs) > MAX_LOGS:
            recent_logs.pop(0)

# Add the custom handler
logger.addHandler(LogHandler())

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            return
        logger.info(f"Broadcasting message: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {str(e)}")
                self.active_connections.remove(connection)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive and handle any incoming messages
            data = await websocket.receive_text()
            logger.info(f"Received WebSocket message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

class Scene(BaseModel):
    id: str
    mediaUrl: str
    script: str
    duration: float

class VideoRequest(BaseModel):
    scenes: List[Scene]

@app.get("/debug")
async def get_debug_info():
    """Get current state and recent logs"""
    try:
        # Get the last 20 lines of the log file
        with open('api.log', 'r') as f:
            file_logs = f.readlines()[-20:]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recent_logs": recent_logs[-20:],
            "file_logs": file_logs,
            "active_connections": len(app.state.get("active_connections", [])),
            "last_error": app.state.get("last_error"),
        }
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/analyze")
async def analyze_media(
    url: Optional[str] = Form(None),
    prompt: Optional[str] = Form(None),
    files: List[UploadFile] = File([])
):
    try:
        logger.info(f"Received analyze request - URL: {url}, Prompt: {prompt}, Files: {[f.filename for f in files]}")
        
        if not url and not files:
            raise HTTPException(status_code=400, detail="Either URL or files must be provided")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")

        # Initialize the agent
        try:
            agent = await agent_main()
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize agent: {str(e)}")

        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            if files:
                for file in files:
                    try:
                        file_path = Path(temp_dir) / file.filename
                        with open(file_path, "wb") as f:
                            f.write(await file.read())
                        file_paths.append(str(file_path))
                        logger.info(f"Saved file to: {file_path}")
                    except Exception as e:
                        logger.error(f"Error saving file {file.filename}: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

            try:
                # Use the agent to analyze media - only once
                if url:
                    logger.info(f"Analyzing URL: {url}")
                    result = await agent.analyze_media(url, prompt)
                else:
                    logger.info(f"Analyzing files: {file_paths}")
                    result = await agent.analyze_media(file_paths, prompt)

                logger.info(f"Analysis result: {result}")

                # Convert agent result to scenes
                scenes = []
                for idx, (media_url, analysis) in enumerate(result.items()):
                    scenes.append({
                        "id": str(idx + 1),
                        "mediaUrl": media_url,
                        "script": analysis.get("description", ""),
                        "duration": 5.0
                    })
                
                logger.info(f"Returning {len(scenes)} scenes")
                return {"scenes": scenes}

            except Exception as e:
                logger.error(f"Error during media analysis: {str(e)}")
                logger.error(traceback.format_exc())
                raise HTTPException(status_code=500, detail=f"Media analysis failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_media: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.post("/generate-video")
async def generate_video(request: VideoRequest):
    try:
        logger.info(f"Received video generation request with {len(request.scenes)} scenes")
        await manager.broadcast("Starting video generation...")
        
        # Initialize the agent
        try:
            agent = await agent_main()
            logger.info("Agent initialized successfully")
            await manager.broadcast("Agent initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize agent: {str(e)}"
            logger.error(error_msg)
            await manager.broadcast(f"Error: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        image_urls = [scene.mediaUrl for scene in request.scenes]
        durations = [scene.duration for scene in request.scenes]

        logger.info(f"Generating video with {len(image_urls)} images")
        await manager.broadcast(f"Processing {len(image_urls)} scenes...")
        
        result = await agent.generate_video(image_urls, durations)
        logger.info(f"Video generation result: {result}")
        await manager.broadcast("Video generation complete!")

        # Return the video URL and stop - no more analysis
        return {
            "video_url": result["video_path"],
            "message": "Video generated successfully"
        }
    except Exception as e:
        error_msg = f"Error in generate_video: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        await manager.broadcast(f"Error: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 