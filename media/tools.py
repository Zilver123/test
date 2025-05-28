from agents.tool import function_tool
from typing import List, Dict, Optional
from .analyzer import MediaAnalyzer
from .generator import VideoGenerator
from scraper import get_product_info


@function_tool
def get_product_info_tool(url: str) -> str:
    """Get product information from a URL"""
    result = get_product_info(url)
    print("[DEBUG] Product info scraped:")
    print(result)
    return result


@function_tool
async def analyze_media_tool(media_path: Optional[str] = None, 
                           image_urls: Optional[List[str]] = None, 
                           num_frames: int = 5) -> str:
    """Analyze media using OpenAI's API"""
    analyzer = MediaAnalyzer()
    return await analyzer.analyze_media(media_path, image_urls, num_frames)


@function_tool
async def merge_images_to_video_tool(image_urls: List[str], 
                                   durations: Optional[List[float]] = None) -> Dict:
    """Create a video from a list of image URLs"""
    generator = VideoGenerator()
    return await generator.create_video(image_urls, durations) 