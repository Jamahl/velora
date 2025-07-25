import os
import logging
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Import CrewAI tools
from crewai_product_cleaner import run_product_cleaner
from crewai_price_comparator import PriceComparatorCrew


from extraction_utils import fetch_firecrawl_contents, extract_price_with_regex

load_dotenv()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Globals & Config ---
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"

app = FastAPI()

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5186", "http://localhost:5182"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class ProductRequest(BaseModel):
    url: str

class Product(BaseModel):
    title: str
    price: Optional[float] = None
    currency: Optional[str] = None
    image_url: Optional[str] = None
    site_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    original_price: Optional[float] = None
    category: Optional[str] = None
    last_checked: Optional[str] = None

# --- API Endpoints ---

def parse_similar_products_result(result, fallback_url=None):
    """
    Parse and normalize CrewAI output for similar products.
    Always returns {"similar_products": [ ... ]} with at least title and url per product.
    Extra fields are passed through. Defaults are used if missing.
    """
    import re
    # 1. Handle string result (possibly with code block markers)
    if isinstance(result, str):
        cleaned = result.strip()
        cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned)
        cleaned = re.sub(r'```$', '', cleaned)
        try:
            result = json.loads(cleaned)
            if isinstance(result, str):
                result = json.loads(result)
        except Exception:
            logger.error(f"Failed to parse agent result as JSON: {cleaned}")
            return {"similar_products": []}
    # 2. CrewOutput with .json_dict or .raw
    if hasattr(result, "json_dict") and result.json_dict:
        result = result.json_dict
    elif hasattr(result, "raw") and result.raw:
        raw = result.raw.strip()
        # Fix common LLM JSON bugs
        if raw.endswith(']"}'):
            raw = raw[:-3] + ']}'
        elif raw.endswith('"}'):
            raw = raw[:-2] + '}'
        elif raw.endswith(']"'):
            raw = raw[:-2] + ']'
        elif raw.endswith('"') and raw.count('"') > raw.count(':'):
            raw = raw[:-1]
        try:
            result = json.loads(raw)
        except Exception:
            logger.error(f"Failed to parse CrewOutput.raw as JSON: {raw}")
            return {"similar_products": []}
    elif hasattr(result, "dict"):
        result = result.dict()
    elif hasattr(result, "to_dict"):
        result = result.to_dict()
    elif hasattr(result, "output"):
        result = result.output
    # 3. Try to find a list of products
    products = []
    if isinstance(result, dict):
        if "similar_products" in result and isinstance(result["similar_products"], list):
            products = result["similar_products"]
        elif any(isinstance(val, list) for val in result.values()):
            # Use first list value
            for val in result.values():
                if isinstance(val, list):
                    products = val
                    break
    elif isinstance(result, list):
        products = result
    # 4. Validate and normalize each product
    normalized = []
    for i, prod in enumerate(products):
        # Accept dicts only
        if not isinstance(prod, dict):
            logger.warning(f"Product at idx {i} is not a dict: {prod}")
            continue
        title = prod.get("title") or prod.get("name") or "Unknown Product"
        url = prod.get("url") or fallback_url or ""
        # Only skip if both title and url are missing
        if not title and not url:
            logger.warning(f"Product missing both title and url: {prod}")
            continue
        # Pass through all fields, but always have title and url
        out = dict(prod)
        out["title"] = title
        out["url"] = url
        normalized.append(out)
        if not prod.get("title") or not prod.get("url"):
            logger.info(f"Defaulted missing fields for product: {out}")
    logger.info(f"Returning {len(normalized)} valid similar products to UI.")
    return {"similar_products": normalized}

