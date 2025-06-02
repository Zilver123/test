import pytest
from video_mvp.backend.tools.scrape_url import scrape_url

def test_scrape_url_basic():
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    result = scrape_url(url)
    assert isinstance(result, dict)
    assert "title" in result and result["title"]
    assert "description" in result and result["description"]
    assert len(result["description"]) > 30  # Should be a meaningful description
    assert "images" in result and isinstance(result["images"], list) and result["images"]
    assert len(result["images"]) >= 8  # Should scrape at least 8 images
    # Optionally check for a known phrase in the description
    assert "Strawberry Maxine" in result["title"] or "Strawberry Maxine" in result["description"] 

def test_scrape_url_image_limit():
    url = "https://www.uncomfy.store/products/preorder-strawberry-maxine-heatable-plush"
    result = scrape_url(url)
    assert "images" in result and isinstance(result["images"], list)
    assert 1 <= len(result["images"]) <= 10
    # Check for absence of icons/logos/thumbnails
    for img_url in result["images"]:
        lowered = img_url.lower()
        for kw in ["icon", "logo", "thumb", "sprite", "favicon", "banner", "arrow", "cart", "star"]:
            assert kw not in lowered 