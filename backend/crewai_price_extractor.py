"""
CrewAI Complete Product Data Extractor
Intelligently extracts all product information from scraped e-commerce content for UI display
"""

from crewai import Agent, Task, Crew
import json

def extract_product_data_with_ai(content: str, url: str = ""):
    """
    Use CrewAI to extract complete product data from hybrid input (structured + raw) for UI cards
    """
    import json as _json
    # Accepts content as a JSON string with 'structured' and 'raw_content' fields
    try:
        hybrid = _json.loads(content) if isinstance(content, str) else content
        structured = hybrid.get("structured")
        raw_content = hybrid.get("raw_content")
    except Exception:
        structured, raw_content = None, content
    agent = Agent(
        role="E-commerce Product Data Analyst",
        goal="Extract complete product information from both structured data and raw content to populate UI product cards",
        backstory="""You are an expert at analyzing e-commerce product pages and extracting comprehensive product information. You understand how to interpret structured data (JSON-LD, microdata, meta tags) and unstructured content (HTML, visible text). You always use structured data as the primary source when available, but fill in missing fields by reasoning over raw content. You clearly distinguish between current prices, original prices, and discounts, and always explain your reasoning for each field.
        
        Your goal is to provide all the data needed to display beautiful product cards in a UI, using all available cues from both structured and unstructured sources."""
    )
    
    task = Task(
        description=f"""
        You are given e-commerce product data from two sources:
        1. Structured data (JSON-LD, microdata, or meta tags) if available
        2. Raw content (HTML/text scraped from the product page)
        
        Your job is to extract the most accurate and complete product information for UI display. Always:
        - Use structured data as your primary source for each field if present
        - For any missing/uncertain fields, reason over the raw content to fill the gaps
        - Clearly reason about price, original price, and discount using all available cues (structured, meta, visible text)
        - Always return at least title, price, and description (make your best guess if missing)
        - For each field, add a note indicating if it was derived from structured data, raw content, or fallback/reasoning
        - Output confidence scores (0-100) and a brief reasoning for each field
        
        Input example:
        {{
            "structured": ... (JSON-LD/microdata/meta tags dict or null),
            "raw_content": ... (HTML/text string or null),
            "url": "..."
        }}
        
        Your output MUST be a single JSON object with these fields:
        {{
            "title": "...",
            "brand": "...",
            "description": "...",
            "category": "...",
            "current_price": {{
                "value": "...",
                "currency": "...",
                "confidence": 0-100,
                "source": "structured"|"raw_content"|"fallback"
            }},
            "original_price": {{
                "value": "...",
                "currency": "...",
                "confidence": 0-100,
                "source": "structured"|"raw_content"|"fallback"
            }},
            "discount": {{
                "amount": "...",
                "percentage": "...",
                "confidence": 0-100,
                "source": "structured"|"raw_content"|"fallback"
            }},
            "availability": "...",
            "rating": "...",
            "key_features": ["..."],
            "extraction_method": "hybrid",
            "overall_confidence": 0-100,
            "field_reasoning": {{
                "title": "...",
                "current_price": "...",
                ...
            }}
        }}
        
        If a field is truly missing, use null and explain why in field_reasoning.
        
        Input:
        Structured: {structured}
        Raw Content: {str(raw_content)[:1200]}...
        URL: {url}
        """,
        expected_output="JSON object with complete product data, with source and reasoning for each field",
        agent=agent,
        input_data={"structured": structured, "raw_content": raw_content, "url": url}
    )
    
    crew = Crew(
        tasks=[task],
        verbose=True  # Enable verbose mode to see agent thinking
    )
    raw_result = crew.kickoff()
    
    print("CrewAI raw result:", raw_result)
    
    try:
        # If result is a string, try to parse as JSON
        if isinstance(raw_result, str):
            # Clean up the result string to extract JSON
            json_start = raw_result.find('{')
            json_end = raw_result.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = raw_result[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(raw_result)
        else:
            result = raw_result
            
        print("CrewAI parsed result:", result)
        
        # Ensure we have at least some basic data
        # Check if result is a dictionary and has values
        if isinstance(result, dict):
            # Check if all values are None
            if not result or all(value is None for value in result.values()):
                # Create a fallback result with minimal information
                fallback_result = {
                    "title": "Product" if not url else url.split('/')[-1].replace('-', ' ').title(),
                    "price": {
                        "value": None,
                        "currency": "USD",
                        "confidence": 0
                    },
                    "description": "Product description not available",
                    "extraction_method": "fallback",
                    "overall_confidence": 0
                }
                print("Using fallback result due to empty AI extraction")
                return fallback_result
        # If result is not a dictionary (like CrewOutput object), convert it to dict
        elif not isinstance(result, dict):
            try:
                # Try to convert to dictionary if possible
                if hasattr(result, '__dict__'):
                    result = result.__dict__
                # If it's a string that looks like JSON, parse it
                elif isinstance(result, str) and result.strip().startswith('{'):
                    result = json.loads(result)
                else:
                    # Extract the raw string and try to find JSON in it
                    result_str = str(result)
                    json_start = result_str.find('{')
                    json_end = result_str.rfind('}') + 1
                    if json_start != -1 and json_end > json_start:
                        result = json.loads(result_str[json_start:json_end])
                    else:
                        # Create a fallback with the object's string representation
                        return {
                            "title": url.split('/')[-1].replace('-', ' ').title() if url else "Product",
                            "price": {
                                "value": None,
                                "currency": "USD",
                                "confidence": 0
                            },
                            "description": "Product description not available",
                            "extraction_method": "object_fallback",
                            "overall_confidence": 0
                        }
            except Exception as e:
                print(f"Error converting result to dictionary: {e}")
                # Return fallback if conversion fails
                return {
                    "title": url.split('/')[-1].replace('-', ' ').title() if url else "Product",
                    "price": {
                        "value": None,
                        "currency": "USD",
                        "confidence": 0
                    },
                    "description": "Product description not available",
                    "extraction_method": "conversion_fallback",
                    "overall_confidence": 0
                }
            
        return result
        
    except Exception as e:
        print("CrewAI JSON parsing error:", e)
        # Create a fallback result with URL-derived information
        product_name = url.split('/')[-1].replace('-', ' ').title() if url else "Product"
        return {
            "title": product_name,
            "price": {
                "value": None,
                "currency": "USD",
                "confidence": 0
            },
            "description": "Product description not available",
            "extraction_method": "error_fallback",
            "error": f"AI extraction failed: {str(e)}",
            "overall_confidence": 0
        }