@app.post("/api/similar-products")
async def find_similar_products(product: Product):
    """
    Find similar products using Exa API and extract product data for each using Firecrawl.
    Returns: {"similar_products": [ ... ]}
    """
    logger.info(f"[Direct] Received find similar products request for: {product.title}")
    try:
        # 1. Call Exa API directly to get similar product URLs
        EXA_API_KEY = os.getenv("EXA_API_KEY")
        EXA_FIND_SIMILAR_URL = "https://api.exa.ai/v1/findSimilar"
        headers = {"Authorization": f"Bearer {EXA_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "url": product.url,
            "numResults": 10
        }
        async with httpx.AsyncClient() as client:
            exa_resp = await client.post(EXA_FIND_SIMILAR_URL, json=payload, headers=headers, timeout=30)
        if exa_resp.status_code != 200:
            logger.error(f"Exa API error: {exa_resp.status_code} {exa_resp.text}")
            raise HTTPException(status_code=502, detail="Exa API error")
        exa_data = exa_resp.json()
        # Parse URLs from Exa response
        similar_products = []
        for item in exa_data.get("results", []):
            url = item.get("url")
            title = item.get("title")
            if url and title:
                similar_products.append({"title": title, "url": url})
        logger.info(f"[Direct] Found {len(similar_products)} similar product URLs from Exa.")
        # 2. For each URL, call Firecrawl to extract product data
        detailed_products = []
        for idx, prod in enumerate(similar_products):
            url = prod["url"]
            logger.info(f"[Direct] ({idx+1}/{len(similar_products)}) Crawling with Firecrawl: {url}")
            firecrawl_data = fetch_firecrawl_contents(url)
            if firecrawl_data:
                firecrawl_data["source_url"] = url
                firecrawl_data["original_title"] = prod["title"]
                detailed_products.append(firecrawl_data)
                logger.info(f"[Direct] Firecrawl extraction success for {url}")
            else:
                logger.warning(f"[Direct] Firecrawl extraction failed for {url}")
        logger.info(f"[Direct] Extracted detailed data for {len(detailed_products)} products using Firecrawl")
        return {"similar_products": detailed_products}
    except Exception as e:
        logger.exception("[Direct] Unexpected error during similar product search.")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

@app.post("/api/product")
async def get_product_data(req: ProductRequest):
    # 1. Call Firecrawl
    headers = {"Authorization": f"Bearer {FIRECRAWL_API_KEY}"}
    payload = {"url": req.url}
    async with httpx.AsyncClient() as client:
        resp = await client.post(FIRECRAWL_API_URL, json=payload, headers=headers, timeout=20)
    if resp.status_code != 200:
        print("Firecrawl error:", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="Firecrawl API error")
    firecrawl_data = resp.json()

    # 2. Run CrewAI agent on Firecrawl output
    try:
        result = run_product_cleaner(firecrawl_data)
    except Exception as e:
        import traceback
        print("CrewAI error:", e)
        traceback.print_exc()
        result = None
    
    metadata = firecrawl_data.get("data", {}).get("metadata", {})

    def create_product_from_firecrawl(metadata):
        return {
            "title": metadata.get("og:title") or metadata.get("title"),
            "price": metadata.get("og:price:amount"),
            "currency": metadata.get("og:price:currency"),
            "image_url": metadata.get("og:image") or metadata.get("ogImage"),
            "site_name": metadata.get("og:site_name") or metadata.get("ogSiteName"),
            "description": metadata.get("og:description") or metadata.get("description"),
            "url": metadata.get("og:url") or metadata.get("url"),
        }

    # Validate CrewAI result. If it seems fake, fallback to Firecrawl.
    is_valid = False
    if result and isinstance(result, dict) and result.get("title"):
        real_title = metadata.get("og:title", "").lower()
        ai_title = result.get("title", "").lower()
        if "sample" not in ai_title and "example" not in ai_title and ai_title in real_title:
            is_valid = True

    if is_valid:
        product_data = result
    else:
        product_data = create_product_from_firecrawl(metadata)

    return Product(**product_data)

