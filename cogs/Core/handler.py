import discord
from discord.ext import commands


class Handler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def _message_handler(self, message):
        ...


def setup(bot):
    bot.add_cog(Handler(bot))