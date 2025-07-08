import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv()

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
FIRECRAWL_API_URL = "https://api.firecrawl.dev/v1/scrape"

app = FastAPI()

# Allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductRequest(BaseModel):
    url: str

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
    print("Firecrawl output:", firecrawl_data)  # Debug print

    # 2. Run CrewAI agent on Firecrawl output
    try:
        from crewai_product_cleaner import run_product_cleaner
        result = run_product_cleaner(firecrawl_data)
        print("CrewAI output:", result)  # Debug print
    except Exception as e:
        import traceback
        print("CrewAI error:", e)
        traceback.print_exc()
        result = None
    metadata = firecrawl_data.get("data", {}).get("metadata", {})

    def create_product_from_firecrawl(metadata):
        """Builds a product dictionary directly from Firecrawl metadata."""
        return {
            "title": metadata.get("og:title") or metadata.get("title"),
            "price": metadata.get("og:price:amount"),
            "currency": metadata.get("og:price:currency"),
            "image_url": metadata.get("og:image") or metadata.get("ogImage"),
            "site_name": metadata.get("og:site_name") or metadata.get("ogSiteName"),
            "description": metadata.get("og:description") or metadata.get("description"),
            "url": metadata.get("og:url") or metadata.get("url"),
            # Fields not typically in metadata are set to None
            "original_price": None,
            "category": None,
            "last_checked": None,
        }

    # Validate CrewAI result. If it seems fake, fallback to Firecrawl.
    is_valid = False
    if result and isinstance(result, dict) and result.get("title"):
        real_title = metadata.get("og:title", "").lower()
        ai_title = result.get("title", "").lower()
        # Simple check: if AI title is not a placeholder and is part of the real title
        if "sample" not in ai_title and "example" not in ai_title and ai_title in real_title:
            is_valid = True

    if is_valid:
        print("Using validated CrewAI result.")
        product = result
    else:
        print("CrewAI result is invalid or missing. Falling back to Firecrawl data.")
        product = create_product_from_firecrawl(metadata)

    return product
