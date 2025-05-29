from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
from pydantic import BaseModel
from .tools.scrape_url import scrape_url
from .tools.analyze_media import analyze_media
from .tools.generate_storyboard import generate_storyboard
from .tools.render_video import render_video

app = FastAPI()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/api/input")
async def input_phase(
    product_url: Optional[str] = Form(None),
    creative_prompt: str = Form(...),
    media: Optional[List[UploadFile]] = File(None)
):
    # Scrape product info if URL provided
    product_data = scrape_url(product_url) if product_url else {}
    # Save uploaded media
    media_files = []
    if media:
        for file in media:
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(await file.read())
            media_files.append(file_path)
    # Analyze media
    media_descriptions = analyze_media(media_files) if media_files else {}
    # Generate storyboard
    storyboard = generate_storyboard(product_data, media_descriptions, creative_prompt)
    return JSONResponse({
        "product": product_data,
        "creative_prompt": creative_prompt,
        "media_files": media_files,
        "media_descriptions": media_descriptions,
        "storyboard": storyboard
    })

class RenderVideoRequest(BaseModel):
    storyboard: str
    media_files: List[str]

@app.post("/api/render_video")
async def render_video_endpoint(req: RenderVideoRequest):
    output_path = os.path.join(UPLOAD_DIR, "output.mp4")
    video_path = render_video(req.storyboard, req.media_files, output_path)
    return JSONResponse({"video_path": video_path}) 