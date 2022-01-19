# Priority: 1
import asyncio

from discord.ext import commands

from utils.CustomObjects import CEmbed


class CommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener("on_member_ban")
    async def blacklist_addition(self, guild, member):
        if guild.id != 834505270075457627:
            return
        e = CEmbed(description=f"{member} was added to blacklist.")
        e.set_footer(text=guild)
        e.set_author(name="Blacklist", icon_url=member.avatar)
        await self.bot.blacklist_logger.send(embed=e)

    @commands.Cog.listener("on_member_unban")
    async def blacklist_removal(self, guild, member):
        if guild.id != 834505270075457627:
            return
        await asyncio.sleep(300)
        try:
            await guild.fetch_ban(member)
        except:
            try:
                await member.send("You have been unbanned from using bot.")
            except:
                ...
            e = CEmbed(description=f"{member} was removed from blacklist.")
            e.set_footer(text=guild)
            e.set_author(name="Blacklist", icon_url=member.avatar)
            await self.bot.blacklist_logger.send(embed=e)

    @commands.Cog.listener("on_message")
    async def command_handler(self, message):
        if message.author.bot:
            return
        ctx = await self.bot.get_context(message)
        if not message.guild and message.author.id != self.bot.user.id:
            if ctx.valid:
                await ctx.send("Commands don't work in DM's please use them in a server.")
            files = [await f.to_file() for f in message.attachments]
            return await self.bot.dm_logger.send(content=message.content, files=files, username=str(message.author) + f" [{message.author.id}]", avatar_url=message.author.avatar)
        if not message.guild:
            return
        if "owners" not in dir(self.bot) or message.author.id in self.bot.owners:
            return
        if ctx.valid:
            ...
            # if ctx.guild.id == 118027756075220992:
            #     if ctx.command.name in ["search", "findmod"]:
            #         pass
            #     elif ctx.command.name in ["help", "build", "gear", "augment", "coeff", "invite", "communities"] and ctx.channel.id in [776238026921082911]:
            #         pass
            #     elif ctx.command.name in ["reportbug"] and ctx.channel.id in [832582272011599902]:
            #         pass
            #     else:
            #         return
        else:
            if ctx.channel.id == 832582272011599902 and not [r.id for r in ctx.author.roles if r.id in [533024164039098371, 125277653199618048,841729071854911568]]:
                try:
                    await asyncio.sleep(2)
                    await ctx.channel.fetch_message(ctx.message.id)
                    prefix = await self.bot.prefix(self.bot, ctx.message)
                    await ctx.channel.send(f"{ctx.author.mention} you aren't allowed to talk or discuss here. You may only report bugs using `{prefix[0]}bugreport`", delete_after=15) # Send Warning
                    await asyncio.sleep(15)
                    await ctx.message.delete()
                except:
                    return
                return
            else:
                pass
        if not ctx.valid and len(ctx.message.mentions) == 1 and ctx.guild.me in ctx.message.mentions and not ctx.message.reference:
            prefix = await self.bot.prefix(bot=self.bot, message=message)
            return await ctx.send(f"Your prefix is `{prefix[0]}`\nUse `{prefix[0]}prefix self <prefix>` to change your prefix.")
        if ctx.valid:
            if message.author.id in self.bot.blacklist:
                e = CEmbed(description=f"{ctx.author} tried to use a command `{message.content}`\n{ctx.message.jump_url}")
                e.set_footer(text=ctx.guild)
                e.set_author(name="Blacklist", icon_url=ctx.author.avatar)
                await self.bot.blacklist_logger.send(embed=e)
                try:
                    await ctx.author.send(f"You've been banned from using bot :) You can appeal at <https://trove.slynx.xyz/appeal>\nThe server is not associated with the bot so do not complain there about a bot blacklist as it won't make a better case futurely in an appeal attempt.\nHere's your ID: `{ctx.author.id}`")
                except:
                    ...
                return await ctx.send("An error occured!", delete_after=15)
            commands = (await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"commands": 1}))["commands"]
            if not self.can_use_command(ctx, commands):
                return
            # giveaway_notice = randint(0,5)
            # if not giveaway_notice and message.guild.id != 118027756075220992:
            #     await ctx.send(f"A giveaway for the ally `Action Pan` (Dev ally inspired on Dan aka Pantong) is being hosted by Trove bot, type `{ctx.prefix}giveaway` to learn more. https://i.imgur.com/9tcPuUu.png", delete_after=90)
            await self.bot.process_commands(message)
        # elif message.content.lower() == "devally":
        #     if message.author.id in self.bot.blacklist:
        #         return
        #     entries = (await self.bot.db.db_bot.find_one({"_id": "0511"}, {"giveaway": 1}))["giveaway"]
        #     if message.author.id in entries:
        #         return await message.author.send("You've already entered the giveaway.", delete_after=12)
        #     try:
        #         await message.author.send("You've entered the giveaway.")
        #     except:
        #         return await ctx.send(f"I can't DM {message.author.mention}, being able to DM you is a requirement.\nOtherwise it will be immediatly rerolled.", delete_after=20)
        #     entries.append(message.author.id)
        #     await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"giveaway": entries}})
        #     await message.add_reaction("<:done:844624767217958922>")

    @commands.Cog.listener("on_message_edit")
    async def command_edit_handler(self, before, after):
        if after.author.bot:
            return
        #if "owners" not in dir(self.bot) or message.author.id in self.bot.owners:
        #    return
        ctx = await self.bot.get_context(after)
        if ctx.valid:
            ...
            # if ctx.guild.id == 118027756075220992:
            #     if ctx.command.name in ["search", "findmod"]:
            #         pass
            #     elif ctx.command.name in ["help", "build", "gear", "augment", "coeff", "invite", "communities"] and ctx.channel.id in [776238026921082911]:
            #         pass
            #     elif ctx.command.name in ["reportbug"] and ctx.channel.id in [832582272011599902]:
            #         pass
            #     else:
            #         return
        if not ctx.valid and len(ctx.message.mentions) == 1 and ctx.guild.me in ctx.message.mentions:
            prefix = await self.bot.prefix(bot=self.bot, message=after)
            return await ctx.send(f"Your prefix is `{prefix[0]}`\nUse `{prefix[0]}prefix self <prefix>` to change your prefix.")
        if ctx.valid and before.content != after.content:
            if ctx.author.id in self.bot.blacklist:
                e = CEmbed(description=f"{ctx.author} tried to use a command `{after.content}`")
                e.set_author(name="Blacklist", icon_url=ctx.author.avatar)
                await self.bot.blacklist_logger.send(embed=e)
                try:
                    ...
                    await ctx.author.send(f"You've been banned from using bot :) You can appeal at <https://trove.slynx.xyz/appeal>\nHere's your ID: `{ctx.author.id}`")
                except:
                    ...
                return await ctx.send("An error occured!", delete_after=15)
            commands = (await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"commands": 1}))["commands"]
            if not self.can_use_command(ctx, commands):
                return
            await self.bot.process_commands(after)

    def can_use_command(self, ctx, settings):
        return True

def setup(bot):
    bot.add_cog(CommandHandler(bot))
