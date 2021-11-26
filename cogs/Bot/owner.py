# Priority: 9
import io
import os
from datetime import datetime

import chat_exporter
import discord
import hjson
from discord.ext import commands
from discord.utils import find

import utils.checks as perms
from utils.modules import get_loaded_modules

wrap = "```py\n{}\n```"

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @perms.owners()
    async def export_chat(self, ctx, limit=100):
        transcript = await chat_exporter.export(ctx.channel, limit)

        if transcript is None:
            return await ctx.reply("There are no messages.")

        _file = discord.File(io.BytesIO(transcript.encode()),
                                    filename=f"transcript-{ctx.channel.name}.html")
        
        await ctx.reply(file=_file)        

    @commands.command()
    @perms.owners()
    async def relocale(self, ctx):
        self.bot._load_locales()
        await ctx.send("Reloaded languages.")

    @commands.command()
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

    @commands.command()
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

    @commands.command()
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

    @commands.command()
    @perms.admins()
    async def restart(self, ctx):
        if ctx.author.id == 565097923025567755:
            await ctx.send("Restarting!")
            await self.bot.change_presence(status=discord.Status.offline)
            os._exit(-1)

    @commands.command()
    @perms.admins()
    async def restartweb(self, ctx):
        if ctx.author.id == 565097923025567755:
            await ctx.send("Restarting website!")
            os.system("screen -XS slynxweb quit")

    @commands.command()
    @perms.admins()
    async def reload_values(self, ctx):
        self.bot.Trove.values._preload(True)
        await ctx.send("Reloaded values")

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
            code = ctx.message.content[8:]
            code = "    " + code.replace("\n", "\n    ")
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
            except Exception as e:
                embed = discord.Embed(description=str(e), colour=self.bot.error)
                await ctx.send(embed=embed)

    @commands.command(name="exception", aliases=["error", "lasterror"])
    @perms.admins()
    async def last_exception(self, ctx):
        if ctx.author.id not in self.bot.admin_ids:
            return
        if self.bot._last_exception:
            if len(self.bot._last_exception) > 2000:
                await ctx.author.send(f"```py\n{self.bot._last_exception[:1990]}```")
                await ctx.author.send(f"```py\n{self.bot._last_exception[1990:3980]}```")
            else:
                await ctx.author.send(f"```py\n{self.bot._last_exception}```")
            await ctx.message.add_reaction("✅")

    @commands.command(aliases=["modules", "mods"])
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
        embed=discord.Embed(colour=self.bot.comment, title=f"Modules - {len(modules)}", description=modulesi)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["ul"])
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
            if module.name.lower() == "owner":
                return await ctx.reply("Can't unload that module.")
            if module not in loaded:
                return await ctx.reply(f"**{module.name}** not loaded.")
            self.bot.unload_extension(module.load)
            await ctx.reply(f"Unloaded **{module.name}**")

    @commands.command(aliases=["load"])
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
            try:
                if module in loaded:
                    self.bot.reload_extension(module.load)
                    await ctx.reply(f"Successfully reloaded {module.name}")
                else:
                    self.bot.load_extension(module.load)
                    await ctx.reply(f"Successfully loaded {module.name}")
            except Exception as e:
                await ctx.reply(f"```py\n#Failed to reload {module.name}\n\n{str(type(e))}: {e}```")

    @commands.command(aliases=["sf"])
    @perms.owners()
    async def send_file(self, ctx, *, file):
        if ctx.author.id not in self.bot.admin_ids:
            return
        try:
            await ctx.author.send(file=discord.File(file))
            await ctx.message.add_reaction("✅")
        except:
            await ctx.send("No file found.")

    @commands.command(aliases=["rf"])
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
