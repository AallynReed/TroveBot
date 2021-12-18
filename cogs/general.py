# Priority: 1
import base64
import json
import typing
from datetime import datetime
from io import BytesIO

import discord
import psutil
import requests
import utils.checks as perms
from discord.ext import commands
from utils.buttons import Paginator


class General(commands.Cog):
    """General module."""

    def __init__(self, bot):
        self.bot = bot
        self.ocr_key = "79f3666bba88957"

    @commands.command(hidden=True)
    async def tooltip(self, ctx):
        response = await self.bot.AIOSession.get("https://trovesaurus.com/collections/pet/delve_hermitcrab_volcano.json")
        data = await response.text()
        data = json.loads(data)
        self.bot.Trove.values.allies[data["name"]] = data
        with open("data/allies.json") as f:
            f.write(json.dumps(self.bot.Trove.values.allies))
        data["token"] = "TkT8qs9lviaI3wyCQdTD"
        try:
            request = await self.bot.AIOSession.post("http://0.0.0.0:10511/trove/tooltip", data=str(json.dumps(data)))
        except:
            return await ctx.send("Can't get tooltip right now, try again later.")
        img = BytesIO(await request.read())
        await ctx.reply(file=discord.File(img, filename="image.png"))

    @commands.command()
    async def slash(self, ctx):
        e = discord.Embed()
        e.description = "You can now have slash commands in your server by clicking in this "
        e.description += "[link](https://discord.com/oauth2/authorize?client_id=425403525661458432&scope=applications.commands)"
        e.description += "\nOnly use this link if the bot is already in your server but doesn't have slash commands, **you do not need to remove bot and readd**"
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Display informtion about the bot", aliases=["bot_info"])
    async def botinfo(self, ctx):
        e = discord.Embed()
        e.color = discord.Color.random()
        e.timestamp = datetime.utcfromtimestamp(self.bot.uptime)
        e.set_footer(text=f"UUID: {self.bot.user.id} | Bot online since")
        e.set_thumbnail(url=ctx.me.avatar)
        e.set_author(name="Bot Info")
        e.add_field(name="Name", value=ctx.me.name)
        e.add_field(name="Discriminator", value=ctx.me.discriminator)
        e.add_field(name="Created", value=discord.utils.format_dt(ctx.me.created_at, "R"))
        e.add_field(name="Owner", value=self.bot.get_user(list(self.bot.owners)[0]))
        e.add_field(name="Servers", value=len(self.bot.guilds))
        e.add_field(name="Users", value=len(self.bot.users))
        e.add_field(name="Ping", value=f"{round(self.bot.latency*1000):,}ms")
        e.add_field(name="Webpage", value="[Here](https://slynx.xyz/trove)")
        e.add_field(name="Invite me", value=f"[Here]({self.bot.invite})")
        await ctx.reply(embed=e)

    @commands.command(aliases=["mutual"])
    async def mutual_servers(self, ctx,* , user: typing.Union[discord.Member, discord.User]=None):
        user = user or ctx.author
        members = sorted([g.get_member(user.id) for g in self.bot.guilds], key=lambda x: x.joined_at.timestamp() if x else 0)
        servers = [f"`[{m.guild.id}]` Joined <t:{int(m.joined_at.timestamp())}:R> | **{m.guild.name}**" for m in members if m]
        e = discord.Embed()
        e.color = discord.Color.random()
        e.description = "\n".join(servers)
        e.set_author(name=f"Mutual servers with {user}", icon_url=user.avatar)
        await ctx.reply(embed=e)

    @commands.command(aliases=["tfi"], hidden=True)
    async def text_from_image(self, ctx):
        if not ctx.message.attachments or ctx.message.attachments[0].content_type not in ["image/png", "image/jpeg"]:
            return await ctx.send("Send a valid image file.")
        if ctx.message.attachments[0].size / 1024 / 1024 > 1:
            return await ctx.send("Max image file size accepted by API is 1 MB.")
        _file = await ctx.message.attachments[0].read()
        payload = {
            "apikey": self.ocr_key,
            "language": "eng",
            f"file.{ctx.message.attachments[0].filename.split('.')[-1]}": _file
        }
        request = await self.bot.AIOSession.post("https://api.ocr.space/parse/image", data=payload)
        text = (await request.json())['ParsedResults'][0]['ParsedText']
        if len(text) > 2000-7:
            return await ctx.send(file=discord.File(BytesIO(text.encode), filename="image.txt"))
        await ctx.reply(f"```\n{text}```")

    @commands.command(aliases=["ga"])
    @commands.bot_has_permissions(embed_links=1)
    async def giveaway(self, ctx):
        return await ctx.reply("There's no giveaway currently going on.", delete_after=8)
        e = discord.Embed()
        e.color = discord.Color.random()
        e.set_author(name="Action Pan Ally giveaway.", icon_url=self.bot.user.avatar)
        e.set_thumbnail(url="https://slynx.xyz/downloads/0511/images/pan.png")
        e.description = "Trove Developer Dan has given Trove bot some unlock codes for the dev ally `Action Pan`"
        e.description += "\n\n**To join the giveaway all you have to do is send the keyword** `DevAlly`\n\n"
        e.description += "Only a few rules to enter the giveaway:\n"
        e.description += " -> You must share a server with the bot.\n"
        e.description += " -> Bot must be able to DM you the code in case you win, otherwise it will be rerolled.\n"
        e.description += " -> You may only enter once the giveaway.\n\n"
        e.description += "This giveaway will end at <t:1628852400:F> <t:1628852400:R>"
        e.description += "\n**3 winners** will be announced in [Trove Bot Server](https://slynx.xyz/trove/support) and automatically sent the codes through DM's"
        entries = (await self.bot.db.db_bot.find_one({"_id": "0511"}, {"giveaway": 1}))["giveaway"]
        e.set_footer(text=f"{len(entries)} people have joined the giveaway.")
        await ctx.reply(embed=e, delete_after=300)

    @commands.command(slash_command=True, help="Disply information about you or a user", aliases=["userinfo", "ui"])
    @commands.bot_has_permissions(embed_links=1)
    @perms.has_permissions("manage_guild")
    async def user_info(self, ctx, *, 
        user: typing.Union[discord.Member, discord.User, int, str]=commands.Option(name="user", default="None", description="Select a user to display their info")):
        badges = {
            "bug_hunter": "<:bug_hunter:864159464630124575>",
            "bug_hunter_level_2": "<:bug_hunter_level_2:864159465112993822>",
            #"discord_certified_moderator": "<:certified_moderator:864159465448407050>",
            "early_supporter": "<:early_supporter:864159465556148224>",
            "early_verified_bot_developer": "<:verified_developer:864159466592796732>",
            "hypesquad": "<:hypesquad:864159465724837919>",
            "hypesquad_balance": "<:hypesquad_balance:864159466072047631>",
            "hypesquad_bravery": "<:hypesquad_bravery:864159466299719760>",
            "hypesquad_brilliance": "<:hypesquad_brilliance:864159466433019964>",
            "partner": "<:partner:864159466513236028>",
            "staff": "<:staff:864166002484969502>",
            "verified_bot_developer": "<:verified_developer:864159466592796732>"
        }
        if isinstance(user, str):
            return await ctx.reply("User not found!")
        if isinstance(user, int):
            try:
                user = await self.bot.fetch_user(user)
            except:
                return await ctx.reply("User not found!")
        else:
            user = user or ctx.author
        if isinstance(user, discord.User):
            for g in self.bot.guilds:
                for m in g.members:
                    if m.id == user.id:
                        user = m
                        break
                if isinstance(user, discord.Member):
                    break
        e = discord.Embed()
        e.color = user.color
        e.set_author(name=str(user) + (" 🤖" if user.bot else ""), icon_url=user.avatar)
        e.set_footer(text=f"UUID: {user.id}")
        e.add_field(name="Created at", value=f"{self.bot.utils.format_dt(user.created_at, 'f')}\n{self.bot.utils.format_dt(user.created_at, 'R')}")
        flags = list(set([e for b, e in badges.items() if getattr(user.public_flags, b)]))
        if flags:
            e.add_field(name="Badges", value=''.join(flags))
        if len(e.fields)%3:
            for _ in range(3-len(e.fields)%3):
                e.add_field(name="\u200b", value="\u200b")
        if isinstance(user, discord.Member):
            if not user.bot:
                for activity in user.activities:
                    if isinstance(activity, discord.Spotify):
                        e.add_field(name="Spotify", value=f"[**{activity.title}**](https://open.spotify.com/track/{activity.track_id})\nby __{''.join(activity.artists)}__\non {activity.album}")
                        e.set_thumbnail(url=activity.album_cover_url)
                    if activity.type is discord.ActivityType.playing or isinstance(activity, discord.Game):
                        e.add_field(name="Game", value=f"Started playing **{activity.name}**\n{self.bot.utils.format_dt(activity.start, 'R') if activity.start else ''}")
                        if "large_image_url" in dir(activity) and activity.large_image_url:
                            e.set_thumbnail(url=activity.large_image_url)
                    if activity.type is discord.ActivityType.streaming or isinstance(activity, discord.Streaming):
                        e.add_field(name="Stream", value=f"Started streaming {activity.game}\non {activity.platform} at [**{activity.twitch_name}**]({activity.url})")
                        if "large_image_url" in dir(activity) and activity.large_image_url:
                            e.set_thumbnail(url=activity.large_image_url)
                    if isinstance(activity, discord.CustomActivity):
                        e.add_field(name="Custom Status", value=f"{activity.emoji if activity.emoji else ''} {activity.name if activity.name else ''}")
            if len(e.fields)%3:
                for _ in range(3-len(e.fields)%3):
                    e.add_field(name="\u200b", value="\u200b")
            if str(user.web_status) != "offline":
                e.add_field(name="Web Status", value=str(user.web_status).capitalize())
            e.add_field(name="Desktop Status", value=str(user.desktop_status).capitalize())
            if str(user.mobile_status) != "offline":
                e.add_field(name="Mobile Status", value=str(user.mobile_status).capitalize())
            if len(e.fields)%3:
                for _ in range(3-len(e.fields)%3):
                    e.add_field(name="\u200b", value="\u200b")
            if user.guild == ctx.guild:
                e.timestamp = user.joined_at
                e.set_footer(text=e.footer.text+" | Joined")
                if user.nick:
                    e.add_field(name="Nickname", value=user.nick)
                e.add_field(name="Boosting since", value=f"{self.bot.utils.format_dt(user.premium_since, 'f')}\n{self.bot.utils.format_dt(user.premium_since, 'R')}" if user.premium_since else "Not Boosting")
            if len(e.fields) in [2, 5, 8, 11, 14]:
                e.add_field(name="\u200b", value="\u200b")
        await ctx.reply(embed=e)

    @commands.command(slash_command=True, help="Send feedback to bot developer")
    @commands.bot_has_permissions(embed_links=1)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def feedback(self, ctx, *, feedback):
        e = discord.Embed(description=feedback)
        e.set_author(name=ctx.author, icon_url=ctx.author.avatar)
        e.timestamp = datetime.utcnow()
        await self.bot.get_channel(859433409016496128).send(embed=e)
        await ctx.send("Feedback sent.")

    @commands.command(slash_command=True, help="Get an invite to bot support server")
    async def support(self, ctx):
        await ctx.send("Join support.\nhttps://discord.gg/YAY3jz4rNG", ephemeral=True)

    @commands.command(aliases=["ji"])
    @commands.bot_has_permissions(embed_links=1)
    async def join_info(self, ctx, user: discord.Member=None):
        if user == None:
            user = ctx.author
        now = datetime.utcnow()
        e = discord.Embed(description="Some in-depth info about user.")
        e.set_author(name=f"{user.name}#{user.discriminator}", icon_url=user.avatar)
        e.add_field(name="Created on", value=f"{user.created_at.year}/{user.created_at.month}/{user.created_at.day} {user.created_at.hour}:{user.created_at.minute} - `{self.bot.utils.time_str(now.timestamp() - user.created_at.timestamp(), abbr=True)[1]}` ago", inline=False)
        e.add_field(name="Joined on", value=f"{user.joined_at.year}/{user.joined_at.month}/{user.joined_at.day} {user.joined_at.hour}:{user.joined_at.minute} - `{self.bot.utils.time_str(now.timestamp() - user.joined_at.timestamp(), abbr=True)[1]}` ago", inline=False)
        e.add_field(name="Joined server after creation", value=f"{self.bot.utils.time_str(user.joined_at.timestamp() - user.created_at.timestamp(), abbr=True)[1]}", inline=False)
        await ctx.send(embed=e)

    @commands.command(aliases=["jil"])
    @commands.bot_has_permissions(embed_links=1)
    async def join_info_list(self, ctx, *, time: str):
        try:
            rank, text = await self.get_join_info_list(ctx.guild, time)
            if not text:
                await ctx.send("Invalid time given.")
                return
        except Exception as e:
            await ctx.send(f"An error occured!")
            return
        if len(rank) == 0:
            await ctx.send("There are no users.")
            return
        page_no = 0
        x=discord.Embed(title=f"Join info list - Users who joined within {text} of account creation.", description=rank[page_no], colour=discord.Color.random())
        x.set_footer(text="Page No: {}/{}".format(page_no + 1, len(rank)), icon_url=ctx.author.avatar)
        sent = await ctx.send(embed=x)
        if len(rank) == 1:
            return
        await sent.add_reaction("◀️")
        await sent.add_reaction("▶️")
        def check(reaction, user):
            return user == ctx.author and reaction.message.id == sent.id and str(reaction.emoji) in ["◀️","▶️"]
        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except Exception as e:
                try:
                    await sent.clear_reactions()
                except:
                    break
                break
            if str(reaction.emoji) == "◀️":
                page_no -= 1
                if page_no < 0:
                    page_no = len(rank) - 1
            if str(reaction.emoji) == "▶️":
                page_no += 1
                if page_no > len(rank) - 1:
                    page_no = 0
            x=discord.Embed(title=f"Join info list - Users who joined within {text} of account creation.", description=rank[page_no], colour=discord.Color.random())
            x.set_footer(text="Page No: {}/{}".format(page_no + 1, len(rank)), icon_url=ctx.author.avatar)
            try:
                await sent.edit(embed=x)
            except:
                pass
            try:
                await reaction.remove(ctx.author)
            except:
                pass

    async def get_join_info_list(self, guild, time):
        timing, time_str = self.bot.utils.time_str(time)
        if timing == 0:
            raise Exception("LOL")
        now = datetime.utcnow()
        guild_members = [m.id for m in guild.members]
        input_data = sorted([[u.joined_at.timestamp() - u.created_at.timestamp(), u] for u in guild.members if (u.joined_at.timestamp() - u.created_at.timestamp()) < timing], key=lambda x: [x[0], x[1].id])
        page_size = 10
        i = 0
        output_data = []
        text = ""
        for user in input_data:
            if i == page_size:
                i = 0
                output_data.append(text)
                text = ""
            i += 1
            timestr = self.bot.utils.time_str(user[0])[1]
            text += f"``{user[1]}`` - Joined **{timestr if timestr else '0s'}** after creation.\n"
        if text != "":
            output_data.append(text)
        return output_data, time_str

    @commands.command(slash_command=True, help="Check out what communities have the bot")
    async def communities(self, ctx, arg=None):
        # msg = ""
        # i = 0
        # for guild in sorted(self.bot.guilds, key=lambda x: x.me.joined_at.timestamp()):
        #     if arg:
        #         if arg.lower() == "true" and ctx.author.id == 565097923025567755:
        #             msg += f"{guild.id} - "
        #     msg += f"`{self.bot.utils.time_str(datetime.utcnow().timestamp()-guild.me.joined_at.timestamp(), abbr=True)[1]}` -> **{guild.name}**\n"
        #     i += 1
        # e=discord.Embed(title=f"**Communities you can find Trove bot in** ({i})",description=msg, color=self.comment)
        await ctx.send("https://slynx.xyz/trove/communities")#embed=e)

    @commands.command(aliases=["iu"])
    @commands.bot_has_permissions(embed_links=1)
    async def imgur_upload(self, ctx):
        try:
            try:
                await ctx.message.delete()
            except:
                pass
            contents = await ctx.message.attachments[0].read()
            b64 = base64.b64encode(contents)
            data = {
                'image': b64,
                'type': 'base64',
            }
            url = 'https://api.imgur.com/3/image'
            headers = {
              'Authorization': f'Client-ID {self.bot.keys["Imgur"]["ClientID"]}'
            }
            i = 0
            if i == 0:
                i += 1
                response = requests.request('POST', url, headers = headers, data = data, allow_redirects=False)
                try:
                    if response .json()["data"]["code"] == 1003:
                        await ctx.send("File Type invalid")
                        return
                except:
                    pass
                linkerino = response.json()["data"]["link"]
                e=discord.Embed(description=f"You imgur link: {linkerino}", color=ctx.author.color)
                message = await ctx.send(embed=e)
                await message.add_reaction("👁")
                while datetime.utcnow().timestamp() < ctx.message.created_at.timestamp() + 60:
                    def check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '👁' and reaction.message.id == message.id
                    try:
                        await self.bot.wait_for('reaction_add', check=check, timeout=60)
                    except:
                        return
                    e=discord.Embed(description=f"You imgur link: {linkerino}", color=ctx.author.color)
                    e.set_image(url=linkerino)
                    await message.edit(embed=e)
                    def _check(reaction, user):
                        return user == ctx.author and str(reaction.emoji) == '👁' and reaction.message.id == message.id
                    try:
                        await self.bot.wait_for('reaction_remove', check=_check, timeout=60)
                    except:
                        return
                    e=discord.Embed(description=f"You imgur link: {linkerino}", color=ctx.author.color)
                    await message.edit(embed=e)
        except Exception as e:
            await ctx.send(f"{e}\nAn error ocurred, try again please!")
            print(e)

    @commands.command(aliases=["hs"], hidden=True)
    @commands.bot_has_permissions(embed_links=1)
    async def hoststats(self, ctx):
        CPU_Usage = psutil.cpu_percent()
        RAM_Usage = psutil.virtual_memory().percent
        Disk_Usage = psutil.disk_usage("/").percent
        e=discord.Embed(title="Host Stats", description="Shows some stats about the bot's host.", color=0xff4500)
        e.add_field(name="CPU Usage", value=f"{CPU_Usage}%")
        e.add_field(name="RAM Usage", value=f"{RAM_Usage}%")
        e.add_field(name="Disk Usage", value=f"{Disk_Usage}%")
        await ctx.send(embed=e)

    # Latency Command
    @commands.command(slash_command=True, help="Check out bot's latency", aliases=["pong"])
    @commands.bot_has_permissions(embed_links=1)
    async def ping(self, ctx):
        latency = f'🏓 Pong!\n{int(round(self.bot.latency * 1000, 0))}ms'
        await ctx.send(content=latency)

    # Invite command
    @commands.command(slash_command=True, help="Invite the bot to your own server")
    async def invite(self, ctx):
        await ctx.send(f"You can invite me with this link <https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=2146959103&scope=bot%20applications.commands>")

    @commands.group()
    async def prefix(self, ctx):
        if not ctx.invoked_subcommand:
            ns = await self.bot.db.db_bot.find_one({"_id": "0511"}, {"prefixes": 1})
            if str(ctx.author.id) not in ns["prefixes"]["users"].keys():
                await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"prefixes.users." + str(ctx.author.id): None}})
                ns = await self.bot.db.db_bot.find_one({"_id": "0511"})
            if str(ctx.guild.id) not in ns["prefixes"]["servers"].keys():
                await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"prefixes.servers." + str(ctx.guild.id): None}})
                ns = await self.bot.db.db_bot.find_one({"_id": "0511"})
            prefixes = ns["prefixes"]
            server_prefix = prefixes["servers"].get(str(ctx.guild.id))
            user_prefix = prefixes["users"].get(str(ctx.author.id))
            e = discord.Embed()
            e.color = discord.Color.random()
            e.set_author(name="List of Prefixes", icon_url=ctx.guild.icon)
            e.description = f"Use `{ctx.prefix}prefix server MyPrefix` to edit server prefix.\n"
            e.description += f"Use `{ctx.prefix}prefix self MyPrefix` to edit your prefix.\n"
            e.add_field(name="Server Prefix", value=f"`{server_prefix}`")
            e.add_field(name="User Prefix", value=f"`{user_prefix}`")
            await ctx.reply(embed=e)

    @prefix.command(name="self")
    async def _self(self, ctx, *, args=None):
        await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"prefixes.users." + str(ctx.author.id): args}})
        if args:
            await ctx.reply(f"Your self prefix is now set to `{args}`")
        else:
            await ctx.reply(f"Your self prefix has been reset.")
            
    @prefix.command(name="server")
    @perms.has_permissions("manage_guild")
    async def _server(self, ctx, *, args=None):
        await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"prefixes.servers." + str(ctx.guild.id): args}})
        if args:
            await ctx.reply(f"Server prefix is now set to `{args}`")
        else:
            await ctx.reply(f"Server prefix has been reset.")

    @commands.group(aliases=["bbl"])
    async def botblacklist(self, ctx):
        ...

    @botblacklist.command(name="list")
    @commands.bot_has_permissions(embed_links=1)
    async def _list(self, ctx):
        guild = await self.bot.fetch_guild(834505270075457627)
        bans = await guild.bans()
        if not bans:
            return await ctx.send("There are no blacklisted users.")
        bans = self.bot.utils.chunks(bans, 20)
        page = 0
        msg = None
        while True:
            e = discord.Embed()
            e.color = discord.Color.random()
            e.description = "\n".join([f"`{b.user.id}` **{b.user}**" for b in bans[page]])
            e.set_author(name="Bot Blacklist", icon_url=self.bot.user.avatar)
            if not msg:
                msg = await ctx.send(embed=e)
                if len(bans) == 1:
                    return
                await msg.add_reaction("⬅️")
                await msg.add_reaction("➡️")
                def check(reaction, user):
                    return reaction.message == msg and user == ctx.author and str(reaction) in ["⬅️", "➡️"]
            else:
                await msg.edit(embed=e)
            try:
                reaction, _ = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except:
                try:
                    await msg.clear_reactions()
                except:
                    try:
                        await msg.remove_reaction("⬅️")
                        await msg.remove_reaction("➡️")
                    except:
                        ...
                return
            if str(reaction) == "⬅️":
                page += 1
                if page > len(bans) - 1:
                    page = 0
            else:
                page -= 1
                if page < 0:
                    page = len(bans) - 1
            try:
                await msg.remove_reaction(str(reaction), ctx.author)
            except:
                ...

    @botblacklist.command(name="info")
    @commands.bot_has_permissions(embed_links=1)
    async def _info(self, ctx, *, user: typing.Union[discord.Member, discord.User]=None):
        guild = self.bot.get_guild(834505270075457627)
        author = guild.get_member(ctx.author.id)
        if user and not (author and author.guild_permissions.administrator):
            return await ctx.reply("You can't look at the reason for other users :P")
        user = user or ctx.author
        try:
            ban = await guild.fetch_ban(user)
        except:
            return await ctx.reply(f"{user.mention} is not blacklisted.", allowed_mentions=discord.AllowedMentions.none())
        e = discord.Embed()
        e.color = discord.Color.random()
        e.description = f"**Reason:**\n{ban.reason}"
        #e.timestamp = ban.created_at
        e.set_author(name=user, icon_url=user.avatar)
        #e.set_footer(text="Banned at")
        if user == ctx.author and not author.guild_permissions.administrator:
            send = ctx.author.send
        else:
            send = ctx.reply
        await send(embed=e)

    @commands.group(invoke_without_command=True, aliases=["diagnose"])
    @commands.bot_has_permissions(embed_links=1)
    async def debug(self, ctx, channels: commands.Greedy[typing.Union[discord.TextChannel, discord.VoiceChannel]]=None):
        bot = ctx.guild.me
        data = await self.bot.db.db_servers.find_one({"_id": ctx.guild.id})
        channels = channels or [c for c in ctx.guild.channels if isinstance(c, (discord.TextChannel, discord.VoiceChannel)) and c.permissions_for(bot).read_messages]
        channels.sort(key=lambda x: (x.category.position if x.category else -1, x.position))
        e = discord.Embed()
        e.set_author(name="Permission Diagnostic Tool", icon_url=bot.avatar)
        e.color = self.bot.progress
        loading = self.bot.utils.emotes["loading"]
        e.description = loading + " Starting debugger..."
        basic_perms = [
            "view_channel",
            "read_message_history",
            "read_messages",
            "send_messages",
            "embed_links",
            "add_reactions",
            "attach_files",
            "external_emojis"
        ]
        extra_perms = [
            "manage_messages"
        ]
        summary = {}
        def convert_perms_to_text(perms):
            return [" ".join([t.capitalize() for t in p.split("_")]) for p in perms]
        for channel in channels:
            perms = channel.permissions_for(bot)
            missing_basic = []
            if isinstance(channel, discord.TextChannel):
                for bperm in basic_perms:
                    if not getattr(perms, bperm):
                        missing_basic.append(bperm)
            missing_extra = []
            if isinstance(channel, discord.TextChannel):
                for eperm in extra_perms:
                    if not getattr(perms, eperm):
                        missing_extra.append(eperm)
            summary[str(channel.id)] = {
                "channel": channel,
                "failed>Basic": {
                    "value": bool(missing_basic),
                    "perms": convert_perms_to_text(missing_basic)
                },
                "failed>Clock": {
                    "value": channel.id == data["clock"]["channel"] and not perms.manage_channels,
                    "perms": ["Manage Channels"]
                },
                "failed>Auto Voice Daily": {
                    "value": channel.id == data["automation"]["daily"]["voice"]["channel"] and not perms.manage_channels,
                    "perms": ["Manage Channels"]
                },
                "failed>Auto Voice Weekly": {
                    "value": channel.id == data["automation"]["weekly"]["voice"]["channel"] and not perms.manage_channels,
                    "perms": ["Manage Channels"]
                },
                "failed>Extra Permissions":  {
                    "value": bool(missing_extra),
                    "perms": convert_perms_to_text(missing_extra)
                },
            }
        msg = await ctx.reply(embed=e)
        pages = self.translate_perms(bot, summary, admin=bot.guild_permissions.administrator)
        view = Paginator(ctx, pages, start_end=True)
        try:
            view.message = await msg.edit(embed=pages[0]["embed"], view=view)
        except:
            pass

    def translate_perms(self, bot, summary, admin=False):
        full_summary = []
        channels_summary = []
        e = discord.Embed()
        e.set_author(name="Permission Diagnostic Tool - Summary", icon_url=bot.avatar)
        e.set_footer(text="❌ Won't behave correctly | ⚠️ Will work but not fully | ✅ All good")
        e.color = discord.Color.random()
        e.description = "You don't need to debug anything, bot is administrator and so it can do all it needs.\n\n" if admin else ""
        emojis = ["❌", "✅", "⚠️"]
        for _, channel in summary.items():
            ce = discord.Embed()
            ce.set_author(name="Permission Diagnostic Tool - Summary", icon_url=bot.avatar)
            ce.color = discord.Color.random()
            ce.description = f"**{channel['channel'].mention}**\n\n"
            failed = False
            warning = False
            for key, value in channel.items():
                if "failed" not in key:
                    continue
                key_name = key.split(">")[1]
                if not failed and key_name in ["Basic", "Clock", "Auto Voice Daily", "Auto Voice Weekly"] and value["value"]:
                    failed = True
                elif not failed and not warning and key_name in ["Extra Permissions"] and value["value"]:
                    warning = True
                ce.add_field(name=(emojis[0] if value["value"] else emojis[1]) + " " + key_name, value=("Missing: **" + "**, **".join(value["perms"]) + "**") if value["value"] else "\u200b", inline=False)
            if failed:
                e.description += emojis[0] + f" {channel['channel'].mention}\n"
            elif warning:
                e.description += emojis[2] + f" {channel['channel'].mention}\n"
            else:
                e.description += emojis[1] + f" {channel['channel'].mention}\n"
            channels_summary.append({"content": None, "embed": ce})
        e.add_field(name="\u200b", value="**Only channels bot has `Read Messages` permission on will display here.**")
        full_summary.append({"content": None, "embed":e})
        return full_summary + channels_summary 

    @debug.command()
    async def info(self, ctx):
        ...

def setup(bot):
    n = General(bot)
    bot.add_cog(n)
