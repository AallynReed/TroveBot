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

        if data["method"] == "mementos":
            return await self.depth_list(websocket, data)

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

    async def depth_list(self, websocket, data):
        if not "memento_list" in self.bot.Trove.sheets:
            return await websocket.send("503")
        memento_list = self.bot.Trove.sheets["memento_list"]
        sheets = []
        for s in memento_list.sheetnames:
            if s == "Oct 11 - 17":
                break
            if re.findall(r"^(Temp Sheet|[a-z]{3,5} [0-9]{1,2}-[0-9]{1,2})$", s, re.IGNORECASE):
                sheets.append(s)
        if data["sheet"] not in sheets:
            return await websocket.send("404")
        _filter = data["filter"].replace(" | ", "|").split("|") if data["filter"] else None
        ml = memento_list[data["sheet"]]
        depths = []
        mount_bosses = {
           # Shadow Towers
            "Spike Walker": ["Mount: Spike Roller", "Mount: Spikewalker Hatchling"],
            "Weeping Prophet": ["Mount: Prophet's Throne", "Mount: Twitching Tentacle"],
            "Vengeful Pinata God": ["Mount: Skulpin Airswimmer", "Mount: Kami of Smoldering Scorn"],
            "Shadow Hydrakken": ["Mount: Hydrasnek", "Mount: Hewn Hydrakken Head"],
            "Darknik Dreadnought": ["Mount: De-Weaponized Worldender", "Mount: Dreadnought Mk I Prototype"],
            "Daughter of the Moon": ["Mount: Moonsail Glider", "Mount: Moonbeam Gunship", "Mount: Lunaclipsia"],
           # Levi
            "Lobstroso": ["Mount: Whirlygig"],
            "Timmense": ["Mount: Timminutive"],
            "Ifera": ["Mount: Sproingy Iferan Spore Colony"],
           # Fae
            "Wild Fae King": ["Mount: Fae Throne", "Mount: Fae Wildride", "Ally: Fae Spider", "Ally: Fae Scavenger", "Ally: Fae Forest Spirit"],
            "Wild Fae Queen": ["Mount: Fae Throne", "Mount: Fae Wildride", "Ally: Fae Spider", "Ally: Fae Scavenger", "Ally: Fae Forest Spirit"],
            "Wild Fae Spider": ["Mount: Fae Throne", "Mount: Fae Wildride", "Ally: Fae Spider", "Ally: Fae Scavenger", "Ally: Fae Forest Spirit"],
           # Others
            "Ice Giant King": ["Mount: Icebreaker Tortoise"],
            "Triceratops": ["Mount: Yoked Yolk"],
            "Deep Waspider": ["Mount: Docile Waspider"],
            "Refracted Balephantom": ["Mount: A Most Ancient Chain"],
            "Quetzalcoatlus": ["Mount: Tamed Quetzel"],
           # Shadow Eve
            "Crimsin Crow": ["Mount: Crimsin"]
        }
        for i in range(141):
            add = 2
            ranges = ["C", "D", "E", "F"]
            mementos = []
            for rang in ranges:
                memento = ml[f'{rang}{i+add}'].value
                mementos.append(memento)
            boss = ml[f'G{i+add}'].value
            # if boss:
            #     mementos.append(boss)
            biome = ml[f'H{i+add}'].value
            if biome == "#N/A":
                biome = None
            npc = ml[f'B{i+add}'].fill.start_color.index not in ["FF000000", "FF222222"]
            # if not (i+1)%3 and biome:
            #     mementos.append(biome)
            if not [m for m in mementos if m] and not boss and not biome:
                continue
            else:
                depth = {
                    "level": 110+i,
                    "mementos": mementos,
                    "boss": boss if boss else "Unknown",
                    "biome": biome if biome else "Unknown",
                    "npc": npc
                }
                depth["has_mount"] = True if boss in mount_bosses.keys() else False
                depth["mounts"] = mount_bosses[boss] if depth["has_mount"] else None
                filter_data = [boss.lower() if boss else "", biome.lower() if biome else "", "mount" if depth["has_mount"] else ""]
                filter_data.extend([m.lower() for m in mementos[:4] if m])
                content = " ".join(filter_data)
                if _filter:
                    cont = True
                    for filt in _filter:
                        if filt in content:
                            cont = False
                            break
                    if cont:
                        continue
                depths.append(depth)
        depths.sort(key=lambda x: x["level"])
        missing = []
        if not _filter and depths:
            missing = [f"{i}" for i in range(110, depths[-1]["level"]+1) if i not in [l["level"] for l in depths]]
        output = {
            "depths": depths,
            "missing": missing,
            "sheets": sheets
        }
        # outfile = io.BytesIO(str(json.dumps(output, indent=4)).encode())
        # await self.bot.get_channel(859440482195341323).send(file=discord.File(outfile, filename="mementos.json"))
        return await websocket.send(str(json.dumps(output)))

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
        e.description = f"**Context**\n{data['Title']}"
        e.timestamp = datetime.utcfromtimestamp(int(data["Created"]))
        e.set_author(name=data["Author"])
        e.add_field(name="Platform", value=data["Platform"])
        e.add_field(name="Trove IGN", value=data["Author"])
        #e.add_field(name="Time", value=)
        e.add_field(name="Expected", value=data["Expected"] if data["Expected"] else "Not provided", inline=False)
        e.add_field(name="Observed", value=data["Context"] if data["Context"] else "Not provided", inline=False)
        e.add_field(name="Reproduction Steps", value=data["Reproduce"] if data["Reproduce"] else "Not provided", inline=False)
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
