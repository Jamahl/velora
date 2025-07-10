import os
import asyncio
from crewai import Agent, Task, Crew
from tools import SearchTools
import json
import httpx
from typing import Dict, List, Any, Optional

# --- No database dependency ---
# Note: Supabase functionality removed as it's not set up yet

class SimilarProductsCrew:
    def __init__(self, product_title: str, product_description: str = None, product_color: str = None, product_price: float = None):
        """Initialize the SimilarProductsCrew with product details."""
        self.product_title = product_title
        self.product_description = product_description or ""
        self.product_color = product_color or ""
        self.product_price = product_price
        # Only using Exa search per requirements
        self.exa_search_tool = SearchTools.ExaSearchTool()

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
        try:
            if isinstance(result, str):
                # Try to parse as JSON string
                cleaned = result.strip()
                # Remove code block markers if present
                if cleaned.startswith('```') and cleaned.endswith('```'):
                    cleaned = '\n'.join(cleaned.split('\n')[1:-1])
                elif cleaned.startswith('```'):
                    # Only start marker
                    cleaned = '\n'.join(cleaned.split('\n')[1:])
                return json.loads(cleaned)
            elif hasattr(result, 'json_dict') and result.json_dict:
                # CrewOutput with json_dict
                return result.json_dict
            elif hasattr(result, 'raw') and result.raw:
                # CrewOutput with raw string
                cleaned = result.raw.strip()
                # Fix common JSON formatting issues
                if cleaned.endswith(']"}'): 
                    cleaned = cleaned[:-3] + ']}'
                elif cleaned.endswith('"}'):
                    cleaned = cleaned[:-2] + '}'
                return json.loads(cleaned)
            elif isinstance(result, dict):
                # Already a dict
                return result
            elif hasattr(result, '__dict__'):
                # Object with dict representation
                return result.__dict__
            else:
                # Return empty dict as fallback
                return {"products": []}
        except Exception as e:
            import logging
            logging.error(f"Error extracting result data: {e}")
            return {"products": []}

    async def run_async(self, product_url=None) -> Dict[str, Any]:
        """Run the similar products search flow asynchronously."""
        # 0. Fetch product metadata (from URL or use existing data)
        url = product_url or self.product_title  # fallback for now
        try:
            # Get product info from the URL or use existing data
            product_info = await self.fetch_product_info(url)
            
            # 1. Generate search term
            summary_result = await self.generate_search_term(product_info)
            
            # Extract search term safely - handle different result structures
            if isinstance(summary_result, dict):
                search_term = summary_result.get("search_term", f"similar to {self.product_title}")
            else:
                # Fallback if we couldn't get a proper search term
                search_term = f"similar to {self.product_title}"
                
            print(f"Using search term: {search_term}")
            
            # 2. Use only Exa for search (per new requirements)
            exa_agent = Agent(
                role="Exa Search Specialist",
                goal="Find similar products to the target product using Exa search.",
                backstory="You are an expert at finding similar products using semantic search. You know how to craft effective search queries and extract relevant information from search results.",
                tools=[self.exa_search_tool],
                allow_delegation=False
            )
            
            exa_task = Task(
                description=(
                    f"Find similar products to '{self.product_title}' (description: {self.product_description}, color: {self.product_color}, price: {self.product_price}). "
                    f"Use the search term: '{search_term}'. "
                    "Use synonyms, related categories, and advanced search operators. "
                    "Return a JSON list of EXACTLY 10 OR FEWER products (title, image_url, description, price, retailer, url). "
                    "If you cannot find 10, that's fine - quality over quantity. Fill missing fields with 'unknown'."
                ),
                expected_output="A JSON list of up to 10 products, each with title, image_url, description, price, retailer, url.",
                agent=exa_agent
            )
            
            # Run Exa search
            exa_crew = Crew(agents=[exa_agent], tasks=[exa_task], verbose=False)
            exa_result = await exa_crew.kickoff_async()
            
            # Process the search results
            product_processor = Agent(
                role="Product Data Processor",
                goal="Process and format product search results for display.",
                backstory="You are an expert at processing and formatting product data. You ensure all products have the required fields and are properly formatted.",
                allow_delegation=False
            )
            
            processor_task = Task(
                description=(
                    f"Process these search results for '{self.product_title}'. "
                    "Format the data as a clean JSON with a 'products' array containing up to 10 items. "
                    "Each product MUST have: title, image_url (use https://via.placeholder.com/400 if missing), "
                    "description, price (as number when possible), retailer, and url. "
                    "Sort by relevance to the original product, then by price ascending. "
                    "CRITICAL: ONLY include products from the search results. If no products are found, return {\"products\": []}. "
                    "Format as clean JSON with no markdown, code blocks, or commentary."
                ),
                expected_output="{\"products\": [ ... ]} with up to 10 products, each with all required fields.",
                agent=product_processor
            )
            
            # Extract the Exa search results
            exa_data = self.extract_result_data(exa_result)
            
            # Set the context for the processor
            processor_crew = Crew(
                agents=[product_processor],
                tasks=[processor_task],
                process_inputs={"search_results": exa_data},
                verbose=False
            )
            
            final_result = processor_crew.kickoff()
            
            # Return the processed results
            return self.extract_result_data(final_result)
            
        except Exception as e:
            import logging
            logging.exception(f"Error in similar products search: {str(e)}")
            # Return empty products list on error
            return {"products": []}
    
    async def run(self) -> Dict[str, Any]:
        """Run the similar products search flow."""
        return await self.run_async()
