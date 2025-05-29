from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import sys
import os
import json

# Add the parent directory to Python path to import agent.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent import main as agent_main

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoRequest(BaseModel):
    url: str
    prompt: str

class VideoResponse(BaseModel):
    product_info: str
    image_urls: list
    image_analysis: str
    storyboard: str = ""
    video_path: str = ""

@app.post("/generate")
async def generate_video(request: VideoRequest):
    try:
        # Run the agent with the provided URL and prompt
        result = await agent_main(request.url, request.prompt)
        
        # Extract the analysis data from the result
        if isinstance(result, dict):
            analysis_data = result
        else:
            # If result is a string, try to parse it as JSON
            try:
                analysis_data = json.loads(result)
            except:
                # If parsing fails, create a basic response
                analysis_data = {
                    "product_info": str(result),
                    "image_urls": [],
                    "image_analysis": "Analysis not available"
                }
        
        # Create response object
        response = VideoResponse(
            product_info=analysis_data.get("product_info", ""),
            image_urls=analysis_data.get("image_urls", []),
            image_analysis=analysis_data.get("image_analysis", ""),
            storyboard=analysis_data.get("storyboard", ""),
            video_path=analysis_data.get("video_path", "")
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 