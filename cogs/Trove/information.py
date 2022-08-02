# Priority: 1
import functools
import json
import typing
from datetime import datetime, timedelta

import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from tabulate import tabulate
from utils.buttons import GemTutorial, Paginator
from utils.CustomObjects import CEmbed


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(message_command=False, slash_command=False, help="Get time information about Advent's Calendar 2021 event on forums")
    async def advent_calendar(self, ctx):
        days = {
            1: "http://forums.trovegame.com/showthread.php?150105-Advent-Calendar-2021-Day-1",
            2: "http://forums.trovegame.com/showthread.php?150104-Advent-Calendar-2021-Day-2",
            3: "http://forums.trovegame.com/showthread.php?150103-Advent-Calendar-2021-Day-3",
            4: "http://forums.trovegame.com/showthread.php?150102-Advent-Calendar-2021-Day-4",
            5: "http://forums.trovegame.com/showthread.php?150101-Advent-Calendar-2021-Day-5",
            6: "http://forums.trovegame.com/showthread.php?150100-Advent-Calendar-2021-Day-6",
            7: "http://forums.trovegame.com/showthread.php?150099-Advent-Calendar-2021-Day-7",
            8: "http://forums.trovegame.com/showthread.php?150098-Advent-Calendar-2021-Day-8",
            9: "http://forums.trovegame.com/showthread.php?150097-Advent-Calendar-2021-Day-9",
            10: "http://forums.trovegame.com/showthread.php?150096-Advent-Calendar-2021-Day-10",
            11: "http://forums.trovegame.com/showthread.php?150095-Advent-Calendar-2021-Day-11",
            12: "http://forums.trovegame.com/showthread.php?150094-Advent-Calendar-2021-Day-12",
            13: "http://forums.trovegame.com/showthread.php?150093-Advent-Calendar-2021-Day-13",
            14: "http://forums.trovegame.com/showthread.php?150092-Advent-Calendar-2021-Day-14",
            15: "http://forums.trovegame.com/showthread.php?150091-Advent-Calendar-2021-Day-15",
            16: "http://forums.trovegame.com/showthread.php?150090-Advent-Calendar-2021-Day-16",
            17: "http://forums.trovegame.com/showthread.php?150089-Advent-Calendar-2021-Day-17",
            18: "http://forums.trovegame.com/showthread.php?150088-Advent-Calendar-2021-Day-18",
            19: "http://forums.trovegame.com/showthread.php?150087-Advent-Calendar-2021-Day-19",
            20: "http://forums.trovegame.com/showthread.php?150086-Advent-Calendar-2021-Day-20",
            21: "http://forums.trovegame.com/showthread.php?150085-Advent-Calendar-2021-Day-21",
            22: "http://forums.trovegame.com/showthread.php?150084-Advent-Calendar-2021-Day-22",
            23: "http://forums.trovegame.com/showthread.php?150083-Advent-Calendar-2021-Day-23",
            24: "http://forums.trovegame.com/showthread.php?150082-Advent-Calendar-2021-Day-24",
        }
        now = datetime.utcnow().replace(microsecond=0) + timedelta(hours=1) # Forum Event time
        tomorrow_add = timedelta(days=1) - timedelta(hours=now.hour+1, minutes=now.minute, seconds=now.second)
        tomorrow = now + tomorrow_add
        timestamp = int(tomorrow.timestamp())
        e = CEmbed()
        e.color = 0xB11E31
        e.set_author(name="Advent Calendar 2021", icon_url=self.bot.user.avatar.url)
        e.description = "[**What is Advent's Calendar?**](http://forums.trovegame.com/showthread.php?150131)"
        e.description += "\n[**Check the calendar**](http://forums.trovegame.com/showthread.php?150130)"
        e.description += f"\n\nNext day <t:{timestamp}:R> | <t:{timestamp}:D>"
        e.set_footer(text="Times represent event time and not real world.")
        if now.day in days:
            today = days.get(now.day)
            e.description += f"\n\nToday's image <t:{int(now.timestamp()-3600)}:f> [**Go To Forums**]({today})"
            response = await (await self.bot.AIOSession.get(today)).text()
            soup = BeautifulSoup(response, "html.parser")
            htmlpost = soup.findAll("div", {"class" : "content"})[0]
            image = htmlpost.find_all('img', {"border": "0"})[1]
            e.set_image(url=image.get("src"))
        await ctx.send(embed=e, ephemeral=True)

    @commands.command(slash_command=True, aliases=["chatcmd"], help="Show popular in game chats for different activities.")
    async def chats(self, ctx):
        chats = {
            "levi": "Join **Leviathan** farms in Geode Topside.",
            "delve|delves": "Join **Delve** farms in Delves.",
            "trade": "Trade your goodies or currency with other players.",
            "fivefarm": "Join **5 Star Dungeon** farms in Geode Topside.",
            "dragon": "Join **Dragon Fragment** farms.",
            "nitro|ganda": "Join **Nitro Glitterine** farms in Geode Topside.",
            "egg": "Join **Egg** farms. __(During **Bunfest** event only)__"
        }
        e = CEmbed()
        e.color = discord.Color.random()
        e.description = ""
        for chat, description in sorted(chats.items()):
            e.description += f"`/join {chat}` -> {description}\n"
        e.set_author(name="Joinable Chats in game", icon_url=self.bot.user.avatar)
        await ctx.send(embed=e)

    @commands.command(slash_command=True, aliases=["effort"], help="Show sources of points towards effort leaderboards.")
    async def effort_leaderboard(self, ctx):
        e = CEmbed()
        e.set_author(name="Effort Contest Objectives", icon_url=ctx.guild.me.avatar)
        e.description = """```py\n#Dungeon Objectives:
    1 star dungeon objective - 1 point
    3 star dungeon objective - 3 points
    5 star dungeon objective - 5 points if completed on time, 1 point if completed after time ran out
    Leviathan lair - 10 points
#Hourly Challenge Objectives:
    Rampage - each tier 8 points
    Coin Collection - each tier 8 points
    Biome Challenge - each tier 8 points
#Delves:
    Public Delve floor completed - 15 points
    Private Delve floor completed - 20 points
    Challenge Delve floor completed - 25 points
#Adventures:
    Trovian Adventures - 3 points
    Luminopolis Adventures - 3 points
    Club Adventures - 3 points
    Geodian Adventures - 3 points
#Bomber Royale:
    Bomber Royale kills - 1 point every few enemies defeated
    Bomber Royale Win - 5 points
#Geode Caves:
    Reliquary Filled - 5 points
    Companion Egg found - 5 points
#Gardening:
    Watering Plants - 1 point every few dozen watered
    Harvesting Plants - 1 point every few dozen harvested
#General Activities:
    Defeating Monsters - 1 point every few dozen enemies defeated
    Defeating World Bosses - 1 point every few enemies defeated
    Destroying Blocks - 1 point every few hundred blocks destroyed```"""
        e.set_footer(text=f"Data provided by {self.bot.get_user(225585842654019584)}")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, aliases=["lightsteps", "lsteps"], help="Show light steps in different game stages.")
    async def light_steps(self, ctx):
        e = CEmbed(title="Light Steps", color=discord.Color.random())
        e.set_image(url="https://i.imgur.com/FTN3hcc.png")
        e.set_footer(text=f"Data provided by {self.bot.get_user(523714260090748938)}")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Show current Meta for different game situations.")
    @commands.bot_has_permissions(embed_links=1)
    async def meta(self, ctx):
        e = CEmbed(color=0x0000ff, timestamp=datetime.utcfromtimestamp(self.bot.Trove.last_updated))
        e.set_author(name="Meta", icon_url=self.bot.user.avatar.url)
        e.description = "Here are the game's Meta classes for each activity."
        e.add_field(name="Farming (Adventure/Topside)", value="Physical: <:c_SH:876846872503943170> **Shadow Hunter** <:c_RV:876846888819777547> **Revenant**\nMagic: <:c_DT:876846922135126036> **Dino Tamer** or <:c_BD:876846944604024842> **Bard**", inline=False)
        e.add_field(name="5 Star Dungeons (Sundered Uplands)", value="Physical: <:c_SL:985310345621020703> **Solarion**", inline=False)
        e.add_field(name="DPS (Single Target)", value="Physical: <:c_SL:985310345621020703> **Solarion**\nMagic: <:c_CM:876846891747410001> **Chloromancer**", inline=False)
        e.add_field(name="Delve Path (Delve Dusk - | Below Depth ~129)", value="Magic: <:c_TR:876846901801123850> **Tomb Raiser** or <:c_DL:876846884143116368> **Dracolyte**", inline=False)
        e.add_field(name="Delve Path (Delve Dusk + | Above Depth ~129)", value="Magic: <:c_IS:876846881311965224> **Ice Sage**", inline=False)
        e.set_footer(text="Last updated")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Shows people currently playing Trove in discord. [Depends on activity]", aliases=["pltrove"])
    @commands.cooldown(1, 180, commands.BucketType.guild)
    async def playing_trove(self, ctx, show_all: typing.Literal["True"]=commands.Option(name="show_all", default=None, description="Whether to show from all servers or not.")):
        if not show_all:
            ctx.command.reset_cooldown(ctx)
        msg = await ctx.send("<a:loading:844624767239192576> Looking for players...")
        def get_members():
            checked = []
            playingtrove = []
            fake = []
            for member in self.bot.get_all_members() if show_all else ctx.guild.members:
                if member.id in checked:
                    continue
                checked.append(member.id)
                for activity in member.activities:
                    if activity.name == "Trove":
                        if "application_id" not in dir(activity):
                            continue
                                                          #       PC                   XBOX            PlayStation
                        if activity.application_id not in [363409000399634432, 438122941302046720, 1234]:
                            fake.append([member.id, member.guild.name, member.guild.id])
                            continue
                        if activity.application_id == 363409000399634432:
                            platform = "<:windows:839445248517079050>"
                        if activity.application_id == 438122941302046720:
                            platform = "<:xbox:839439645359603713>"
                        if activity.application_id == 1234:
                            platform = "<:playstation:921080331782737990>"
                        is_in = bool(ctx.guild.get_member(member.id))
                        playingtrove.append([str(member), member.id, activity.created_at.timestamp(), platform, is_in])
                        break
            return checked, playingtrove, fake
        task = functools.partial(get_members)
        checked, playingtrove, fake = await self.bot.loop.run_in_executor(None, task)
        playingtrove.sort(key=lambda x: x[2])
        pages = self.bot.utils.chunks(playingtrove, 10)
        page = 0
        e = CEmbed(color=discord.Color.random())
        e.set_author(name=f"Playing Trove... ({len(playingtrove)})", icon_url="https://i.imgur.com/sCIbgLX.png")
        if len(pages) == 0:
            e.description = "There's no one in this server playing trove right now!"
            return await msg.edit(content=None, embed=e)
        e.set_footer(text="This depends on Discord Game Activity.\n⭐-> Is in current server.")
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["◀️", "▶️"]
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")
        while True:
            stime = datetime.utcnow().timestamp()
            e.description = ""
            for member, _, time, platform, is_in in pages[page]:
                e.description += f"{platform}`{member}` playing for {self.bot.utils.time_str(stime - time)[1]}{' ⭐' if is_in else ''}\n"
            try:
                await msg.edit(content=None, embed=e)
                reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except:
                try:
                    await msg.clear_reactions()
                except:
                    try:
                        await msg.remove_reaction("◀️")
                        await msg.remove_reaction("▶️")
                    except:
                        break
                    break
                break
            if str(reaction.emoji) == "◀️":
                page -= 1
                if page < 0:
                    page = len(pages) - 1
            if str(reaction.emoji) == "▶️":
                page += 1
                if page > len(pages) - 1:
                    page = 0
            try:
                await reaction.remove(ctx.author)
            except:
                pass

    # @commands.command(slash_command=True, help="Shows current weekly [May be slow to update]", aliases=["week"])
    # async def weekly(self, ctx):
    #     if not self.bot.Trove.sheets["summer"]:
    #         await ctx.send("Try again in a few seconds, fetching info...")
    #         return
    #     sheet = self.bot.Trove.sheets["summer"]["Chaos Chests + Weekly"]
    #     now = self.bot.time.now
    #     if sheet["A10"].value.timestamp() + 86400 * 6 < now.timestamp():
    #         await ctx.send("Info fetched is outdated, try again later.")
    #         return
    #     weekly = self.bot.Trove.weekly_data[str(self.bot.Trove.time.weekly_time)]
    #     num = 10
    #     if sheet["A10"].value.timestamp() > now.timestamp():
    #         num = 11
    #     e = CEmbed(description="\nWeekly's info was fetched from **[this spreadsheet](https://trove.summerhaas.com/luxion)** made by **__SummerHaas__**", color=self.bot.comment, timestamp=sheet[f"A{num}"].value)
    #     e.set_author(name="Chaos Chests & Weekly")
    #     e.add_field(name="CC Loot", value=sheet[f"B{num}"].value if sheet[f"B{num}"].value else "Unknown")
    #     e.add_field(name="Weekly bonus", value=weekly["name"])
    #     e.add_field(name="\u200b", value="\u200b")
    #     e.add_field(name="Weekly Deal", value=sheet[f"D{num}"].value)
    #     if sheet[f"E{num}"].value:
    #         e.add_field(name="Event", value=sheet[f"E{num}"].value)
    #     else:
    #         e.add_field(name="\u200b", value="\u200b")
    #     e.add_field(name="\u200b", value="\u200b")
    #     await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Show daily and weekly bonuses.")
    async def bonuses(self, ctx):
        e = CEmbed(color=discord.Color.random())
        e.set_author(name="Bonuses", icon_url=self.bot.user.avatar)
        now = self.bot.time.now
        now -= timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        daily_bonuses = ""
        for i in range(7):
            if i:
                now += timedelta(seconds=86400)
            daily_time = now + timedelta(hours=11)
            daily = self.bot.Trove.daily_data[str(daily_time.weekday())]
            if not i:
                daily_bonuses += f"\\{daily['emoji']}{daily['name']} - Now"
            else:
                daily_bonuses += f"\n\\{daily['emoji']}{daily['name']} - <t:{int(daily_time.timestamp())}:R>"
        now = self.bot.time.now
        now -= timedelta(days=now.weekday(), hours=now.hour, minutes=now.minute, seconds=now.second)
        weekly_bonuses = ""
        for i in range(4):
            if i:
                now += timedelta(seconds=604800)
            weekly_time = now + timedelta(hours=11)
            weekly = self.bot.Trove.weekly_data[str(self.bot.time.get_weekly_time(weekly_time))]
            if not i:
                weekly_bonuses += f"\\{weekly['emoji']}{weekly['name']} - Now"
            else:
                weekly_bonuses += f"\n\\{weekly['emoji']}{weekly['name']} - <t:{int(weekly_time.timestamp())}:R>"
        e.add_field(name="Daily Bonuses", value=daily_bonuses)
        e.add_field(name="Weekly Bonuses", value=weekly_bonuses)
        await ctx.reply(embed=e)

    @commands.command(slash_command=True, help="Shows a list of prime numbers up to a 1000", aliases=["primes"])
    async def prime_numbers(self, ctx):
        prime_numbers = list(self.bot.utils.primes(1, 1000))
        chunked_primes = self.bot.utils.chunks(prime_numbers, 8)
        table = tabulate(chunked_primes, tablefmt='psql', numalign="left")
        e = CEmbed(description="```py\n"+table+"\n```", color=0x0000ff)
        e.set_author(name="Prime Numbers (in 1000)")
        await ctx.send(embed=e, ephemeral=True)

    @commands.command(slash_command=True, help="Shows a list of light sources to achieve max light")
    async def max_light(self, ctx):
        e = CEmbed(color=discord.Color.random(), timestamp=datetime.utcfromtimestamp(1655282095))
        links = {
            "gem_forge": "https://trovesaurus.com/placeable/crafting/forge_gem",
            "pearl": "https://trovesaurus.com/item/crafting/pearl",
            "light": "https://trovesaurus.com/collection/effects/Light",
            "geode": "https://trovesaurus.com/geode",
            "chaos_dragon": "https://trovesaurus.com/collections/mount/dragon_chaos",
            "corruxion": "https://trovesaurus.com/corruxion",
            "chaos_fragments": "https://trovesaurus.com/item/dragon/egg/chaos_notrade_fragment",
            "ring_box": "https://trovesaurus.com/search/Golden%20Sign/items",
            "ifera": "https://trovesaurus.com/npc/rampage/jellyfish_shadow",
            "upgraded_torch": r"https://trovesaurus.com/search/Torch%20of%20the/styles",
            "sunseekers": "https://trovesaurus.com/placeable/crafting/geode/workbench_geode_adventure",
            "freerange": "https://trovesaurus.com/item/food/delve/tier_03",
            "berserk": "https://trovesaurus.com/item/gem/large/opal_battle_frenzy_t109",
            "delves": "https://trovesaurus.com/delves",
            "topside": "https://trovesaurus.com/biome=37/geode-topside",
            "solarion": "https://trovesaurus.com/class/solarion",
            "irradiant_dragon": "https://trovesaurus.com/collections/mount/dragon_sunseeker",
        }
        data = [
            ["<:hat:834512699585069086>", "Hat", 845, f"Crystal 4 | 5 <:Star:841018551087530024> fully <:pearl:923919738768330752> [pearled]({links['pearl']})"],
            ["<:sword:834512699593064518>", "Weapon", 1690, f"Crystal 4 | 5 <:Star:841018551087530024> fully <:pearl:923919738768330752> [pearled]({links['pearl']})"],
            ["<:face:834512699441938442>", "Face", 845, f"Crystal 4 | 5 <:Star:841018551087530024> fully [<:pearl:923919738768330752> pearled]({links['pearl']})"],
            ["<:cosmic_emp:923920434045521920>", "Cosmic Empowered Gem", 1450, f"3 <:boost:873291316447047761> in Light stat, check <:gem_forge:923919985875759114>[Gem Forge]({links['gem_forge']})"],
            ["<:cosmic_lesser:923920433894531102>", "Cosmic Lesser Gem 1", 1350, f"3 <:boost:873291316447047761> in Light stat, check <:gem_forge:923919985875759114>[Gem Forge]({links['gem_forge']})"],
            ["<:cosmic_lesser:923920433894531102>", "Cosmic Lesser Gem 2", 1350, f"3 <:boost:873291316447047761> in Light stat, check <:gem_forge:923919985875759114>[Gem Forge]({links['gem_forge']})"],
            ["<:qubesly:834512699361853530>", "Ally", 400, f"[Allies List]({links['light']})"],
            ["<:geodemr:844624767210487808>", "Geode Mastery", 1000, f"[Geode mastery]({links['geode']}) gives 10 light per level [Max Lvl: 100]"],
            ["<:dragon_coin:858061506074378276>", f"Chaos Dragon", 50, f"[Chaos Dragon]({links['chaos_dragon']}) through the purchase of [<:chaos_frag:923960128498204682> 50 Fragments]({links['chaos_fragments']}) in [<:charl:923960128288489482> Corruxion]({links['corruxion']})"],
            ["<:c_SL:985310345621020703>", f"Subclass", 140, f"Using [Solarion]({links['solarion']})'s subclass you can obtain light (efficacy affected by class level)"],
            ["<:zeuztian:988059820844253224>", f"Irradiant Dragon", 25, f"[Zeuztian, the Eternal Irradiance]({links['irradiant_dragon']})"],
            ["<:ring:923960128401719337>", "Ring", 325, f"Crystal 4, obtained through [Golden Signatory Box]({links['ring_box']})"],
            ["<:torch:923967418756370533>", "Banner", 900, f"[Upgraded Legendary Torch]({links['upgraded_torch']}) from leviathans in [Geode Topside U10]({links['topside']}) or [Delves]({links['delves']}) ([Ifera Boss]({links['ifera']})) check [Sunseeker's Crystalforge]({links['sunseekers']}))"],
            ["<:food:834512699424505886>", "Food", 300, f"[Freerange Electrolytic Crystals]({links['freerange']})"],
            ["<:cosmic_emp:923920434045521920>", "Gem Ability", -750, f"[Berserk Battler]({links['berserk']}) when attacking enemies light temporarily increases."]
        ]
        data.sort(key=lambda x: -x[2])
        e.description = "Also available at [**Trovesaurus**](https://trovesaurus.com/light)\n\n" + "\n\n".join([f"{i[0]} `{abs(i[2])}` **{i[1]}** → {i[3]}" for i in data])
        e.set_author(name=f"Max Light | {sum([i[2] for i in data if i[2] > 0])} (+{sum([abs(i[2]) for i in data if i[2] < 0])})", icon_url="https://i.imgur.com/zxVjBzO.png")
        e.set_footer(text="Last updated")
        await ctx.reply(embed=e)

    @commands.command(slash_command=True, aliases=["gt"], help="Learn how gems work, and learn how to best manage them.")
    async def gem_tutorial(self, ctx):
        tabs = {
            "tabs": {
                "Basic": "Learn all the basics of gems as a begginner.",
                "Medium": "Learn what to do after getting your gem set sorted out.",
                "Advanced": "Tryhard in a damn children's game nerd."
            }
        }
        e = CEmbed(color=discord.Color(3092790), timestamp=datetime.utcfromtimestamp(1640702807))
        e.set_author(name="Gem Tutorial", icon_url=self.bot.user.avatar)
        e.description = "Welcome to the gem tutorial.\n\n"
        e.description += "Pick one of the difficulties below:\n\n"
        e.description += "\n".join([f"> **{tab}:** {text}" for tab, text in tabs["tabs"].items()])
        e.set_footer(text="Last updated")
        tabs["embed"] = e
        raw_topics = json.loads(open("locales/en/gems.json").read())
        class Topic():
            def __init__(self, **args):
                for name, embed in args.items():
                    setattr(self, name, embed)
        topics = [Topic(tab=k.split(" | ")[1], name=k.split(" | ")[0], embed=e) for k, e in raw_topics.items()]
        view = GemTutorial(ctx, tabs, topics)
        view.message = await ctx.reply(embed=e, view=view)

    @commands.command(slash_command=True, message_command=False, help="Look for keywords in previous patch notes")
    async def search_post(self, ctx,
        _filter: typing.Literal["PTS Patches", "Live Patches", "Console Patches"]=commands.Option(name="filter", default=None, description="Filter posts to find keywords in."),
        keywords=commands.Option(description="Filter posts by keywords, keywords separated with ;")
    ):
        keywords = keywords.split(";")
        kws = "` `".join(keywords)
        found_posts = []
        async for post in self.bot.db.db_forums.find({}):
            if _filter and _filter != post["type"]:
                continue
            if not (content := post.get("content")):
                continue
            posti = [kw for kw in keywords if kw.lower() not in content.lower()]
            if not posti:
                found_posts.append(post)
        if not found_posts:
            return await ctx.send(f"No posts matching keywords `{kws}` were found.", ephemeral=True)
        found_posts.sort(key=lambda x: -x["created_at"])
        raw_pages = self.bot.utils.chunks(found_posts, 4)
        pages = []
        i = 0
        for raw_page in raw_pages:
            i += 1
            e = CEmbed(description=f"Posts for `{kws}`")
            e.set_author(name=f"Forum Posts Search [{i}/{len(raw_pages)}]")
            for post in raw_page:
                e.add_field(name=f"[{post['_id']}] {post['title']}", value=f"[Check out here](https://trove.slynx.xyz/posts/{post['_id']}/)\nBy {post['author']}\nPosted on <t:{int(post['created_at'])}:D>\n[Forums Link]({post['link']})\n\u200b", inline=False)
            page = {
                "content": None,
                "page": i,
                "embed": e
            }
            pages.append(page)
        view = Paginator(ctx, pages, start_end=True)
        view.message = await ctx.send(embed=pages[0]["embed"], view=view)
        
    @commands.command(slash_command=True, name="gamigo_resources", aliases=["trove_resources"], help="List of gamigo resources, for new or contacting")
    async def _list_gamigo_resources(self, ctx):
        resources = {
            "<:trove:943719336395309097> Trove Resources": {
                "Forums": "http://forums.trovegame.com/forum.php",
                "Support": "https://support.gamigo.com/hc/en-us/categories/200198383-Trove",
                "Report Player": "https://gameservices.gamigo.com/PlayerReports/TROVE",
                "Discord": "https://discord.gg/VqFgpu4Fyz",
                "Youtube": "https://www.youtube.com/trove",
                "Twitter": "http://twitter.com/trovegame",
                "Instagram": "http://instagram.com/trovegame",
                "Facebook/Meta": "https://www.facebook.com/trovegame",
            },
            "<:gamigo:943719015031926825> Gamigo Resources": {
                "Support": "https://support.gamigo.com/hc/en-us/",
                "Youtube": "https://www.youtube.com/channel/UC79b7oBigBct0kgmc4xQ61g",
                "Twitch": "https://www.twitch.tv/gamigogames",
                "Twitter": "https://twitter.com/gamigo",
                "Instagram": "https://www.instagram.com/gamigogroup",
                "Facebook/Meta": "https://www.facebook.com/gamigo.group/"
            }
        }
        e = CEmbed()
        e.set_author(name="Gamigo Resources", icon_url="")
        e.description = "This is a list of Gamigo/Trove Resources for the player including social media.\n\n"
        for resource, tree in resources.items():
            text = "\n".join([f"[**{name}**]({link})" for name, link in tree.items()])
            e.add_field(name=resource, value=text)
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(Information(bot))
