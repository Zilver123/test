import os
import cv2
import numpy as np
import base64
import asyncio
import aiohttp
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


class MediaAnalyzer:
    """Handles media analysis using OpenAI's API with concurrent processing"""
    
    def __init__(self, max_concurrent: int = 10):
        self.client = OpenAI()
        self.max_concurrent = max_concurrent
        self.download_semaphore = asyncio.Semaphore(max_concurrent)
        self.api_semaphore = asyncio.Semaphore(max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        self.active_downloads = 0
        self.active_api_calls = 0
        print(f"[DEBUG] Initialized MediaAnalyzer with {max_concurrent} concurrent operations")
    
    async def analyze_media(self, media_path: Optional[str] = None, 
                          image_urls: Optional[List[str]] = None, 
                          num_frames: int = 5) -> str:
        """Analyze either a video or a list of images using concurrent processing"""
        print(f"\n[DEBUG] Starting media analysis with {self.max_concurrent} concurrent operations...")
        try:
            results = []
            
            if media_path:
                results = await self._analyze_video(media_path, num_frames)
            elif image_urls:
                results = await self._analyze_images_concurrent(image_urls)
            else:
                return "Error: Either media_path or image_urls must be provided"

            if not results:
                return "No media could be analyzed."

            return self._format_analysis_results(results, media_path is not None)
            
        except Exception as e:
            error_msg = f"Error analyzing media: {e}"
            print(f"[DEBUG] {error_msg}")
            return error_msg

    async def _analyze_video(self, video_path: str, num_frames: int) -> List[Dict]:
        """Extract and analyze frames from a video using concurrent processing"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found at {video_path}")

        # Extract frames in a separate thread to avoid blocking
        print("[DEBUG] Starting frame extraction in thread pool...")
        frames, timestamps = await asyncio.get_event_loop().run_in_executor(
            self.executor, self._extract_frames, video_path, num_frames
        )

        if not frames:
            raise ValueError("Could not extract any frames from the video")

        print(f"[DEBUG] Extracted {len(frames)} frames, starting concurrent analysis...")
        return await self._analyze_frames_concurrent(frames, timestamps)

    def _extract_frames(self, video_path: str, num_frames: int) -> Tuple[List[np.ndarray], List[float]]:
        """Extract frames from video (runs in thread pool)"""
        print("[DEBUG] Frame extraction thread started")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("Could not open video file")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        duration = total_frames / fps
        print(f"[DEBUG] Video duration: {duration:.2f} seconds, FPS: {fps:.2f}")

        interval = max(1, total_frames // num_frames)
        print(f"[DEBUG] Will extract 1 frame every {interval} frames")

        frames = []
        timestamps = []
        count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            if count % interval == 0:
                frames.append(frame)
                timestamps.append(count / fps)
                print(f"[DEBUG] Extracted frame at {count/fps:.2f}s")
            count += 1
        cap.release()
        print(f"[DEBUG] Frame extraction completed: {len(frames)} frames")
        return frames, timestamps

    async def _analyze_images_concurrent(self, image_urls: List[str]) -> List[Dict]:
        """Analyze multiple images concurrently"""
        print(f"[DEBUG] Starting concurrent analysis of {len(image_urls)} images")
        
        # First, download all images concurrently
        async with aiohttp.ClientSession() as session:
            print("[DEBUG] Initiating concurrent image downloads...")
            download_tasks = [
                self._download_image(session, url, idx, len(image_urls))
                for idx, url in enumerate(image_urls)
            ]
            image_data_results = await asyncio.gather(*download_tasks, return_exceptions=True)
            
            # Filter out failed downloads
            valid_images = []
            for idx, result in enumerate(image_data_results):
                if isinstance(result, Exception):
                    print(f"[DEBUG] Error downloading image {image_urls[idx]}: {result}")
                    continue
                valid_images.append((image_urls[idx], result))
            
            if not valid_images:
                return []
            
            print(f"[DEBUG] Successfully downloaded {len(valid_images)} images")
        
        # Then, analyze all images concurrently
        print("[DEBUG] Starting concurrent image analysis...")
        analysis_tasks = []
        for url, image_data in valid_images:
            task = asyncio.create_task(self._analyze_single_image(url, image_data))
            analysis_tasks.append(task)
        
        # Wait for all analysis tasks to complete
        results = []
        for future in tqdm(asyncio.as_completed(analysis_tasks), 
                         total=len(analysis_tasks),
                         desc="Analyzing images"):
            try:
                result = await future
                results.append(result)
            except Exception as e:
                print(f"[DEBUG] Error in analysis task: {e}")
        
        return results

    async def _download_image(self, session: aiohttp.ClientSession, 
                            url: str, idx: int, total: int) -> bytes:
        """Download a single image with retry logic"""
        async with self.download_semaphore:
            self.active_downloads += 1
            print(f"[DEBUG] Active downloads: {self.active_downloads}/{self.max_concurrent}")
            try:
                for attempt in range(3):
                    try:
                        async with session.get(url, timeout=10) as response:
                            response.raise_for_status()
                            print(f"[DEBUG] Downloaded image {idx + 1}/{total}")
                            return await response.read()
                    except Exception as e:
                        if attempt == 2:
                            raise
                        print(f"[DEBUG] Download attempt {attempt + 1} failed for {url}: {e}")
                        await asyncio.sleep(1)
            finally:
                self.active_downloads -= 1
                print(f"[DEBUG] Active downloads: {self.active_downloads}/{self.max_concurrent}")

    async def _analyze_single_image(self, url: str, image_data: bytes) -> Dict:
        """Analyze a single image with rate limiting"""
        async with self.api_semaphore:
            self.active_api_calls += 1
            print(f"[DEBUG] Active API calls: {self.active_api_calls}/{self.max_concurrent}")
            try:
                image_b64 = base64.b64encode(image_data).decode('utf-8')
                analysis = await self._get_image_analysis(image_b64)
                return {
                    "url": url,
                    "analysis": analysis
                }
            except Exception as e:
                print(f"[DEBUG] Error analyzing image {url}: {e}")
                return {
                    "url": url,
                    "analysis": f"Error: {str(e)}"
                }
            finally:
                self.active_api_calls -= 1
                print(f"[DEBUG] Active API calls: {self.active_api_calls}/{self.max_concurrent}")

    async def _analyze_frames_concurrent(self, frames: List[np.ndarray], 
                                       timestamps: List[float]) -> List[Dict]:
        """Analyze multiple video frames concurrently"""
        print(f"[DEBUG] Starting concurrent analysis of {len(frames)} frames")
        # Convert frames to base64 in thread pool
        print("[DEBUG] Converting frames to base64 in thread pool...")
        frame_b64_tasks = [
            asyncio.get_event_loop().run_in_executor(
                self.executor, self._frame_to_base64, frame
            )
            for frame in frames
        ]
        frame_b64_list = await asyncio.gather(*frame_b64_tasks)
        
        print("[DEBUG] Starting concurrent frame analysis...")
        # Analyze frames concurrently with rate limiting
        analysis_tasks = [
            self._analyze_single_frame(timestamp, frame_b64)
            for timestamp, frame_b64 in zip(timestamps, frame_b64_list)
        ]
        
        results = []
        for future in tqdm(asyncio.as_completed(analysis_tasks),
                          total=len(analysis_tasks),
                          desc="Analyzing frames"):
            try:
                result = await future
                results.append(result)
            except Exception as e:
                print(f"[DEBUG] Error in frame analysis task: {e}")
        
        return results

    def _frame_to_base64(self, frame: np.ndarray) -> str:
        """Convert frame to base64 (runs in thread pool)"""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')

    async def _analyze_single_frame(self, timestamp: float, frame_b64: str) -> Dict:
        """Analyze a single frame with rate limiting"""
        async with self.api_semaphore:  # Limit concurrent API calls
            self.active_api_calls += 1
            print(f"[DEBUG] Active API calls: {self.active_api_calls}/{self.max_concurrent}")
            try:
                analysis = await self._get_image_analysis(frame_b64)
                return {
                    "timestamp": timestamp,
                    "analysis": analysis
                }
            except Exception as e:
                print(f"[DEBUG] Error analyzing frame at {timestamp:.1f}s: {e}")
                return {
                    "timestamp": timestamp,
                    "analysis": f"Error: {str(e)}"
                }
            finally:
                self.active_api_calls -= 1
                print(f"[DEBUG] Active API calls: {self.active_api_calls}/{self.max_concurrent}")

    async def _get_image_analysis(self, image_b64: str) -> str:
        """Get analysis from OpenAI for a base64 encoded image"""
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: self.client.responses.create(
                    model="gpt-4o",
                    input=[{
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": "Analyze this image and describe:\n1. The visual elements and their significance\n2. How this image contributes to the product's story\n3. The emotional impact and messaging\n4. Any suggestions for improvement"},
                            {
                                "type": "input_image",
                                "image_url": f"data:image/jpeg;base64,{image_b64}"
                            },
                        ],
                    }],
                )
            )
            return getattr(response, 'output_text', None) or getattr(response, 'choices', [{}])[0].get('message', {}).get('content', None)
        except Exception as e:
            print(f"[DEBUG] API call error: {e}")
            raise

    def _format_analysis_results(self, results: List[Dict], is_video: bool) -> str:
        """Format analysis results into a readable string"""
        analysis_output = "\n=== Media Analysis Results ===\n\n"
        
        if is_video:
            for result in results:
                analysis_output += f"At {result['timestamp']:.1f}s:\n"
                analysis_output += f"{result['analysis']}\n"
                analysis_output += "-" * 80 + "\n"
        else:
            for result in results:
                analysis_output += f"Image URL: {result['url']}\n"
                analysis_output += f"{result['analysis']}\n"
                analysis_output += "-" * 80 + "\n"

        return analysis_output 