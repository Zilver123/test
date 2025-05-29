import os
import tempfile
from fastapi.testclient import TestClient
from video_mvp.backend.main import app

client = TestClient(app)

def test_render_video_api(tmp_path):
    # Create two dummy image files
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"
    img1.write_bytes(b"fake image data 1")
    img2.write_bytes(b"fake image data 2")
    storyboard = f"""[STORYBOARD]\n[SCRIPT]\n\"Test video!\"\n[MEDIA]\n00:00-00:02 - {img1}\n00:02-00:04 - {img2}\n[END STORYBOARD]"""
    response = client.post(
        "/api/render_video",
        json={
            "storyboard": storyboard,
            "media_files": [str(img1), str(img2)]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "video_path" in data
    assert os.path.exists(data["video_path"])
    assert data["video_path"].endswith(".mp4")
    assert os.path.getsize(data["video_path"]) > 0 