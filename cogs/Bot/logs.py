# Priority: 1
import traceback
from datetime import datetime

import discord
import magic
from discord.ext import commands
from utils.buttons import Traceback


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_guild_join")
    async def guild_join(self, guild):
        await self.bot.db.database_check(guild.id)
        server = guild
        e=discord.Embed(description="{} is in {:,} servers and connected to {:,} users.".format(self.bot.user.name, len(self.bot.guilds), len(self.bot.users)), colour=0x00aa00, timestamp=datetime.utcnow())
        e.set_author(name="Joined a server!", icon_url=self.bot.user.avatar)
        e.add_field(name="Server Name", value=server.name, inline=False)
        e.add_field(name="Server ID", value=server.id, inline=False)
        e.add_field(name="Server Owner", value="{}\n{}".format(server.owner, server.owner.id), inline=False)
        e.add_field(name="Total members", value="{} members".format(len(server.members)), inline=False)
        mutual = list(map(lambda x: x.name, sorted([x for x in self.bot.guilds if server.owner in x.members and x != server], key=lambda x: x.member_count, reverse=True)))
        if len(mutual) > 15:
            e.add_field(name="Mutual Servers (Owner)", value="\n".join(mutual[:15]) + "\n and {} more...".format(len(mutual)-15), inline=False)
        else:
            e.add_field(name="Mutual Servers (Owner)", value="\n".join(mutual) if len(mutual) != 0 else "None", inline=False)
        if server.icon:
            e.set_thumbnail(url=server.icon)
        else:
            e.set_thumbnail(url="https://cdn.discordapp.com/attachments/344091594972069888/396285725605363712/no_server_icon.png")
        await self.bot.guild_logger.send(embed=e, username="Server Logs", avatar_url=self.bot.user.avatar)
        if not server.chunked:
            await server.chunk()
            server = self.bot.get_guild(server.id)
        dm = guild.owner
        try:
            async for log in server.audit_logs(limit=10, action=discord.AuditLogAction.bot_add):
                if log.target == self.bot.user:
                    dm = log.user
                    break
        except:
            ...
        if len([m for m in server.members if not m.bot]) < 10 and server.owner.id not in self.bot.owners:
            try:
                await dm.send("Unfortunately I am unable to join your server, 10 members (non bots) are required for me to join.\nThis is due to Discord limiting bot to 100 servers, and me wainting bot to reach as many people as possible whilst not losing access to important data it relies on to work properly such as knowing what is in your message content to know whether you used or not a command and which one you used.\n\nApologies for the inconvenience.")
            except:
                ...
        elif 620784025518473226 in [m.id for m in guild.bots]:
            try:
                await dm.send("Unfortunately <@620784025518473226> `TEA` bot is in your server, since I don't support naming and shaming of people who've broke ToS (which doing so is also breaking ToS) I also don't support Surge's crusade to shame people, thus Trove bot will not join a server that has TEA bot in it. You can participate in TEA which is a great concept (on paper) but sadly making a bot to blacklist and exclude people is where I draw the line, and change as to start somewhere.\nApologies and if you want to discuss about this matter privately feel free to do so by hitting me up in trove's support server where I'll create a channel for you 🙂")
            except:
                ...
        else:
            return
        await guild.leave()

    @commands.Cog.listener("on_guild_remove")
    async def guild_leave(self, guild):
        server = guild
        e=discord.Embed(description="{} is in {:,} servers and connected to {:,} users.".format(self.bot.user.name, len(self.bot.guilds), len(self.bot.users)), colour=0xaa0000, timestamp=datetime.utcnow())
        e.set_author(name="Left a server!", icon_url=self.bot.user.avatar)
        e.add_field(name="Server Name", value=server.name, inline=False)
        e.add_field(name="Server ID", value=server.id, inline=False)
        e.add_field(name="Server Owner", value="{}\n{}".format(server.owner, server.owner.id), inline=False)
        e.add_field(name="Total members", value="{} members".format(len(server.members)), inline=False)
        try:
            time_stayed_x = datetime.utcnow() - server.me.joined_at
            time_stayed = time_stayed_x.total_seconds()
            e.add_field(name="Stayed For", value=self.bot.utils.time_str(time_stayed, False)[1], inline=False)
        except:
            pass
        if server.icon:
            e.set_thumbnail(url=server.icon)
        else:
            e.set_thumbnail(url="https://cdn.discordapp.com/attachments/344091594972069888/396285725605363712/no_server_icon.png")
        await self.bot.guild_logger.send(embed=e, username="Server Logs", avatar_url=self.bot.user.avatar)

    @commands.Cog.listener("on_command_error")
    async def error_handler(self, ctx, error, *args, **kwargs):
        channel = ctx.channel
        prefix = ctx.prefix
        if isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(f"I require `{'`, `'.join(error.missing_permissions)}` to execute the command.")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You are missing permissions to use this command.", delete_after=10)#, ephemeral=True)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("You cannot use bot commands in direct messages.", delete_after=10)#, ephemeral=True)
        elif isinstance(error, commands.DisabledCommand):
            extra = ""
            if ctx.command.slash_command and (ctx.command.slash_command_guilds is None or ctx.guild.id in ctx.command.slash_command_guilds):
                extra += "\nUse slash command version instead"
            await ctx.send(f"**{ctx.command}** is currently disabled!" + extra, delete_after=10)#, ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.command.name == "reportbug":
                try:
                    await ctx.message.delete()
                except:
                    pass
                return await channel.send("This command is already in use. Please wait a moment before you report your bug.", delete_after=15)
            else:
                m, s = divmod(error.retry_after, 60)
                h, m = divmod(m, 60)
                if h == 0:
                    time = "%d minutes %d seconds" % (m, s)
                elif h == 0 and m == 0:
                    time = "%d seconds" % (s)
                else:
                    time = "%d hours %d minutes %d seconds" % (h, m, s)
                return await channel.send("This command is on cooldown! Try again in {}".format(time), delete_after=10)
        elif isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            command_name = str(ctx.command)
            subcommands = command_name.split(" ")
            if subcommands:
                command_db  = await self.bot.db.db_help.find_one({"_id": subcommands[0]})
            else:
                command_db  = await self.bot.db.db_help.find_one({"_id": command_name})
            if not command_db:
                e = discord.Embed()
                e.description = "That's not the correct usage for that command, but it seems the developer forgot to make a help entry for this one, contact `Sly#0511`"
                return await ctx.send(embed=e)
            if len(subcommands) == 1:
                command_name = self.bot.all_commands[subcommands[0]]
                command_path = command_db
                description = command_path["description"]
                subcommands = list(command_path["subcommands"])
                example =  command_path["example"].replace("{prefix}", prefix).replace("\n", "`\n`")
            elif len(subcommands) == 2:
                command_name = self.bot.all_commands[subcommands[0]].all_commands[subcommands[1]]
                command_path = command_db["subcommands"][subcommands[1]]
                description = command_path["description"]
                example = command_path["example"].replace("{prefix}", prefix).replace("\n", "`\n`")
            elif len(subcommands) == 3:
                command_name = self.bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]]
                command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]
                description = command_path["description"]
                example = command_path["example"].replace("{prefix}", prefix).replace("\n", "`\n`")
            elif len(subcommands) == 4:
                command_name = self.bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]].all_commands[subcommands[3]]
                command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]["subcommands"][subcommands[3]]
                description = command_path["description"]
                example = command_path["example"].replace("{prefix}", prefix).replace("\n", "`\n`")
            embed=discord.Embed(title=str(command_name).capitalize(), colour=discord.Color.random())
            embed.add_field(name="Description", value=description, inline=False)
            if command_name.usage:
                embed.add_field(name="Usage", value=command_name.usage, inline=False)
            embed.add_field(name="Example", value=f'`{example}`', inline=False)
            if command_path["aliases"]:
                embed.add_field(name="Aliases", value=", ".join(command_path["aliases"]), inline=False)
            if "extra_text" in command_path:
                embed.add_field(name="More Info", value=command_path["extra_text"])
            if "subcommands" in command_path and command_path["subcommands"]:
                embed.add_field(name="Subcommands", value=", ".join(list(command_path["subcommands"])), inline=False)
            try:
                await ctx.message.delete()
            except:
                pass
            await ctx.send(embed=embed, delete_after=120)
        elif isinstance(error, commands.CommandNotFound):
            pass
        elif isinstance(error, commands.CommandInvokeError):
            message = "Error in command **{}** - **({})**.\n```Error: {}```\nCheck console for more details.".format(
                ctx.command.qualified_name, ctx.command.cog_name, error
            )
            exception_log = "Exception in command '{}' - {}\n" "".format(ctx.command.qualified_name, ctx.command.cog_name)
            exception_log += "".join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot._last_exception = exception_log
            tb = None
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.send(f"I am missing permissions to complete this command, please use `{ctx.prefix}debug {ctx.channel.id}`")
            else:
                try:
                    tb = Traceback(ctx, exception_log)
                    msg = await ctx.send(f"An error occured.", view=tb)
                except:
                    pass
            #print("".join(traceback.format_exception(type(error), error, error.__traceback__)))
            c=discord.Embed(description=str(error), colour=0x080808)
            c.set_author(name="Errors")
            c.add_field(name="Server", value=ctx.message.guild, inline=False)
            c.add_field(name="Command", value=ctx.command, inline=False)
            c.add_field(name="Author", value=ctx.author, inline=False)
            c.add_field(name="Date", value=datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S"), inline=False)
            if ctx.author.id != 565097923025567755:
                await self.bot.error_logger.send(embed=c, username="Error Logs")
            if tb:
                await tb.wait()
                await msg.edit(view=None)

    @commands.Cog.listener("on_command")
    async def command_logger(self, ctx, *args, **kwargs):
        # if not ctx.guild:
        #     return
        # bot_info = await self.bot.db.db_bot.find_one({"_id": "0511"}, {"commands_usage": 1})
        # if str(ctx.command) not in bot_info["commands_usage"]:
        #     bot_info["commands_usage"][str(ctx.command)]= {}
        #     bot_info["commands_usage"][str(ctx.command)]["times_used"] = 0
        #     bot_info["commands_usage"][str(ctx.command)]["users"] = []
        #     bot_info["commands_usage"][str(ctx.command)]["servers"] = []

        # bot_info["commands_usage"][str(ctx.command)]["times_used"] +=1
        # if ctx.author.id not in bot_info["commands_usage"][str(ctx.command)]["users"]:
        #     bot_info["commands_usage"][str(ctx.command)]["users"].append(ctx.author.id)
        # if ctx.guild.id not in bot_info["commands_usage"][str(ctx.command)]["servers"]:
        #     bot_info["commands_usage"][str(ctx.command)]["servers"].append(ctx.guild.id)

        # await self.bot.db.db_bot.update_one(
        #     {"_id": "0511"},
        #     {"$set": {"commands_usage": bot_info["commands_usage"]},
        #     "$inc": {"stats.commands_used": 1}}, upsert=True)
        if ctx.author.id != 565097923025567755:
            await self.command_logging(ctx, kwargs)
        if not ctx.command_failed and ctx.invoked_subcommand is None and isinstance(ctx.command, commands.core.Group) and str(ctx.command) not in ["ptsprofile", "profile", "debug", "prefix"]:
            e = await self.bot.utils.get_subcommand_help(ctx, self.bot)
            await ctx.send(embed=e)

    async def command_logging(self, ctx, kwargs):
        try:
            prefix = ctx.prefix if not ctx.interaction else "/"
            embed1 = discord.Embed(title="Command Executed!", url=ctx.message.jump_url, colour=ctx.guild.owner.color, timestamp=datetime.utcnow())
            embed1.set_author(name=f"{ctx.guild.name} [{ctx.guild.id}]", icon_url=self.bot.user.avatar)
            if ctx.guild.icon:
                embed1.set_thumbnail(url=ctx.guild.icon)
            embed1.set_footer(text=f"Member Count: {ctx.guild.member_count}")
            embed1.add_field(name="Channel", value="Channel Name: `#{}`\nChannel ID: `{}`".format(ctx.channel.name, str(ctx.channel.id)), inline=False)
            embed1.add_field(name="Author", value="Author: `@{}`\nAuthor ID: `{}`".format(ctx.author, ctx.author.id), inline=False)
            embed1.add_field(name="Command", value="Prefix: {}\nCommand: {}\nArgs: {}".format(prefix, ctx.command, kwargs), inline=False)
            embed1.add_field(name="Message", value="Message Id: `{}`\nMessage Content: `{}`".format(ctx.message.id, str(ctx.message.content)), inline=False)
            attachments = ""
            image_types = ["image/jpeg", "image/png", "image/gif"]
            embeds = []
            if ctx.message.attachments:
                for attach in ctx.message.attachments:
                    file_type = magic.from_buffer(await attach.read(), mime=True)
                    if file_type in image_types:
                        if embed1.image.url == discord.Embed.Empty:
                            embed1.set_image(url=attach.url)
                            continue
                        embed = discord.Embed(url=ctx.message.jump_url)
                        embed.set_image(url=attach.url)
                        embeds.append(embed)
                    else:
                        attachments += f"{attach.url}\n"
                embed1.add_field(name="Attachments", value="\u200b" + attachments, inline=False)
            logger = self.bot.slash_commands_logger if ctx.interaction else self.bot.commands_logger
            await logger.send(embeds=[embed1] + embeds, username="Command Logs")
        except:
            pass

def setup(bot):
    bot.add_cog(Logs(bot))
