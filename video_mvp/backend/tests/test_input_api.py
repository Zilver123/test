import os
import tempfile
import shutil
import pytest
from fastapi.testclient import TestClient
from video_mvp.backend.main import app

client = TestClient(app)

def test_input_api_with_media():
    # Create a dummy image file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp.write(b"fake image data")
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            response = client.post(
                "/api/input",
                data={
                    "product_url": "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush",
                    "creative_prompt": "10 sec vid"
                },
                files={"media": (os.path.basename(tmp_path), f, "image/jpeg")}
            )
        assert response.status_code == 200
        data = response.json()
        assert "product" in data and data["product"].get("title")
        assert "creative_prompt" in data and data["creative_prompt"] == "10 sec vid"
        assert "media_files" in data and len(data["media_files"]) == 1
        assert "media_descriptions" in data
        for path in data["media_files"]:
            assert path in data["media_descriptions"]
            assert isinstance(data["media_descriptions"][path], str)
    finally:
        os.remove(tmp_path) 