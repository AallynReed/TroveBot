# Priority: 4
from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord.utils import get


class PartnerTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.archive_task.start()

    def cog_unload(self):
        self.archive_task.cancel()

    @tasks.loop(seconds=15)
    async def archive_task(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow().timestamp()
        to_close = self.bot.db.db_ts_archives.find({"close_at": {"$lte": now}})
        if not to_close:
            return
        guild = self.bot.get_guild(118027756075220992)
        category = guild.get_channel(772434558330601542)
        target = guild.default_role
        async for archive_data in to_close:
            channel = get(category.text_channels, id=int(archive_data["_id"]))
            if not channel:
                continue
            new_overwrites = channel.overwrites
            new_overwrites[target].view_channel = False
            await self.bot.db.db_ts_archives.delete_one({"_id": channel.id})
            await channel.edit(overwrites=new_overwrites, reason="Closing archive after time limit was reached.")

def setup(bot):
    bot.add_cog(PartnerTasks(bot))
