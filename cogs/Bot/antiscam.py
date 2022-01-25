#Priority: 1
import re
from copy import copy
from datetime import datetime, timedelta
from json import dumps

import discord
from discord.ext import commands

from utils.CustomObjects import CEmbed, Colorize, TimeConverter


class ScamLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.domain_regex = r"(?:[a-z0-9](?:[a-z0-9-]{0,63}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,63}[a-z0-9]"

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
        try:
            timeout = TimeConverter(mode)
        except:
            return await ctx.reply("Input is not valid, -1, 0 or a time range like '1 day 3 hours'")
        if not (0 < int(timeout) <= 2419200):
            return await ctx.reply("Timeout range is 1 seconds - 28 days.", ephemeral=True)
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"anti_scam.settings.mode": int(timeout)}})
        await ctx.reply(f"Bot will delete messages containing scam links and timeout senders for **{timeout}**.", ephemeral=True)

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

    @_anti_scam.command(slash_command=True, name="blacklist", help="Blacklist a custom domain in your server.")
    async def _toggle_blacklist(self, ctx, *, domain=commands.Option(description="")):
        domains = re.findall(self.domain_regex, domain, re.IGNORECASE)
        if not domains:
            return await ctx.send("Add a valid URL or Domain Name", ephemeral=True)
        server_data = await ctx.get_guild_data(anti_scam=1)
        custom_domains = server_data["anti_scam"]["settings"]["custom_domains"]
        removed = []
        for domain in domains:
            for custom_domain in copy(custom_domains):
                if domain == custom_domain:
                    custom_domains.remove(domain)
                    removed.append(domain)
        replaced = {}
        for domain in domains:
            for custom_domain in copy(custom_domains):
                if self.match_domain(custom_domain, domain):
                    custom_domains.remove(custom_domain)
                    custom_domains.append(domain)
                    replaced[custom_domain] = domain
        added = []
        for domain in domains:
            if domain in removed:
                continue
            custom_domains.append(domain)
            added.append(domain)
        e = CEmbed(color=discord.Color.random())
        e.set_author(name="Custom Domains Blacklist", icon_url=ctx.guild.icon)
        e.description = "```ansi\n"
        max_added = 0 if not added else max([len(d) for d in added])-5
        max_removed = 0 if not removed else max([len(d) for d in removed])-7
        max_replaced = 0 if not replaced.items() else max([len(d+c) for c, d in replaced.items()])-5
        e.description += f"§$2<%Added%>{max_added*' '} | §$1<%Removed%>{max_removed*' '} | §$3<%Replaced%>{max_replaced*' '}"
        for i in range(max([len(added), len(removed), len(replaced.items())])):
            add = (added[i] if len(added) >= i+1 else "").ljust(max_added+5)
            remove = (removed[i] if len(removed) >= i+1 else "").ljust(max_removed+7)
            replacement = replaced.items()[i] if len(replaced.items()) >= i+1 else ""
            if replacement:
                replace = f"{replacement[0]} > {replacement[1]}".ljust(max_replaced+5)
            else:
                replace = "".ljust(max_replaced+8)
            e.description += f"\n§$2<%{add}%> | §$1<%{remove}%> | §$3<%{replace}%>"
        e.description = str(Colorize(e.description+"\n```"))
        await ctx.reply(embed=e)

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
            self.bot.dispatch("link_post", settings, server_data["anti_scam"], message, results)

    @commands.Cog.listener("on_message_edit")
    async def _message_edit_filter(self, _, message):
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
            self.bot.dispatch("link_post", settings, server_data["anti_scam"], message, results)

    async def check_databases(self, domains):
        data = self.bot.db.db_servers.find({}, {"anti_scam": 1})
        async for server in data:
            custom = server["anti_scam"]["settings"]["custom_domains"]
            for custom_domain in custom:
                for domain in domains:
                    if not self.match_domain(custom_domain, domain):
                        continue
                    await self.bot.db.db_servers.update_one({"_id": server["_id"]}, {"$pull": {"anti_scam.settings.custom_domains": custom_domain}})

    @commands.Cog.listener("on_link_post")
    async def _scam_link_detector(self, settings, keys, message, matches):
        req = await self.bot.AIOSession.post(
            "https://anti-fish.bitflow.dev/check", 
            data=dumps({"message": message.content}),
            headers={'content-type': 'application/json', "User-Agent": "Trove Bot (https://trove.slynx.xyz/)"}
        )
        confirmed = []
        api_confirmed = []
        if req.status == 200:
            response = await req.json()
            for match in response["matches"]:
                if match["trust_rating"] >= 0.95:
                    confirmed.append(match["domain"])
                    api_confirmed.append(match["domain"])
        for match in matches:
            for custom_domain in settings["custom_domains"]:
                if self.match_domain(match, custom_domain):
                    confirmed.append(custom_domain)
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
        await self.bot.get_channel(924623456291680296).send(content=f"Server: **{message.guild.name}**", embed=e)
        if not channel:
            #await message.channel.send(f"{message.author.mention} sent a scam link.\nEnable logs with `{(await self.bot.prefix(self.bot, message))[0]}anti_scam log_channel #Channel`", delete_after=15)
            return
        await channel.send(embed=e)
        await self.check_databases(api_confirmed)

    def match_domain(self, domain, match):
        domain = domain.split(".")
        match = match.split(".")
        diff = len(domain) - len(match)
        return domain[diff:] == match

def setup(bot):
    bot.add_cog(ScamLogs(bot))
