# Priority: 1
import asyncio
import re
from datetime import datetime, timedelta

import discord
import utils.checks as perms
from discord.ext import commands, tasks


class OnlyFans(commands.Cog):
    """Automation module for my club"""
    def __init__(self, bot):
        self.bot = bot
        self.only_fans_verification.start()

    def cog_unload(self):
        self.only_fans_verification.cancel()

    @commands.Cog.listener("on_voice_state_update")
    async def voice_tracker(self, member, before, after):
        if member.guild.id != 890613748266586142:
            return
        channel = self.bot.get_channel(890613748266586145)
        if not before.channel and after.channel:
            await channel.send(f"{member.mention} joined {after.channel.mention}", allowed_mentions=discord.AllowedMentions.none())
        if before.channel and not after.channel:
            await channel.send(f"{member.mention} left {before.channel.mention}", allowed_mentions=discord.AllowedMentions.none())
        if before.channel and after.channel and before.channel != after.channel:
            await channel.send(f"{member.mention} moved from {before.channel.mention} to {after.channel.mention}", allowed_mentions=discord.AllowedMentions.none())

    @tasks.loop(seconds=60)
    async def only_fans_verification(self):
        guild = self.bot.get_guild(567505514108289044)
        if not guild:
            return
        role = guild.get_role(703314865032396901)
        if role:
            verified = await self.bot.db.db_profiles.find({"Bot Settings.Server": 0}).distinct("discord_id")
            for v in verified:
                m = guild.get_member(v)
                if m:
                    await self.bot.utils.give_roles(m, role)
            for m in guild.members:
                if m.id not in verified:
                    await self.bot.utils.take_roles(m, role)

    @commands.command(name="levi", hidden=True)
    @commands.cooldown(1, 180, commands.BucketType.default)
    async def __levi(self, ctx, levi=None):
        await ctx.message.delete()
        if not levi:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Usage: `>levi 10`", delete_after=10)
        regex = "(?i)^(?:u|uber)?(?: )?(8|9|10)$"
        result = re.findall(regex, levi)
        if not result or int(result[0]) not in [8, 9, 10]:
            ctx.command.reset_cooldown(ctx)
            return await ctx.send("Invalid uber", delete_after=10)
        else:
            levi = int(result[0])
        if levi == 10:
            role = 703319772128870560
        elif levi == 9:
            role = 814845443929800705
        elif levi == 8:
            role = 814845443904110622
        msg = None
        timer = 90
        while True:
            if not msg:
                msg = await ctx.send(f"<@&{role}> by {ctx.author.mention} | It will start in {self.bot.utils.time_str(timer)[1]}", delete_after=300)
            else:
                await msg.edit(content=f"<@&{role}> by {ctx.author.mention} | It will start in {self.bot.utils.time_str(timer)[1]}")
            timer -= 1
            await asyncio.sleep(1)
            if timer == 0:
                break
        await msg.edit(content=f"<@&{role}> by {ctx.author.mention}", delete_after=180)
        await msg.add_reaction("💀")
        try:
            def check(reaction, user):
                return user == ctx.author and reaction.message.id == msg.id and str(reaction.emoji) in ["💀"]
            await self.bot.wait_for("reaction_add", check=check, timeout=180)
            await msg.delete()
        except:
            pass

    @commands.command(hidden=True)
    @commands.cooldown(1, 180, commands.BucketType.default)
    async def ramp(self, ctx):
        if ctx.channel.id != 812762716908552272:
            return ctx.command.reset_cooldown(ctx)
        await ctx.message.delete()
        now = datetime.utcnow()
        if (now - timedelta(hours=11)).weekday() == 4 and ((19 > now.minute >= 0) or (49 > now.minute >= 30)):
            minute = 20 if now.minute < 20 else 50
            await ctx.send(f"<@&703319770233307166>", delete_after=(minute - now.minute) * 60 - now.second)
        elif 19 > now.minute >= 0:
            await ctx.send(f"<@&703319770233307166>", delete_after=(20 - now.minute) * 60 - now.second)
        else:
            ctx.command.reset_cooldown(ctx)

    @commands.command(aliases=["lo"], hidden=True)
    async def levi_odds(self, ctx):
        guild = self.bot.get_guild(567505514108289044)
        ch = guild.get_channel(813061157475713035)
        if ctx.channel == ch:
            return
        i = 0
        x = 0
        async for m in ch.history(limit=100):
            values = m.content.split("/")
            i += int(values[0])
            x += int(values[1].split(" ")[0])
        await ctx.send(f"{i}/{x} -> **{round(i/x*100, 3)}%**")

    @commands.command(hidden=True)
    @commands.cooldown(2, 600, commands.BucketType.default)
    @perms.admins()
    async def pts_status(self, ctx):
        ch = self.bot.get_channel(757953204863369271)
        if await ctx.locale("pts_status_if") in ch.name:
            await ch.edit(name=await ctx.locale("pts_status_off"))
        else:
            await ch.edit(name=await ctx.locale("pts_status_on"))
        await ctx.reply(await ctx.locale("pts_status_reply"))

def setup(bot):
    bot.add_cog(OnlyFans(bot))
