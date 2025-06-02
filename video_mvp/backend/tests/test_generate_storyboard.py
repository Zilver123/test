import pytest
from video_mvp.backend.tools.generate_storyboard import generate_storyboard
import re
import json

def test_generate_storyboard_basic():
    input_json = {
        "creative_prompt": "10 sec vid",
        "product": {
            "title": "Test Product",
            "description": "A great product for testing.",
            "images": ["/uploads/test1.jpg", "/uploads/test2.jpg"]
        },
        "media": [
            {"path": "/uploads/test1.jpg", "description": "A red plush toy on a white background."},
            {"path": "/uploads/test2.jpg", "description": "A close-up of the plush toy's face."}
        ]
    }
    result = generate_storyboard(input_json)
    # Should be valid JSON
    data = json.loads(result)
    assert "script" in data and isinstance(data["script"], str)
    assert "media" in data and isinstance(data["media"], list)
    # Should mention at least one media file
    assert any(item["file"] == "/uploads/test1.jpg" for item in data["media"])

def test_generate_storyboard_media_references():
    input_json = {
        "creative_prompt": "10 sec vid",
        "product": {
            "title": "Test Product",
            "description": "A great product for testing.",
            "images": ["/uploads/test1.jpg", "/uploads/test2.jpg", "/uploads/test3.jpg"]
        },
        "media": [
            {"path": "/uploads/test1.jpg", "description": "A red plush toy on a white background."},
            {"path": "/uploads/test2.jpg", "description": "A close-up of the plush toy's face."},
            {"path": "/uploads/test3.jpg", "description": "A group shot of plush toys."}
        ]
    }
    result = generate_storyboard(input_json)
    data = json.loads(result)
    assert "script" in data and isinstance(data["script"], str)
    assert "media" in data and isinstance(data["media"], list)
    valid_files = set(m["path"] for m in input_json["media"])
    for item in data["media"]:
        assert set(item.keys()) == {"start", "end", "file"}
        assert item["file"] in valid_files, f"MEDIA file {item['file']} not in uploaded files"

def test_generate_storyboard_strict_json():
    input_json = {
        "creative_prompt": "10 sec vid",
        "product": {
            "title": "Test Product",
            "description": "A great product for testing."
        },
        "media": [
            {"path": "/uploads/test1.jpg", "description": "A red plush toy on a white background."},
            {"path": "/uploads/test2.jpg", "description": "A close-up of the plush toy's face."}
        ]
    }
    result = generate_storyboard(input_json)
    # Should be valid JSON
    try:
        data = json.loads(result)
    except Exception as e:
        pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result}")
    assert "script" in data and isinstance(data["script"], str)
    assert "media" in data and isinstance(data["media"], list)
    for item in data["media"]:
        assert set(item.keys()) == {"start", "end", "file"}
        assert isinstance(item["start"], str)
        assert isinstance(item["end"], str)
        assert isinstance(item["file"], str)

def test_generate_storyboard_sequential_timings():
    input_json = {
        "creative_prompt": "10 sec vid",
        "product": {
            "title": "Test Product",
            "description": "A great product for testing."
        },
        "media": [
            {"path": f"/uploads/test{i}.jpg", "description": f"Image {i}"} for i in range(10)
        ]
    }
    result = generate_storyboard(input_json)
    data = json.loads(result)
    media = data["media"]
    assert len(media) == 10
    # Check that timings are sequential and non-overlapping
    prev_end = 0
    for idx, item in enumerate(media):
        start = int(item["start"].split(":")[1])
        end = int(item["end"].split(":")[1])
        assert start == prev_end, f"Image {idx} start {start} != previous end {prev_end}"
        assert end > start, f"Image {idx} end {end} <= start {start}"
        prev_end = end
    # Total duration should be 10 seconds
    assert prev_end == 10, f"Total duration {prev_end} != 10" 