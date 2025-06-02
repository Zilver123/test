import os
import tempfile
from fastapi.testclient import TestClient
from video_mvp.backend.main import app
import json
import cv2
import numpy as np
import requests
from PIL import Image
import imagehash

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
    # Check product description is meaningful
    assert "product" in data and data["product"].get("description")
    assert len(data["product"]["description"]) > 30
    # Check all media (scraped + uploaded) are present in media_files
    assert "media_files" in data and len(data["media_files"]) >= 2
    # Check media_descriptions covers all media_files
    for path in data["media_files"]:
        assert path in data["media_descriptions"]
        assert isinstance(data["media_descriptions"][path], str)
        assert data["media_descriptions"][path]
    # Check storyboard is valid JSON and uses product description
    storyboard = data["storyboard"]
    sb = json.loads(storyboard)
    assert "script" in sb and isinstance(sb["script"], str)
    # The script should mention something from the product description
    desc_words = set(data["product"]["description"].lower().split())
    script_words = set(sb["script"].lower().split())
    assert desc_words.intersection(script_words)
    # The media list should include all uploaded images
    uploaded_files = [os.path.basename(str(img1)), os.path.basename(str(img2))]
    media_files_in_sb = [os.path.basename(m["file"]) for m in sb["media"]]
    for uf in uploaded_files:
        assert uf in media_files_in_sb
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

