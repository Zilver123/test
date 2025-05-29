import pytest
from video_mvp.backend.tools.scrape_url import scrape_url

def test_scrape_url_basic():
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    result = scrape_url(url)
    assert isinstance(result, dict)
    assert "title" in result and result["title"]
    assert "description" in result and result["description"]
    assert "images" in result and isinstance(result["images"], list) and result["images"]
    # Optionally check for a known phrase in the description
    assert "Strawberry Maxine" in result["title"] or "Strawberry Maxine" in result["description"] 