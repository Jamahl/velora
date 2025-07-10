import logging
from typing import List, Dict, Any
from crewai.tools import BaseTool
from duckduckgo_search import DDGS
import os
import requests
import json
from dotenv import load_dotenv
from exa_py import Exa

# Load environment variables from .env file
load_dotenv()

# Get Exa API key from environment variables
EXA_API_KEY = os.getenv("EXA_API_KEY", "24b1e244-275f-4343-bd1d-0578e3ddc020")  # Fallback to provided key if not in .env

# Initialize Exa client
exa_client = Exa(EXA_API_KEY)

class SearchTools:
    class FirecrawlTool(BaseTool):
        name: str = "Firecrawl Web Scraper"
        description: str = "A tool to scrape product details from a URL including title, price, images, and description."
        
        def _run(self, url: str) -> str:
            import logging
            logger = logging.getLogger(__name__)
            
            # Fallback to direct web request if Firecrawl API key not available
            firecrawl_api_key = os.getenv("FIRECRAWL_API_KEY")
            
            try:
                if firecrawl_api_key:
                    # Use Firecrawl API for better extraction
                    headers = {"Authorization": f"Bearer {firecrawl_api_key}"}
                    response = requests.post(
                        "https://api.firecrawl.dev/scrape",
                        json={"url": url, "elements": ["title", "images", "meta", "price", "description"]},
                        headers=headers
                    )
                    if response.status_code == 200:
                        return json.dumps(response.json(), indent=2)
                
                # Fallback to simpler extraction method
                logger.info(f"Using fallback extraction for URL: {url}")
                
                # Use Exa's get_contents as fallback
                content_result = exa_client.get_contents(url=url)
                
                # Extract basic data
                result = {
                    "url": url,
                    "title": "",
                    "description": "",
                    "price": "",
                    "images": []
                }
                
                if hasattr(content_result, 'results') and content_result.results:
                    # Extract title
                    if hasattr(content_result.results[0], 'title'):
                        result["title"] = content_result.results[0].title
                        
                    # Extract content
                    if hasattr(content_result.results[0], 'text'):
                        text = content_result.results[0].text
                        result["description"] = text[:300] if text else ""
                        
                        # Look for price in text
                        import re
                        price_patterns = [
                            r'\$\d+(?:\.\d{2})?',  # $X.XX or $XX
                            r'€\d+(?:\.\d{2})?',  # €X.XX or €XX
                            r'£\d+(?:\.\d{2})?',  # £X.XX or £XX
                        ]
                        for pattern in price_patterns:
                            match = re.search(pattern, text)
                            if match:
                                result["price"] = match.group(0)
                                break
                    
                    # Extract images
                    if hasattr(content_result.results[0], 'image_urls'):
                        result["images"] = content_result.results[0].image_urls[:5] if content_result.results[0].image_urls else []
                
                return json.dumps(result, indent=2)
                
            except Exception as e:
                logger.exception(f"Error scraping URL {url}: {e}")
                return json.dumps({"error": str(e), "url": url})
    
    class WebSearchTool(BaseTool):
        name: str = "Web Search Tool"
        description: str = "A tool to search the web for a given query. Returns the top 5 results."

        def _run(self, query: str) -> str:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                return str(results)

    class ExaSearchTool(BaseTool):
        name: str = "Exa Web Search Tool"
        description: str = "A tool to search the web using Exa.ai for a given query. Returns the top 5 results."

        def _run(self, query: str) -> str:
            if not EXA_API_KEY:
                return "EXA_API_KEY not set."
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {EXA_API_KEY}",
            }
            data = {
                "query": query,
                "num_results": 5
            }
            try:
                response = requests.post(
                    "https://api.exa.ai/search",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                response.raise_for_status()
                return str(response.json().get("results", []))
            except Exception as e:
                return f"Exa search failed: {e}"
                
logger_exa_find_similar = logging.getLogger("tools.ExaFindSimilarTool")

class ExaFindSimilarTool(BaseTool):
    name: str = "ExaFindSimilarTool"
    description: str = "Find similar links to a URL using Exa's find_similar endpoint"
    
    def __init__(self):
        """Initialize with API key from environment."""
        super().__init__()
        self.exa_api_key = os.getenv("EXA_API_KEY")
        if not self.exa_api_key:
            logger_exa_find_similar.warning("EXA_API_KEY not found in environment variables")
        exa.api_key = self.exa_api_key
    
    def _run(self, url: str, num_results: int = 8) -> List[Dict[str, Any]]:
        """Find similar links to the provided URL using Exa's find_similar endpoint.
        
        Args:
            url: The URL to find similar links for.
            num_results: Number of similar links to return (default=8).
            
        Returns:
            List of dictionaries with title and URL of similar products.
        """
        logger_exa_find_similar.info(f"Finding similar links for {url}, num_results={num_results}")
        similar_products = []
        
        # Try URL-based search first
        try:
            logger_exa_find_similar.info("Attempting to find similar products using URL...")
            result = exa_client.find_similar(url=url, num_results=num_results)
            logger_exa_find_similar.info(f"Found {len(result.results)} similar links from URL search")
            for item in result.results:
                similar_products.append({
                    "title": item.title,
                    "url": item.url,
                    "score": item.similarity_score
                })
        except Exception as e:
            error_str = str(e)
            logger_exa_find_similar.warning(f"Error in URL-based search: {error_str}")
            # Check if it's a 422 FETCH_DOCUMENT_ERROR
            if "422" in error_str and "FETCH_DOCUMENT_ERROR" in error_str:
                logger_exa_find_similar.info("Detected 422 FETCH_DOCUMENT_ERROR - attempting fallback")
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    if domain:
                        path_parts = urlparse(url).path.split('/')
                        potential_product_name = next((part for part in path_parts if len(part) > 5 and '-' in part), '')
                        if potential_product_name:
                            search_query = potential_product_name.replace('-', ' ') + f" site:{domain}"
                            logger_exa_find_similar.info(f"Attempting fallback search with: {search_query}")
                            try:
                                content_result = exa_client.search(search_query, num_results=num_results)
                                logger_exa_find_similar.info(f"Fallback search found {len(content_result.results)} results")
                                for item in content_result.results:
                                    similar_products.append({
                                        "title": item.title,
                                        "url": item.url,
                                        "score": 0.5
                                    })
                            except Exception as search_err:
                                logger_exa_find_similar.error(f"Fallback search failed: {str(search_err)}")
                except Exception as fallback_err:
                    logger_exa_find_similar.error(f"Error setting up fallback search: {str(fallback_err)}")
        
        # Always return something, even if empty
        if not similar_products:
            logger_exa_find_similar.warning("No similar products found through any method")
            return [{"title": "Error processing this URL", "url": url, "score": 0.0, "error": True}]
        return similar_products

    class ExaSimilarLinksTool(BaseTool):
        name: str = "Exa Similar Links Tool"
        description: str = "A tool to find similar links using Exa.ai and fetches content for each similar product."

        def _run(self, url: str) -> str:
            import logging
            logger = logging.getLogger(__name__)
            
            if not EXA_API_KEY:
                logger.error("EXA_API_KEY not set in environment variables")
                return "EXA_API_KEY not set."
                
            try:
                logger.info(f"Finding similar links for URL: {url}")
                logger.info(f"Using Exa API key: {EXA_API_KEY[:4]}...{EXA_API_KEY[-4:]}")
                
                # Step 1: Find similar links first
                logger.info("Step 1: Calling Exa find_similar API with parameters: url=%s, num_results=10", url)
                similar_results = exa_client.find_similar(
                    url=url,
                    num_results=8  # Get 8 similar products as requested
                )
                
                logger.info(f"Exa find_similar API call successful. Found {len(similar_results.results)} similar links")
                
                # Format results with more detailed data
                formatted_results = []
                
                # Step 2: Fetch content for each similar URL
                for i, result in enumerate(similar_results.results):
                    try:
                        result_url = result.url if hasattr(result, 'url') else ""
                        if not result_url:
                            continue
                            
                        # Fetch content for this URL
                        logger.info(f"Step 2.{i+1}: Fetching content for URL: {result_url}")
                        content_result = exa_client.get_contents(url=result_url)
                        
                        # Extract useful product data from content
                        text_content = ""
                        image_url = "https://via.placeholder.com/400"  # Default placeholder
                        price_text = "[Price not available]"
                        
                        if hasattr(content_result, 'results') and content_result.results:
                            # Get text content
                            if hasattr(content_result.results[0], 'text') and content_result.results[0].text:
                                text_content = content_result.results[0].text[:500]  # Truncate to reasonable size
                            
                            # Try to extract image URL from content
                            if hasattr(content_result.results[0], 'image_urls') and content_result.results[0].image_urls:
                                if len(content_result.results[0].image_urls) > 0:
                                    image_url = content_result.results[0].image_urls[0]  # Get first image
                            
                            # Try to find price in content
                            if text_content:
                                # Simple pattern matching for prices
                                import re
                                price_patterns = [
                                    r'\$\d+(?:\.\d{2})?',  # $X.XX or $XX
                                    r'€\d+(?:\.\d{2})?',   # €X.XX or €XX
                                    r'£\d+(?:\.\d{2})?',   # £X.XX or £XX
                                    r'\d+(?:\.\d{2})? USD', # X.XX USD or XX USD
                                    r'\d+(?:\.\d{2})? EUR', # X.XX EUR or XX EUR
                                    r'\d+(?:\.\d{2})? GBP'  # X.XX GBP or XX GBP
                                ]
                                for pattern in price_patterns:
                                    price_match = re.search(pattern, text_content)
                                    if price_match:
                                        price_text = price_match.group(0)
                                        break
                        
                        # Extract retailer from domain
                        from urllib.parse import urlparse
                        domain = urlparse(result_url).netloc
                        # Remove www. and .com/.org/etc.
                        retailer = domain.replace('www.', '')
                        retailer = retailer.split('.')[0].title()
                        
                        # Create comprehensive result data
                        result_data = {
                            "title": result.title if hasattr(result, 'title') else "",
                            "url": result_url,
                            "description": text_content[:200] if text_content else "[No description available]",
                            "price": price_text,
                            "retailer": retailer,
                            "image_url": image_url,
                            "score": result.score if hasattr(result, 'score') else 0
                        }
                        formatted_results.append(result_data)
                        logger.info(f"Result {i+1}: title='{result_data['title']}', url='{result_data['url']}', retailer='{result_data['retailer']}', price={result_data['price']}")
                    except Exception as e:
                        logger.error(f"Error processing result {i}: {e}")
                        continue
                
                # Return the formatted results as a JSON string
                result_json = json.dumps(formatted_results, indent=2)
                logger.info(f"Returning {len(formatted_results)} formatted results with detailed content")
                return result_json
                
            except Exception as e:
                logger.exception(f"Exa similar links search failed: {e}")
                import traceback
                logger.error(f"Detailed traceback: {traceback.format_exc()}")
                return f"Exa similar links search failed: {e}"
