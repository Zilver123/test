import os
import pytest
from video_mvp.backend.tools.analyze_media import analyze_media

def test_analyze_media_basic(tmp_path):
    # Create a dummy image file
    img_path = tmp_path / "test.jpg"
    img_path.write_bytes(b"fake image data")
    result = analyze_media([str(img_path)])
    assert isinstance(result, dict)
    assert str(img_path) in result
    assert isinstance(result[str(img_path)], str)
    assert result[str(img_path)]  # Should not be empty 