def test_video_frames_match_storyboard(tmp_path):
    # Create 3 dummy images with different colors
    img_paths = []
    colors = [(255,0,0), (0,255,0), (0,0,255)]
    for i, color in enumerate(colors):
        img_path = tmp_path / f"img{i}.jpg"
        img = np.full((100, 100, 3), color, dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        img_paths.append(str(img_path))
    # Build storyboard JSON
    media = []
    times = [(0,3), (3,7), (7,10)]
    for i, p in enumerate(img_paths):
        media.append({
            "start": f"00:0{times[i][0]}",
            "end": f"00:{str(times[i][1]).zfill(2)}",
            "file": p
        })
    sb = {"script": "Test video", "media": media}
    output_path = str(tmp_path / "output.mp4")
    from video_mvp.backend.tools.render_video import render_video
    render_video(json.dumps(sb), img_paths, output_path)
    # Read video and check frames
    cap = cv2.VideoCapture(output_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    # Should be 10 frames
    assert len(frames) == 10
    # Check color of frames in each segment
    for i, (start, end) in enumerate(times):
        for f in range(start, end):
            mean = frames[f].mean(axis=(0,1))
            assert np.allclose(mean, colors[i], atol=5), f"Frame {f} does not match color {colors[i]}"

def test_api_video_duration_and_media_coverage(tmp_path):
    # Create 3 dummy images with different colors
    img_paths = []
    colors = [(255,0,0), (0,255,0), (0,0,255)]
    for i, color in enumerate(colors):
        img_path = tmp_path / f"img{i}.jpg"
        img = np.full((100, 100, 3), color, dtype=np.uint8)
        cv2.imwrite(str(img_path), img)
        img_paths.append(str(img_path))
    # Step 1: Call /api/input
    files = [("media", (os.path.basename(p), open(p, "rb"), "image/jpeg")) for p in img_paths]
    response = client.post(
        "/api/input",
        data={"creative_prompt": "10 sec test"},
        files=files
    )
    assert response.status_code == 200
    data = response.json()
    storyboard = data["storyboard"]
    media_files = data["media_files"]
    # Step 2: Call /api/render_video
    response2 = client.post(
        "/api/render_video",
        json={"storyboard": storyboard, "media_files": media_files}
    )
    assert response2.status_code == 200
    data2 = response2.json()
    video_path = data2["video_path"]
    assert os.path.exists(video_path)
    # Step 3: Check video duration and unique frames
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    duration = len(frames)
    print(f"Video duration (frames): {duration}")
    # Count unique frames by mean color
    means = [tuple(np.round(f.mean(axis=(0,1)))) for f in frames]
    unique_means = set(means)
    print(f"Unique frame colors: {unique_means}")
    print(f"Number of unique frames: {len(unique_means)}")
    # Should be 10 frames (10 seconds at 1 fps)
    assert duration == 10
    # Should be at least 3 unique frames (one per image)
    assert len(unique_means) >= 3

def test_multistage_real_data_pipeline(tmp_path):
    import sys
    from pprint import pprint
    # --- Stage 1: Input ---
    product_url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    creative_prompt = "10 sec tiktok marketing video"
    response = client.post(
        "/api/input",
        data={"product_url": product_url, "creative_prompt": creative_prompt},
        files=[]
    )
    print("\n[STAGE 1] INPUT:")
    print(f"product_url: {product_url}\ncreative_prompt: {creative_prompt}")
    print("[STAGE 1] OUTPUT:")
    pprint(response.json(), stream=sys.stdout)
    assert response.status_code == 200
    data = response.json()
    assert data["product"]["title"]
    assert data["product"]["description"]
    # Must have at least 3 scraped images
    scraped_images = [p for p in data["media_files"] if p.startswith("http")]
    assert len(scraped_images) >= 3, f"Expected at least 3 scraped images, got {len(scraped_images)}"
    # --- Stage 2: Media Download ---
    print("\n[STAGE 2] INPUT:")
    pprint(scraped_images, stream=sys.stdout)
    local_files = []
    for url in scraped_images:
        r = requests.get(url)
        assert r.status_code == 200
        img_path = tmp_path / (url.split("/")[-1].split("?")[0])
        with open(img_path, "wb") as f:
            f.write(r.content)
        img = cv2.imread(str(img_path))
        assert img is not None, f"Failed to read image from {url}"
        local_files.append(str(img_path))
    print("[STAGE 2] OUTPUT:")
    print(f"Downloaded files: {local_files}")
    # --- Stage 3: Storyboard Generation ---
    print("\n[STAGE 3] INPUT:")
    print(f"media_files: {scraped_images}")
    print(f"creative_prompt: {creative_prompt}")
    print(f"description: {data['product']['description']}")
    from video_mvp.backend.tools.generate_storyboard import generate_storyboard
    input_json = {
        "creative_prompt": creative_prompt,
        "product": data["product"],
        "media": [{"path": p, "description": data["media_descriptions"][p]} for p in scraped_images]
    }
    sb_json = generate_storyboard(input_json)
    sb = json.loads(sb_json)
    print("[STAGE 3] OUTPUT:")
    pprint(sb, stream=sys.stdout)
    assert "script" in sb and sb["script"]
    assert "media" in sb and len(sb["media"]) >= 3
    # All scraped images must be present in storyboard media
    def basename_no_query(url):
        return os.path.basename(url.split("?")[0])
    scraped_basenames = {basename_no_query(url) for url in scraped_images}
    storyboard_basenames = {basename_no_query(m["file"]) for m in sb["media"]}
    missing = scraped_basenames - storyboard_basenames
    assert not missing, f"Missing scraped images in storyboard: {missing}"
    # Timings must be sequential and cover full duration
    prev_end = 0
    for m in sb["media"]:
        start = int(m["start"].split(":")[1])
        end = int(m["end"].split(":")[1])
        assert start == prev_end
        assert end > start
        prev_end = end
    assert prev_end == 10
    # --- Stage 4: Video Rendering ---
    print("\n[STAGE 4] INPUT:")
    print(f"storyboard: {sb}")
    storyboard_media_files = [m["file"] for m in sb["media"]]
    response2 = client.post(
        "/api/render_video",
        json={"storyboard": json.dumps(sb), "media_files": storyboard_media_files}
    )
    print("[STAGE 4] OUTPUT:")
    pprint(response2.json(), stream=sys.stdout)
    assert response2.status_code == 200
    data2 = response2.json()
    video_path = data2["video_path"]
    assert os.path.exists(video_path)
    # Check video duration and unique frames
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    print(f"Video duration (frames): {len(frames)}")
    means = [tuple(np.round(f.mean(axis=(0,1)))) for f in frames]
    unique_means = set(means)
    print(f"Unique frame colors: {unique_means}")
    print(f"Number of unique frames: {len(unique_means)}")
    assert len(frames) == 10
    # Each downloaded image must appear in video frames (phash match, after resize/pad)
    def resize_and_pad(img, width=720, height=1280):
        # img: PIL Image
        w, h = img.size
        scale = min(width / w, height / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = img.resize((new_w, new_h))
        padded = Image.new('RGB', (width, height), (0, 0, 0))
        x_off = (width - new_w) // 2
        y_off = (height - new_h) // 2
        padded.paste(resized, (x_off, y_off))
        return padded
    frame_hashes = [imagehash.phash(Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))) for f in frames]
    found_count = 0
    for img_path in local_files:
        img = Image.open(img_path).convert('RGB')
        padded = resize_and_pad(img)
        img_hash = imagehash.phash(padded)
        match = any(img_hash - fh <= 8 for fh in frame_hashes)
        print(f"phash for {img_path}: {img_hash}, matched: {match}")
        if match:
            found_count += 1
    print(f"Matched {found_count} out of {len(local_files)} scraped images in video frames (phash, padded).")
    assert found_count >= 8, f"Only {found_count} out of {len(local_files)} scraped images found in video frames (phash, padded)!"
    # --- Stage 5: Analysis ---
    print("\n[STAGE 5] ANALYSIS:")
    print("All stages passed. Inputs and outputs printed above.") 