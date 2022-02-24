# Priority: 1
import re
from datetime import datetime

import discord
import html2text
from discord.app import Option
from utils.buttons import Pager
from utils.objects import ACResponse, SlashCommand

htmlhandler = html2text.HTML2Text()
htmlhandler.ignore_images = True
htmlhandler.ignore_emphasis = True
htmlhandler.body_width = 0

class SearchModCommand(SlashCommand, name="search_mod", description="Search for a mod at Trovesaurus"):
    query = Option(description="What mod to search on Trovesaurus", autocomplete=True)
    async def callback(self):
        ctx = await self.get_context()
        if len(self.query) < 3:
            return await ctx.send("Query string too small.")
        await self._get_mods_list(self.query)
        view = Pager(ctx, start_end=False, step_10=True)
        i = 0
        for mod in ctx.bot.Trove.mods_list:
            if re.findall(f"(?:\W|^)({re.escape(self.query.lower())})", mod["name"].lower()):
                i += 1
                e = view.make_page()
                e.color = discord.Color.random()
                e.timestamp = datetime.utcfromtimestamp(int(mod["date"]))
                e.description = htmlhandler.handle(mod["description"])
                e.title = mod["name"]
                e.url = "https://trovesaurus.com/mod=" + mod["id"]
                e.set_author(name=str(mod.get("author")) + (f" | Mod {i} out of {len(ctx.bot.Trove.mods_list)}" if len(ctx.bot.Trove.mods_list) > 1 else ""))
                e.add_field(name="Type", value=mod["type"], inline=False)
                e.add_field(name="Views", value=mod["views"])
                e.add_field(name="Downloads", value=mod["totaldownloads"])
                e.add_field(name="Likes", value=mod["votes"])
                e.set_image(url=mod["image_full"])
                e.set_footer(text=f"Source: Trovesaurus | ID: {mod['id']} | Created at", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
        if not len(view.pages):
            return await ctx.send("No mods match that query.")
        view.message = await view.selected_page.send(ctx.send, view=view.start())

    async def _get_mods_list(self, query):
        if not hasattr(self.client.Trove, "mods_list") or datetime.utcnow().timestamp() - self.client.Trove.mods_list_update > 1800:
            mods_list = await self.client.AIOSession.post(self.client.keys["Trovesaurus"]["Mods"])
            mods_list = await mods_list.json()
            self.client.Trove.mods_list = sorted(mods_list, key=lambda x: x["name"])
            self.client.Trove.mods_list_update = datetime.utcnow().timestamp()

    async def autocomplete(self, options, focused):
        response = ACResponse()
        query = options[focused]
        query = query.lower()
        await self._get_mods_list(query)
        if len(query) < 3:
            return response
        for mod in self.client.Trove.mods_list:
            if re.findall(f"(?:\W|^)({query.lower()})", mod["name"].lower()):
                response.add_option(f"{mod['name']} | by {mod['author']}", mod["name"])
        return response[:25]

def setup(bot):
    bot.application_command(SearchModCommand)
