import discord
from discord.ext import commands


class SystemMessage():
    def __init__(self, message: discord.Message):
        self.original = message

regexes = {
    "pins": r"(.*) pinned a message to this channel\.",
    "threads": r"(.*) started a thread: \*\*(.*)\*\*. See all \*\*threads\*\*\."
}

class SystemLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_message")
    async def _message_filter(self, message):
        if message.is_system():
            self.bot.dispatch("system_message", SystemMessage(message))

    @commands.Cog.listener()
    async def on_system_message(self, message: SystemMessage):
        channel = self.bot.get_channel(859440482195341323)
        await channel.send("`"*3+message.original.system_content+"`"*3)

def setup(bot):
    bot.add_cog(SystemLogs(bot))