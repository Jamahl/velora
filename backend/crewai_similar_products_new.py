import os
import asyncio
import logging
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from exa_py import Exa
from tools import SearchTools
import json
import httpx
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# --- Configure logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- No database dependency ---
# Note: Supabase functionality removed as it's not set up yet

# Get Exa API key from environment
EXA_API_KEY = os.getenv("EXA_API_KEY", "24b1e244-275f-4343-bd1d-0578e3ddc020")
exa_client = Exa(EXA_API_KEY)

# Define the Exa tools as top-level classes with proper type annotations
class ExaFindSimilarTool(BaseTool):
    name: str = "ExaFindSimilarTool"
    description: str = "Finds similar products to a given URL using Exa's findSimilar endpoint. Returns up to 10 similar links."
    
    def _run(self, url: str) -> str:
        logger.info(f"Finding similar products for URL: {url}")
        similar_products = []
        
        # Try URL-based search first
        try:
            logger.info("Attempting to find similar products using URL...")
            result = exa_client.find_similar(url=url, num_results=10)
            logger.info(f"Found {len(result.results)} similar links from URL search")
            
            for item in result.results:
                similar_products.append({
                    "title": item.title,
                    "url": item.url,
                    "score": getattr(item, 'similarity_score', 0.75)
                })
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Error in URL-based search: {error_str}")
            
            # Check if it's a 422 FETCH_DOCUMENT_ERROR
            if "422" in error_str and "FETCH_DOCUMENT_ERROR" in error_str:
                logger.info("Detected 422 FETCH_DOCUMENT_ERROR - attempting fallback")
                
                # Extract domain for better search results
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(url).netloc
                    if domain:
                        # Try to extract title/product name from URL
                        path_parts = urlparse(url).path.split('/')
                        potential_product_name = next((part for part in path_parts if len(part) > 5 and '-' in part), '')
                        
                        # Build search query from URL parts
                        if potential_product_name:
                            search_query = potential_product_name.replace('-', ' ') + f" site:{domain}"
                            logger.info(f"Attempting fallback search with: {search_query}")
                            
                            try:
                                # Perform content search as fallback
                                content_result = exa_client.search(search_query, num_results=10)
                                logger.info(f"Fallback search found {len(content_result.results)} results")
                                
                                for item in content_result.results:
                                    similar_products.append({
                                        "title": item.title,
                                        "url": item.url,
                                        "score": 0.5  # Default fallback score
                                    })
                            except Exception as search_err:
                                logger.error(f"Fallback search failed: {str(search_err)}")
                except Exception as fallback_err:
                    logger.error(f"Error setting up fallback search: {str(fallback_err)}")
        
        # Always return something, even if empty
        if not similar_products:
            logger.warning("No similar products found through any method")
            # Include the original URL as context for debugging
            return json.dumps([{"title": "Error processing this URL", "url": url, "score": 0.0, "error": True}])
        
        # Return as JSON string for the agent
        return json.dumps(similar_products)

class ExaContentsTool(BaseTool):
    name: str = "ExaContentsTool"
    description: str = "Fetches content from a URL using Exa's contents endpoint. Returns text content, images, and other page details."
    
    def _run(self, url: str) -> str:
        try:
            logger.info(f"Fetching content for URL: {url}")
            content = exa_client.get_contents(url=url)
            
            # Extract valuable information
            result = {"url": url}
            
            if hasattr(content, 'results') and content.results:
                content_result = content.results[0]
                
                # Extract title
                result["title"] = content_result.title if hasattr(content_result, 'title') else ""
                
                # Extract text content (truncate for reasonable size)
                result["text"] = content_result.text[:2000] if hasattr(content_result, 'text') else ""
                
                # Extract images
                result["image_urls"] = content_result.image_urls if hasattr(content_result, 'image_urls') else []
            
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.exception(f"Error fetching content: {e}")
            return json.dumps({"error": str(e), "url": url})

