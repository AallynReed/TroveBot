# Priority: 1
from datetime import datetime
from random import choices
from string import ascii_letters, digits

import discord
from discord.ext import commands
from json import dumps


class BuildCodes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def GenerateCode(self, length):
        return "".join(choices(ascii_letters+digits, k=length))

    @commands.command()
    async def build_code(self, ctx):
        config = {'_class': 'Chloromancer', 'build_type': 'farm', 'build': ((0, 9), (11, 7), (3, 0, 0), (1, 3, 2)), 'subclass': 'Dino Tamer', 'primordial': False, 'crystal5': False, 'light': 8000, 'cd_count': 0, 'deface': False, 'ally': {'name': 'Orchian', 'type': 'farm', 'damage': 'MD', 'stats': {'Damage': 25, 'Light': 400}}, 'mod': False, 'bardcd': False, 'food': True, 'filter': None}
        time = int(datetime.utcnow().timestamp())
        data = {
            "code":         self.GenerateCode(16),
            "creator":      ctx.author.id,
            "name":         None,
            "alias":        None,
            "description":  None,
            "created_at":   time,
            "last_updated": time,
            "config":       config
        }
        await ctx.send(f"```json\n{dumps(data, separators=(',', ':'))}```")

def setup(bot):
    bot.add_cog(BuildCodes(bot))
