import os
import tempfile
from PIL import Image
from video_mvp.backend.tools.render_video import render_video
import json

def test_render_video_basic(tmp_path):
    # Create two dummy image files
    img1 = tmp_path / "img1.jpg"
    img2 = tmp_path / "img2.jpg"
    img1.write_bytes(b"fake image data 1")
    img2.write_bytes(b"fake image data 2")
    storyboard = """[STORYBOARD]
[SCRIPT]
"Test video!"
[MEDIA]
00:00-00:02 - {img1}
00:02-00:04 - {img2}
[END STORYBOARD]""".format(img1=img1, img2=img2)
    output_path = tmp_path / "output.mp4"
    result = render_video(storyboard, [str(img1), str(img2)], str(output_path))
    assert os.path.exists(result)
    assert result.endswith(".mp4")
    assert os.path.getsize(result) > 0

def test_render_video_with_local_images(tmp_path):
    # Create 3 dummy images
    img_paths = []
    for i in range(3):
        img_path = tmp_path / f"img{i}.jpg"
        img = Image.new("RGB", (320, 240), (i*80, 100, 200))
        img.save(img_path)
        img_paths.append(str(img_path))
    # Build storyboard JSON
    media = []
    for i, p in enumerate(img_paths):
        media.append({
            "start": f"00:0{i}",
            "end": f"00:0{i+1}",
            "file": p
        })
    sb = {"script": "Test video", "media": media}
    output_path = str(tmp_path / "output.mp4")
    result = render_video(json.dumps(sb), img_paths, output_path)
    assert os.path.exists(result)
    assert os.path.getsize(result) > 1000  # Should be a real video file 