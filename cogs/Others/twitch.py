# Priority: 0
from datetime import datetime

import discord
import pycountry
from discord.ext import commands, tasks

from twitch import TwitchHelix, api, constants, helix, resources
from utils.buttons import Paginator


class Twitch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.clientID = self.bot.keys["Twitch"]["ClientID"]
        self.clientSecret = self.bot.keys["Twitch"]["ClientSecret"]
        self.start_twitch_client()
        self.get_trove_id()
        self.check_streams.start()

    def cog_unload(self):
        self.check_streams.cancel()

    def start_twitch_client(self):
        self.client = TwitchHelix(
            client_id=self.clientID,
            client_secret=self.clientSecret,
            scopes=[
                constants.OAUTH_SCOPE_ANALYTICS_READ_EXTENSIONS,
                constants.OAUTH_SCOPE_USER_READ_BROADCAST
            ]
        )
        self.client.get_oauth()
        self.api = api.users.Users(client_id=self.clientID, oauth_token=self.client._oauth_token)

    async def get_user(self, login):
        headers = {
            "Client-ID": self.clientID,
            "Authorization": "Bearer {}".format(self.client._oauth_token)
        }
        url = f"https://api.twitch.tv/helix/users?login={login}"
        request = await self.bot.AIOSession.get(url, headers=headers)
        users = (await request.json())["data"]
        return users[0] if users else None

    def get_trove_id(self):
        self.trove_id = self.client.get_games(names=["Trove"])[0].id
    
    def get_live_streams(self, streamers_list):
        streamers_pages = self.bot.utils.chunks(streamers_list, 100)
        for streamers in streamers_pages:
            for streamer in self.client.get_streams(user_ids=streamers):
                yield streamer

    def get_live_trove_streams(self, start=0):
        x = 0
        for i in self.client.get_streams(after=str(start) if start else None, page_size=100, game_ids=[self.trove_id]):
            x += 1
            if not x%100:
                for i in self.get_trove_streams(start+x):
                    yield i
            yield i

    @tasks.loop(seconds=6000)
    async def check_streams(self):
        streamers_list = []
        servers = []
        async for server in self.bot.db.db_servers.find({"$and": [{"twitch.channels": {"$exists": True}}, {"twitch.channels": {"$ne": []}}]}, {"twitch": 1}):
            for channel in server["twitch"]["channels"]:
                streamers_list.append(channel["id"])
            servers.append(server)
        streams = self.get_live_streams(list(set(streamers_list)))
        for stream in streams:
            for server in servers:
                for channel in server["twitch"]["channels"]:
                    if channel["id"] == stream["user_id"]:
                        server["twitch"]["notified"].append(stream["id"])

    @commands.group()
    async def twitch(self, _):
        ...

    @twitch.command(aliases=["ts"])
    async def trove_streams(self, ctx):
        streams = self.get_live_trove_streams()
        streams_text = []
        for stream in streams:
            text = f"`👁️️{stream['viewer_count']}` [**{stream['user_name']}**](https://www.twitch.tv/{stream['user_name']}) | <t:{int(stream['started_at'].timestamp())}:R>"
            language = pycountry.languages.get(alpha_2=stream["language"]).name
            text += f" [**{language}**]"
            if stream["is_mature"]:
                text += " 🔞"
            streams_text.append(text)
        stream_pages = self.bot.utils.chunks(streams_text, 10)
        pages = []
        for page in range(len(stream_pages)):
            e = discord.Embed()
            e.set_footer(text="Viewers | Name | Started at | Language | Mature")
            e.color = discord.Color.random()
            e.description = "\n".join(stream_pages[page])
            e.set_author(name=f"Trove Streams ({len(streams_text)}) | Page {page+1} of {len(stream_pages)}")
            _page = {
                "content": None,
                "embed": e
            }
            pages.append(_page)
        view = Paginator(ctx, pages, start_end=True)
        view.message = await ctx.reply(embed=pages[0]["embed"], view=view)


    @twitch.command()
    async def search(self, ctx, twitch_name):
        user = await self.get_user(twitch_name)
        e = discord.Embed()
        e.description = user["description"]
        e.timestamp = datetime.strptime(user["created_at"], "%Y-%m-%dT%H:%M:%SZ")
        e.color = discord.Color.random()
        e.set_author(name=user["display_name"], icon_url=user["profile_image_url"])
        e.add_field(name="ID", value=user["id"])
        e.add_field(name="Total Views", value=user["view_count"])
        e.set_image(url=user["offline_image_url"])
        e.set_footer(text="Created")
        await ctx.reply(embed=e)

    @twitch.command()
    async def follow(self, ctx, twitch_name):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        channels.append(self.stream_entry(user["id"]))
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"twitch.channels": channels}})
        channel = ctx.guild.get_channel(data["channel"])
        await ctx.reply(f"`{user['display_name']}` is now being followed " + ("and notifications will be posted in {channel.mention}" if channel else "but no channel is set for it's notifications."))

    @twitch.command()
    async def unfollow(self, ctx, twitch_name):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        if not [c for c in channels if c["id"] == user["id"]]:
            return await ctx.reply(f"You are not following `{user['display_name']}`")
        for channel in channels:
            if channel["id"] == user["id"]:
                channels.remove(channel)
                break
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"twitch.channels": channels}})
        await ctx.reply(f"`{user['display_name']}` is no longer being followed.")

    @twitch.command()
    async def settings(self, ctx):
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channel = ctx.guild.get_channel(data["channel"])
        e = discord.Embed()
        e.color = discord.Color.random()
        e.set_author(name="Twitch Settings", icon_url="https://i.imgur.com/xpa32t6.png")
        e.add_field(name="Channel", value=channel.mention if channel else "Not Set")
        e.add_field(name="Message", value=data["channel"] or "Not Set", inline=False)
        await ctx.reply(embed=e)

    @twitch.group()
    async def channel(self, _):
        ...

    @channel.command()
    async def only_trove(self, ctx, twitch_name):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        if not [c for c in channels if c["id"] == user["id"]]:
            return await ctx.reply(f"You are not following `{user['display_name']}`")
        for channel in channels:
            if channel["id"] == user["id"]:
                if channel["only_trove"]:
                    channel["only_trove"] = False
                    message = "will be notified when they stream on any category."
                else:
                    channel["only_trove"] = True
                    message = "will be notified only when they stream Trove."
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"twitch.channels": channels}})
        await ctx.reply(f"`{user['display_name']}` {message}")

    @channel.command(aliases=["mention", "role"])
    async def role_mention(self, ctx, twitch_name, role: discord.Role=None):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        if not [c for c in channels if c["id"] == user["id"]]:
            return await ctx.reply(f"You are not following `{user['display_name']}`")
        for channel in channels:
            if channel["id"] == user["id"]:
                if role:
                    channel["mention_role"] = role.id
                    message = f"notification will mention {role.mention}"
                else:
                    channel["mention_role"] = None
                    message = "notifications will no longer mention a role."
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"twitch.channels": channels}})
        await ctx.reply(f"`{user['display_name']}` {message}", allowed_mentions=discord.AllowedMentions.none())

    @channel.command(aliases=["channel"])
    async def text_channel(self, ctx, twitch_name, text_channel: discord.TextChannel=None):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        if not [c for c in channels if c["id"] == user["id"]]:
            return await ctx.reply(f"You are not following `{user['display_name']}`")
        for channel in channels:
            if channel["id"] == user["id"]:
                if text_channel:
                    channel["custom_channel"] = text_channel.id
                    message = f"notifications will be sent to {text_channel.mention}"
                else:
                    channel["custom_channel"] = None
                    message = "notifications will be sent to general notification channel."
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"twitch.channels": channels}})
        await ctx.reply(f"`{user['display_name']}` {message}")

    @channel.command()
    async def settings(self, ctx, twitch_name):
        user = await self.get_user(twitch_name)
        if not user:
            return await ctx.reply(f"`{twitch_name}` was not found.")
        data = (await ctx.get_guild_data(twitch=1))["twitch"]
        channels = data["channels"]
        if not [c for c in channels if c["id"] == user["id"]]:
            return await ctx.reply(f"You are not following `{user['display_name']}`")
        for channel in channels:
            if channel["id"] == user["id"]:
                break
        ch = ctx.guild.get_channel(channel["custom_channel"])
        role = ctx.guild.get_role(channel["mention_role"])
        e = discord.Embed()
        e.color = discord.Color.random()
        e.set_author(name=f"{user['display_name']} Settings", icon_url=user["profile_image_url"])
        e.add_field(name="Only Trove", value="Yes" if channel["only_trove"] else "No")
        e.add_field(name="Mention Role", value= role.mention if role else "Not Set")
        e.add_field(name="Custom Channel", value= ch.mention if ch else "Not Set")
        e.add_field(name="Custom Message", value=channel["custom_message"] or "Not Set", inline=False)
        if channel["last_time_online"]:
            e.timestamp = datetime.utcfromtimestamp(channel["last_time_online"])
            e.set_footer(text="Last time online")
        await ctx.reply(embed=e)

    def stream_entry(self, _id):
        return {
            "id": _id,
            "mention_role": None,
            "only_trove": True,
            "last_time_online": 0,
            "custom_message": None,
            "custom_channel": None
        }

def setup(bot):
    bot.add_cog(Twitch(bot))
