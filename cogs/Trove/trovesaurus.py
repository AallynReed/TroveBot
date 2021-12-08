# Priority: 1
import asyncio
import json
import re
from datetime import datetime, timedelta
from io import BytesIO

import discord
import html2text
import utils.checks as perms
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from discord.ext import commands


class Trovesaurus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession()
        htmlhandler = html2text.HTML2Text()
        htmlhandler.ignore_images = True
        htmlhandler.ignore_emphasis = True
        htmlhandler.body_width = 0
        self.htmlhandler = htmlhandler

    def cog_unload(self):
        asyncio.create_task(self.terminate_cog())

    async def terminate_cog(self):
        await self.session.close()

    def _get_figures(self, soup, search, nav):
        items = soup.findAll("figure", {"class": "figure"})
        items = [
            {
                "name": item.find("figcaption").find("a").string.strip(),
                "link": item.find("a").get("href"),
                "image": item.find("a").find("img").get("src"),
                "nav": nav
            }
            for item in items if re.findall(f"(\W|^){search.lower()}", item.find("figcaption").find("a").string.strip().lower())
        ]
        return items

    @commands.command(slash_command=True, help="Search for items, decos or styles on Trovesaurus.")
    async def search(self, ctx, *, search=commands.Option(name="search", description="What to search on Trovesaurus?")):
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
        async with self.session.post("https://trovesaurus.com/search/", data={"Search": search}, allow_redirects=True) as request:
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
                async with self.session.post(f"https://trovesaurus.com/search/{serch}/{data['qname']}") as req:
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
                return await ctx.send(f"No items match `{search}` in the following categories: `{'`, `'.join([i.capitalize() for i in whitelist])}`")
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
        if len(mod) < 4:
            return await ctx.send("Search word too small.")
        async with self.session.post(self.bot.keys["Trovesaurus"]["Mods"]) as request:
            mods_list = sorted(list(filter(lambda x: mod.lower() in x["name"].lower(),json.loads(await request.text()))), key=lambda x: -int(x["totaldownloads"]))
            if not mods_list:
                return await ctx.send("No mods found.")
            i = 0
            e = discord.Embed(description="<a:loading:844624767239192576> Looking for mods...")
            msg = await ctx.send(embed=e)
            def reactioncheck(reaction, user):
                return user == ctx.author and reaction.emoji in ["▶", "◀"] and reaction.message.id == msg.id
            reacted = False
            while True:
                mod = mods_list[i]
                e = discord.Embed()
                e.color = discord.Color.random()
                e.timestamp = datetime.utcfromtimestamp(int(mod["date"]))
                e.description = self.htmlhandler.handle(mod["description"])
                e.title = mod["name"]
                e.url = "https://trovesaurus.com/mod=" + mod["id"]
                #e.description += "\n".join()
                e.set_author(name=str(mod.get("author")) + (f" | Mod {i+1} out of {len(mods_list)}" if len(mods_list) > 1 else ""))
                e.add_field(name="Type", value=mod["type"], inline=False)
                e.add_field(name="Views", value=mod["views"])
                e.add_field(name="Downloads", value=mod["totaldownloads"])
                e.add_field(name="Likes", value=mod["votes"])
                e.set_image(url=mod["image_full"])
                e.set_footer(text=f"Source: Trovesaurus | ID: {mod['id']} | Created at", icon_url="https://trovesaurus.com/images/logos/Sage_64.png?1")
                await msg.edit(embed=e)
                if len(mods_list) == 1:
                    return
                if not reacted:
                    await msg.add_reaction("◀")
                    await msg.add_reaction("▶")
                    reacted = True
                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", timeout=120, check=reactioncheck)
                    if reaction.emoji == "▶":
                        if i + 1 == len(mods_list):
                            i = 0
                        else:
                            i += 1
                    elif reaction.emoji == "◀":
                        if i - 1 < 0:
                            i = len(mods_list) - 1
                        else:
                            i -= 1
                    try:
                        await msg.remove_reaction(str(reaction), ctx.author)
                    except:
                        pass
                except:
                    try:
                        await msg.clear_reactions()
                    except:
                        pass
                    break

    @commands.command(name="reportbug", aliases=["bugreport", "rbug", "bugr"], hidden=True)
    @commands.cooldown(1, 1800, commands.BucketType.guild)
    async def _report_a_bug(self, ctx):
        if ctx.channel.id != 832582272011599902:
            return
        try:
            await ctx.message.delete()
        except:
            pass
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
        async def delete_message(m):
            try:
                await m.delete()
            except:
                pass
        final_e = discord.Embed(color=discord.Color.random(), timestamp=datetime.utcnow())
        final_e.set_author(name=f"Bug report by {ctx.author}", icon_url=ctx.author.avatar)
        e = discord.Embed(title="Bug Report Form", description="Welcome to the bug report form!\n\nThis allows for better reporting of static formats for devs.\n\nIf you intend to share any media (images/videos) please use YouTube (videos) and Imgur (Images), media is extremely important for devs, despite it being optional try to give most of the time some sort of media to better picture your report.\n\nAlways remember that bugs that may be caused by mods should be attempted to repro with mods disabled. IE:`My UI doesn't show something that it should.` disable UI mods and make sure it still happens.\n\nYou'll be asked some questions, some are optionals others are required.\n\nDo you wish to proceed with the report?", color=discord.Color.random())
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        msg = await ctx.send(embed=e)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        def check1(reaction, user):
            return reaction.message == msg and user == ctx.author and str(reaction) in ["✅", "❌"]
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check1, timeout=90)
            if str(r) == "❌":
                ctx.command.reset_cooldown(ctx)
                return await msg.edit(content=f"{ctx.author.mention} cancelled the bug report.", embed=None, delete_after=15)
        except:
            try:
                ctx.command.reset_cooldown(ctx)
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
       # Platform
        try:
            await msg.clear_reactions()
        except:
            pass
        e.description = "**Platform**\n\nWhat platform did you experience this bug on?```\n1. PC\n2. PTS\n3. PS4\n4. Xbox\n5. Nintendo Switch```"
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        e.color = discord.Color.random()
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        servers = ["PC", "PTS", "PS4", "Xbox", "Nintendo Switch"]
        for r in reactions:
            await msg.add_reaction(r)
        def check2(reaction, user):
            return reaction.message == msg and user == ctx.author and str(reaction) in reactions
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check2, timeout=60)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.add_field(name="Platform", value=servers[reactions.index(str(r))])
        data["platform"] = servers[reactions.index(str(r))]
        try:
            await msg.clear_reactions()
        except:
            for r in reactions:
                await msg.remove_reaction(r, ctx.guild.me)
        try:
            await msg.clear_reactions()
        except:
            pass
       # Trove Name
        e.description = "**Trove InGame Name**\n\nWhat is your ingame name on the platform you picked?\n\nThis is relevant because devs are able to look into logs and filter them down to digestible sizes making it much easier to tackle certain issues."
        e.set_footer(text="Type cancel to stop report.")
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check4(m):
            if not m.author.bot and m.channel.id == 832582272011599902 and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(delete_message(m))
            return m.channel == ctx.channel and m.author == ctx.author and (re.findall(r"^([a-zA-Z0-9_]{3,19})$", m.content) or m.content.lower() == "cancel")
        try:
            m = await self.bot.wait_for("message", check=check4, timeout=600)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.add_field(name="Trove IGN", value=m.content)
        data["trove_name"] = m.content
       # Time
        e.description = "**Time frame** [2 minutes]\n\nHow long ago was the last time you experienced the bug? [Limit: 1 Week]\n\nIt doesn't need to be 100% accurate, try to get as close as possible as times help devs find logs and data more quickly in order to tackle the possible issue.```5 minutes\n4 hours 37 minutes\n7 days```"
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check3(m):
            if not m.author.bot and m.channel.id == 832582272011599902 and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(delete_message(m))
            return m.channel == ctx.channel and ((m.author == ctx.author and self.bot.utils.time_str(m.content.lower())[0] and self.bot.utils.time_str(m.content.lower())[0] <= 604800) or m.content.lower() == "cancel")
        try:
            m = await self.bot.wait_for("message", check=check3, timeout=120)
            if m.content.lower() == "cancel":
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        time_ago = timedelta(seconds=self.bot.utils.time_str(m.content.lower())[0])
        final_e.add_field(name="Time", value=datetime.utcnow().replace(microsecond=0) - time_ago)
        data["time"] = str(datetime.utcnow().replace(microsecond=0) - time_ago)
       # Context
        e.description = "**Bug Title** [10 minutes]\n\nPlease give the title of the bug.\n\nKeep in mind steps to reproduce and expected vs observed will be asked afterwards.\nSo only include a simple description of the bug and any data you find useful."
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        def check6(m):
            if not m.author.bot and m.channel.id == 832582272011599902 and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(delete_message(m))
            return m.channel == ctx.channel and m.author == ctx.author
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=600)
            if m.content.lower() == "cancel":
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.description = "**Context**\n" + m.content
        data["description"] = m.content
       # Expected
        e.description = "**Expected Result** [3 minutes]\n\nWhat was the expected behaviour?"
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=180)
            if m.content.lower() == "cancel":
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.add_field(name="Expected", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["expected"] = m.content
       # Observed
        e.description = "**Observed Result** [3 minutes]\n\nWhat actually happened?"
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=180)
            if m.content.lower() == "cancel":
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.add_field(name="Observed", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["result"] = m.content
       # Reproduction
        e.description = "**Reproduction Steps** [5 minutes]\n\nPlease give a brief description of what are the steps to make this bug happen, include all information you find valuable towards the bug **only**.\n\nThis step is very important, it tells devs how to make the bug happen so they can better understand what's happening in their testing environments."
        e.color = discord.Color.random()
        try:
            await msg.edit(embed=e)
        except:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
        try:
            m = await self.bot.wait_for("message", check=check6, timeout=300)
            if m.content.lower() == "cancel":
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        final_e.add_field(name="Reproduction Steps", value=m.content if len(m.content) <= 1024 else m.content[:1024-45] + "...\n**[Text visually redacted due to size]**", inline=False)
        data["reproduction"] = m.content
       # Media
        e.description = "**Media linking**\n\nPlease send links of any media you have on the bug. [Limit: 10]\n\nOnly [YouTube](https://www.youtube.com/) and [Imgur](https://imgur.com/)\n\nIf you are done or don't have any media to share, just type `Done`\n\n"
        yt_regex = r"(?:https?://)?(?:www\.)?youtu(?:be\.com/watch\?(?:.*?&(?:amp;)?)?v=|\.be/)(?:[\w\-]+)(?:&(?:amp;)?[\w\?=]*)?"
        imgur_regex = r"(?:(?:http|https):\/\/)?(?:i\.)?imgur.com\/(?:(?:gallery\/)(?:\w+)|(?:a\/)(?:\w+)#?)?(?:\w*)"
        def check5(m):
            if not m.author.bot and m.channel.id == 832582272011599902 and (not [r.id for r in m.author.roles if r.id in [533024164039098371, 125277653199618048]] or m.author == ctx.author):
                asyncio.create_task(delete_message(m))
            return m.channel == ctx.channel and m.author == ctx.author and (re.findall(yt_regex, m.content) or re.findall(imgur_regex, m.content) or m.content.lower() in ["done", "cancel"])
        while True:
            if len(data["media_links"]) == 10:
                break
            e.color = discord.Color.random()
            try:
                await msg.edit(embed=e)
            except:
                ctx.command.reset_cooldown(ctx)
                return await ctx.send("An error occured while reporting your bug please try again.", delete_after=15)
            try:
                m = await self.bot.wait_for("message", check=check5, timeout=120)
                if m.content.lower() == "cancel":
                    try:
                        await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                    except:
                        pass
                    return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
                if m.content.lower() == "done":
                    break
                links = list(set([i for i in re.findall(yt_regex, m.content) if i not in data["media_links"]] + [i for i in re.findall(imgur_regex, m.content) if i not in data["media_links"]]))
                data["media_links"] += links[:10]
                if "**Media Links:**" not in e.description:
                    e.description += "**Media Links:**\n"
                e.description += "\n".join(["<" + link + ">" for link in links])
            except:
                ctx.command.reset_cooldown(ctx)
                try:
                    return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
                except:
                    return
        if data["media_links"]:
            final_e.add_field(name="Media", value="\n".join(data["media_links"]), inline=False)
       # Finalization
        try:
            await msg.delete()
        except:
            pass
        reporti = await ctx.send(embed=final_e)
        conf_e = discord.Embed(description="This is the final look at your bug report, do you want to submit?\n\nThis action can't be undone.", color=discord.Color.random())
        conf_e.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        msg = await ctx.send(embed=conf_e)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        try:
            r, _ = await self.bot.wait_for("reaction_add", check=check1, timeout=60)
            if str(r) == "❌":
                ctx.command.reset_cooldown(ctx)
                try:
                    await reporti.delete()
                except:
                    pass
                try:
                    await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
                except:
                    pass
                return await msg.edit(content="You've cancelled the bug report.", embed=None, delete_after=15)
        except:
            ctx.command.reset_cooldown(ctx)
            try:
                await reporti.delete()
            except:
                pass
            try:
                await ctx.author.send(content="This report was cancelled but here it is, in case you want to retry.", embed=final_e)
            except:
                pass
            try:
                return await msg.edit(content=f"Time Out {ctx.author.mention}, you didn't answer in time", embed=None, delete_after=15)
            except:
                return
        try:
            await msg.delete()
        except:
            pass
        try:
            await reporti.delete()
        except:
            pass
        final_e.set_footer(text="Reported via Bot")
        report = await self.bot.get_channel(812354696320647238).send(embed=final_e)
        data["message_id"] = report.id
        data["message_jump"] = report.jump_url
        async with self.bot.AIOSession.post("https://trovesaurus.com/discord/issues", data={"payload": json.dumps(data), "Token": self.bot.keys["Trovesaurus"]["Token"]}) as request:
            if request.status == 200:
                await ctx.send(f"{ctx.author.mention} Bug report submitted successfully.")#, delete_after=15)
                final_e.add_field(name="\u200b", value=f"[View on Trovesaurus Issue Tracker]({await request.text()})")
                await report.edit(embed=final_e)
            else:
                try:
                    await report.delete()
                except:
                    pass
                try:
                    await ctx.author.send(content="This report failed to be sent to Trovesaurus, so here it is for you to retry.", embed=final_e)
                except:
                    pass
                await ctx.send(f"{ctx.author.mention} Bug report wasn't submitted, an error occured.")
        ctx.command.reset_cooldown(ctx)

    @commands.command(slash_command=True, slash_command_guilds=[118027756075220992])
    @commands.has_any_role(125277653199618048)
    async def repost(self, ctx, message=commands.Option(description="ID of the message to repost")):
        try:
            await ctx.message.delete()
        except:
            ...
        try:
            m = await ctx.channel.fetch_message(int(message))
        except:
            return await ctx.send("Message ID is invalid or message was not found", delete_after=10, ephemeral=True)
        await ctx.send("Ok", ephemeral=True)
        await ctx.channel.send(content=m.content, embed=m.embeds[0] if m.embeds else None, reference=None)
        


    @commands.Cog.listener("on_raw_reaction_add")
    async def reaction_listener(self, payload):
        if payload.channel_id != 812354696320647238:
            return
        user = payload.member
        allowed_roles = [841729071854911568, 533024164039098371, 125277653199618048]
        emojis = {
            "👌": "ok_hand",
            "325430109043556352": "plus1",
            "832749567497863201": "pannotes"
        }
        for role in allowed_roles:
            if role in [r.id for r in user.roles]:
                try:
                    msg = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    url = [field for field in msg.embeds[0].fields if field.name == "\u200b"][0].value
                    if not payload.emoji.id:
                        react = emojis[str(payload.emoji)]
                    else:
                        react = emojis[str(payload.emoji.id)]
                    data = {
                        "ticket_id": int(re.findall(r"\/issues\/view\/([0-9]{0,4})", url)[0]),
                        "reaction": react
                    }
                except Exception as e:
                    print(e)
                    return
                await self.bot.AIOSession.post("https://trovesaurus.com/discord/issues", data={"payload": json.dumps(data), "Token": self.bot.keys["Trovesaurus"]["Token"]})
                break

    @commands.command(hidden=True)
    @perms.owners()
    async def update_allies(self, ctx):
        result = await self.bot.AIOSession.get("https://trovesaurus.com/collection/Pets.json")
        allies_list = await result.json()
        now = int(datetime.utcnow().timestamp())
        i = 0
        x = 0
        y = 0
        z = 0
        old_allies = json.loads(open("data/allies.json").read())
        allies = json.loads(open("data/allies.json").read())
        found_allies = []
        for ally_item in allies_list:
            i += 1
            ally = ally_item.split("/")[-1]
            found_allies.append(ally)
            stop = False
            for data in old_allies.keys():
                if ally == data:
                    if old_allies[data]["updated_at"] + 86400 > now:
                        stop = True
                        break    
            if stop:
                continue
            ally_result = await self.bot.AIOSession.get("https://trovesaurus.com/collections/pet/"+ally+".json")
            ally_data = await ally_result.json()
            if ally in allies.keys():
                old_ally = allies[ally]
                ally_data["updated_at"] = old_ally["updated_at"]
                if ally_data == old_ally:
                    continue
                x += 1
            else:
                z += 1
            ally_data["updated_at"] = now
            allies[ally] = ally_data
            if not i%50:
                with open("data/allies.json", "w+") as f:
                    f.write(json.dumps(allies, indent=4, sort_keys=True))
        to_delete = []
        for qualified_name in old_allies.keys():
            if qualified_name not in found_allies:
                to_delete.append(qualified_name)
                y += 1
        for dele in to_delete:
            del allies[dele]
        with open("data/allies.json", "w+") as f:
            f.write(json.dumps(allies, indent=4, sort_keys=True))
        await ctx.send(f"Done - Checked: **{i}** | Updated: **{x}** | Removed: **{y}** | Added: **{z}**")

def setup(bot):
    bot.add_cog(Trovesaurus(bot))
