# Priority: 9
import asyncio
import json
import os
import re
import traceback
from datetime import datetime

import discord
import hjson
from discord.ext import commands
from discord.utils import find

import utils.checks as perms
from utils.buttons import Paginator, Traceback
from utils.CustomObjects import CEmbed, TimeConverter
from utils.modules import get_loaded_modules


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=True, aliases=["changelog", "cl"], help="Check out the latest changes to the bot.")
    async def change_log(self, ctx):
        pages = []
        async for message in self.bot.get_channel(922275962861801503).history(limit=10000):
            e = CEmbed(description=message.content, color=discord.Color.random())
            if self.bot.version[0] in message.content:
                e.set_author(name="Change Log - Latest", icon_url=self.bot.user.avatar)
            else:
                e.set_author(name="Change Log", icon_url=self.bot.user.avatar)
            pages.append({
                "content": None,
                "embed": e
            })
        pages.reverse()
        view = Paginator(ctx, pages, page=len(pages)-1, start_end=True, timeout=300)
        view.message = await ctx.reply(embed=pages[-1]["embed"], view=view)

    @commands.command(hidden=True)
    @perms.admins()
    async def export_servers(self, ctx, stuff: int=0):
        logs_guild = self.bot.get_guild(834505270075457627)
        logs = {}
        async for message in logs_guild.get_channel(860465862578274314).history(limit=999999):
            if message.author.id == 860466099173457940 and message.embeds:
                guild_id = re.findall(r".*\[([0-9]+)\]", message.embeds[0].author.name)[0]
                if not self.bot.get_guild(int(guild_id)):
                    await message.delete(silent=True)
                    continue
                if guild_id not in logs.keys() or message.created_at > logs[guild_id]:
                    logs[guild_id] = message.created_at
                if ctx.message.created_at.timestamp() - message.created_at.timestamp() > 5184000:
                    asyncio.create_task(message.delete())
        async for message in logs_guild.get_channel(891310035953655808).history(limit=999999):
            if message.author.id == 891310112071880755 and message.embeds:
                guild_id = re.findall(r".*\[([0-9]+)\]", message.embeds[0].author.name)[0]
                if not self.bot.get_guild(int(guild_id)):
                    await message.delete(silent=True)
                    continue
                if guild_id not in logs.keys() or message.created_at > logs[guild_id]:
                    logs[guild_id] = message.created_at
                if ctx.message.created_at.timestamp() - message.created_at.timestamp() > 5184000:
                    asyncio.create_task(message.delete())
        guilds = sorted(
            self.bot.guilds, key=lambda x: (
                x.me.joined_at.timestamp() if stuff==0 else 
                -len(x.members) if stuff==1 else
                -(logs.get(str(x.id)).timestamp() if logs.get(str(x.id)) else 0)
            )
        )
        text = []
        for guild in guilds:
            add = f"[{guild.id:<18}] "
            add += f"({len(guild.members):<5}) "
            add += f"{str(TimeConverter(datetime.utcnow().timestamp()-guild.me.joined_at.timestamp())):<33} | "
            log = logs.get(str(guild.id))
            last_time = str(TimeConverter(datetime.utcnow().timestamp()-log.timestamp())) if log else "Over 2 months..."
            add += f"{last_time:<33} > {guild.name}"
            text.append(add)
        await self.bot.utils.to_file(ctx, "\n".join(text), "txt")

    @commands.command(hidden=True)
    @perms.admins()
    async def slashless(self, ctx):
        text = ""
        for command in self.bot.commands:
            if not command.slash_command and not command.hidden:
                text += f"{command.name}\n"
        await ctx.send(text)

    @commands.command(hidden=True)
    @perms.admins()
    async def helpless(self, ctx):
        data = hjson.loads(open("data/help.hjson").read()).keys()
        commands = []
        for command in self.bot.commands:
            if command.name not in data and not command.hidden:
                commands.append(command.name)
        await ctx.send("\n".join(commands))      

    @commands.command(hidden=True)
    @perms.owners()
    async def relocale(self, ctx):
        self.bot._load_locales()
        await ctx.send("Reloaded languages.")

    @commands.command(hidden=True)
    @perms.owners()
    async def clearm(self, ctx, amount: int):
        i = 0
        async for message in ctx.channel.history(limit=1000):
            if message.author.id != self.bot.user.id:
                continue
            try:
                await message.delete()
            except:
                pass
            i += 1
            if i == amount:
                break
        #await ctx.send(f"Deleted {i} messages.", delete_after=5)

    @commands.command(hidden=True)
    @perms.owners()
    async def dm_owners(self, ctx, *, content):
        done = []
        i = 0
        x = 0
        y = 0
        if not content or len(content) < 100:
            return await ctx.send("Nothing to send!")
        for g in self.bot.guilds:
            if g.id == 118027756075220992:
                continue
            if g.owner.id in done:
                continue
            i += 1
            try:
                await g.owner.send(content, file=await ctx.message.attachments[0].to_file() if ctx.message.attachments else None)
                done.append(g.owner.id)
                x += 1
            except:
                y += 1
                pass
        await ctx.send(f"Sent to {x}/{i}, failed {y}")

    @commands.command(hidden=True)
    @perms.owners()
    async def dm(self, ctx, user: discord.User, *, content=None):
        try:
            if not content and not ctx.message.attachments:
                return await ctx.send("Nothing to send!")
            f = await ctx.message.attachments[0].to_file() if ctx.message.attachments else None
            await user.send(content=content, file=f)
            await ctx.message.add_reaction("<:done:844624767217958922>")
        except Exception as e:
            await ctx.send(str(e))

    @commands.command(hidden=True)
    @perms.admins()
    async def restart(self, ctx):
        if ctx.author.id == 565097923025567755:
            await ctx.send("Restarting!")
            await self.bot.change_presence(status=discord.Status.offline)
            os._exit(-1)

    @commands.command(hidden=True)
    @perms.admins()
    async def restartweb(self, ctx):
        if ctx.author.id == 565097923025567755:
            await ctx.send("Restarting website!")
            os.system("screen -XS slynxweb quit")

    @commands.command(hidden=True)
    @perms.admins()
    async def reload_values(self, ctx):
        self.bot.Trove.values._preload(True)
        await ctx.send("Reloaded values")

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

    @commands.command(hidden=True, aliases=["uh"])
    @perms.admins()
    async def updatehelp(self, ctx):
        if ctx.author.id not in self.bot.admin_ids:
            return
        help = hjson.loads(open("data/help.hjson").read())
        data = []
        for key, value in help.items():
            value["_id"] = key
            data.append(value)
        await self.bot.db.db_help.delete_many({})
        await self.bot.db.db_help.insert_many(data)
        await ctx.send("Successfully updated help!")

    @commands.command(hidden=True)
    @perms.admins()
    async def parse(self, ctx):
        if ctx.author.id in self.bot.admin_ids:
            code = re.findall(r"(?i)(?s)```py\n(.*?)```", ctx.message.content)
            if not code:
                return await ctx.send("No code detected.", ephemeral=True)
            code = "    " + code[0].replace("\n", "\n    ")
            code = "async def __eval_function__():\n" + code
            #Base Variables
            async def to_file(text, format="json"):
                _f = f"file.{format}"
                with open(_f, "w+") as f:
                    f.write(text)
                await ctx.send(file=discord.File(_f))
                os.remove(_f)
            additional = {}
            additional["self"] = self
            additional["feu"] = self.bot.fetch_user
            additional["fem"] = ctx.channel.fetch_message
            additional["dlt"] = ctx.message.delete
            additional["now"] = datetime.utcnow()
            additional["nowts"] = datetime.utcnow().timestamp()
            additional["ctx"] = ctx
            additional["sd"] = ctx.send
            additional["channel"] = ctx.channel
            additional["author"] = ctx.author
            additional["guild"] = ctx.guild
            additional["to_file"] = to_file
            try:
                exec(code, {**globals(), **additional}, locals())

                await locals()["__eval_function__"]()
            except Exception as error:
                built_error = "".join(traceback.format_exception(type(error), error, error.__traceback__))
                view = Traceback(ctx, built_error)
                await ctx.send(content="An error occured.", view=view)

    @commands.command(name="exception", aliases=["error", "lasterror"], hidden=True)
    @perms.admins()
    async def last_exception(self, ctx):
        if self.bot._last_exception:
            view = Traceback(ctx, self.bot._last_exception)
            await ctx.send(content="Last error...", view=view)
            await ctx.message.add_reaction("✅")
        else:
            await ctx.reply("No error.")

    @commands.command(aliases=["modules", "mods"], hidden=True)
    @perms.admins()
    async def cogs(self, ctx):
        "Shows all the cogs."
        modules = self.bot.modules("cogs/")
        modules.sort(key=lambda x: x.name.lower())
        loaded = get_loaded_modules(self.bot, modules)
        modulesi = ""
        total_size = sum([m.size for m in modules])
        if not modules:
            modulesi = "There are no modules!"
        else:
            for module in modules:
                size = round(module.size/1024, 2)
                if module in loaded:
                    modulesi += "📥 **" + module.name.capitalize() + f"** {size}KB\n"
                else:
                    modulesi += "📤 **" + module.name.capitalize() + f"** {size}KB\n"
        modulesi += f"\nTotal: {round(total_size/1024, 2)}KB"
        embed=CEmbed(colour=self.bot.comment, title=f"Modules - {len(modules)}", description=modulesi)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["ul"], hidden=True)
    @perms.admins()
    async def unload(self, ctx, *, mod: str=None):
        """unloads a part of the bot."""
        modules = self.bot.modules("cogs/")
        loaded = get_loaded_modules(self.bot, modules)
        if not mod:
            i = 0
            for module in loaded:
                if module.name.lower() == "owner":
                    continue
                i += 1
                self.bot.unload_extension(module.load)
            extra = len(modules) != len(loaded)
            await ctx.reply(f"Unloaded **{i}/{len(modules)}** modules." + (f" **{len(modules)-len(loaded)}** were already unloaded." if extra else ""))
        else:
            module = find(lambda x: x.name.startswith(mod.lower()), modules)
            if not module:
                return await ctx.send(f"Module `{mod}` not found.")
            if module.name.lower() == "owner":
                return await ctx.reply("Can't unload that module.")
            if module not in loaded:
                return await ctx.reply(f"**{module.name}** not loaded.")
            self.bot.unload_extension(module.load)
            await ctx.reply(f"Unloaded **{module.name}**")

    @commands.command(aliases=["load"], hidden=True)
    @perms.admins()
    async def reload(self, ctx, *, mod: str=None):
        modules = self.bot.modules("cogs/")
        loaded = get_loaded_modules(self.bot, modules)
        if not mod:
            failed = []
            i = 0
            for module in modules:
                if not module.priority:
                    continue
                i += 1
                if module in loaded:
                    self.bot.reload_extension(module.load)
                else:
                    self.bot.load_extension(module.load)
            return await ctx.reply(f"Successfully reloaded **{i-len(failed)}/{len(modules)}** modules." + (f" Failed to reload {len(failed)}" if failed else ""))
        else:
            module = find(lambda x: x.name.startswith(mod.lower()), modules)
            if not module:
                return await ctx.send(f"Module `{mod}` not found.")
            try:
                if module in loaded:
                    self.bot.reload_extension(module.load)
                    await ctx.reply(f"Successfully reloaded **{module.name}**")
                else:
                    self.bot.load_extension(module.load)
                    await ctx.reply(f"Successfully loaded **{module.name}**")
            except Exception as e:
                await ctx.reply(f"```py\n#Failed to reload **{module.name}**\n\n{str(type(e))}: {e}```")

    @commands.command(aliases=["sf"], hidden=True)
    @perms.owners()
    async def send_file(self, ctx, *, file):
        if ctx.author.id not in self.bot.admin_ids:
            return
        try:
            await ctx.author.send(file=discord.File(file))
            await ctx.message.add_reaction("✅")
        except:
            await ctx.send("No file found.")

    @commands.command(aliases=["rf"], hidden=True)
    @perms.owners()
    async def receive_file(self, ctx, *, file):
        if ctx.author.id not in self.bot.admin_ids:
            return
        try:
            await ctx.message.attachments[0].save(file)
            await ctx.message.delete()
            await ctx.send("File Saved.")
        except:
            await ctx.send("No file found.")

def setup(bot):
    n = Owner(bot)
    bot.add_cog(n)
