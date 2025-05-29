from typing import Dict
import openai
import os

# Placeholder for agent tool registration
def function_tool(func):
    return func

@function_tool
def generate_storyboard(product: Dict, media_descriptions: Dict[str, str], creative_prompt: str) -> str:
    """Generate a storyboard from product info, media descriptions, and creative prompt."""
    try:
        client = openai.OpenAI()
        # Compose a prompt for the LLM
        prompt = f"""
You are an expert marketing video creator. Given the following product info, media descriptions, and creative prompt, generate a short-form video storyboard in this format:
[STORYBOARD]
[SCRIPT]
"<script>"
[MEDIA]
<timing> - <media file>
[END STORYBOARD]

Product:
Title: {product.get('title')}
Description: {product.get('description')}
Media:
"""
        for path, desc in media_descriptions.items():
            prompt += f"{path}: {desc}\n"
        prompt += f"\nCreative prompt: {creative_prompt}\n"
        prompt += "\nStoryboard:"
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=512
        )
        return response.choices[0].message.content
    except Exception as e:
        # Fallback: mocked storyboard
        return f"""[STORYBOARD]
[SCRIPT]
"Introducing {product.get('title', 'our product')}! {creative_prompt}"
[MEDIA]
00:00-00:05 - {list(media_descriptions.keys())[0] if media_descriptions else 'image1.jpg'}
00:05-00:10 - {list(media_descriptions.keys())[1] if len(media_descriptions)>1 else 'image2.jpg'}
[END STORYBOARD]""" 