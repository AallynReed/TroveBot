# Priority: 0

from datetime import datetime

from discord import app_commands
from discord.ext import commands, tasks
from utils.CustomObjects import TimeConverter
from utils.objects import TimeConvert, TrovePlayer


class Blacklist(commands.Cog, app_commands.Group, name="blacklist", description="Manage your club's blacklist"):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_timeouts.start()

    def cog_unload(self):
        self.blacklist_timeouts.cancel()
  
  # Tasks

    @tasks.loop(seconds=60)
    async def blacklist_timeouts(self):
        now = datetime.utcnow().timestamp()
        servers = ["live", "pts"]
        for s in servers:
            blacklisted = await self.bot.db.database[f"blacklist_{s}"].find({"timeout": {"$ne": None}}).to_list(length=999999)
            for bl in blacklisted:
                if not bl["added_at"]+bl["timeout"] < now:
                    continue
                guild = self.bot.get_guild(bl["server"])
                if not guild:
                    continue
                settings = await self.bot.db.db_servers.find_one({"_id": guild.id}, {"blacklist": 1})
                channel = guild.get_channel(settings["blacklist"]["channel"])
                if not channel:
                    continue
                await self.bot.db.database[f"blacklist_{s}"].delete_one({"_id": bl["_id"]})
                await channel.send(f"**{bl['name']}** removed from blacklist after **{TimeConverter(bl['timeout'])}** timeout for **{bl['reason']}**")

  # Commands

    @app_commands.command(name="add", description="Add a player to club's blacklist")
    @app_commands.describe_command(
        player_name="Input a player name",
        time="Amount of time for the timeout",
        reason="Input a reason to blacklist the user"
    )
    @app_commands.rename(player_name="player")
    @app_commands.has_permissions(manage_guild=True)
    async def add(self, ctx, player_name: TrovePlayer, reason: str, time: TimeConvert=None):
        if time:
            settings = await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"blacklist": 1})
            if not settings["blacklist"]["channel"]:
                return await ctx.reply(f"You need to set a notification channel to use timeouts. `{ctx.prefix}blacklist channel #MyChannel`")
            if time.seconds < 86400:
                return await ctx.reply("Minimum timout is 1 day.", ephemeral=True)
        bl = {
            "name": player_name,
            "reason": reason,
            "added_at": datetime.utcnow().timestamp(),
            "discord": None,
            "server": ctx.guild.id,
            "added_by": ctx.author.id,
            "timeout": time.seconds if time else time
        }
        try:
            all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("name")
            for user in all_users:
                if player_name.casefold() == user.casefold():
                    await ctx.send("That player was already added to the blacklist.")
                    return
        except:
            pass
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].insert_one(bl)
        await ctx.send(f"**{player_name}** was added to the club's blacklist.\nReason: {reason}" + (f"\nTimeout: {time}" if time else ""))

async def setup(bot: commands.Bot):
    await bot.add_cog(Blacklist(bot))
