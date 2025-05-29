import json
from typing import Dict, Optional
from media.generator import VideoGenerator
import requests
from bs4 import BeautifulSoup

async def main(url: str = None, user_prompt: str = None, websocket = None):
    try:
        # Initialize video generator with WebSocket for updates
        generator = VideoGenerator(websocket=websocket)
        
        # Fetch images from the provided URL
        image_urls = []
        if url:
            try:
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                # Look for images in the page
                for img in soup.find_all('img'):
                    src = img.get('src')
                    if src and (src.endswith('.jpg') or src.endswith('.jpeg') or src.endswith('.png')):
                        if not src.startswith('http'):
                            # Handle relative URLs
                            if src.startswith('/'):
                                base_url = '/'.join(url.split('/')[:3])
                                src = base_url + src
                            else:
                                src = url + '/' + src
                        image_urls.append(src)
            except Exception as e:
                print(f"[ERROR] Error fetching images from URL: {e}")
        
        # If no images found, use sample images
        if not image_urls:
            image_urls = [
                "https://www.uncomfy.store/cdn/shop/files/IMG_8222.jpg?v=1744352119&width=1445",
                "https://www.uncomfy.store/cdn/shop/files/IMG_82232.jpg?v=1744352078&width=1946"
            ]
        
        # Generate video
        result = await generator.create_video(image_urls)
        
        if "error" in result:
            return result
            
        # Return result with additional information
        return {
            "product_info": f"Product information based on {url}",
            "image_urls": image_urls,
            "image_analysis": f"Analysis based on {user_prompt}",
            "storyboard": f"Storyboard based on {user_prompt}",
            "video_path": result["video_path"]
        }
    except Exception as e:
        print(f"[ERROR] Error in agent main: {e}")
        return {
            "error": str(e),
            "product_info": "",
            "image_urls": [],
            "image_analysis": "",
            "storyboard": "",
            "video_path": ""
        } 