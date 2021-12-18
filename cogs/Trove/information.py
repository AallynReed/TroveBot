# Priority: 1
import functools
import typing
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from tabulate import tabulate


class Information(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=["chatcmd"])
    async def chats(self, ctx):
        chats = {
            "levi": "Join **Leviathan** farms in Geode Topside.",
            "delve": "Join **Delve** farms in Delves.",
            "trade": "Trade your goodies or currency with other players.",
            "fivefarm": "Join **5 Star Dungeon** farms in Geode Topside.",
            "dragon": "Join **Dragon Fragment** farms.",
            "nitro": "Join **Nitro Glitterine** farms in Geode Topside.",
            "ganda": "Join **Nitro Glitterine** farms in Geode Topside.",
            "egg": "Join **Egg** farms. __(During **Bunfest** event only)__"
        }
        e = discord.Embed()
        e.color = discord.Color.random()
        e.description = ""
        for chat, description in sorted(chats.items()):
            e.description += f"`/join {chat}` -> {description}\n"
        e.set_author(name="Joinable Chats in game", icon_url=self.bot.user.avatar)
        await ctx.send(embed=e)

    @commands.command(aliases=["effort"])
    async def effort_leaderboard(self, ctx):
        e = discord.Embed()
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

    @commands.command(aliases=["lightsteps", "lsteps"])
    async def light_steps(self, ctx):
        e = discord.Embed(title="Light Steps", color=discord.Color.random())
        e.set_image(url="https://i.imgur.com/FTN3hcc.png")
        e.set_footer(text=f"Data provided by {self.bot.get_user(523714260090748938)}")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Show current Meta for different game situations.")
    @commands.bot_has_permissions(embed_links=1)
    async def meta(self, ctx):
        e = discord.Embed(color=0x0000ff, timestamp=datetime.utcfromtimestamp(self.bot.Trove.last_updated))
        e.set_author(name="Meta", icon_url=self.bot.user.avatar.url)
        e.description = "Here are the game's Meta classes for each activity."
        e.add_field(name="Farming (Adventure/Topside)", value="Physical: <:c_NN:876846928808259654> **Neon Ninja**\nMagic: <:c_DT:876846922135126036> **Dino Tamer** or <:c_BD:876846944604024842> **Bard**", inline=False)
        e.add_field(name="DPS (Single Target)", value="Magic: <:c_CM:876846891747410001> **Chloromancer**", inline=False)
        e.add_field(name="Delve Path (Delve Dusk - | Below Depth ~129)", value="Magic: <:c_TR:876846901801123850> **Tomb Raiser**", inline=False)
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
                                                          #       PC                   XBOX
                        if activity.application_id not in [363409000399634432, 438122941302046720]:
                            fake.append([member.id, member.guild.name, member.guild.id])
                            continue
                        if activity.application_id == 363409000399634432:
                            platform = "<:windows:839445248517079050>"
                        if activity.application_id == 438122941302046720:
                            platform = "<:xbox:839439645359603713>"
                        # if activity.application_id == 1234:
                        #     platform = "<:playstation:921080331782737990>"
                        is_in = bool(ctx.guild.get_member(member.id))
                        playingtrove.append([str(member), member.id, activity.created_at.timestamp(), platform, is_in])
                        break
            return checked, playingtrove, fake
        task = functools.partial(get_members)
        checked, playingtrove, fake = await self.bot.loop.run_in_executor(None, task)
        playingtrove.sort(key=lambda x: x[2])
        pages = self.bot.utils.chunks(playingtrove, 10)
        page = 0
        e = discord.Embed(color=discord.Color.random())
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

    @commands.command(slash_command=True, help="Shows current weekly [May be slow to update]", aliases=["week"])
    async def weekly(self, ctx):
        if not self.bot.Trove.sheets["summer"]:
            await ctx.send("Try again in a few seconds, fetching info...")
            return
        sheet = self.bot.Trove.sheets["summer"]["Chaos Chests + Weekly"]
        now = datetime.utcnow() - timedelta(hours=11)
        if sheet["A10"].value.timestamp() + 86400 * 6 < now.timestamp():
            await ctx.send("Info fetched is outdated, try again later.")
            return
        num = 10
        if sheet["A10"].value.timestamp() > now.timestamp():
            num = 11
        e = discord.Embed(description="\nWeekly's info was fetched from **[this spreadsheet](https://trove.summerhaas.com/luxion)** made by **__SummerHaas__**", color=self.bot.comment, timestamp=sheet[f"A{num}"].value)
        e.set_author(name="Chaos Chests & Weekly")
        e.add_field(name="CC Loot", value=sheet[f"B{num}"].value if sheet[f"B{num}"].value else "Unknown")
        e.add_field(name="Weekly bonus", value=sheet[f"C{num}"].value)
        e.add_field(name="\u200b", value="\u200b")
        e.add_field(name="Weekly Deal", value=sheet[f"D{num}"].value)
        if sheet[f"E{num}"].value:
            e.add_field(name="Event", value=sheet[f"E{num}"].value)
        else:
            e.add_field(name="\u200b", value="\u200b")
        e.add_field(name="\u200b", value="\u200b")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Shows a list of prime numbers up to a 1000.", aliases=["primes"])
    async def prime_numbers(self, ctx):
        prime_numbers = list(self.bot.utils.primes(1, 1000))
        chunked_primes = self.bot.utils.chunks(prime_numbers, 8)
        table = tabulate(chunked_primes, tablefmt='psql', numalign="left")
        e = discord.Embed(description="```py\n"+table+"\n```", color=0x0000ff)
        e.set_author(name="Prime Numbers (in 1000)")
        await ctx.send(embed=e, ephemeral=True)

def setup(bot):
    bot.add_cog(Information(bot))
