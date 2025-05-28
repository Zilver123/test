import asyncio
from agents.agent import Agent
from agents.run import Runner
import re
from media.models import AnalysisData
from media.analyzer import MediaAnalyzer
from media.tools import get_product_info_tool, analyze_media_tool, merge_images_to_video_tool


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

    4. Video Analysis:
       - Call analyze_media_tool with the video_path
       - Review the analysis and compare it with the original storyboard
       - Identify any gaps or areas for improvement

    5. Iterative Improvement:
       If the user requests changes:
       - Parse the user's feedback
       - Update the storyboard accordingly
       - Regenerate the video
       - Re-analyze the new version
       - Continue until the user is satisfied

    Output Format:
    For each iteration, present:
    1. The current storyboard
    2. The video generation results
    3. The video analysis
    4. A prompt for user feedback

    The user can then provide feedback in the format:
    [FEEDBACK]
    Scene X: [specific changes requested]
    [END FEEDBACK]

    Continue this process until the user indicates satisfaction with the final video.
    """,
    tools=[get_product_info_tool, analyze_media_tool, merge_images_to_video_tool],
)


async def main():
    """Main function to run the marketing video creation process"""
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
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
    
    # Analyze images using the agent
    print("\n[DEBUG] Analyzing product images...")
    try:
        result = await Runner.run(agent, input=f"Analyze these images: {', '.join(image_urls)}")
        image_analysis = result.final_output
        if "Error" in image_analysis or "No media could be analyzed" in image_analysis:
            raise Exception("Image analysis failed")
        print(image_analysis)
    except Exception as e:
        print(f"\n[ERROR] Image analysis failed: {str(e)}")
        print("Continuing with default analysis...")
        image_analysis = "Default analysis: Product images show a plush toy with warm, comforting features."
    
    # Store analysis results
    analysis_data = AnalysisData(
        product_info=product_info,
        image_urls=image_urls,
        image_analysis=image_analysis
    )
    
    # Format initial input
    input_text = f"""URL: {url}
Prompt: {user_prompt}

[ANALYSIS_DATA]
{analysis_data.__dict__}
[END_ANALYSIS_DATA]
"""
    
    # Storyboard iteration phase
    while True:
        try:
            result = await Runner.run(agent, input=input_text)
            
            # Extract storyboard
            storyboard = ""
            if "[STORYBOARD]" in result.final_output:
                start_idx = result.final_output.find("[STORYBOARD]")
                end_idx = result.final_output.find("[END STORYBOARD]")
                if end_idx == -1:
                    end_idx = result.final_output.find("---", start_idx)
                storyboard = result.final_output[start_idx:end_idx + len("[END STORYBOARD]")]
            
            if not storyboard:
                print("\n[ERROR] No storyboard found in the result. Retrying...")
                continue
            
            print("\n=== Proposed Storyboard ===")
            print(storyboard)
            
            # Get storyboard approval
            print("\nDo you approve this storyboard? (yes/no)")
            approval = input().strip().lower()
            
            if approval != 'yes':
                print("\nPlease provide feedback on the storyboard:")
                print("[FEEDBACK]")
                print("Scene X: [your changes]")
                print("[END FEEDBACK]")
                feedback = input("\nYour feedback: ").strip()
                input_text = f"""Previous Result: {result.final_output}

[ANALYSIS_DATA]
{analysis_data.__dict__}
[END_ANALYSIS_DATA]

User Feedback: {feedback}"""
                continue
            
            # Generate video
            print("\n=== Generating Video ===")
            video_result = await Runner.run(agent, input=input_text)
            print("\n=== Video Generation Results ===")
            print(video_result.final_output)
            
            # Show final storyboard
            print("\n=== Final Storyboard ===")
            print(storyboard)
            
            # Get final feedback
            print("\n=== Provide Feedback ===")
            print("Enter your feedback in the format:")
            print("[FEEDBACK]")
            print("Scene X: [your changes]")
            print("[END FEEDBACK]")
            print("Or type 'done' to finish")
            
            feedback = input("\nYour feedback: ").strip()
            if feedback.lower() == 'done':
                break
                
            input_text = f"""Previous Result: {video_result.final_output}

[ANALYSIS_DATA]
{analysis_data.__dict__}
[END_ANALYSIS_DATA]

User Feedback: {feedback}"""
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {str(e)}")
            print("Retrying with the same input...")
            continue


if __name__ == "__main__":
    asyncio.run(main())