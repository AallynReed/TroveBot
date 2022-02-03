# Priority: 1
import asyncio
import json
import math
import re
import typing
from datetime import datetime
from io import BytesIO

import discord
from aiohttp import ClientSession, MultipartWriter
from discord.ext import commands
from utils.buttons import Confirm, Paginator, ProfileView
from utils.CustomObjects import CEmbed, MetricsConverter
from utils.objects import GameClass, TroveClass, TrovePlayer


class Profiles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession()
        self.quick_request = {}

    def cog_unload(self):
        asyncio.create_task(self.terminate_cog())

    async def terminate_cog(self):
        await self.session.close()
    
    @commands.Cog.listener()
    async def on_profile_create(self, metrics, message):
        if message:
            channel = message.channel
            if not message.guild:
                return await channel.send("You can't submit profiles in DM's.")
            await self.log(message, f"Started submitting a profile.\n[exportMetrics.txt]({str(await self.post_mystb_in(metrics))})")
            await message.delete(silent=True)
        try:
            data = MetricsConverter(self.bot.keys["Bot"]["Profile Encryption"], metrics).get_profile()
            if not data.get("Environment"):
                return await channel.send("Please make sure your game is in english before submitting a profile.", delete_after=10)
            server = 0 if data["Environment"] == "PTS" else 1
            del data["Environment"]
        except Exception as e:
            if message:
                await self.log(message, f"Failed to submit a profile. **{e}**")
            return
        if message:
            if server:
                await self.trovesaurus_submit_profile(metrics)
            quick_request = self.quick_request.get(str(message.author.id))
            if not quick_request or datetime.utcnow().timestamp() - quick_request > 900:
                if quick_request:
                    del self.quick_request[str(message.author.id)]
                text = "You are about to submit a export metrics file to create a profile."
                text += "Are you sure you want to proceed?"
                interaction = Confirm(message, timeout=30)
                interaction.message = await channel.send(text, view=interaction, delete_after=30)
                await interaction.wait()
                try:
                    await interaction.message.delete()
                except:
                    pass
                if interaction.value is None:
                    return await channel.send("Time out! Profile submission was cancelled because you took too much time to answer.", delete_after=10)
                elif not interaction.value:
                    return await channel.send("Profile submission was cancelled.", delete_after=10)
                self.quick_request[str(message.author.id)] = int(datetime.utcnow().timestamp())
        try:
            name, _class = await self.save_profile(message.author.id if message else None, data, server)
        except:
            if message:
                await channel.send(f"You can't submit this profile as it already belongs to someone else or the stats are invalid, if you think this is wrong contact <@565097923025567755> ||Sly#0511||\nMetrics were still submitted to Trovesaurus at "+f'<https://trovesaurus.com/metrics/account/{data["Player Info"]["Name"]}>')
            return
        if message:
            text = f"Profile for **{name}** as **{_class}** was submitted successfully."
            text += f"\nCheck out at <https://trovesaurus.com/metrics/account/{name}>" if server and message.guild.id == 118027756075220992 else ""
            text += " **(Quick request mode on)**" if quick_request else ""
            await channel.send(text)
        await self.log(message, f"**{name}** submitted a profile for {_class}.\n")

    @commands.Cog.listener("on_message")
    async def metrics_detector(self, message):
        if not hasattr(self.bot, "blacklist"):
            return
        if message.author.id in self.bot.blacklist:
            return
        if message.author.bot:
            return
        if not message.attachments:
            if message.channel.id == 915277668096827442:
                await message.delete()
            return
        f = message.attachments[0]
        if f.filename != "exportMetrics.txt":
            return
        content = await f.read()
        self.bot.dispatch("profile_create", content.decode("utf-8"), message)

    async def trovesaurus_submit_profile(self, file):
        data = {
            "SubmitMetrics": "cool", 
            "Token": self.bot.keys["Trovesaurus"]["Token"],
            "File": file
        }
        async with self.session.post("https://trovesaurus.com/metrics", data=data) as request:
            if request.status != 200:
                print("An error occured sending metrics to trovesaurus.")

    async def post_mystb_in(self, content):
        payload = {"meta": [{"index":0, "syntax":"properties"}]}
        multi_part_write = MultipartWriter()
        paste_content = multi_part_write.append(content)
        paste_content.set_content_disposition("form-data", name="data")
        paste_content = multi_part_write.append_json(payload)
        paste_content.set_content_disposition("form-data", name="meta")
        request = await self.bot.AIOSession.post(
            "https://mystb.in/api/pastes",
            data=multi_part_write
        )
        if request.status == 200:
            data = await request.json()
            return "https://mystb.in/" + data["pastes"][0]["id"] + ".text"
        return

    async def log(self, message, text):
        e = CEmbed()
        e.color = discord.Color.random()
        e.timestamp = message.created_at
        e.description = text
        if message.id != 511:
            e.set_author(name=message.author, icon_url=message.author.avatar)
        e.set_thumbnail(url=message.guild.icon)
        e.set_footer(text=f"{message.guild.name} - {message.guild.id}")
        await self.bot.profiles_logger.send(embed=e, username="Profiles")

    async def save_profile(self, user_id, data, server=1):
        odata = await self.bot.db.db_profiles.find_one({"Name": {"$regex": f'(?i){data["Player Info"]["Name"]}'}, "Bot Settings.Server": server})
        if user_id:
            if odata and odata["discord_id"] != user_id:
                raise Exception("Nope")
            if not odata:
                odata = await self.bot.db.db_profiles.find_one({"discord_id": user_id, "Bot Settings.Server": server})
        else:
            if not odata:
                raise Exception("Nope")
            user_id = odata["discord_id"]
        profile, _class = self.get_profile(user_id, data, odata=odata, server=server)
        if not odata:
            await self.bot.db.db_profiles.insert_one(profile)
        else:
            await self.bot.db.db_profiles.update_one({"discord_id": user_id, "Bot Settings.Server": server}, {"$set": profile}, upsert=True)
        return profile["Name"], _class
        
    def get_profile(self, user_id, data, odata=None, server=1):
        profile = {}
        profile["discord_id"] = user_id
        profile["Clubs"] = data["Clubs"]
        profile["Name"] = data["Player Info"]["Name"]
        profile["Classes"] = {}
        _class = GameClass().cconvert(data["Player Info"]["Class"])
        if odata:
            profile["Classes"] = odata["Classes"]
            diff = data["Mastery Info"]["Trove Mastery Rank"] - odata["Trove Mastery"]
            mf_add = (data["Mastery Info"]["Trove Mastery Rank"] - 500) - (odata["Trove Mastery"] - 500)
            if diff:
                if odata["Trove Mastery"] > 500:
                    pr = diff
                elif odata["Trove Mastery"] + diff < 500:
                    pr = diff * 4
                elif odata["Trove Mastery"] < 500 and data["Mastery Info"]["Trove Mastery Rank"] > 500:
                    pr = 500 - odata["Trove Mastery"] * diff * 4 + data["Mastery Info"]["Trove Mastery Rank"] - 500
                for c in profile["Classes"].keys():
                    profile["Classes"][c]["Power Rank"] += pr
                    if mf_add:
                        profile["Classes"][c]["Magic Find"] += pr
        else:
            profile["Bot Settings"] = {}
            profile["Bot Settings"]["Hidden Clubs"] = []
            profile["Bot Settings"]["Primary"] = _class.name
            profile["Bot Settings"]["Server"] = server
        profile["Classes"][data["Player Info"]["Class"]] = data["Combat Stat Info"]
        profile["Classes"][data["Player Info"]["Class"]]["Critical Hit"] = profile["Classes"][data["Player Info"]["Class"]]["Critical Hit"] / 10
        profile["Classes"][data["Player Info"]["Class"]]["Last Update"] = int(datetime.utcnow().timestamp())
        if _class.dmg_type == "MD":
            damage = data["Combat Stat Info"]["Magic Damage"]
            basedmg = data["Combat Stat Info"]["Magic Damage Base"]
            bonus = data["Combat Stat Info"]["Magic Damage Bonus"]
            if bonus > 140:
                raise Exception("Invalid Stats - Damage Bonus MD")
        else:
            damage = data["Combat Stat Info"]["Physical Damage"]
            basedmg = data["Combat Stat Info"]["Physical Damage Base"]
            bonus = data["Combat Stat Info"]["Physical Damage Bonus"]
            if bonus > 145:
                raise Exception("Invalid Stats - Damage Bonus PD")
        if data["Combat Stat Info"]["Light"] > 9574:
            raise Exception("Invalid Stats - Light")
        if _class.short in ["NN", "LL", "DT"]:
            as_cap = 310
        else:
            as_cap = 279
        if data["Combat Stat Info"]["Attack Speed"] > as_cap:
            raise Exception("Invalid Stats - Attack Speed")
        critchance = profile["Classes"][data["Player Info"]["Class"]]["Critical Hit"] if profile["Classes"][data["Player Info"]["Class"]]["Critical Hit"] < 100 else 100
        crit = data["Combat Stat Info"]["Critical Damage"]
        ccoeff = round((100 - critchance) * damage / 100 + critchance * (damage * (1 + crit / 100)) / 100)
        cbonus = 1 + _class.class_bonus / 100
        coeff = round((100 - critchance) * (basedmg * (1 + bonus / 100)) * cbonus / 100 + critchance * ((basedmg * (1 + bonus / 100)) * cbonus * (1 + crit / 100)) / 100)
        if abs(ccoeff - coeff) > 1000:
            raise Exception("Invalid Stats - Coefficient")
        profile["Classes"][data["Player Info"]["Class"]]["Coefficient"] = coeff
        profile["Classes"][data["Player Info"]["Class"]]["Level"] = data["Player Info"]["Class Level"]
        profile["Classes"][data["Player Info"]["Class"]]["Subclass"] = data["Player Info"]["Subclass"]
        profile["Classes"][data["Player Info"]["Class"]]["Prestige Level"] = data["Player Info"]["Paragon Class Level"] + data["Player Info"]["Paragon Millenia rollovers"] * 1000
        profile["Classes"][data["Player Info"]["Class"]]["Prestige Reset"] = data["Player Info"]["Paragon Millenia rollovers"]
        profile["Stats"] = data["Player Metric Info"]
        profile["Geode Mastery"] = data["Mastery Info"]["Geode Mastery Rank"]
        profile["Trove Mastery"] = data["Mastery Info"]["Trove Mastery Rank"]
        profile["Trove Mastery Points"] = data["Mastery Info"]["Total Mastery XP"]
        profile["Total Mastery"] = profile["Geode Mastery"] + profile["Trove Mastery"]
        del data["Mastery Info"]["Geode Mastery Rank"]
        del data["Mastery Info"]["Trove Mastery Rank"]
        del data["Mastery Info"]["Total Mastery XP"]
        profile["Collected Mastery"] = data["Mastery Info"]
        return profile, _class

    @commands.group(
        slash_command=True,
        help="Check out someone's profile or manage your own",
        name="profile",
        invoke_without_command=True,
        aliases=["p", "prof"])
    async def profile(self, ctx, user: typing.Union[GameClass, discord.Member, TrovePlayer, discord.User, str]=None, _class: typing.Optional[GameClass]=None):
        await self._profile(ctx, user, _class)

    @commands.group(
        slash_command=False,
        help="Check out someone's PTS profile or manage your own",
        name="ptsprofile",
        invoke_without_command=True,
        aliases=["pp", "pprof"])
    async def pprofile(
        self,
        ctx,
        user: typing.Union[GameClass, discord.Member, TrovePlayer, discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player name"),
        _class: typing.Optional[GameClass]=commands.Option(name="class", default=None, description="Input a class")):
        await self._profile(ctx, user, _class, 0)

    async def _profile(self, ctx, user, _class, server=1, is_active=False):
        if isinstance(user, TroveClass):
            _class = user
            user = None
        user = user or ctx.author
        if isinstance(user, str):
            data = await self.bot.db.db_profiles.find_one({"Name": {"$regex": f"(?i)^{user}$"}, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        else:
            data = await self.bot.db.db_profiles.find_one({"discord_id": user.id, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        if not data:
            await ctx.send(f"No profile found for **{user}**" + (f"\nUse `{ctx.prefix}profile request` to learn how to submit one." if user == ctx.author else ""))
            # if server:
            #     await ctx.reply(f"PTS Profiles are default, if you just submitted a profile use `{ctx.prefix}pp`")
            return
        _class = _class or GameClass().cconvert(data["Bot Settings"]["Primary"])
        if _class.name not in data["Classes"].keys():
            await ctx.send(f"**{user}** hasn't submitted that class yet.")
            # if server:
            #     await ctx.reply(f"PTS Profiles are default, if you just submitted a profile use `{ctx.prefix}pp`")
            return
        # Avatar Image
        if isinstance(user, str):
            user = self.bot.get_user(data["discord_id"]) or await self.bot.fetch_user(data["discord_id"])
        if isinstance(user, discord.Member):
            avatar = user.display_avatar
        else:
            avatar = user.avatar if user.avatar else user.default_avatar
        stats = data["Classes"][_class.name]
        classes = [c for c in self.bot.Trove.values.classes if c.name in data["Classes"].keys() and c.name != _class.name]
        try:
            subclass = GameClass().cconvert(stats["Subclass"])
        except:
            subclass = None
        db_bot = (await self.bot.db.db_bot.find_one({"_id": "0511"}, {"mastery": 1}))["mastery"]
        max_live_mastery = db_bot["max_live_mastery"]
        percentage = math.floor(data["Trove Mastery Points"] / max_live_mastery * 1000)/10
        percentage = percentage if percentage - int(percentage) else int(percentage)
        try:
            data = {
                "Token": "TkT8qs9lviaI3wyCQdTD",
                "User": str(user),
                "Nick": data["Name"],
                "Class": _class.image,
                "Subclass": subclass.subimage if subclass else None,
                "Avatar": str(avatar.replace(format="png", size=256).url),
                "Power Rank": int(stats["Power Rank"]),
                "Level": stats["Level"],
                "Prestige Level": stats["Prestige Level"],
                "Trove Mastery": data["Trove Mastery"],
                "Trove Percentage": percentage,
                "Geode Mastery": data["Geode Mastery"],
                "Total Mastery": data["Total Mastery"],
                "Physical Damage": stats["Physical Damage"],
                "Magic Damage": stats["Magic Damage"],
                "Maximum Health": stats["Maximum Health"],
                "Maximum Energy": stats["Maximum Energy"],
                "Health Regen": stats["Health Regen"],
                "Energy Regen": stats["Energy Regen"],
                "Movement Speed": stats["Movement Speed"],
                "Attack Speed": stats["Attack Speed"],
                "Jump": stats["Jump"],
                "Critical Hit": stats["Critical Hit"],
                "Critical Damage": stats["Critical Damage"],
                "Magic Find": stats["Magic Find"],
                "Light": stats["Light"],
                "Coefficient": stats["Coefficient"],
                "Clubs": data["Clubs"],
                "Hidden": data["Bot Settings"]["Hidden Clubs"],
                "Server": server
            }
        except:
            return await ctx.send(f"Your profile for **{_class.name}** is outdated", delete_after=10, ephemeral=True)
        try:
            request = await self.session.post("https://trove.slynx.xyz/profiles/image", data=str(json.dumps(data)))
        except:
            return await ctx.send("Can't get profile right now, try again later.")
        img = discord.File(BytesIO(await request.read()), filename="image.png")
        view = ProfileView(ctx, self._profile, user, classes, server)
        if is_active:
            view.message = is_active
            return view, img
        view.message = await ctx.reply(file=img, view=view if classes else None)

    @profile.command(slash_command=True, name="show", help="Show your's or someone's profile.")
    async def _show(self, ctx, 
        user: typing.Union[GameClass, discord.Member, TrovePlayer, discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player name"),
        _class: typing.Optional[GameClass]=commands.Option(name="class", default=None, description="Input a class")):
        await self._profile(ctx, user, _class)

    @pprofile.command(slash_command=True, name="show", help="Show your's or someone's PTS profile.")
    async def __show(self, ctx, 
        user: typing.Union[GameClass, discord.Member, TrovePlayer, discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player name"),
        _class: typing.Optional[GameClass]=commands.Option(name="class", default=None, description="Input a class")):
        await self._profile(ctx, user, _class, 0)

    @profile.command(slash_command=True, help="Learn how to request a profile", name="request")
    async def request(self, ctx):
        await self.__request(ctx)

    @pprofile.command(slash_command=True, help="Learn how to request a PTS profile", name="request")
    async def _request(self, ctx):
        await self.__request(ctx)

    async def __request(self, ctx):
        e = CEmbed()
        e.color = discord.Color.random()
        e.set_author(name="How to submit a profile?")
        e.description = "The method to submit has changed.\n\nNow you go in-game and use `/exportmetrics` then grab file called `exportMetrics.txt` and just send it on discord."
        e.description += "\n**No command required** Bot will detect it automatically."
        e.description += "\n\n**Directories:**```"
        e.description += "Glyph: \n  C:\Program Files (x86)\Glyph\Games\Trove\Live\n"
        e.description += "Steam: \n  C:\Program Files (x86)\Steam\steamapps\common\Trove\Games\Trove\Live\```"
        await ctx.send(embed=e)

    @profile.command(name="primary", slash_command=True, help="Select which class is shown by default in your profile")
    async def primary(self, ctx, _class: GameClass):
        await self.__primary(ctx, _class)

    @pprofile.command(name="primary", slash_command=True, help="Select which class is shown by default in your PTS profile")
    async def _primary(self, ctx, _class: GameClass=commands.Option(name="class", description="Input a class")):
        await self.__primary(ctx, _class, 0)

    async def __primary(self, ctx, _class, server=1):
        data = await self.bot.db.db_profiles.find_one({"discord_id": ctx.author.id, "Bot Settings.Server": server}, {"Bot Settings": 1, "Classes": 1})
        if not data:
            return await ctx.send(f"No profile found for **{ctx.author}**\nUse `{ctx.prefix}profile request` to learn how to submit one.")
        if data["Bot Settings"]["Primary"] == _class.name:
            return await ctx.reply(f"**{_class.name}** is already your primary class.")
        if _class.name not in data["Classes"]:
            return await ctx.reply(f"You must submit that class first before setting it as primary.")
        await self.bot.db.db_profiles.update_one({"discord_id": ctx.author.id, "Bot Settings.Server": server}, {"$set": {"Bot Settings.Primary": _class.name}})

    @profile.command(name="list", slash_command=True, help="List all the classes you've submitted to your profile")
    async def _list(self, ctx, user: typing.Union[discord.User, str]=None):
        await self.__list_(ctx, user)

    @pprofile.command(name="list", slash_command=True, help="List all the classes you've submitted to your PTS profile")
    async def __list(self, ctx, user: typing.Union[discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or a player")):
        await self.__list_(ctx, user, 0)

    async def __list_(self, ctx, user, server=1):
        user = user or ctx.author
        if isinstance(user, str):
            data = await self.bot.db.db_profiles.find_one({"Name": {"$regex": f"(?i)^{user}$"}, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        else:
            data = await self.bot.db.db_profiles.find_one({"discord_id": user.id, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        if not data:
            return await ctx.send(f"No profile found for **{user}**\nUse `{ctx.prefix}profile request` to learn how to submit one.")
        if isinstance(user, str):
            user = self.bot.get_user(data["discord_id"]) or await self.bot.fetch_user(data["discord_id"])
        e = CEmbed()
        e.color = discord.Color.random()
        e.set_author(name="Classes submitted to profile.", icon_url=user.avatar)
        primary = GameClass().cconvert(data["Bot Settings"]["Primary"])
        e.description = "\n".join([f"<t:{v['Last Update']}:R> {k}" for k, v in sorted(data["Classes"].items(), key=lambda x: -x[1]["Last Update"])])
        e.set_thumbnail(url=primary.image)
        await ctx.reply(embed=e)

    @profile.command(
        name="hide_club",
        slash_command=True,
        help="Hide/Unhide a club from your profile", 
        aliases=["hideclub", "show_club", "showclub"])
    async def hide_club(self, ctx, *, club):
        await self.__hide_club(ctx, club)

    @pprofile.command(
        name="hide_club",
        slash_command=True,
        help="Hide/Unhide a club from your PTS profile", 
        aliases=["hideclub", "show_club", "showclub"])
    async def _hide_club(self, ctx, *, club=commands.Option(name="club", description="Input a club name")):
        await self.__hide_club(ctx, club, 0)

    async def __hide_club(self, ctx, club, server=1):
        data = await self.bot.db.db_profiles.find_one({"discord_id": ctx.author.id, "Bot Settings.Server": server}, {"Bot Settings": 1, "Clubs": 1})
        if not data:
            return await ctx.send(f"No profile found for **{ctx.author}**\nUse `{ctx.prefix}profile request` to learn how to submit one.")
        for cl in data["Clubs"]:
            if club.lower() in cl.lower():
                hidden = data["Bot Settings"]["Hidden Clubs"]
                if cl in hidden:
                    hidden.remove(cl)
                    await ctx.send("Club is now visible.")
                else:
                    hidden.append(cl)
                    await ctx.send("Club is now hidden.")
                return await self.bot.db.db_profiles.update_one({"discord_id": ctx.author.id, "Bot Settings.Server": server}, {"$set": {"Bot Settings.Hidden Clubs": hidden}})
        await ctx.send("That club is not in your clubs.")

    @profile.command(
        name="delete",
        slash_command=True,
        help="Delete your profile", 
        aliases=["del"])
    async def delete(self, ctx, user: typing.Union[discord.User, str]=None):
        await self.__delete(ctx, user)

    @pprofile.command(
        name="delete",
        slash_command=True,
        help="Delete your PTS profile", 
        aliases=["del"])
    async def _delete(self, ctx, user: typing.Union[discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player")):
        await self.__delete(ctx, user, 0)

    async def __delete(self, ctx, user, server=1):
        user = user or ctx.author
        if isinstance(user, str):
            data = await self.bot.db.db_profiles.find_one({"Name": {"$regex": f"(?i)^{user}$"}, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        else:
            data = await self.bot.db.db_profiles.find_one({"discord_id": user.id, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        if not data:
            return await ctx.send(f"No profile found for **{user}**\nUse `{ctx.prefix}profile request` to learn how to submit one.")
        if isinstance(user, str):
            user = self.bot.get_user(data["discord_id"]) or await self.bot.fetch_user(data["discord_id"])
        if ctx.author.id not in [565097923025567755] and user != ctx.author:
            return await ctx.send("You don't have the permission to delete other's profiles.")
        msg = await ctx.send(f"You are about to delete a profile for **{user}**. Are you sure you want to proceed?", delete_after=30)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        def check(reaction, user):
            return reaction.message.id == msg.id and str(reaction) in ["✅","❌"] and user == ctx.author
        try:
            reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=30)
            await msg.delete()
            if str(reaction) == "❌":
                return await ctx.send("Profile deletion was cancelled.", delete_after=10)
            await self.bot.db.db_profiles.delete_one({"discord_id": user.id, "Bot Settings.Server": server})
            await ctx.send(f"**{user}**'s profile deleted.")
        except:
            try:
                await msg.clear_reactions()
            except:
                pass
            return await ctx.send("Time out! Profile deletion was cancelled because you took to much time to answer.", delete_after=10)

    @profile.command(name="total", slash_command=True, help="Check amount of PTS profiles submitted")
    async def total(self, ctx):
        i = len(await self.bot.db.db_profiles.find({"Bot Settings.Server": 1}, {"discord_id": 1}).to_list(length=999999))
        await ctx.send(f"There's a total of **{i}** profiles.")

    @pprofile.command(name="total", slash_command=True, help="Check amount of PTS profiles submitted")
    async def _total(self, ctx):
        i = len(await self.bot.db.db_profiles.find({"Bot Settings.Server": 0}, {"discord_id": 1}).to_list(length=999999))
        await ctx.send(f"There's a total of **{i}** PTS profiles.")

    @profile.command(name="stats", slash_command=True, help="Check out the stats in your's or someone's profile")
    async def stats(self, ctx, user: typing.Union[discord.User, str]=None):
        await self.mastery_stats(ctx, user, "Stats")

    @pprofile.command(name="stats", slash_command=True, help="Check out the stats in your's or someone's PTS profile")
    async def _stats(self, ctx, user: typing.Union[discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player")):
        await self.mastery_stats(ctx, user, "Stats", 0)

    @profile.command(slash_command=True, name="mastery", help="Check out the mastery your's or someone's profile")
    async def mastery(self, ctx, user: typing.Union[discord.User, str]=None):
        await self.mastery_stats(ctx, user, "Collected Mastery")

    @pprofile.command(slash_command=True, name="mastery", help="Check out the mastery your's or someone's PTS profile")
    async def _mastery(self, ctx, user: typing.Union[discord.User, str]=commands.Option(name="user_or_player", default=None, description="Input a user or player")):
        await self.mastery_stats(ctx, user, "Collected Mastery", 0)

    async def mastery_stats(self, ctx, user, t, server=1):
        user = user or ctx.author
        if isinstance(user, str):
            data = await self.bot.db.db_profiles.find_one({"Name": {"$regex": f"(?i)^{user}$"}, "Bot Settings.Server": server}, {"discord_id": 1, t: 1})
        else:
            data = await self.bot.db.db_profiles.find_one({"discord_id": user.id, "Bot Settings.Server": server}, {"discord_id": 1, t: 1})
        if not data:
            return await ctx.send(f"No profile found for **{user}**\nUse `{ctx.prefix}profile request` to learn how to submit one.")
        if isinstance(user, str):
            user = self.bot.get_user(data["discord_id"]) or await self.bot.fetch_user(data["discord_id"])
        stats = self.bot.utils.chunks([f"{stat} = {value}" for stat, value in data[t].items()], 15)
        pages = []
        for i in range(len(stats)):
            stat_page = stats[i]
            e = CEmbed()
            e.color = discord.Color.random()
            e.set_author(name=f"{t} for {user} | Page {i+1} of {len(stats)}", icon_url=user.avatar)
            e.description = "```py\n"
            e.description +=  re.sub(" in", " In", "\n".join(stat_page))
            e.description += "\n```"
            page = {
                "content": None,
                "embed": e
            }
            pages.append(page)
        view = Paginator(ctx, pages, start_end=True)
        view.message = await ctx.reply(embed=pages[0]["embed"], view=view)

    @profile.command(slash_command=True, help="Export Live profile to PTS profile.")
    async def export(self, ctx):
        live_profile = await self.bot.db.db_profiles.find_one({"discord_id": ctx.author.id, "Bot Settings.Server": 1})
        if not live_profile:
            return await ctx.reply("You don't have a live profile to export.")
        text = "You are about to export your Live profile to a PTS Profile are you sure you want to do this? **This won't delete your Live Profile**"
        interaction = Confirm(ctx, timeout=30)
        msg = await ctx.reply(text, view=interaction, delete_after=30)
        await interaction.wait()
        try:
            await msg.delete()
        except:
            pass
        if interaction.value is None:
            return await ctx.reply("Time out! Profile export cancelled.", delete_after=10)
        elif not interaction.value:
            return await ctx.reply("Profile export cancelled.", delete_after=10)
        await self.bot.db.db_profiles.delete_one({"discord_id": ctx.author.id, "Bot Settings.Server": 0})
        del live_profile["_id"]
        live_profile["Bot Settings"]["Server"] = 0
        live_profile["Clubs"] = []
        await self.bot.db.db_profiles.insert_one(live_profile)
        await ctx.reply("Profile exported successfully.")
        
def setup(bot):
    bot.add_cog(Profiles(bot))
