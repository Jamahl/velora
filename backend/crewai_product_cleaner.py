from crewai import Agent, Task, Crew

import json

def run_product_cleaner(firecrawl_data):
    # Use only the metadata for extraction
    metadata = firecrawl_data.get("data", {}).get("metadata", {})
    url = metadata.get("url") or metadata.get("og:url") or metadata.get("ogUrl")
    agent = Agent(
        role="product_cleaner",
        goal="Extract and clean product data from e-commerce metadata JSON.",
        backstory="You are an expert product data extractor. Only use values from the input JSON. Never invent or guess."
    )
    task = Task(
        description=(
            'You are a data extraction expert. Your mission is to analyze the Firecrawl metadata JSON provided and extract key product information with extreme accuracy. ' 
            'You MUST NOT invent, guess, or hallucinate any data. Every piece of information in your output must be sourced directly from the input metadata.'
        ),
        expected_output=(
            'A single, clean JSON object containing the extracted product data. Follow these rules strictly:\n'
            '1. **Source from Metadata ONLY**: Every value in the output JSON MUST be extracted from the `metadata` input. Do not use the `markdown` field.\n'
            '2. **Never Invent Data**: If a value is not present in the metadata, use `null` for that field. Do not make up values like "Sample Product" or prices.\n'
            '3. **Field Mapping**: Use the following logic to find the best value for each field:\n'
            '   - `title`: Use `og:title` first, then `title`.\n'
            '   - `price`: Use `og:price:amount`. Extract only the number.\n'
            '   - `image_url`: Use `og:image` first, then `ogImage`.\n'
            '   - `site_name`: Use `og:site_name` first, then `ogSiteName`.\n'
            '   - `description`: Use `og:description` first, then `description`.\n'
            '   - `url`: Use `og:url` first, then `url`.\n'
            '   - `category`, `original_price`, `last_checked`: Set to `null` as they are not in the metadata.\n'
            '4. **Example**:\n'
            '   - **Input Metadata**: `{"og:title": "Cool T-Shirt", "og:price:amount": "19.99", "og:image": "http://example.com/img.png"...}`\n'
            '   - **Correct Output**: `{"title": "Cool T-Shirt", "price": 19.99, "image_url": "http://example.com/img.png", "site_name": null, ...}`\n'
            '5. **Output Format**: Return ONLY the final, valid JSON object and nothing else.'
        ),
        input_data={**metadata, "url": url},
        agent=agent
    )
    crew = Crew(tasks=[task])
    raw_result = crew.kickoff()
    print("CrewAI raw result:", raw_result)
    try:
        # If result is a string, try to parse as JSON
        if isinstance(raw_result, str):
            result = json.loads(raw_result)
        else:
            result = raw_result
        print("CrewAI parsed result:", result)
        return result
    except Exception as e:
        print("CrewAI JSON parsing error:", e)
        return None
