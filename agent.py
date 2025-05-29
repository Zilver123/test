import asyncio
from agents.agent import Agent
from agents.run import Runner
import re
from media.models import AnalysisData
from media.analyzer import MediaAnalyzer
from media.tools import get_product_info_tool, analyze_media_tool, merge_images_to_video_tool
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from moviepy.editor import ImageClip, concatenate_videoclips
import json


agent = Agent(
    name="Marketing Agent",
    instructions="""You are a marketing agent specialized in creating high-quality marketing videos through an iterative process. The input will include pre-analyzed data in the [ANALYSIS_DATA] section. Use this data for all iterations.

    Follow these steps in order:

    1. Use Provided Analysis:
       - Product information is in analysis_data["product_info"]
       - Image URLs are in analysis_data["image_urls"]
       - Image analysis is in analysis_data["image_analysis"]
       - Use this data for all storyboard iterations

    2. Storyboard Creation:
       Create a storyboard in the following format:
       [STORYBOARD]
       Scene 1:
       Media: [image/video URL]
       Media Description: [detailed description of the visual]
       Script: [voice over text]
       Duration: [seconds]
       ---
       Scene 2:
       Media: [image/video URL]
       Media Description: [detailed description of the visual]
       Script: [voice over text]
       Duration: [seconds]
       ---
       [END STORYBOARD]

       Guidelines for storyboard creation:
       - Each scene should have a clear purpose in the marketing narrative
       - Media descriptions should be detailed enough for visual understanding
       - Script should be concise and impactful
       - Durations should be appropriate for the content (typically 3-5 seconds per scene)
       - Total video length should be 30-60 seconds

    3. Video Generation:
       - Extract media URLs and durations from the storyboard
       - Call merge_images_to_video_tool with the ordered URLs and durations
       - The tool will return a video_path

    Output Format:
    For each iteration, present:
    1. The current storyboard
    2. The video generation results
    """,
    tools=[get_product_info_tool, analyze_media_tool, merge_images_to_video_tool],
)


async def main(url: str = None, user_prompt: str = None, websocket = None):
    """Main function to run the marketing video creation process"""
    if url is None:
        url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    if user_prompt is None:
        user_prompt = "Create a marketing video that highlights the comfort and warmth features of this plush toy"
    
    # Initial analysis phase
    print("\n=== Initial Analysis Phase ===")
    
    # Get product info using the agent
    result = await Runner.run(agent, input=f"Get product information from {url}")
    product_info = result.final_output
    print("\n[DEBUG] Product info scraped:")
    print(product_info)
    
    # Extract image URLs from product info
    image_urls = []
    lines = product_info.split('\n')
    for line in lines:
        if 'http' in line:
            url_match = re.search(r'https?://[^\s<>"]+?(?:\.jpg|\.jpeg|\.png|\.gif)(?:\?[^\s<>"]*)?', line)
            if url_match:
                url = url_match.group(0)
                if url not in image_urls:
                    image_urls.append(url)
    
    if not image_urls:
        print("\n[ERROR] No image URLs found in product info. Using fallback URLs...")
        image_urls = [
            "https://www.uncomfy.store/cdn/shop/files/IMG_8222.jpg?v=1744352119&width=1445",
            "https://www.uncomfy.store/cdn/shop/files/IMG_82232.jpg?v=1744352078&width=1946"
        ]
    
    print(f"\n[DEBUG] Found {len(image_urls)} image URLs:")
    for url in image_urls:
        print(f"- {url}")
    
    # Analyze images using MediaAnalyzer directly
    print("\n[DEBUG] Analyzing product images...")
    analyzer = MediaAnalyzer()
    image_analysis = await analyzer.analyze_media(image_urls=image_urls)
    print("\n[DEBUG] Image analysis complete:")
    print(image_analysis)
    
    # Create analysis data
    analysis_data = {
        "product_info": product_info,
        "image_urls": image_urls,
        "image_analysis": image_analysis
    }
    
    # Generate video using the agent with analysis data
    print("\n=== Video Generation Phase ===")
    result = await Runner.run(
        agent,
        input=f"""Create a marketing video based on this analysis data:
        [ANALYSIS_DATA]
        {json.dumps(analysis_data, indent=2)}
        [/ANALYSIS_DATA]
        
        User Prompt: {user_prompt}
        """
    )
    
    # Extract video path from the result
    video_path = None
    if isinstance(result.final_output, dict):
        video_path = result.final_output.get("video_path")
    else:
        # Try to find video path in the text output
        video_match = re.search(r'Video Path: `(.*?)`', result.final_output)
        if video_match:
            video_path = video_match.group(1)
    
    # Create video using the video generator
    if video_path is None:
        print("\n[DEBUG] No video path found in agent output, generating video directly...")
        generator = VideoGenerator(websocket)
        durations = [3.0] * len(image_urls)  # Default 3 seconds per image
        result = await generator.create_video(image_urls, durations)
        video_path = result.get("video_path")
    
    # Return the complete analysis data
    return {
        "product_info": product_info,
        "image_urls": image_urls,
        "image_analysis": image_analysis,
        "storyboard": result.final_output if isinstance(result.final_output, str) else "",
        "video_path": video_path
    }


async def generate_video(self, image_urls: List[str], durations: List[float]) -> Dict[str, str]:
    """Generate a video from a list of image URLs and durations."""
    try:
        await manager.broadcast("Starting video generation process...")
        
        # Validate inputs
        if not image_urls or not durations:
            raise ValueError("Image URLs and durations must not be empty")
        if len(image_urls) != len(durations):
            raise ValueError("Number of image URLs must match number of durations")
        
        await manager.broadcast(f"Processing {len(image_urls)} scenes...")
        
        # Create video clips
        clips = []
        for i, (url, duration) in enumerate(zip(image_urls, durations)):
            await manager.broadcast(f"Processing scene {i + 1}/{len(image_urls)}...")
            try:
                clip = await self._create_clip(url, duration)
                clips.append(clip)
                await manager.broadcast(f"Scene {i + 1} processed successfully")
            except Exception as e:
                await manager.broadcast(f"Error processing scene {i + 1}: {str(e)}")
                raise
        
        await manager.broadcast("All scenes processed. Merging into final video...")
        
        # Generate the final video
        output_path = await self._generate_video(clips)
        await manager.broadcast("Video generation complete!")
        
        return {
            "video_path": output_path,
            "message": "Video generated successfully"
        }
    except Exception as e:
        error_msg = f"Error in video generation: {str(e)}"
        await manager.broadcast(f"Error: {error_msg}")
        raise Exception(error_msg)

async def _generate_video(self, clips: List[ImageClip]) -> str:
    """Generate the final video from clips."""
    try:
        await manager.broadcast("Starting final video compilation...")
        
        # Create output directory if it doesn't exist
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(output_dir / f"marketing_video_{timestamp}.mp4")
        
        await manager.broadcast("Rendering video...")
        
        # Merge clips into final video
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        await manager.broadcast("Video rendering complete!")
        return output_path
    except Exception as e:
        error_msg = f"Error in video compilation: {str(e)}"
        await manager.broadcast(f"Error: {error_msg}")
        raise Exception(error_msg)


if __name__ == "__main__":
    asyncio.run(main())