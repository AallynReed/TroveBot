# Priority: 1
import re
from datetime import datetime
from json import loads, dumps

import discord
from discord.ext import commands, tasks
from utils.CustomObjects import Colorize


class ScamLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url_regex = r"https?:\/\/(?:www\.)?([-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6})\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)"
        self.domain_regex = r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]"
        self.scam_links_cache = []
        self.scam_databases = {
            "json": [
                "https://raw.githubusercontent.com/nikolaischunk/discord-phishing-links/main/domain-list.json"
            ],
            "txt": [
                "https://raw.githubusercontent.com/BuildBot42/discord-scam-links/main/list.txt",
                "https://raw.githubusercontent.com/0x4Hydro/SteamNitroPhishingLinks/main/Steam-Nitro_URLs",
                "https://raw.githubusercontent.com/DevSpen/scam-links/master/src/links.txt",
                "https://raw.githubusercontent.com/Discord-AntiScam/scam-links/main/list.txt"
            ],
            "list": [
                "https://api.hyperphish.com/gimme-domains"
            ]
            
        }
        #self._update_scam_links_cache.start()

    def cog_unload(self):
        ...
        #self._update_scam_links_cache.cancel()

    @commands.command()
    async def scam_db_size(self, ctx):
        await ctx.reply(f"There are **{len(self.scam_links_cache)}** scam links cached")

    @tasks.loop(seconds=600)
    async def _update_scam_links_cache(self):
        for t in self.scam_databases.keys():
            for url in self.scam_databases[t]:
                request = await self.bot.AIOSession.get(url)
                if request.status == 200:
                    text = await request.text()
                    if t == "txt":
                        cache_update = [s.strip() for s in text.split("\n")]
                    elif t == "json":
                        raw_data = loads(text)
                        cache_update = raw_data["domains"]
                    elif t == "list":
                        cache_update = loads(text)
                    for domain in cache_update:
                        if domain not in self.scam_links_cache:
                            self.scam_links_cache.append(domain)
        for domain in self.scam_links_cache:
            if domain in [
                "iscord.gift",
                "discordapp.co"
            ]:
                self.scam_links_cache.remove(domain)

    @commands.Cog.listener("on_message")
    async def _message_filter(self, message):
        if message.author.id == self.bot.user.id:
            return
        if not message.guild:
            return
        results = re.findall(self.domain_regex, message.content, re.IGNORECASE)
        if results:
            self.bot.dispatch("link_post", message)

    @commands.Cog.listener("on_link_post")
    async def _scam_link_detector(self, message):
        channel = self.bot.get_channel(924623456291680296)
        req = await self.bot.AIOSession.post(
            "https://anti-fish.bitflow.dev/check", 
            data=dumps({"message": message.content}),
            headers={'content-type': 'application/json', "User-Agent": "Trove Bot (https://slynx.xyz/trove)"}
        )
        if req.status != 200:
            return
        confirmed = []
        # unknown = []
        # for domain in domains:
        #     if domain in unknown:
        #         continue
        #     for scam_domain in self.scam_links_cache:
        #         if scam_domain in domain:
        #             if domain in confirmed.keys():
        #                 continue
        #             confirmed[domain] = scam_domain
        #     if domain not in confirmed.keys():
        #         unknown.append(domain)
        response = await req.json()
        for match in response["matches"]:
            if match["trust_rating"] == 1:
                confirmed.append(match["domain"])
        e = discord.Embed(description="", color=0x00ffff)
        e.set_author(name="Malicious domains detected")
        e.description += f"**{message.guild.name}** in `#{message.channel.name}`\n"
        scam_domains = "\n".join([f"§$1<%{domain}%>" for domain in confirmed])
        # other_domains = "\n".join([f"§$2<%{domain}%>" for domain in unknown])
        e.description += f"```ansi\n{scam_domains or 'None'}\n```"
        # e.description += f"\n**Other Domains**```ansi\n{other_domains or ' '}\n```"
        e.description = str(Colorize(e.description))
        elapsed = int((datetime.utcnow().timestamp() - message.created_at.timestamp()) * 1000)
        e.add_field(name="Time elapsed", value=f"{elapsed}ms")
        await channel.send(embed=e)
        if confirmed:
            await message.delete(silent=True)

def setup(bot):
    bot.add_cog(ScamLogs(bot))
