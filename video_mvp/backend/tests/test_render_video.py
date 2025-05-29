import os
import tempfile
from video_mvp.backend.tools.render_video import render_video

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