@app.post("/api/compare-price")
async def compare_price(product: Product):
    logger.info(f"Received price comparison request for: {product.title}")

    if not product.price:
        logger.warning("Price comparison request failed: Product has no price.")
        raise HTTPException(status_code=400, detail="Product must have a price to compare.")
    
    try:
        logger.info(f"Kicking off PriceComparatorCrew for '{product.title}' with price {product.price}")
        comparator_crew = PriceComparatorCrew(product_title=product.title, original_price=product.price)
        cheaper_option = await comparator_crew.run()
        
        logger.info(f"PriceComparatorCrew finished. Result: {cheaper_option}")
        
        # Parse string output from CrewAI if necessary
        if isinstance(cheaper_option, str):
            # Remove code block markers (triple backticks and optional 'json')
            import re
            cleaned = cheaper_option.strip()
            cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', cleaned)
            cleaned = re.sub(r'```$', '', cleaned)
            try:
                # Try parsing once
                cheaper_option = json.loads(cleaned)
                # If still a string, parse again (double-encoded JSON)
                if isinstance(cheaper_option, str):
                    cheaper_option = json.loads(cheaper_option)
            except Exception as e:
                logger.error(f"Failed to parse agent result as JSON: {cheaper_option}")
                raise HTTPException(status_code=500, detail="AI agent returned invalid JSON.")
        logger.info(f"Parsed cheaper_option type: {type(cheaper_option)} value: {cheaper_option}")

        # Convert CrewOutput to dict if needed
        if hasattr(cheaper_option, "json_dict") and cheaper_option.json_dict:
            cheaper_option = cheaper_option.json_dict
        elif hasattr(cheaper_option, "raw") and cheaper_option.raw:
            raw = cheaper_option.raw
            # Fix common LLM JSON bugs (e.g., {"offers":[]"})
            cleaned = raw
            # Remove trailing quote after array/object if present
            if cleaned.endswith(']"}'):
                cleaned = cleaned[:-3] + ']}'
            elif cleaned.endswith('"}'):
                cleaned = cleaned[:-2] + '}'
            elif cleaned.endswith(']"'):
                cleaned = cleaned[:-2] + ']'
            elif cleaned.endswith('"') and cleaned.count('"') > cleaned.count(':'):
                cleaned = cleaned[:-1]
            if cleaned != raw:
                logger.warning(f"Cleaned malformed JSON from agent: {raw} -> {cleaned}")
            try:
                cheaper_option = json.loads(cleaned)
            except Exception as e:
                logger.error(f"Failed to parse CrewOutput.raw as JSON (after cleaning): {cleaned}")
                raise HTTPException(status_code=500, detail="AI agent returned invalid JSON in CrewOutput.raw.")
        elif hasattr(cheaper_option, "dict"):
            cheaper_option = cheaper_option.dict()
        elif hasattr(cheaper_option, "to_dict"):
            cheaper_option = cheaper_option.to_dict()
        elif hasattr(cheaper_option, "output"):
            cheaper_option = cheaper_option.output
        
        # Validate structure: must be dict with 'offers' (list of dicts with required fields)
        if (
            not cheaper_option or
            not isinstance(cheaper_option, dict) or
            "offers" not in cheaper_option or
            not isinstance(cheaper_option["offers"], list)
        ):
            logger.error(f"Crew returned an invalid result: {cheaper_option}")
            raise HTTPException(status_code=500, detail="AI agent returned an invalid result.")

        valid_offers = []
        for offer in cheaper_option["offers"]:
            if (
                isinstance(offer, dict)
                and isinstance(offer.get("title"), str)
                and isinstance(offer.get("image_url"), str)
                and isinstance(offer.get("description"), str)
                and isinstance(offer.get("price"), (int, float))
                and isinstance(offer.get("retailer"), str)
                and isinstance(offer.get("url"), str)
                and offer.get("url").strip()
            ):
                valid_offers.append(offer)
            else:
                logger.warning(f"Invalid offer found and skipped: {offer}")

        return {"cheaper_offers": valid_offers}
    except Exception as e:
        logger.exception("An unexpected error occurred during price comparison.")
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")

class PriceExtractionRequest(BaseModel):
    content: str
    url: Optional[str] = ""

@app.post("/api/extract-price-ai")
async def extract_price_ai(request: PriceExtractionRequest):
    """Extract price information using direct pipeline: Firecrawl → regex fallback. No CrewAI."""
    logger.info(f"[Direct] Received price extraction request for URL: {request.url}")
    try:
        # 1. Call Firecrawl for content extraction
        firecrawl_data = fetch_firecrawl_contents(request.url)
        logger.info(f"[Direct] Firecrawl data: {bool(firecrawl_data)}")
        result = {}
        confidence = 0
        raw_content = None
        if firecrawl_data:
            result = firecrawl_data.copy()
            raw_content = firecrawl_data.get("description") or firecrawl_data.get("text") or None
            confidence = firecrawl_data.get("overall_confidence", 0)
        else:
            logger.warning(f"[Direct] Firecrawl extraction failed for {request.url}")
        # 2. Fallback: if missing price, use regex on raw_content
        price = result.get("price") if isinstance(result, dict) else None
        if not price and raw_content:
            fallback_price = extract_price_with_regex(raw_content)
            if fallback_price:
                result["price"] = fallback_price
                result["price_extraction_fallback"] = "regex"
                logger.info(f"[Direct] Fallback regex price used: {fallback_price}")
        # 3. Log final result
        logger.info(f"[Direct] Final extraction result: {result}")
        return {
            "success": True,
            "extraction_result": result,
            "confidence": confidence
        }
    except Exception as e:
        logger.exception("[Direct] Unexpected error during price extraction.")
        return {
            "success": False,
            "error": str(e),
            "extraction_result": None,
            "confidence": 0
        }
