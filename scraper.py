import requests
from bs4 import BeautifulSoup


def get_product_info(url: str) -> str:
    try:
        # Send a GET request to the URL
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract product information
        product_info = {
            'title': None,
            'description': None,
            'price': None,
            'images': []
        }
        
        # Try to find product title
        title_elem = (
            soup.find('h1') or
            soup.find('title') or
            soup.find('div', class_='product-title') or
            soup.find('div', class_='product__title')
        )
        if title_elem:
            product_info['title'] = title_elem.text.strip()
        
        # Try to find full product description
        description_elem = (
            soup.find('div', class_='product__description') or
            soup.find('div', class_='product-description') or
            soup.find('div', class_='description') or
            soup.find('section', class_='product__description') or
            soup.find('section', class_='product-description')
        )
        if not description_elem:
            # Try to find any div/section with 'description' in the class name
            description_elem = soup.find(lambda tag: tag.name in ['div', 'section'] and tag.get('class') and any('description' in c for c in tag.get('class')))
        if description_elem:
            product_info['description'] = description_elem.get_text(separator=' ', strip=True)
        else:
            # Fallback to meta description
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                product_info['description'] = meta_desc.get('content', '').strip()
        
        # Try to find product price
        price_elem = (
            soup.find('span', {'class': 'price'}) or
            soup.find('div', {'class': 'price'}) or
            soup.find('span', {'class': 'product__price'}) or
            soup.find('div', {'class': 'product__price'})
        )
        if price_elem:
            product_info['price'] = price_elem.text.strip()
        
        # Find all product images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            if src and not src.startswith('data:'):
                if not src.startswith('http'):
                    # Handle relative URLs
                    src = requests.compat.urljoin(url, src)
                product_info['images'].append(src)
        
        # Format the output
        output = []
        if product_info['title']:
            output.append(f"Title: {product_info['title']}")
        if product_info['description']:
            output.append(f"Description: {product_info['description']}")
        if product_info['price']:
            output.append(f"Price: {product_info['price']}")
        if product_info['images']:
            output.append("\nProduct Images:")
            for img_url in product_info['images']:
                output.append(f"- {img_url}")
        
        return "\n".join(output) if output else "No product information found."
        
    except requests.RequestException as e:
        return f"Error fetching product information: {str(e)}"
    except Exception as e:
        return f"Error processing product information: {str(e)}" 