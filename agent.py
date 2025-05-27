import asyncio
from agents import Agent, Runner, function_tool
from scraper import get_product_info
from replicate_api import ReplicateClient
import os
import tempfile
import requests
from moviepy.editor import ImageClip, concatenate_videoclips, VideoFileClip
from typing import List, Dict
import cv2
import numpy as np
import base64
from datetime import datetime


@function_tool
def get_product_info_tool(url: str) -> str:
    result = get_product_info(url)
    print("[DEBUG] Product info scraped:")
    print(result)
    return result


@function_tool
async def analyze_image_tool(image_urls: List[str], prompt: str = "Describe this product image in detail, focusing on visual elements that would be important for a marketing video. Include details about colors, composition, and any notable features.") -> str:
    print(f"[DEBUG] Analyzing {len(image_urls)} images with prompt: {prompt}")
    try:
        client = ReplicateClient()
        results = []
        for url in image_urls:
            try:
                result = await client.analyze_image(url, prompt)
                if result.status == "error":
                    print(f"[DEBUG] Error analyzing image {url}: {result.error}")
                    results.append({"url": url, "description": f"Error: {result.error}"})
                elif not result.output:
                    print(f"[DEBUG] No output received for image {url}")
                    results.append({"url": url, "description": "No analysis available"})
                else:
                    print(f"[DEBUG] Successfully analyzed image {url}")
                    results.append({"url": url, "description": result.output})
            except Exception as e:
                print(f"[DEBUG] Exception analyzing image {url}: {str(e)}")
                results.append({"url": url, "description": f"Error: {str(e)}"})
        
        # Format results as a structured string
        formatted_results = "Image Analysis Results:\n"
        for idx, result in enumerate(results, 1):
            formatted_results += f"\nImage {idx}:\n"
            formatted_results += f"URL: {result['url']}\n"
            formatted_results += f"Description: {result['description']}\n"
            formatted_results += "-" * 80 + "\n"
        
        return formatted_results
    except Exception as e:
        error_msg = f"Exception during batch image analysis: {str(e)}"
        print(f"[DEBUG] {error_msg}")
        return error_msg


@function_tool
async def merge_images_to_video_tool(image_urls: List[str], durations: List[float] = None) -> dict:
    print(f"[DEBUG] Merging {len(image_urls)} images into video")
    try:
        # Create a temporary directory to store images
        with tempfile.TemporaryDirectory() as tmpdir:
            print(f"[DEBUG] Created temporary directory: {tmpdir}")
            image_paths = []
            for idx, url in enumerate(image_urls):
                img_path = os.path.join(tmpdir, f"img_{idx}.jpg")
                try:
                    print(f"[DEBUG] Downloading image {idx + 1}/{len(image_urls)} from {url}")
                    r = requests.get(url, timeout=10)
                    r.raise_for_status()
                    with open(img_path, "wb") as f:
                        f.write(r.content)
                    print(f"[DEBUG] Saved image to {img_path}")
                    image_paths.append(img_path)
                except Exception as e:
                    print(f"[DEBUG] Failed to download {url}: {e}")
            
            if not image_paths:
                return {"error": "No images could be downloaded."}
            
            print(f"[DEBUG] Successfully downloaded {len(image_paths)} images")
            
            # Create video clips from images
            clips = []
            for idx, path in enumerate(image_paths):
                duration = durations[idx] if durations and idx < len(durations) else 3.0
                print(f"[DEBUG] Creating clip {idx + 1}/{len(image_paths)} with duration {duration}s")
                clip = ImageClip(path).set_duration(duration)
                clips.append(clip)
            
            print("[DEBUG] Concatenating video clips")
            video = concatenate_videoclips(clips, method="compose")
            
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.expanduser(f"~/Desktop/marketing_video_{timestamp}.mp4")
            print(f"[DEBUG] Will save video to: {output_path}")
            
            print("[DEBUG] Writing video file...")
            video.write_videofile(output_path, fps=24, codec="libx264", audio=False)
            video.close()
            print(f"[DEBUG] Video successfully saved to: {output_path}")
            
            # Verify the file exists
            if os.path.exists(output_path):
                print(f"[DEBUG] Verified file exists at: {output_path}")
                file_size = os.path.getsize(output_path)
                print(f"[DEBUG] File size: {file_size} bytes")
            else:
                print(f"[DEBUG] WARNING: File not found at: {output_path}")
            
            return {"video_path": output_path, "message": f"Video saved to {output_path}"}
    except Exception as e:
        error_msg = f"Error creating video: {e}"
        print(f"[DEBUG] {error_msg}")
        return {"error": error_msg}


