import os
import replicate
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ReplicateResponse(BaseModel):
    """Schema for Replicate API response"""
    output: str
    status: str
    error: Optional[str] = None

class ReplicateClient:
    def __init__(self, api_token: Optional[str] = None):
        """Initialize Replicate client with API token"""
        self.api_token = api_token or os.getenv("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN not found in .env file")
        self.client = replicate.Client(api_token=self.api_token)

    async def generate_marketing_content(self, product_url: str) -> ReplicateResponse:
        """
        Generate marketing content using Replicate's models
        
        Args:
            product_url (str): URL of the product to generate marketing content for
            
        Returns:
            ReplicateResponse: Response containing the generated content
        """
        try:
            output = list(self.client.run(
                "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                input={
                    "prompt": f"Create marketing content for the product at this URL: {product_url}",
                    "temperature": 0.7,
                    "max_length": 500
                }
            ))[0]
            
            return ReplicateResponse(
                output=str(output),
                status="success"
            )
            
        except Exception as e:
            return ReplicateResponse(
                output="",
                status="error",
                error=str(e)
            )

    async def analyze_image(self, image_url: str, prompt: str = "What is unusual about this image?") -> ReplicateResponse:
        """
        Analyze an image using Replicate's LLaVA model
        
        Args:
            image_url (str): URL of the image to analyze
            prompt (str): Prompt to guide the image analysis
            
        Returns:
            ReplicateResponse: Response containing the analysis
        """
        try:
            prediction = self.client.predictions.create(
                version="19be067b589d0c46689ffa7cc3ff321447a441986a7694c01225973c2eafc874",
                input={
                    "image": image_url,
                    "prompt": prompt
                }
            )
            output = ""
            for event in prediction.stream():
                if hasattr(event, 'data'):
                    output += str(event.data)
            output = output.strip()
            if output.endswith("{}"):
                output = output[:-2].rstrip()
            return ReplicateResponse(
                output=output,
                status="success"
            )
        except Exception as e:
            return ReplicateResponse(
                output="",
                status="error",
                error=str(e)
            )


async def main():
    # Example usage
    client = ReplicateClient()
    response = await client.generate_marketing_content(
        "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    )
    print(response.dict())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
