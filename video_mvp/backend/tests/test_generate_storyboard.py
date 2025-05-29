import pytest
from video_mvp.backend.tools.generate_storyboard import generate_storyboard

def test_generate_storyboard_basic():
    product = {
        "title": "Test Product",
        "description": "A great product for testing.",
        "images": ["/uploads/test1.jpg", "/uploads/test2.jpg"]
    }
    media_descriptions = {
        "/uploads/test1.jpg": "A red plush toy on a white background.",
        "/uploads/test2.jpg": "A close-up of the plush toy's face."
    }
    creative_prompt = "10 sec vid"
    result = generate_storyboard(product, media_descriptions, creative_prompt)
    assert isinstance(result, str)
    assert "[STORYBOARD]" in result
    assert "[SCRIPT]" in result
    assert "[MEDIA]" in result
    assert "[END STORYBOARD]" in result
    # Should mention at least one media file
    assert any(img in result for img in product["images"]) 