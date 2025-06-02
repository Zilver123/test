import os
import tempfile
from PIL import Image
import cv2
import numpy as np
import requests

def test_render_video_with_cv2(tmp_path):
    # Create 3 dummy images
    img_paths = []
    for i in range(3):
        img_path = tmp_path / f"img{i}.jpg"
        img = Image.new("RGB", (320, 240), (i*80, 100, 200))
        img.save(img_path)
        img_paths.append(str(img_path))
    # Read images and stack into video
    output_path = str(tmp_path / "output_cv2.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 1, (320, 240))
    for p in img_paths:
        frame = cv2.imread(p)
        out.write(frame)
    out.release()
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000  # Should be a real video file

def test_render_video_with_downloaded_image(tmp_path):
    # Download a real product image
    url = "https://www.uncomfy.store/cdn/shop/files/IMG_82232.jpg?v=1744352078&width=1946"
    img_path = tmp_path / "downloaded.jpg"
    r = requests.get(url, timeout=10)
    with open(img_path, "wb") as f:
        f.write(r.content)
    # Use OpenCV to create a video
    output_path = str(tmp_path / "output_dl.mp4")
    img = cv2.imread(str(img_path))
    assert img is not None, "Downloaded image could not be read by OpenCV"
    height, width, _ = img.shape
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, 1, (width, height))
    for _ in range(3):
        out.write(img)
    out.release()
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 1000  # Should be a real video file 