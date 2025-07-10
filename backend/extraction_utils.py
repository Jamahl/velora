import os
import json
import logging
import requests
from exa_py import Exa
from firecrawl import JsonConfig, FirecrawlApp
from pydantic import BaseModel

logger = logging.getLogger("extraction_utils")

EXA_API_KEY = os.getenv("EXA_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

exa_client = Exa(EXA_API_KEY) if EXA_API_KEY else None

class ProductSchema(BaseModel):
    title: str = ''
    price: str = ''
    discounted_price: str = ''
    discount_percentage: str = ''
    currency: str = ''
    brand: str = ''
    product_description: str = ''
    image_url: str = ''
    site_name: str = ''
    url: str = ''

def fetch_firecrawl_contents(url: str):
    """
    Extract product data from a single URL using Firecrawl SDK with ProductSchema.
    Returns parsed product data dict, or None on error.
    """
    if not FIRECRAWL_API_KEY:
        logger.error("FIRECRAWL_API_KEY not set.")
        return None
    
    try:
        logger.info(f"[Firecrawl SDK] Extracting product data for URL: {url}")
        
        # Initialize Firecrawl SDK with API key
        app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)
        json_config = JsonConfig(schema=ProductSchema)
        
        # Use SDK to scrape URL with our product schema
        result = app.scrape_url(
            url,
            formats=["json"],
            json_options=json_config,
            only_main_content=False,
            timeout=60000  # 60 seconds in milliseconds
        )
        
        # Check if we got valid results
        if result and result.json:
            logger.info(f"[Firecrawl SDK] Extraction successful for {url}")
            print("\n[Firecrawl SDK Output]\n" + json.dumps(result.json, indent=2))
            
            # Convert to dict if needed
            product_data = result.json
            if not isinstance(product_data, dict):
                product_data = dict(product_data)
                
            # Add URL if not present
            if 'url' not in product_data:
                product_data['url'] = url
                
            return product_data
        else:
            logger.error(f"[Firecrawl SDK] No data returned for {url}")
    except Exception as e:
        logger.error(f"[Firecrawl SDK] Extraction failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return None



def extract_price_with_regex(text: str):
    """
    Fallback price extraction using regex on raw text.
    Returns price string or None.
    """
    import re
    if not text:
        return None
    price_patterns = [
        r'[$€£]\s?\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?',  # $1,299.99 or €299.99
        r'\d{1,3}(?:[,.]\d{3})*(?:[,.]\d{2})?\s?(USD|EUR|GBP)',
    ]
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None