class SimilarProductsCrew:
    def __init__(self, product_title: str, product_description: str = None, product_color: str = None, product_price: float = None, url: str = None):
        """Initialize the SimilarProductsCrew with product details."""
        self.product_title = product_title
        self.product_description = product_description or ""
        self.product_color = product_color or ""
        self.product_price = product_price
        self.url = url
        
        # Initialize the LLM for agents
        self.llm = LLM(model="gpt-4o-mini")
        
        # Set up logging
        self.logger = logger
        
        # Initialize the Exa tools that have been defined at the top level
        self.exa_find_similar_tool = ExaFindSimilarTool()
        self.exa_contents_tool = ExaContentsTool()

    async def fetch_product_info(self, url: str) -> Dict[str, Any]:
        """Extract product info from URL or use existing data."""
        # Since we don't have a database, we'll extract info from the URL or use the title
        print(f"Using product title as fallback for URL: {url}")
        
        # Extract potential product info from URL or title
        product_info = {
            "title": self.product_title,
            "description": self.product_description or "",
            "color": self.product_color or "",
            "price": self.product_price,
            "url": url
        }
        
        # Try to extract more info from the URL if possible
        try:
            # Simple parsing of product name from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            path_segments = parsed_url.path.strip('/').split('/')
            
            # If we have path segments, the last one might contain product info
            if path_segments and len(path_segments) > 0:
                # Replace hyphens/underscores with spaces for a cleaner product name
                potential_name = path_segments[-1].replace('-', ' ').replace('_', ' ')
                if len(potential_name) > 3:  # Only use if it seems like a valid name
                    product_info["extracted_name"] = potential_name
                    
            # Extract domain as potential retailer
            product_info["retailer"] = parsed_url.netloc
        except Exception as e:
            print(f"Error parsing URL: {str(e)}")
            
        return product_info

    async def generate_search_term(self, product_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a search term for finding similar products."""
        # Mini agent: summarize product and generate search term
        agent = Agent(
            role="Product Search Term Generator",
            goal="Given a product's title, description, color, and price, generate a short, natural search phrase for finding similar products online.",
            backstory="You are an expert at e-commerce and product categorization. You know how to turn product details into effective search queries.",
            allow_delegation=False
        )
        task = Task(
            description=(
                f"Given the following product details, output a JSON object with: 'summary' (one sentence summary), 'search_term' (natural search phrase for similar products), and echo back the fields.\n"
                f"title: {product_info.get('title', '')}\n"
                f"description: {product_info.get('description', '')}\n"
                f"color: {product_info.get('color', '')}\n"
                f"price: {product_info.get('price', '')}\n"
            ),
            expected_output="A JSON object: { 'summary': ..., 'search_term': ..., 'title': ..., 'description': ..., 'color': ..., 'price': ... }",
            agent=agent
        )
        crew = Crew(tasks=[task])
        result = crew.kickoff()
        
        # Handle different result types
        try:
            if isinstance(result, str):
                # Parse JSON string
                return json.loads(result)
            elif hasattr(result, 'json_dict') and result.json_dict:
                # CrewOutput with json_dict
                return result.json_dict
            elif hasattr(result, 'raw') and result.raw:
                # CrewOutput with raw string
                return json.loads(result.raw)
            elif hasattr(result, '__dict__'):
                # Object with dict representation
                return result.__dict__
            else:
                # Return as is
                return result
        except Exception as e:
            print(f"Error parsing search term result: {e}")
            # Return a default search term based on the product title
            return {
                "search_term": f"similar to {self.product_title}",
                "summary": self.product_title
            }

    def extract_result_data(self, result) -> Dict[str, Any]:
        """Extract data from various result types (string, CrewOutput, dict, etc.)"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Extracting result data from type: {type(result)}")
        if hasattr(result, 'raw'):
            logger.info(f"Result has raw attribute: {result.raw[:200]}...")
        
        # IMPORTANT: Direct forwarding of results
        # First priority: Check if result.raw is a valid JSON array and use it directly
        if hasattr(result, 'raw') and result.raw:
            cleaned = result.raw.strip()
            logger.info(f"Processing CrewOutput.raw: {cleaned[:200]}...")
            
            # Check if the raw output is a JSON array
            if cleaned.startswith('[') and cleaned.endswith(']'):
                try:
                    parsed = json.loads(cleaned)
                    logger.info(f"Successfully parsed raw as JSON array with {len(parsed)} items")
                    return {"similar_products": parsed}
                except json.JSONDecodeError:
                    logger.warning("Failed to parse raw as JSON array, continuing with other methods")
        
        try:
            # If result is already a list of products, wrap it in a dict
            if isinstance(result, list):
                logger.info(f"Result is a list with {len(result)} items")
                return {"similar_products": result}
            
            elif isinstance(result, str):
                # Try to parse as JSON string
                cleaned = result.strip()
                logger.info(f"Cleaning string result: {cleaned[:200]}...")
                
                # Remove code block markers if present
                if cleaned.startswith('```') and cleaned.endswith('```'):
                    cleaned = '\n'.join(cleaned.split('\n')[1:-1])
                elif cleaned.startswith('```'):
                    # Only start marker
                    cleaned = '\n'.join(cleaned.split('\n')[1:])
                    
                # Try to parse as JSON
                try:
                    parsed = json.loads(cleaned)
                    logger.info(f"Successfully parsed string as JSON: {type(parsed)}")
                    if isinstance(parsed, list):
                        return {"similar_products": parsed}
                    return parsed
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse as JSON, returning as text: {cleaned[:100]}...")
                    return {"similar_products": [{"text": cleaned, "url": "", "title": "Extracted Text"}]}
            
            elif hasattr(result, 'raw') and result.raw:
                # Already tried direct JSON parsing above, now try extracting JSON from text
                cleaned = result.raw.strip()
                
                # Try to extract JSON from the text (common in agent outputs)
                import re
                json_match = re.search(r'\[\s*{.*}\s*\]', cleaned, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(0)
                        logger.info(f"Found JSON array in raw text: {json_str[:200]}...")
                        parsed = json.loads(json_str)
                        return {"similar_products": parsed}
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse extracted JSON array")
                
                # Fix common JSON formatting issues and try again
                if cleaned.endswith(']"}'): 
                    cleaned = cleaned[:-3] + ']}' 
                elif cleaned.endswith('"}'):
                    cleaned = cleaned[:-2] + '}'
                    
                try:
                    parsed = json.loads(cleaned)
                    logger.info(f"Parsed fixed JSON: {type(parsed)}")
                    if isinstance(parsed, list):
                        return {"similar_products": parsed}
                    return parsed
                except json.JSONDecodeError:
                    logger.warning("Failed to parse fixed JSON")
                    
            elif hasattr(result, 'json_dict') and result.json_dict:
                # CrewOutput with json_dict
                logger.info(f"Using CrewOutput.json_dict: {type(result.json_dict)}")
                if isinstance(result.json_dict, list):
                    return {"similar_products": result.json_dict}
                return result.json_dict
                
            elif isinstance(result, dict):
                # Already a dict
                logger.info(f"Result is already a dict with keys: {result.keys()}")
                # If it doesn't have similar_products key, add it
                if "similar_products" not in result and any(isinstance(val, list) for val in result.values()):
                    # Find the first list value and use it as similar_products
                    for key, val in result.items():
                        if isinstance(val, list):
                            logger.info(f"Using list value from key '{key}' as similar_products")
                            return {"similar_products": val}
                return result
                
            elif hasattr(result, '__dict__'):
                # Object with dict representation
                logger.info(f"Converting object to dict: {type(result)}")
                return result.__dict__
                
            else:
                # Return empty dict as fallback
                logger.warning(f"Unhandled result type: {type(result)}, returning empty products list")
                return {"similar_products": []}
                
        except Exception as e:
            logger.error(f"Error extracting result data: {str(e)}")
            return {"similar_products": []}

    def create_product_processor_agent(self):
        """Create an agent to process and filter similar products."""
        return Agent(
            role="Product Processor",
            goal="Filter and rank similar products by relevance to the original product",
            backstory="""You are an expert at evaluating product similarity and relevance. 
                        You know how to determine which products are truly similar to a target product.
                        
                        For clothing, you identify similar items within the same category.
                        For accessories, include similar accessories. The goal is to always return some
                        results for the user to see, even if they aren't exact category matches. For each product
                        you include, extract important details like title, price, and description.""",
            verbose=True,
            llm=self.llm
        )
    
    async def run_async(self, product_url=None) -> Dict[str, Any]:
        """Run the similar products search flow using a three-agent architecture with Exa tools."""
        try:
            # Use URL if provided, otherwise use existing URL
            url = product_url or self.url
            if not url:
                self.logger.error("No URL provided. Cannot find similar products.")
                return {"error": "No URL provided", "similar_products": []}
            
            # Get product info to understand what we're searching for
            product_info = await self.fetch_product_info(url)
            self.logger.info(f"Product info extracted: {json.dumps(product_info)[:200]}...")
            
            # Generate appropriate search term
            search_result = await self.generate_search_term(product_info)
            self.logger.info(f"Search term generated: {json.dumps(search_result)[:200]}...")
            
            # STEP 1: Find similar links using Exa findSimilar endpoint
            self.logger.info("STEP 1: Creating Exa Similar Links agent")
            
            # Define Pydantic models for structured output
            class SimilarProduct(BaseModel):
                title: str = Field(..., description="The title or name of the product")
                url: str = Field(..., description="The URL where the product can be found")
                score: Optional[float] = Field(None, description="Similarity score if available")
                
            class SimilarProductsOutput(BaseModel):
                similar_products: List[SimilarProduct] = Field(..., description="List of similar products found")
            
            # Create the ExaFindSimilarTool agent
            finder_agent = Agent(
                role="Exa Similar Products Finder",
                goal="Find similar products to a given URL using Exa's findSimilar API",
                backstory="You are an expert at finding relevant similar products for comparison shopping.",
                tools=[self.exa_find_similar_tool],
                allow_delegation=False,
                verbose=True
            )
            
            # Create a task for finding similar products via Exa
            finder_task = Task(
                description="Using the EXACT input URL, find similar products using ONLY the ExaFindSimilarTool with find_similar method and url parameter. Do not modify the URL. Return a list of objects with title and url properties.",
                expected_output="A list of similar product objects with title and url properties formatted as {\"similar_products\": [{\"title\": \"Product name\", \"url\": \"Product URL\"}]}",
                output_pydantic=SimilarProductsOutput,
                agent=finder_agent
            )
            
            # Run the first agent to find similar products
            self.logger.info(f"Starting similar products search for URL: {url}")
            similar_crew = Crew(
                agents=[finder_agent],
                tasks=[finder_task],
                verbose=True
            )
            
            similar_result = similar_crew.kickoff()
            
            # DIRECT USE OF AGENT OUTPUT: Force the agent's raw output to be the result
            if hasattr(similar_result, 'raw') and similar_result.raw:
                try:
                    # Directly use the agent's raw output if it's valid JSON
                    cleaned_raw = similar_result.raw.strip()
                    if cleaned_raw.startswith('[') and cleaned_raw.endswith(']'):
                        parsed_products = json.loads(cleaned_raw)
                        if isinstance(parsed_products, list):
                            self.logger.info(f"Directly using agent output as similar products: {len(parsed_products)} items")
                            return {"similar_products": parsed_products}
                except Exception as e:
                    self.logger.warning(f"Failed to directly use agent raw output: {str(e)}")
                    # Continue to fallback processing
            
            # Extract similar products data
            similar_data = self.extract_result_data(similar_result)
            self.logger.info(f"Found {len(similar_data) if isinstance(similar_data, list) else 0} similar products")
            
            # If we got no results or results in wrong format, handle gracefully
            if not isinstance(similar_data, list) or len(similar_data) == 0:
                self.logger.error("No similar products found or invalid result format")
                return {"similar_products": []}
            
            # STEP 2: For each similar product URL, fetch its content
            self.logger.info("STEP 2: Creating Content Extraction agent")
            content_agent = Agent(
                role="Product Content Extractor",
                goal="Extract detailed product information from each URL",
                backstory="You're an expert at extracting product details from web pages. You use Exa's contents endpoint to get text, images, and other data from product pages.",
                tools=[self.exa_contents_tool],
                verbose=True,
                llm=self.llm
            )
            
            # Create a task that processes each URL individually
            content_task = Task(
                description=(
                    "For each product URL in the list:\n"
                    "1. Use the ExaContentsTool to extract content from the URL\n"
                    "2. From the extracted content, create a structured product entry with these fields:\n"
                    "   - title: Use the title from the page\n"
                    "   - url: Use the original URL\n"
                    "   - retailer: Extract from the URL domain (e.g., 'thepearlsource.com' → 'The Pearl Source')\n"
                    "   - description: Extract from page text if available, otherwise use '[No description available]'\n"
                    "   - price: Look for price patterns in text (e.g. $XX.XX), if none found use '[Price not available]'\n"
                    "   - image_url: Use the first image URL if available, otherwise use placeholder\n\n"
                    "IMPORTANT INSTRUCTIONS:\n"
                    "- Process each URL individually with the ExaContentsTool\n"
                    "- NEVER make up data - only use what's available from the tool results\n"
                    "- When data is missing, use clear placeholders\n"
                    "- Return a well-formatted JSON array of product entries\n"
                ),
                expected_output="JSON array of products with details extracted from each URL",
                agent=content_agent,
                context=similar_data  # Pass the similar products as context
            )
            
            # Run the content extraction agent
            self.logger.info("Starting content extraction for similar products")
            content_crew = Crew(
                agents=[content_agent],
                tasks=[content_task],
                verbose=True
            )
            
            content_result = content_crew.kickoff()
            
            # Extract detailed product data
            detailed_products = self.extract_result_data(content_result)
            self.logger.info(f"Extracted detailed data for {len(detailed_products) if isinstance(detailed_products, list) else 0} products")
            
            # STEP 3: Filter products for relevance
            self.logger.info("STEP 3: Creating Product Filter agent")
            filter_agent = Agent(
                role="Product Relevance Filter",
                goal="Filter products for relevance to the original product",
                backstory="You're an expert at determining product relevance. You can identify which products are truly similar to the original product based on type, category, and features.",
                verbose=True,
                llm=self.llm
            )
            
            filter_task = Task(
                description=(
                    f"Filter these products for relevance to the original product:\n"
                    f"Original product: '{self.product_title}'\n"
                    f"Description: '{self.product_description}'\n"
                    f"Color: '{self.product_color}'\n"
                    f"Price: {self.product_price}\n\n"
                    "FILTERING INSTRUCTIONS:\n"
                    "- Keep only products that match the SAME TYPE as the original product\n"
                    "- Example: If original is a pearl necklace, keep only other jewelry items\n"
                    "- Example: If original is a belt, keep only other belts or similar accessories\n"
                    "- Be somewhat generous with your filtering - include broadly related items\n"
                    "- Keep at least 3-5 products if possible\n"
                    "- Ensure every product has title, url, description, price, retailer, and image_url fields\n"
                    "- Return a clean JSON with 'similar_products' as the root key\n"
                ),
                expected_output="{'similar_products': [...]} containing only relevant filtered products",
                agent=filter_agent,
                context=detailed_products  # Pass the detailed products as context
            )
            
            # Run the filter agent
            self.logger.info("Starting product filtering")
            filter_crew = Crew(
                agents=[filter_agent],
                tasks=[filter_task],
                verbose=True
            )
            
            filter_result = filter_crew.kickoff()
            
            # Extract final filtered results
            final_results = self.extract_result_data(filter_result)
            
            # Make sure we have the expected format for frontend
            if not isinstance(final_results, dict) or "similar_products" not in final_results:
                self.logger.warning("Final result not in expected format, reformatting")
                if isinstance(final_results, list):
                    final_results = {"similar_products": final_results}
                else:
                    final_results = {"similar_products": []}
            
            self.logger.info(f"Final result has {len(final_results.get('similar_products', [])) if isinstance(final_results.get('similar_products'), list) else 0} products")
            return final_results
            
        except Exception as e:
            self.logger.exception(f"Error in similar products search: {str(e)}")
            import traceback
            self.logger.error(f"Detailed traceback: {traceback.format_exc()}")
            # Return empty similar_products list on error
            return {"similar_products": []}
    
    async def run(self) -> Dict[str, Any]:
        """Run the similar products search flow."""
        return await self.run_async()
