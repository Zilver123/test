from typing import Dict, List
import requests
from bs4 import BeautifulSoup

# Placeholder for agent tool registration
def function_tool(func):
    return func

@function_tool
def scrape_url(url: str) -> Dict:
    """Scrape product title, description, and images from a product page URL."""
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    # Title
    title = soup.find('title').text.strip() if soup.find('title') else ''
    # Description (try meta description, then product description)
    desc = ''
    meta_desc = soup.find('meta', attrs={'name': 'description'})
    if meta_desc and meta_desc.get('content'):
        desc = meta_desc['content']
    else:
        # Try to find a product description div
        desc_div = soup.find('div', {'class': 'product__description'})
        if desc_div:
            desc = desc_div.get_text(strip=True)
    # Images: collect all <img> tags, check src, data-src, srcset
    images = set()
    for img in soup.find_all('img'):
        # src
        src = img.get('src')
        if src:
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = 'https://www.uncomfy.store' + src
            images.add(src)
        # data-src
        data_src = img.get('data-src')
        if data_src:
            if data_src.startswith('//'):
                data_src = 'https:' + data_src
            elif data_src.startswith('/'):
                data_src = 'https://www.uncomfy.store' + data_src
            images.add(data_src)
        # srcset (take the first URL)
        srcset = img.get('srcset')
        if srcset:
            first_url = srcset.split(',')[0].strip().split(' ')[0]
            if first_url.startswith('//'):
                first_url = 'https:' + first_url
            elif first_url.startswith('/'):
                first_url = 'https://www.uncomfy.store' + first_url
            images.add(first_url)
    images = list(images)
    return {
        'title': title,
        'description': desc,
        'images': images,
    } 