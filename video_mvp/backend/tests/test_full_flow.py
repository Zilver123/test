import os
import tempfile
from fastapi.testclient import TestClient
from video_mvp.backend.main import app

client = TestClient(app)

def test_full_flow(tmp_path):
    # Step 1: Create dummy image files
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"
    img1.write_bytes(b"fake image data 1")
    img2.write_bytes(b"fake image data 2")
    # Step 2: Call /api/input
    with open(img1, "rb") as f1, open(img2, "rb") as f2:
        response = client.post(
            "/api/input",
            data={
                "product_url": "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush",
                "creative_prompt": "10 sec vid"
            },
            files=[
                ("media", (os.path.basename(img1), f1, "image/jpeg")),
                ("media", (os.path.basename(img2), f2, "image/jpeg")),
            ]
        )
    assert response.status_code == 200
    data = response.json()
    assert "storyboard" in data
    assert "media_files" in data and len(data["media_files"]) >= 2
    # Step 3: Call /api/render_video
    response2 = client.post(
        "/api/render_video",
        json={
            "storyboard": data["storyboard"],
            "media_files": data["media_files"]
        }
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert "video_path" in data2
    assert os.path.exists(data2["video_path"])
    assert data2["video_path"].endswith(".mp4")
    assert os.path.getsize(data2["video_path"]) > 0 