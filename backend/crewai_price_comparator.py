import os
import asyncio
from crewai import Agent, Task, Crew
from tools import SearchTools

class PriceComparatorCrew:
    def __init__(self, product_title: str, original_price: float):
        self.product_title = product_title
        self.original_price = original_price
        self.web_search_tool = SearchTools.WebSearchTool()
        self.exa_search_tool = SearchTools.ExaSearchTool()

    async def run_async(self):
        # 1. Define parallel agents
        duck_agent = Agent(
            role="DuckDuckGo Search Analyst",
            goal=f"Find all offers for '{self.product_title}' cheaper than {self.original_price} using DuckDuckGo.",
            backstory="You are an expert at searching for deals using DuckDuckGo. You know how to find the best prices from across the web.",
            tools=[self.web_search_tool],
            allow_delegation=False
        )
        exa_agent = Agent(
            role="Exa Search Analyst",
            goal=f"Find all offers for '{self.product_title}' cheaper than {self.original_price} using Exa.",
            backstory="You are a professional price hunter who uses Exa search to find the lowest prices and best offers online.",
            tools=[self.exa_search_tool],
            allow_delegation=False
        )

        duck_task = Task(
            description=f"Search for cheaper offers for '{self.product_title}' (current price: {self.original_price}) using DuckDuckGo. Return a JSON list of offers (title, image_url, description, price, retailer, url).",
            expected_output="A JSON list of offers, each with title, image_url, description, price, retailer, url.",
            agent=duck_agent
        )
        exa_task = Task(
            description=f"Search for cheaper offers for '{self.product_title}' (current price: {self.original_price}) using Exa. Return a JSON list of offers (title, image_url, description, price, retailer, url).",
            expected_output="A JSON list of offers, each with title, image_url, description, price, retailer, url.",
            agent=exa_agent
        )

        # 2. Run both tasks in parallel (async)
        duck_crew = Crew(agents=[duck_agent], tasks=[duck_task], verbose=False)
        exa_crew = Crew(agents=[exa_agent], tasks=[exa_task], verbose=False)
        duck_future = duck_crew.kickoff_async()
        exa_future = exa_crew.kickoff_async()
        duck_result, exa_result = await asyncio.gather(duck_future, exa_future)

        # 3. Boss agent
        boss_agent = Agent(
            role="Offer Synthesizer",
            goal="Deduplicate, merge, and sort all offers from both sources. Only return offers cheaper than the original price. Present the best options to the user.",
            backstory="You are an expert at synthesizing and curating product offers. Your job is to merge, deduplicate, filter, and sort offers to present only the very best cheaper options to the user.",
            allow_delegation=False
        )
        # Extract dict or string context from CrewOutput for boss agent
        import json
        def extract_context(result):
            if hasattr(result, "json_dict") and result.json_dict:
                return result.json_dict
            elif hasattr(result, "raw") and result.raw:
                try:
                    return json.loads(result.raw)
                except Exception:
                    return {}
            elif isinstance(result, dict):
                return result
            elif isinstance(result, str):
                try:
                    return json.loads(result)
                except Exception:
                    return {}
            else:
                return {}
        merged_context = {
            "duck_results": extract_context(duck_result),
            "exa_results": extract_context(exa_result)
        }
        boss_task = Task(
            description=(
                f"You are given two lists of offers for '{self.product_title}' (current price: {self.original_price}), "
                "one from DuckDuckGo, one from Exa. Each offer has: title, image_url, description, price, retailer, url. "
                "Your job: 1) Merge both lists into one, 2) Remove duplicates (same url or same title+retailer), "
                "3) Filter out any offers with price >= {self.original_price}, 4) Sort the final list by price ascending, "
                "5) Return ONLY the following JSON: {\"offers\": [ ... ]}. "
                "If no valid offers, return {\"offers\": []}. Do NOT add any markdown, code blocks, or extra commentary."
            ),
            expected_output="A JSON object: {\"offers\": [ ... ]} with only unique, cheaper offers sorted by price ascending.",
            agent=boss_agent,
            context=merged_context
        )
        boss_crew = Crew(agents=[boss_agent], tasks=[boss_task], verbose=False)
        boss_result = boss_crew.kickoff()
        return boss_result

    async def run(self):
        return await self.run_async()
