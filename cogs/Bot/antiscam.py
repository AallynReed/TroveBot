#Priority: 1
import re
from datetime import datetime, timedelta
from json import dumps

import discord
from discord.ext import commands
from utils.CustomObjects import CEmbed, TimeConverter


class ScamLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.domain_regex = r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]"

    @commands.group(slash_command=True, name="anti_scam", aliases=["antiscam"], help="Main command for antiscam.")
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def _anti_scam(self, _):
        ...

    @_anti_scam.command(slash_command=True, name="toggle", help="Turn antiscam on or off.")
    async def _toggle(self, ctx):
        server_data = await ctx.get_guild_data(anti_scam=1)
        value = server_data["anti_scam"]["settings"]["toggle"]
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.toggle": not value}})
        if value:
            return await ctx.reply("Antiscam links **disabled**.", ephemeral=True)
        else:
            return await ctx.reply("Antiscam links **enabled**.", ephemeral=True)

    @_anti_scam.command(slash_command=True, name="log_channel", help="Set a log channel for antiscam.")
    async def _set_log_channel(self, ctx, channel: discord.TextChannel=commands.Option(default=None, description="Set a log channel for antiscam.")):
        ch = channel.id if channel else channel
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.log_channel": ch}})
        if ch:
            return await ctx.reply(f"Set {channel.mention} as antiscam logging.", ephemeral=True)
        else:
            return await ctx.reply("No longer logging antiscam.", ephemeral=True)

    @_anti_scam.command(slash_command=True, name="mode", help="Set mode for antiscam punishments.")
    @commands.bot_has_permissions(moderate_members=True, ban_members=True)
    async def _set_mode(self, ctx, *, mode=commands.Option(description="-1 == Nothing | 0 == Ban | '1d 3h' -> Timeout")):
        if mode == "-1":
            await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.mode": -1}})
            await ctx.reply("Bot will just delete messages containing scam links.", ephemeral=True)
        elif mode == "0":
            await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.mode": 0}})
            await ctx.reply("Bot will delete messages containing scam links and ban senders.", ephemeral=True)
        elif (timeout := TimeConverter(mode).seconds) > 0:
            if timeout > 2419200:
                return await ctx.reply("You can't timeout for more than 28 days.", ephemeral=True)
            await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.mode": timeout}})
            await ctx.reply(f"Bot will delete messages containing scam links and timeout senders for **{TimeConverter(mode)}**.", ephemeral=True)
        else:
            await ctx.reply("Input is not valid, -1, 0 or a time range like '1 day 3 hours'")

    @_anti_scam.command(slash_command=True, name="stats", help="Show stats on antiscam.")
    async def _show_stats(self, ctx):
        server_data = await ctx.get_guild_data(anti_scam=1)
        e = CEmbed(color=ctx.guild.owner.color)
        e.set_author(name="Anti Scam", icon_url=ctx.guild.icon)
        hit_count = server_data["anti_scam"]["hit_count"]
        e.description = f"Anti Scam was triggered **{hit_count}** times.\n\n"
        e.description += "Top 10 Domains:\n"
        for domain, hits in sorted(server_data["anti_scam"]["domains"].items(), key=lambda x: (-x[1], x[0])):
            e.description += f"• **{hits}** > `{domain}`\n"
        await ctx.reply(embed=e, ephemeral=True)
            
    @commands.Cog.listener("on_message")
    async def _message_filter(self, message):
        if message.author.id == self.bot.user.id:
            return
        if not message.guild:
            return
        ctx = await self.bot.get_context(message)
        server_data = await ctx.get_guild_data(anti_scam=1)
        settings = server_data["anti_scam"]["settings"]
        if not settings["toggle"]:
            return
        results = re.findall(self.domain_regex, message.content, re.IGNORECASE)
        if results:
            self.bot.dispatch("link_post", settings, server_data["anti_scam"], message)

    @commands.Cog.listener("on_link_post")
    async def _scam_link_detector(self, settings, keys, message):
        req = await self.bot.AIOSession.post(
            "https://anti-fish.bitflow.dev/check", 
            data=dumps({"message": message.content}),
            headers={'content-type': 'application/json', "User-Agent": "Trove Bot (https://trove.slynx.xyz/)"}
        )
        if req.status != 200:
            return
        confirmed = []
        response = await req.json()
        for match in response["matches"]:
            if match["trust_rating"] >= 0.95:
                confirmed.append(match["domain"])
        if not confirmed:
            return
        for domain in list(set(confirmed)):
            if not keys["domains"].get(domain):
                keys["domains"][domain] = 0
            keys["domains"][domain] += 1
        await self.bot.db.db_servers.update_one({"_id": message.guild.id}, {"$inc": {"anti_scam.hit_count": 1}, "$set": {"anti_scam.domains": keys["domains"]}})
        await message.delete(silent=True)
        if settings["mode"] == -1:
            ...
        elif settings["mode"] == 0:
            try:
                await message.author.ban(reason="Sending scam links.")
            except:
                ...
        elif settings["mode"] > 0:
            try:
                await message.author.edit(timeout_until=message.created_at + timedelta(seconds=settings["mode"]), reason="Sending scam links.")
            except:
                ...
        channel = self.bot.get_channel(settings["log_channel"])
        e = discord.Embed(description="", color=0xff0000)
        e.timestamp = message.created_at
        e.set_author(name="Malicious domains detected")
        e.description += f"In `#{message.channel.name}`\nby {message.author.mention} | `{message.author}`\n"
        scam_domains = "\n".join(confirmed)
        e.description += f"```ansi\n{scam_domains or 'None'}\n```"
        elapsed = int((datetime.utcnow().timestamp() - e.timestamp.timestamp()) * 1000)
        e.add_field(name="Time elapsed", value=f"{elapsed}ms")
        await self.bot.get_channel(924623456291680296).send(embed=e)
        if not channel:
            #await message.channel.send(f"{message.author.mention} sent a scam link.\nEnable logs with `{(await self.bot.prefix(self.bot, message))[0]}anti_scam log_channel #Channel`", delete_after=15)
            return
        await channel.send(embed=e)

def setup(bot):
    bot.add_cog(ScamLogs(bot))
