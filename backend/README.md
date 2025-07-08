# Velora2 Backend (FastAPI)

This backend provides a single `/api/product` endpoint that:
- Accepts a product URL (POST JSON `{ "url": "..." }`)
- Calls Firecrawl API to scrape product data
- Optionally enriches data with a CrewAI agent
- Returns structured product JSON for the frontend

## Setup

1. Copy `.env.example` to `.env` and add your Firecrawl API key:
   ```sh
   cp .env.example .env
   # Edit .env and set FIRECRAWL_API_KEY
   ```
2. Install dependencies (in a virtualenv):
   ```sh
   pip install -r requirements.txt
   ```
3. Run the server:
   ```sh
   uvicorn main:app --reload --port 8000
   ```

## Endpoint

- `POST /api/product` with JSON `{ "url": "..." }`
- Returns product data: title, price, image, description, etc.

## Notes
- Firecrawl API key is required.
- CrewAI agent is used to clean/enrich product data (no API key required).
- CORS is enabled for local frontend dev.

---

See `main.py` for implementation details.