@function_tool
async def analyze_video_tool(video_path: str, num_frames: int = 5) -> str:
    """
    Analyze a video by extracting frames and using GPT-4V to describe the storyline.
    
    Args:
        video_path: Path to the video file
        num_frames: Number of frames to extract for analysis (default: 5)
    
    Returns:
        A description of the video's storyline based on frame analysis
    """
    print(f"[DEBUG] Analyzing video: {video_path}")
    try:
        if not os.path.exists(video_path):
            return f"Error: Video file not found at {video_path}"
            
        # Create a temporary directory for frames
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                # Open the video file
                video = VideoFileClip(video_path)
                duration = video.duration
                
                # Calculate frame timestamps
                timestamps = np.linspace(0, duration, num_frames)
                
                # Extract frames
                frame_paths = []
                for idx, timestamp in enumerate(timestamps):
                    try:
                        frame = video.get_frame(timestamp)
                        frame_path = os.path.join(tmpdir, f"frame_{idx}.jpg")
                        cv2.imwrite(frame_path, cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                        frame_paths.append(frame_path)
                    except Exception as e:
                        print(f"[DEBUG] Error extracting frame at {timestamp}s: {e}")
                
                if not frame_paths:
                    return "Error: Could not extract any frames from the video"
                
                # Analyze frames using GPT-4V
                client = ReplicateClient()
                prompt = """Analyze these frames from a marketing video and describe:
1. The overall storyline and progression
2. Key visual elements and their significance
3. How the frames work together to tell the product's story
4. The emotional impact and messaging
5. Suggestions for improvement (if any)

Focus on how the visual narrative supports the marketing goals."""
                
                results = []
                for idx, frame_path in enumerate(frame_paths):
                    try:
                        # Read the frame as base64
                        with open(frame_path, "rb") as f:
                            frame_data = f.read()
                        frame_b64 = base64.b64encode(frame_data).decode()
                        
                        # Analyze frame using Replicate API
                        result = await client.analyze_image(frame_b64, prompt)
                        if result.status == "success" and result.output:
                            results.append({
                                "timestamp": timestamps[idx],
                                "analysis": result.output
                            })
                    except Exception as e:
                        print(f"[DEBUG] Error analyzing frame {idx}: {e}")
                
                # Compile results into a storyline
                if not results:
                    return "No frames could be analyzed."
                
                storyline = "Video Storyline Analysis:\n\n"
                for result in results:
                    storyline += f"At {result['timestamp']:.1f}s:\n"
                    storyline += f"{result['analysis']}\n"
                    storyline += "-" * 80 + "\n"
                
                return storyline
                
            except Exception as e:
                return f"Error reading video file: {e}"
            finally:
                if 'video' in locals():
                    video.close()
            
    except Exception as e:
        return f"Error analyzing video: {e}"


agent = Agent(
    name="Marketing Agent",
    instructions="""You are a marketing agent specialized in creating high-quality marketing videos. Follow these steps in order:

    1. Product Information Gathering:
       - Use get_product_info_tool to scrape and extract all product details from the URL
       - Document key features, benefits, and unique selling points
       - Extract all unique image URLs from the product information

    2. Image Analysis:
       - Call analyze_image_tool once with ALL unique image URLs
       - The tool will return structured results with both URLs and descriptions
       - Document key visual features and potential video scenes based on the analysis

    3. User Intent Analysis:
       - Analyze the user prompt to understand marketing goals
       - Extract specific requirements and preferences
       - Document key marketing objectives

    4. Target Audience Definition:
       - Based on product features and user intent, define:
         * Primary and secondary target audiences
         * Demographics and psychographics
         * Pain points and desires
         * Platform preferences

    5. Video Style Selection:
       Choose one primary style from:
       - Educational: Focus on product features and benefits
       - Storytime: Narrative-driven approach
       - UGC-style: Authentic, user-generated content feel
       - Aesthetic: Visually focused, lifestyle-oriented
       - Question-based: Problem-solution format
       Justify the style choice based on target audience and product type

    6. Storyboard Creation:
       Create a detailed scene-by-scene storyboard including:
       - Scene number and duration
       - Visual elements and transitions
       - Key messaging points
       - Music and sound effects
       - Text overlays or graphics
       - For each scene, specify:
         * The exact image URL to use
         * Why this image was chosen
         * How it supports the scene's message

    7. Script Development:
       Write a complete script that includes:
       - Opening hook
       - Main content sections
       - Call to action
       - Voice-over text
       - Timing for each section

    8. Video Creation and Iterative Analysis:
       - Extract the ordered list of image URLs from the storyboard
       - Call merge_images_to_video_tool with the ordered URLs and durations
       - The tool will return a video_path
       - Call analyze_video_tool with the video_path
       - Review the storyline analysis and ensure it aligns with marketing goals
       - If the analysis suggests improvements (e.g., image order, timing, or selection), update the storyboard/image list and re-run merge_images_to_video_tool and analyze_video_tool as needed until the video meets the marketing objectives

    Output Format:
    Present the complete marketing video plan in a structured format with clear sections for each step.
    Include both the image URLs and their descriptions in the storyboard section.
    End with the video analysis results and any suggested improvements or iterations made.
    """,
    tools=[get_product_info_tool, analyze_image_tool, merge_images_to_video_tool, analyze_video_tool],
)


async def main():
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    user_prompt = "Create a marketing video that highlights the comfort and warmth features of this plush toy"
    
    # Format the input as a string with both URL and prompt
    input_text = f"URL: {url}\nPrompt: {user_prompt}"
    result = await Runner.run(agent, input=input_text)
    print(result.final_output)


async def test_scraping_and_image_analytics():
    print("\n=== Testing Product Info Tool ===")
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    from scraper import get_product_info
    result = get_product_info(url)
    print(f"Product Info Result: {result}")

    print("\n=== Testing Image Analysis Tool ===")
    image_urls = [
        "https://www.uncomfy.store/cdn/shop/files/IMG_8222.jpg?v=1744352119&width=1445",
        "https://www.uncomfy.store/cdn/shop/files/IMG_82232.jpg?v=1744352078&width=1946"
    ]
    prompt = "Describe this image in detail."
    client = ReplicateClient()
    analysis_result = await analyze_image_tool(image_urls, prompt)
    print(analysis_result)


if __name__ == "__main__":
    asyncio.run(main())