# Priority: 1
import asyncio
from random import randint

import discord
from discord.ext import commands

from utils.CustomObjects import CEmbed


class CommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener("on_member_ban")
    async def blacklist_addition(self, guild, member):
        if self.bot.is_clone:
            return
        if guild.id != 834505270075457627:
            return
        e = CEmbed(description=f"{member} was added to blacklist.")
        e.set_footer(text=guild)
        e.set_author(name="Blacklist", icon_url=member.avatar)
        await self.bot.blacklist_logger.send(embed=e)

    @commands.Cog.listener("on_member_unban")
    async def blacklist_removal(self, guild, member):
        if self.bot.is_clone:
            return
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
        if message.author.bot or message.author.id in self.bot.owners:
            return
        await self.bot.wait_until_ready()
        ctx = await self.bot.get_context(message)
        if not ctx.guild:
            return self.bot.dispatch("dm_message", ctx, message)
        if self.bot.is_clone and ctx.guild.get_member(425403525661458432):
            return
        if ctx.valid and ctx.author.id in self.bot.blacklist:
            e = CEmbed(description=f"{ctx.author} tried to use a command `{ctx.message.content}`\n{ctx.message.jump_url}")
            e.set_footer(text=ctx.guild)
            e.set_author(name="Blacklist", icon_url=ctx.author.avatar)
            await self.bot.blacklist_logger.send(embed=e)
            try:
                await ctx.author.send(f"You've been banned from using bot :) You can appeal at <https://trove.slynx.xyz/appeal>\nThe server is not associated with the bot so do not complain there about a bot blacklist as it won't make a better case futurely in an appeal attempt.\nHere's your ID: `{ctx.author.id}`")
            except:
                ...
            return await ctx.send("An error occured!", delete_after=15)
        if message.content.lower() == "#pride":
            return self.bot.dispatch("giveaway_keyword", ctx)
        self.bot.dispatch("giveaway", ctx)
        if ctx.valid:
            await self.bot.process_commands(message)
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
            if len(ctx.message.mentions) == 1 and ctx.guild.me in ctx.message.mentions and not ctx.message.reference:
                prefix = await self.bot.prefix(bot=self.bot, message=message)
                return await ctx.send(f"Your prefix is `{prefix[2]}`\nUse `{prefix[2]}prefix self <prefix>` to change your prefix.", delete_after=12)

    @commands.Cog.listener("on_message_edit")
    async def command_edit_handler(self, before, message):
        if message.author.bot or message.author.id in self.bot.owners:
            return
        if before.content == message.content:
            return
        await self.bot.wait_until_ready()
        ctx = await self.bot.get_context(message)
        if not ctx.guild:
            return self.bot.dispatch("dm_message", ctx, message)
        if self.bot.is_clone and ctx.guild.get_member(425403525661458432):
            return
        if ctx.valid and ctx.author.id in self.bot.blacklist:
            e = CEmbed(description=f"{ctx.author} tried to use a command `{ctx.message.content}`\n{ctx.message.jump_url}")
            e.set_footer(text=ctx.guild)
            e.set_author(name="Blacklist", icon_url=ctx.author.avatar)
            await self.bot.blacklist_logger.send(embed=e)
            try:
                await ctx.author.send(f"You've been banned from using bot :) You can appeal at <https://trove.slynx.xyz/appeal>\nThe server is not associated with the bot so do not complain there about a bot blacklist as it won't make a better case futurely in an appeal attempt.\nHere's your ID: `{ctx.author.id}`")
            except:
                ...
            return await ctx.send("An error occured!", delete_after=15)
        if message.content.lower() == "#pride":
            return self.bot.dispatch("giveaway_keyword", ctx)
        if ctx.valid:
            await self.bot.process_commands(message)
        else:
            if len(ctx.message.mentions) == 1 and ctx.guild.me in ctx.message.mentions and not ctx.message.reference:
                prefix = await self.bot.prefix(bot=self.bot, message=message)
                return await ctx.send(f"Your prefix is `{prefix[2]}`\nUse `{prefix[2]}prefix self <prefix>` to change your prefix.")

    @commands.Cog.listener("on_dm_message")
    async def _dm_message(self, ctx, message):
        files = [await f.to_file() for f in message.attachments]
        await self.bot.dm_logger.send(
            content=message.content,
            files=files,
            username=str(message.author) + f" [{message.author.id}]",
            avatar_url=message.author.avatar,
            allowed_mentions=discord.AllowedMentions.none()
        )
        if ctx.valid:
            await ctx.send("Commands don't work in DM's please use them in a server.")
     
    @commands.Cog.listener("on_giveaway_keyword")
    async def _handle_giveaway_entry(self, ctx):
        return
        if ctx.author.id in self.bot.blacklist:
            return
        entries = (await self.bot.db.db_bot.find_one({"_id": "0511"}, {"giveaway": 1}))["giveaway"]
        if ctx.author.id in entries:
            return await ctx.send("You've already entered the giveaway.", delete_after=12)
        await ctx.send("You've entered the giveaway.", delete_after=12)
        entries.append(ctx.author.id)
        await self.bot.db.db_bot.update_one({"_id": "0511"}, {"$set":{"giveaway": entries}})
        await ctx.message.add_reaction("<:done:844624767217958922>")

    @commands.Cog.listener("on_giveaway")
    async def _giveaway_notice(self, ctx):
        return
        giveaway_notice = randint(0,20)
        if not giveaway_notice and ctx.guild.id == 836383545772998686:
            await ctx.send(f"A giveaway for `10 Million flux` is being hosted by **Events & Giveaways** community in their annual Pride Event to shine light on being different and being proud be being so, type `/pride2022` to learn more. https://i.imgur.com/wzZi8MZ.gif", delete_after=12)

    @commands.command(slash_command=True, help="Show information about the pride event giveaway from Events & Giveaways community")
    @commands.bot_has_permissions(embed_links=1)
    async def pride2022(self, ctx):
        return
        #return await ctx.reply("There's no giveaway currently going on.", delete_after=8)
        e = CEmbed()
        e.color = discord.Color.random()
        e.set_author(name="10 Million Flux Giveaway.", icon_url=self.bot.user.avatar)
        e.set_thumbnail(url="https://i.imgur.com/wzZi8MZ.gif")
        e.description = "Trove Events and Giveaways has given Trove Bot flux to be given away"
        e.description += "\n\n**To join the giveaway all you have to do is send the keyword**\n `#Pride`\n\n"
        e.description += "Only a few rules to enter the giveaway:\n"
        e.description += " -> You must share a server with the bot to join giveaway and use the provided keyword to join.\n"
        e.description += " -> Organizers must be able to DM you in case you win, otherwise it may be rerolled.\n"
        e.description += " -> You may only enter once the giveaway.\n\n"
        e.description += "This giveaway begins at <t:1655355600:F> and will end <t:1655614799:R>"
        e.description += "\n**2 winners** will be announced in [Events & Giveaways Server](https://discord.gg/mbkwsp4zHt) and winners will receive their rewards through DM's from one of the event organizers"
        e.description += "\n**IMPORTANT NOTE:** Make sure your DM's are accessible so that you can be DM'd, failing to answer may lead to the loss of this giveaway reward."
        entries = (await self.bot.db.db_bot.find_one({"_id": "0511"}, {"giveaway": 1}))["giveaway"]
        e.set_footer(text=f"{len(entries)} people have joined the giveaway.")
        await ctx.reply(embed=e, delete_after=300)

def setup(bot):
    bot.add_cog(CommandHandler(bot))
