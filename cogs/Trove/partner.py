# Priority: 1
import asyncio
import json
import re
from datetime import datetime, timedelta

import discord
import html2text
from bs4 import BeautifulSoup
from discord.ext import commands
from utils.buttons import Confirm, OptionPicker, Paginator
from utils.CustomObjects import CEmbed


class Partner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        htmlhandler = html2text.HTML2Text()
        htmlhandler.ignore_images = True
        htmlhandler.ignore_emphasis = True
        htmlhandler.body_width = 0
        self.htmlhandler = htmlhandler

    @commands.command(message_command=False, slash_command=True, slash_command_guilds=[118027756075220992], name="reportbug", help="Report an ingame bug to developers.")
    @commands.cooldown(1, 1800, commands.BucketType.guild)
    async def _report_a_bug(self, ctx):
        if ctx.channel.id not in [832582272011599902]:
            return await ctx.reply("You can't use this command in this channel.", ephemeral=True)
        await ctx.message.delete(silent=True)
        data = {
            "user": {
                "id": ctx.author.id,
                "avatar_url": str(ctx.author.avatar.replace(format="webp") if ctx.author.avatar else ctx.author.default_avatar),
                "name": ctx.author.name,
                "nickname": ctx.author.nick,
                "discriminator": ctx.author.discriminator,
                "display_name": str(ctx.author)
            },
            "platform": None,
            "trove_name": None,
            "time": None,
            "description": None,
            "result": None,
            "expected": None,
            "reproduction": None,
            "media_links": [],
            "message_id": 0,
            "message_jump": None
        }
        final_e = CEmbed(color=discord.Color.random(), timestamp=datetime.utcnow())
        final_e.set_author(name=f"Bug report by {ctx.author}", icon_url=ctx.author.avatar)
        e = CEmbed(title="Bug Report Form", description="Welcome to the bug report form!\n\nThis allows for better reporting of static formats for devs.\n\nIf you intend to share any media (images/videos) please use YouTube (videos) and Imgur (Images), media is extremely important for devs, despite it being optional try to give most of the time some sort of media to better picture your report.\n\nAlways remember that bugs that may be caused by mods should be attempted to repro with mods disabled. IE:`My UI doesn't show something that it should.` disable UI mods and make sure it still happens.\n\nYou'll be asked some questions, some are optionals others are required.\n\nDo you wish to proceed with the report?", color=discord.Color.random())
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        confirmation = Confirm(ctx, 30)
        msg = await ctx.send(embed=e, view=confirmation)
        await confirmation.wait()
        if confirmation.value is None:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        if not confirmation.value:
            return await self.bot.utils.eedit(msg, content=f"{ctx.author.mention} cancelled the bug report.", embed=None, view=None, delete_after=15)
       # Platform
        servers = [
            {"text":"PC", "emoji": "<:windows:839445248517079050>"}, 
            {"text":"PTS", "emoji": "<:sageclown:923956528434794496>"}, 
            {"text":"PS4", "emoji": "<:playstation:921080331782737990>"}, 
            {"text":"Xbox", "emoji": "<:xbox:839439645359603713>"}, 
            {"text":"Switch", "emoji": "<:switch:921081085083926569>"}
        ]
        e.description = "**Platform**\n\nWhat platform did you experience this bug on?"
        picker = OptionPicker(ctx, servers)
        if not await self.bot.utils.eedit(msg, embed=e, view=picker):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", ephemeral=True)
        e.color = discord.Color.random()
        await picker.wait()
        if picker.value is None:
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.add_field(name="Platform", value=picker.value)
        data["platform"] = picker.value
       # Trove Name
        e.description = "**Trove InGame Name**\n\nWhat is your ingame name on the platform you picked?\n\nThis is relevant because devs are able to look into logs and filter them down to digestible sizes making it much easier to tackle certain issues."
        e.set_footer(text="Type cancel to stop report.")
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e, view=None):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check4(m):
            if not m.author.bot and m.channel.id == ctx.channel.id and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(m.delete(silent=True))
            return m.channel == ctx.channel and m.author == ctx.author and (re.findall(r"^([a-zA-Z0-9_]{3,19})$", m.content) or m.content.lower() == "cancel")
        try:
            m = await self.bot.wait_for("message", check=check4, timeout=600)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.add_field(name="Trove IGN", value=m.content)
        data["trove_name"] = m.content
       # Time
        e.description = "**Time frame** [2 minutes]\n\nHow long ago was the last time you experienced the bug? [Limit: 1 Week]\n\nIt doesn't need to be 100% accurate, try to get as close as possible as times help devs find logs and data more quickly in order to tackle the possible issue.```5 minutes\n4 hours 37 minutes\n7 days```"
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check3(m):
            if not m.author.bot and m.channel.id == ctx.channel.id and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(m.delete(silent=True))
            return m.channel == ctx.channel and ((m.author == ctx.author and self.bot.utils.time_str(m.content.lower())[0] and self.bot.utils.time_str(m.content.lower())[0] <= 604800) or m.content.lower() == "cancel")
        try:
            m = await self.bot.wait_for("message", check=check3, timeout=120)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        time_ago = timedelta(seconds=self.bot.utils.time_str(m.content.lower())[0])
        final_e.add_field(name="Time", value=datetime.utcnow().replace(microsecond=0) - time_ago)
        data["time"] = str(datetime.utcnow().replace(microsecond=0) - time_ago)
       # Context
        e.description = "**Bug Title** [10 minutes]\n\nPlease give the title of the bug.\n\nKeep in mind steps to reproduce and expected vs observed will be asked afterwards.\nSo only include a simple description of the bug and any data you find useful."
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e):
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check6(m):
            if not m.author.bot and m.channel.id == ctx.channel.id and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(m.delete(silent=True))
            return m.channel == ctx.channel and m.author == ctx.author
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=600)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.description = "**Context**\n" + m.content
        data["description"] = m.content
       # Expected
        e.description = "**Expected Result** [3 minutes]\n\nWhat was the expected behaviour?"
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=180)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                await self.bot.utils.ssend(ctx.author, content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.add_field(name="Expected", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["expected"] = m.content
       # Observed
        e.description = "**Observed Result** [3 minutes]\n\nWhat actually happened?"
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15, ephemeral=True)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=180)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                await self.bot.utils.ssend(ctx.author, content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.add_field(name="Observed", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["result"] = m.content
       # Reproduction
        e.description = "**Reproduction Steps** [5 minutes]\n\nPlease give a brief description of what are the steps to make this bug happen, include all information you find valuable towards the bug **only**.\n\nThis step is very important, it tells devs how to make the bug happen so they can better understand what's happening in their testing environments."
        e.color = discord.Color.random()
        if not await self.bot.utils.eedit(msg, embed=e):
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=300)
            await m.delete(silent=True)
            if m.content.lower() == "cancel":
                await self.bot.utils.ssend(ctx.author, content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        final_e.add_field(name="Reproduction Steps", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["reproduction"] = m.content
       # Media
        e.description = "**Media linking**\n\nPlease send links of any media you have on the bug. [Limit: 10]\n\nOnly [YouTube](https://www.youtube.com/) and [Imgur](https://imgur.com/)\n\nIf you are done or don't have any media to share, just type `Done`\n\n"
        yt_regex = r"(?:https?://)?(?:www\.)?youtu(?:be\.com/watch\?(?:.*?&(?:amp;)?)?v=|\.be/)(?:[\w\-]+)(?:&(?:amp;)?[\w\?=]*)?"
        imgur_regex = r"(?:(?:http|https):\/\/)?(?:i\.)?imgur.com\/(?:(?:gallery\/)(?:\w+)|(?:a\/)(?:\w+)#?)?(?:\w*)"
        def check5(m):
            if not m.author.bot and m.channel.id == ctx.channel.id and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(m.delete(silent=True))
            return m.channel == ctx.channel and m.author == ctx.author and (re.findall(yt_regex, m.content) or re.findall(imgur_regex, m.content) or m.content.lower() in ["done", "cancel"])
        while True:
            if len(data["media_links"]) == 10:
                break
            e.color = discord.Color.random()
            if not await self.bot.utils.eedit(msg, embed=e):
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
            try:
                m = await self.bot.wait_for("message", check=check5, timeout=120)
                await m.delete(silent=True)
                if m.content.lower() == "cancel":
                    await self.bot.utils.ssend(ctx.author, content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                    return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
                if m.content.lower() == "done":
                    break
                links = list(set([i for i in re.findall(yt_regex, m.content) if i not in data["media_links"]] + [i for i in re.findall(imgur_regex, m.content) if i not in data["media_links"]]))
                data["media_links"] += links[:10]
                if "**Media Links:**" not in e.description:
                    e.description += "**Media Links:**\n"
                e.description += "\n".join(["<" + link + ">" for link in links])
            except:
                ctx.command.reset_cooldown(ctx)
                return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
        if data["media_links"]:
            final_e.add_field(name="Media", value="\n".join(data["media_links"]), inline=False)
       # Finalization
        await msg.delete(silent=True)
        reporti = await ctx.send(embed=final_e)
        conf_e = CEmbed(description="This is the final look at your bug report, do you want to submit?\n\nThis action can't be undone.", color=discord.Color.random())
        conf_e.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        confirmation = Confirm(ctx, 90)
        msg = await ctx.send(embed=conf_e, view=confirmation)
        await confirmation.wait()
        if not confirmation.value:
            ctx.command.reset_cooldown(ctx)
            await self.bot.utils.ssend(ctx.author, content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
            await reporti.delete(silent=True)
            await msg.delete(silent=True)
            if confirmation.value is None:
                return await self.bot.utils.eedit(msg, content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, view=None, delete_after=15)
            return await self.bot.utils.eedit(msg, content="You've cancelled the bug report.", embed=None, view=None, delete_after=15)
        final_e.set_footer(text="Reported via Bot")
        report = await self.bot.get_channel(859440482195341323).send(embed=final_e)
        data["message_id"] = report.id
        data["message_jump"] = report.jump_url
        async with self.bot.AIOSession.post("https://trovesaurus.com/discord/issues", data={"payload": json.dumps(data), "Token": self.bot.keys["Trovesaurus"]["Token"]}) as request:
            if request.status == 200:
                await ctx.send(f"{ctx.author.mention} Bug report submitted successfully.")#, delete_after=15)
                final_e.add_field(name="\u200b", value=f"[View on Trovesaurus Issue Tracker]({await request.text()})")
                await report.edit(embed=final_e)
            else:
                await report.delete(silent=True)
                await self.bot.utils.ssend(ctx.author, content="This report failed to be sent to Trovesaurus, so here it is for you to retry.", embed=final_e)
                await ctx.send(f"{ctx.author.mention} Bug report wasn't submitted, an error occured.")
        ctx.command.reset_cooldown(ctx)

    @commands.command(slash_command=True, name="calendar", aliases=["events"], help="Check out Trovesaurus calendar.")
    async def _show_events(self, ctx):
        request = await self.bot.AIOSession.get("https://trovesaurus.com/calendar/feed")
        calendar = await request.json(content_type="text/html")
        e = CEmbed(color=0x2a5757)
        e.description = f"You can check current and upcoming events at [Trovesaurus](https://trovesaurus.com/calendar/new)"
        e.set_author(name="Trovesaurus Calendar", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
        if calendar:
            calendar.sort(key= lambda x: x["enddate"])
            e.set_thumbnail(url=calendar[0]["icon"])
            for event in calendar:
                url = f"https://trovesaurus.com/event={event['id']}"
                name = event["name"]
                category = event["category"]
                start, end = event["startdate"], event["enddate"]
                e.add_field(name=f"{category}: {name}", value=f"[About this event]({url})\nStarted on <t:{start}:F>\nEnds <t:{end}:R>", inline=False)
        else:
            e.description += "\n\nNo Events are happening at the time."
        await ctx.reply(embed=e)

    @commands.command(slash_command=True, help="Search for items, decos or styles on Trovesaurus.")
    async def search(self, ctx, *, search=commands.Option(name="search", description="What to search on Trovesaurus?")):
        await ctx.defer()
        whitelist = [
            "Collections",
            "Items",
            "Deco",
            "Styles",
            "News",
            "Guides",
            "Users"
        ]
        results = {}
        request = await self.bot.AIOSession.post("https://trovesaurus.com/search/", data={"Search": search}, allow_redirects=True)
        soup = BeautifulSoup(await request.text(), "html.parser")
        # Get Categories
        nav_list = soup.find("ul", id="searchResultsNav")
        raw_categories = [i.find_next("a").text.replace("\n", " ").strip() for i in nav_list.findAll("li")]
        categories = [c for c in re.findall("([a-z ]+) ([0-9]+)", str(raw_categories), re.IGNORECASE) if c[0] in whitelist]
        for category, result_count in categories:
            results[category] = {
                "qname": category.replace(" ", "").lower(),
                "count": int(result_count),
                "results": []
            }
        # ...
        serch = search.replace(" ", "%20")
        search_link = request.url
        for category, data in results.items():
            req = await self.bot.AIOSession.post(f"https://trovesaurus.com/search/{serch}/{data['qname']}")
            soup = BeautifulSoup(await req.text(), "html.parser")
            if category in ["Collections", "Items", "Deco", "Styles"]:
                items = soup.findAll("figure", {"class": "figure"})
                data["results"] = [
                    {
                        "name": item.find("figcaption").find("a").string.strip(),
                        "extra_info": "",
                        "link": item.find("a").get("href"),
                        "image": item.find("a").find("img").get("src")
                    }
                    for item in items if re.findall(f"(?:\W|^)({search.lower()})", item.find("figcaption").find("a").string.strip().lower())
                ]
            if category in ["Guides"]:
                page_results = soup.findAll("div", {"class": "col-md-9"})[0]
                items = page_results.find_all("li", {"class": "nav-item"})
                data["results"] = [
                    {
                        "name": item.find("div", {"class": "text-shadow"}).text.strip(),
                        "extra_info": "",
                        "link": item.find("a").get("href"),
                        "image": None
                    }
                    for item in items if re.findall(f"(?:\W|^)({search.lower()})", item.find("div", {"class": "text-shadow"}).text.strip().lower())
                ]
            if category in ["News"]:
                page_results = soup.findAll("div", {"class": "col-md-9"})[0]
                items = page_results.find_all(["a", "img"], {"loading": "lazy", "class": None})
                data["results"] = [
                    {
                        "name": item.parent.text.strip(),
                        "extra_info": "",
                        "link": item.parent.get("href"),
                        "image": item.get("src")
                    }
                    for item in items if re.findall(f"(?:\W|^)({search.lower()})", item.parent.text.strip().lower())
                ]
            if category in ["Users"]:
                page_results = soup.findAll("div", {"class": "col-md-9"})[0]
                items = page_results.find_all("a", {"class": None, "href": lambda x: x.startswith("https://trovesaurus.com/user=") if x is not None else False})
                data["results"] = [
                    {
                        "name": item.text.strip(),
                        "extra_info": "",
                        "link": item.get("href"),
                        "image": ("https:" if item.parent.parent.parent.findNext("img").get("src").startswith("//") else "") + item.parent.parent.parent.findNext("img").get("src")
                    }
                    for item in items if item if re.findall(f"(?:\W|^)({search.lower()})", item.text.strip().lower())
                ]
            # if category in ["Strings"]:
            #     page_results = soup.findAll("div", {"class": "col-md-9"})[0]
            #     items = page_results.find_all("blockquote")
            #     data["results"] = [
            #         {
            #             "name": item.find_previous_sibling('p').findNext('strong').text.strip(),
            #             "extra_info": item.text.strip(),
            #             "link": None,
            #             "image": None
            #         }
            #         for item in items if item
            #     ]
        items = []
        for nav, data in results.items():
            for res in data["results"]:
                res["postname"] = f"{nav}/{res['name']}"
                items.append(res)
        if not items:
            return await ctx.send(f"No items match `{search}` in the following categories: `{'`, `'.join([i.capitalize() for i in whitelist])}`", ephemeral=True)
        e = discord.Embed()
        e.color = discord.Color.random()
        e.description = ""
        e.set_author(name=f"Results for search '{search}' at Trovesaurus", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
        for item in items[:8]:
            e.description += f"[`{item['postname']}`]({item['link']})\n"
        if len(items) > 8:
            e.description += f"... and more\n"
        if len(items) == 1 and items[0]["image"]:
            e.set_thumbnail(url=items[0]["image"])
        e.description += f"\nGet more results for this search at [Trovesaurus]({search_link})"
        await ctx.send(embed=e, reference=ctx.message.reference, mention_author=True)

    @commands.command(slash_command=True, aliases=["sm", "mod", "searchmod", "find_mod", "findmod"], help="Search for mods on Trovesaurus.")
    async def search_mod(self, ctx, *, mod=commands.Option(name="search", description="What mod to find on Trovesaurus?")):
        await ctx.defer()
        if len(mod) < 4:
            return await ctx.send("Search word too small.")
        request = await self.bot.AIOSession.post(self.bot.keys["Trovesaurus"]["Mods"])
        mods_list = sorted(list(filter(lambda x: mod.lower() in x["name"].lower(),json.loads(await request.text()))), key=lambda x: -int(x["totaldownloads"]))
        if not mods_list:
            return await ctx.send("No mods found.")
        i = 0
        pages = []
        for mod in mods_list:
            i += 1
            e = discord.Embed()
            e.color = discord.Color.random()
            e.timestamp = datetime.utcfromtimestamp(int(mod["date"]))
            e.description = self.htmlhandler.handle(mod["description"])
            e.title = mod["name"]
            e.url = "https://trovesaurus.com/mod=" + mod["id"]
            e.set_author(name=str(mod.get("author")) + (f" | Mod {i} out of {len(mods_list)}" if len(mods_list) > 1 else ""))
            e.add_field(name="Type", value=mod["type"], inline=False)
            e.add_field(name="Views", value=mod["views"])
            e.add_field(name="Downloads", value=mod["totaldownloads"])
            e.add_field(name="Likes", value=mod["votes"])
            e.set_image(url=mod["image_full"])
            e.set_footer(text=f"Source: Trovesaurus | ID: {mod['id']} | Created at", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
            page = {
                "content": None,
                "page": i,
                "embed": e
            }
            pages.append(page)
        view = Paginator(ctx, pages, start_end=True)
        view.message = await ctx.send(embed=pages[0]["embed"], view=view)    

def setup(bot):
    bot.add_cog(Partner(bot))
