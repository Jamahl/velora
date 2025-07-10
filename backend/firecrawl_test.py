from firecrawl import JsonConfig, FirecrawlApp
from pydantic import BaseModel
import os
import json

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

api_key = "fc-610fb046b36f48a4b79d236bbecdefa2"

app = FirecrawlApp(api_key=api_key)
json_config = JsonConfig(schema=ProductSchema)

result = app.scrape_url(
    'https://www.farfetch.com/es/shopping/men/versace-leather-hooded-jacket-item-27152057.aspx',
    formats=["json"],
    json_options=json_config,
    only_main_content=False,
    timeout=120000
)

print(json.dumps(result.json, indent=2))
