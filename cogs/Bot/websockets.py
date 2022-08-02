# Priority: 1
import asyncio
import json
import re
import urllib.request as urlget
from datetime import datetime

import discord
from aiohttp import ClientSession
from discord.ext import commands, tasks
from openpyxl import load_workbook

import websockets
from utils.CustomObjects import CEmbed, MetricsConverter


class WebSockets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if self.bot.is_clone:
            return
        self.session = ClientSession()
        self.ws = None
        self.guild_data = []
        self.get_servers.start()
        self.load_spreadsheets.start()
        asyncio.create_task(self.launch_websocket())
        self.port = self.bot.keys["Bot"]["Websocket"]["Port"]

    @tasks.loop(seconds=60)
    async def load_spreadsheets(self):
        def load_sheets():
            urlget.urlretrieve("https://docs.google.com/spreadsheets/d/1YBf3__CPCy9iL4HDEoF1_q88vaFtAR6mA4GZxIzOEG8/export?format=xlsx&id=1YBf3__CPCy9iL4HDEoF1_q88vaFtAR6mA4GZxIzOEG8", 'data/sheets/memento_list_sheet1.xlsx')
            self.memento_list = load_workbook(filename="data/sheets/memento_list_sheet1.xlsx", data_only=True)
        await self.bot.loop.run_in_executor(None, load_sheets)

    def cog_unload(self):
        self.get_servers.cancel()
        self.load_spreadsheets.cancel()
        asyncio.create_task(self.terminate())

    async def terminate(self):
        await self.session.close()
        if self.ws:
            self.ws.close()
            print(f"Killed websocket at port {self.port}")

    async def websocket(self, websocket, path):
        del path
        data = await websocket.recv()
        data = json.loads(data)

        if data["method"] == "appeal":
            return await self.websocket_appeal(websocket, data)

        if data["method"] == "metrics":
            return await self.websocket_metrics(websocket, data)

        if data["method"] == "guilds":
            return await self.guilds(websocket, data)

        if data["method"] == "posts":
            return await self.trove_posts(websocket, data)

        if data["method"] == "issues":
            return await self.issues(websocket, data)

        if data["method"] == "trovesaurus_metrics":
            return await self.websocket_trovesaurus_metrics(websocket, data)

        await websocket.send("400")

    async def launch_websocket(self):
        await asyncio.sleep(5)
        try:
            self.ws = await websockets.serve(self.websocket, "0.0.0.0", self.port)
        except:
            return print("Failed to open websocket, port in use.")
        print(f"Started websocket at port {self.port}")

    async def websocket_appeal(self, websocket, odata):
        try:
            user = await self.bot.fetch_user(odata["user_id"])
        except:
            return await websocket.send(str(json.dumps({"text": "User ID is incorrect.", "color": "#ff0000"})))
        if user.id not in self.bot.blacklist:
            return await websocket.send(str(json.dumps({"text": "You are not blacklisted, no reason to appeal.", "color": "#ffff00"})))
        data = {
            "id": user.id,
            "name": user.name,
            "discriminator": user.discriminator,
            "avatar_url": str(user.avatar.replace(static_format="png", size=128)),
            "text": "Your appeal was submitted successfully.",
            "color": "#00ff00"
        }
        guild = await self.bot.fetch_guild(834505270075457627)
        for ban in await guild.bans():
            if ban.user.id == user.id:
                break
        e = CEmbed(description="**Appeal Message:** " + odata["appeal"] + f"\n\n**Reason:** {ban.reason}", color=0x0000ff, timestamp=datetime.utcnow())
        e.set_author(name=user, icon_url=user.avatar)
        e.set_footer(text=str(user.id))
        await self.bot.appeal_logger.send(embed=e, username="Blacklist Appeals", avatar_url=self.bot.user.avatar)
        return await websocket.send(str(json.dumps(data)))

    async def websocket_metrics(self, websocket, odata):
        data = {
            "color": "#ff0000"
        }
        try:
            user = await self.bot.fetch_user(odata["user_id"])
        except:
            data["text"] = "User ID is incorrect."
            return await websocket.send(str(json.dumps(data)))
        if user.id in self.bot.blacklist:
            e = CEmbed(description=f"{user} tried to submit a profile on web.")
            e.set_author(name="Blacklist", icon_url=user.avatar)
            await self.bot.blacklist_logger.send(embed=e)
            data["text"] = "You are blacklisted, you can't create a profile."
            return await websocket.send(str(json.dumps(data)))
        try:
            data = MetricsConverter(odata["metrics"]).get_profile()
        except Exception as e:
            await self.log(user, f"Failed to submit a profile. **{e}**")
            data["text"] = "Try again."
            return await websocket.send(str(json.dumps(data)))
        try:
            name, _class = await self.save_profile(user, data)
        except Exception as e:
            data["text"] = str(e)
            await self.log(user, str(e))
            return await websocket.send(str(json.dumps(data)))
        await self.log(user, f"**{name}** submitted a profile for {_class}.\n")
        data["id"] = user.id
        data["name"] = user.name
        data["discriminator"] = user.discriminator
        data["avatar_url"] = str(user.avatar_url_as(static_format="png", size=128))
        data["text"] = "Profile submitted successfully."
        data["color"] = "#00ff00"
        return await websocket.send(str(json.dumps(data)))

    async def websocket_trovesaurus_metrics(self, websocket, data):
        request = await self.bot.AIOSession.get(data["url"])
        text = await request.text()
        self.bot.dispatch("profile_create", text, None)
        return await websocket.send("200")

    async def trove_posts(self, websocket, data):
        post = await self.bot.db.db_forums.find_one({"_id": data["post_id"]})
        if not post:
            return await websocket.send("404")
        #post["created_at"] = (datetime.utcfromtimestamp(post["created_at"]).astimezone(pytz.timezone("gmt"))-timedelta(hours=7)).strftime("%m-%d-%Y %I:%M %p")
        time =  datetime.utcfromtimestamp(post["created_at"])
        now = datetime.utcnow()
        pre = ""
        if time.month == now.month and time.year == now.year:
            if time.day == now.day:
                pre = "Today "
            elif time.day == now.day-1:
                pre = "Yesterday "
        post["created_at"] = pre + time.strftime("%m-%d-%Y %I:%M %p" if not pre else "%I:%M %p") + " UTC"
        return await websocket.send(str(json.dumps(post)))

    async def issues(self, websocket, data):
        channel = self.bot.get_channel(812354696320647238)
        e = CEmbed(color=discord.Color.random())
        reduce_size = ["Expected", "Context", "Reproduce"]
        cap_text = "...\n\n**Text Exceeds maximum size, view in web**"
        for field in reduce_size:
            if len(data[field]) > 1024:
                data[field] = data[field][:1024-len(cap_text)] + cap_text
        e.timestamp = datetime.utcfromtimestamp(int(data["Created"]))
        e.set_author(name=data["Author"])
        e.add_field(name="What were you doing?", value=data["Title"] if data["Title"] else "Not provided", inline=False)
        e.add_field(name="Short description of the bug", value=data["Context"] if data["Context"] else "Not provided", inline=False)
        e.add_field(name="What did you expect to happen?", value=data["Expected"] if data["Expected"] else "Not provided", inline=False)
        e.add_field(name="How can we reproduce this bug?", value=data["Reproduce"] if data["Reproduce"] else "Not provided", inline=False)
        e.add_field(name="Trove IGN", value=data["Author"])
        e.add_field(name="Platform", value=data["Platform"])
        e.add_field(name="\u200b", value=f"[View on Trovesaurus Issue Tracker]({data['URL']})")
        e.set_footer(text="Reported via Website")
        await channel.send(embed=e)
        return await websocket.send(str(json.dumps("200")))

    @tasks.loop(seconds=600)
    async def get_servers(self):
        await self.bot.wait_until_ready()
        guild_data = []
        i = 0
        for g in sorted(self.bot.guilds, key=lambda x: -len(x.members)):
            gdata = {
                "index": i,
                "spaced": bool(i%3),
                "id": g.id,
                "name": g.name,
                "icon_url": str(g.me.avatar),
                "description": g.description if g.description else "No description",
                "member_count": len(g.members),
                "loyalty_time_str": self.bot.utils.time_str(int(datetime.utcnow().timestamp() - g.me.joined_at.timestamp()), abbr=True)[1],
                "loyalty_time": int(datetime.utcnow().timestamp() - g.me.joined_at.timestamp()),
                "invite": None
            }
            i += 1
            if g.icon:
                gdata["icon_url"] = str(g.icon.replace(static_format="webp", size=256))
            try:
                if "VANITY_URL" in g.features:
                    invite = (await g.vanity_invite()).url
                else:
                    invite = [i.url for i in sorted(await g.invites(), key=lambda x: x.created_at.timestamp())][0]
                gdata["invite"] = invite
            except:
                pass
            if g.id == 118027756075220992:
                gdata["invite"] = "https://discord.gg/trovesaurus"
            guild_data.append(gdata)
        self.guild_data.clear()
        self.guild_data.extend(guild_data)

    async def guilds(self, websocket, data):
        while not self.guild_data:
            await asyncio.sleep(3)
        return await websocket.send(str(json.dumps(self.guild_data)))

    async def log(self, ctx, text):
        e = CEmbed()
        e.color = discord.Color.random()
        e.timestamp = datetime.utcnow()
        e.description = text
        e.set_author(name=ctx, icon_url=ctx.author.avatar)
        e.set_footer(text=f"Web submission")
        await self.bot.profiles_logger.send(embed=e, username="Profiles")

def setup(bot):
    bot.add_cog(WebSockets(bot))
