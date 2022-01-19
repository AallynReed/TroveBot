# Priority: 1
import re
from json import loads

import discord
from discord.ext import commands, tasks


class ScamLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = r"https?:\/\/(?:www\.)?([-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
        self.scam_links_cache = []
        self.scam_database = "https://raw.githubusercontent.com/nikolaischunk/discord-phishing-links/main/domain-list.json"
        self._update_scam_links_cache.start()

    def cog_unload(self):
        self._update_scam_links_cache.cancel()

    @tasks.loop(seconds=600)
    async def _update_scam_links_cache(self):
        request = await self.bot.AIOSession.get(self.scam_database)
        if request.status == 200:
            raw_data = loads(await request.text())
            cache_update = raw_data["domains"]
            for domain in cache_update:
                if domain not in self.scam_links_cache:
                    self.scam_links_cache.append(domain)

    @commands.Cog.listener("on_message")
    async def _message_filter(self, message):
        if not message.guild:
            return
        if message.guild.id not in [118027756075220992]:
            return
        results = re.findall(self.url_regex, message.content)
        if results:
            self.bot.dispatch("link_post", results)

    @commands.Cog.listener("on_link_post")
    async def _scam_link_detector(self, domains):
        channel = self.bot.get_channel(924623456291680296)
        confirmed = {}
        unknown = []
        for domain in domains:
            if domain in unknown:
                continue
            for scam_domain in self.scam_links_cache:
                if scam_domain in domain:
                    if domain in confirmed.keys():
                        continue
                    confirmed[domain] = scam_domain
            if domain not in confirmed.keys():
                unknown.append(domain)
        e = discord.Embed(description="```\n", color=0xff0000)
        e.set_author(name="Scam domains detected")
        scam_domains = "\n".join(confirmed.values())
        await channel.send(scam_domains)
        e.description += scam_domains+"`"*3
        await channel.send(embed=e)
        e = discord.Embed(description="```\n", color=0x00ffff)
        e.set_author(name="Other domains detected")
        other_domains = "\n".join(unknown)
        e.description += other_domains+"`"*3
        await channel.send(embed=e)

def setup(bot):
    bot.add_cog(ScamLogs(bot))
