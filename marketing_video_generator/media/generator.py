import os
import tempfile
import requests
from typing import List, Dict, Optional
from datetime import datetime
from PIL import Image
from moviepy.editor import ImageClip, concatenate_videoclips
from pathlib import Path
import json
import asyncio
from fastapi import WebSocket

class VideoGenerator:
    """Handles video generation from images"""
    
    def __init__(self, websocket: Optional[WebSocket] = None):
        self.target_width = 1080  # TikTok vertical format width
        self.target_height = 1920  # TikTok vertical format height
        self.websocket = websocket

    async def _send_update(self, message: str, message_type: str = "update"):
        """Send update to UI if websocket is available"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": message_type,
                    "message": message
                })
            except Exception as e:
                print(f"[DEBUG] Failed to send websocket update: {e}")

    async def create_video(self, image_urls: List[str], 
                          durations: Optional[List[float]] = None) -> Dict:
        """Create a video from a list of image URLs"""
        print(f"[DEBUG] Starting video generation with {len(image_urls)} images")
        await self._send_update("Starting video generation...")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                print(f"[DEBUG] Created temporary directory: {tmpdir}")
                image_paths = await self._download_images(image_urls, tmpdir)
                if not image_paths:
                    print("[DEBUG] No images could be downloaded")
                    return {"error": "No images could be downloaded."}

                print(f"[DEBUG] Downloaded {len(image_paths)} images")
                clips = await self._create_clips(image_paths, durations)
                print(f"[DEBUG] Created {len(clips)} video clips")
                output_path = await self._generate_video(clips)
                print(f"[DEBUG] Generated video at: {output_path}")
                
                # Send the video path to UI immediately
                web_path = f"/videos/{Path(output_path).name}"
                print(f"[DEBUG] Sending video ready message with path: {web_path}")
                await self._send_update(web_path, "video_ready")
                
                return {"video_path": output_path, 
                       "message": f"Video saved to {output_path}"}
        except Exception as e:
            error_msg = f"Error creating video: {e}"
            print(f"[DEBUG] {error_msg}")
            await self._send_update(f"Error: {error_msg}")
            return {"error": error_msg}

    async def _download_images(self, urls: List[str], tmpdir: str) -> List[str]:
        """Download images from URLs to temporary directory"""
        image_paths = []
        for idx, url in enumerate(urls):
            img_path = os.path.join(tmpdir, f"img_{idx}.jpg")
            try:
                print(f"[DEBUG] Downloading image {idx + 1}/{len(urls)} from {url}")
                await self._send_update(f"Downloading image {idx + 1}/{len(urls)}...")
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(r.content)
                print(f"[DEBUG] Saved image to {img_path}")
                image_paths.append(img_path)
            except Exception as e:
                print(f"[DEBUG] Failed to download {url}: {e}")
                await self._send_update(f"Failed to download image {idx + 1}: {e}")
        return image_paths

    async def _create_clips(self, image_paths: List[str], 
                           durations: Optional[List[float]]) -> List[ImageClip]:
        """Create video clips from images with proper formatting"""
        clips = []
        for idx, path in enumerate(image_paths):
            duration = durations[idx] if durations and idx < len(durations) else 3.0
            print(f"[DEBUG] Creating clip {idx + 1}/{len(image_paths)} with duration {duration}s")
            await self._send_update(f"Creating clip {idx + 1}/{len(image_paths)}...")
            
            processed_path = await self._process_image(path, idx)
            clip = ImageClip(processed_path).set_duration(duration)
            clips.append(clip)
        return clips

    async def _process_image(self, image_path: str, idx: int) -> str:
        """Process image to fit vertical format"""
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # Calculate scaling to fit the target dimensions while maintaining aspect ratio
        scale = min(self.target_width / img_width, self.target_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create a black background
        background = Image.new('RGB', (self.target_width, self.target_height), (0, 0, 0))
        
        # Calculate position to center the image
        x = (self.target_width - new_width) // 2
        y = (self.target_height - new_height) // 2
        
        # Paste the resized image onto the background
        background.paste(img, (x, y))
        
        # Save the processed image
        processed_path = os.path.join(os.path.dirname(image_path), f"processed_{idx}.jpg")
        background.save(processed_path)
        return processed_path

    async def _generate_video(self, clips: List[ImageClip]) -> str:
        """Generate final video from clips"""
        print("[DEBUG] Starting video compilation")
        await self._send_update("Concatenating video clips...")
        video = concatenate_videoclips(clips, method="compose")
        
        # Create videos directory if it doesn't exist
        videos_dir = Path("videos")
        videos_dir.mkdir(exist_ok=True)
        print(f"[DEBUG] Using videos directory: {videos_dir.absolute()}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(videos_dir / f"marketing_video_{timestamp}.mp4")
        print(f"[DEBUG] Will save video to: {output_path}")
        await self._send_update("Rendering final video...")
        
        print("[DEBUG] Writing video file...")
        video.write_videofile(output_path, fps=24, codec="libx264", audio=False)
        video.close()
        
        if os.path.exists(output_path):
            print(f"[DEBUG] Verified file exists at: {output_path}")
            file_size = os.path.getsize(output_path)
            print(f"[DEBUG] File size: {file_size} bytes")
            await self._send_update("Video generation complete!")
        else:
            print(f"[DEBUG] WARNING: File not found at: {output_path}")
            await self._send_update("Error: Video file not found after generation")
        
        return output_path 