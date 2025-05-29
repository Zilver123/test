from typing import List, Dict
import os
import openai

# Placeholder for agent tool registration
def function_tool(func):
    return func

@function_tool
def analyze_media(media_paths: List[str]) -> Dict[str, str]:
    """Analyze each media file and return a description using OpenAI Vision."""
    client = openai.OpenAI()
    results = {}
    for path in media_paths:
        try:
            with open(path, "rb") as f:
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "user", "content": [
                            {"type": "text", "text": "Describe this image for a marketing video."},
                            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{f.read().hex()}"}
                        ]}
                    ],
                    max_tokens=256
                )
                desc = response.choices[0].message.content
                results[path] = desc
        except Exception as e:
            results[path] = f"Error analyzing {path}: {e}"
    return results 