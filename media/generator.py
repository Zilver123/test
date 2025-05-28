import os
import tempfile
import requests
from typing import List, Dict, Optional
from datetime import datetime
from PIL import Image
from moviepy.editor import ImageClip, concatenate_videoclips


class VideoGenerator:
    """Handles video generation from images"""
    
    def __init__(self):
        self.target_width = 1080  # TikTok vertical format width
        self.target_height = 1920  # TikTok vertical format height

    async def create_video(self, image_urls: List[str], 
                          durations: Optional[List[float]] = None) -> Dict:
        """Create a video from a list of image URLs"""
        print(f"[DEBUG] Merging {len(image_urls)} images into video")
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                image_paths = await self._download_images(image_urls, tmpdir)
                if not image_paths:
                    return {"error": "No images could be downloaded."}

                clips = await self._create_clips(image_paths, durations)
                output_path = await self._generate_video(clips)
                
                return {"video_path": output_path, 
                       "message": f"Video saved to {output_path}"}
        except Exception as e:
            error_msg = f"Error creating video: {e}"
            print(f"[DEBUG] {error_msg}")
            return {"error": error_msg}

    async def _download_images(self, urls: List[str], tmpdir: str) -> List[str]:
        """Download images from URLs to temporary directory"""
        image_paths = []
        for idx, url in enumerate(urls):
            img_path = os.path.join(tmpdir, f"img_{idx}.jpg")
            try:
                print(f"[DEBUG] Downloading image {idx + 1}/{len(urls)} from {url}")
                r = requests.get(url, timeout=10)
                r.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(r.content)
                print(f"[DEBUG] Saved image to {img_path}")
                image_paths.append(img_path)
            except Exception as e:
                print(f"[DEBUG] Failed to download {url}: {e}")
        return image_paths

    async def _create_clips(self, image_paths: List[str], 
                           durations: Optional[List[float]]) -> List[ImageClip]:
        """Create video clips from images with proper formatting"""
        clips = []
        for idx, path in enumerate(image_paths):
            duration = durations[idx] if durations and idx < len(durations) else 3.0
            print(f"[DEBUG] Creating clip {idx + 1}/{len(image_paths)} with duration {duration}s")
            
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
        print("[DEBUG] Concatenating video clips")
        video = concatenate_videoclips(clips, method="compose")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.expanduser(f"~/Desktop/marketing_video_{timestamp}.mp4")
        print(f"[DEBUG] Will save video to: {output_path}")
        
        print("[DEBUG] Writing video file...")
        video.write_videofile(output_path, fps=24, codec="libx264", audio=False)
        video.close()
        
        if os.path.exists(output_path):
            print(f"[DEBUG] Verified file exists at: {output_path}")
            file_size = os.path.getsize(output_path)
            print(f"[DEBUG] File size: {file_size} bytes")
        else:
            print(f"[DEBUG] WARNING: File not found at: {output_path}")
        
        return output_path 