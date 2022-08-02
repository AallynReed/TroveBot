# Priority: 1
import re
from typing import Literal

import discord
from discord.app import Option
from utils.CustomObjects import CEmbed
from utils.objects import ACResponse, SlashCommand


class SearchCommand(SlashCommand, name="search", description="What to search on Trovesaurus?"):
    query = Option(description="What to search on Trovesaurus?", autocomplete=True)
    filtering: Literal["Collections", "Items", "Deco", "Styles"] = Option(default=None, description="Filter results by type")
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        categories = ["collections", "items", "deco", "styles"]
        ctx = await self.get_context()
        if len(self.query) < 3:
            return await ctx.send("Query string too small.")
        request = await self.client.AIOSession.get(f"https://trovesaurus.com/search/{self.query}.json")
        result = await request.json()
        if result.get("error"):
            return await ctx.send(f"No results found for `{self.query}`", ephemeral=True)
        items = []
        for category in categories:
            if category_results := result.get(category):
                for item in category_results["results"].items():
                    if re.findall(f"(?:\W|^)({re.escape(self.query.lower())})", item[1]["name"].lower()):
                        item[1]["type"] = category
                        items.append(item)
        items.sort(key=lambda x: x[1]["name"])
        e = CEmbed()
        e.color = discord.Color.random()
        e.description = ""
        e.set_author(name=f"Results for search '{self.query}' at Trovesaurus", icon_url="https://trovesaurus.com/images/logos/Sage_64.png")
        for key, value in items[:8]:
            raw = key.split("/")[-1]
            e.description += f"[`{value['type']}/{value['name']}`](https://trovesaurus.com/{key}) `{raw}`\n"
        if len(items) > 8:
            e.description += f"\n... and more\n"
        if len(items) == 1 and items[0][1]["icon"]:
            e.set_thumbnail(url=value["icon"])
        e.description += f"\nGet more results for this search at [Trovesaurus](https://trovesaurus.com/search/{self.query.replace(' ', '%20')})"
        await ctx.send(embed=e)
    
    async def autocomplete(self, options, focused: str):
        categories = ["collections", "items", "deco", "styles"]
        response = ACResponse()
        query = options[focused]
        query = query.lower()
        if len(query) < 3:
            return response
        request = await self.client.AIOSession.get(f"https://trovesaurus.com/search/{query}.json")
        try:
            result = await request.json()
        except:
            return response
        if result.get("error"):
            return response
        for category in categories:
            category_results = result.get(category)
            if category_results:
                for key, value in category_results["results"].items():
                    if re.findall(f"(?:\W|^)({re.escape(query.lower())})", value["name"].lower()):
                        response.add_option(name=f"{category}/{value['name']}", value=value["name"])
        return response[:25]

def setup(bot):
    bot.application_command(SearchCommand)
