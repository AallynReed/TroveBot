# Priority: 1
import os
import typing
from datetime import datetime

import discord
from discord.ext import commands, tasks

import utils.checks as perms
from utils.objects import TimeConvert, TimeConverter, TrovePlayer
from utils.buttons import Paginator


class Club(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.blacklist_timeouts.start()

    def cog_unload(self):
        self.blacklist_timeouts.cancel()

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

    @commands.group(slash_command=True, help="Manage your club's blacklist", aliases=["bl"])
    @perms.has_permissions("administrator")
    async def blacklist(self, ctx):
        ...
    
    @blacklist.command(slash_command=True, help="Add a player to club's blacklist")
    async def add(self, ctx, 
        player_name: TrovePlayer=commands.Option(name="player", description="Input a player name"),
        time: typing.Optional[TimeConvert]=commands.Option(default=None, description="Amount of time for the timeout"), 
        *, reason=commands.Option(name="reason", description="Input a reason to blacklist the user")):
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

    @blacklist.command(slash_command=True, help="Remove a player from blacklist", aliases=["rem"])
    async def remove(self, ctx, player_name: TrovePlayer=commands.Option(name="player", description="Input a player name")):
        all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("name")
        for useri in all_users:
            if useri.lower().startswith(player_name.lower()):
                player_name = useri
                break
        player = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"name": {"$regex": f"(?i)^{player_name}$"}, "server": ctx.guild.id})
        if player is None:
            await ctx.send("That player is not in the blacklist.")
            return
        user = player["name"]
        unbanned = False
        if player["discord"]:
            bans = await ctx.guild.bans()
            for ban in bans:
                if ban.user.id != player["discord"]:
                    continue
                try:
                    await ctx.guild.unban(ban.user)
                    unbanned = True
                except:
                    pass
                break
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].delete_one({"_id": player["_id"], "server": ctx.guild.id})
        await ctx.send(f"Removed **{user}** from the blacklist." + (f"\n**{ban.user}** `{ban.user.id}` unbanned from server." if unbanned else ""))

    @blacklist.command(slash_command=True, help="List all players in club's blacklist", name="list")
    async def _list(self, ctx, as_file=commands.Option(name="send_as_file", default=False, description="Send blacklist as formatted text file")):
        blacklisted = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).to_list(length=999999)
        if len(blacklisted) == 0:
            await ctx.send("No players blacklisted.")
            return
        blacklisted.sort(key=lambda x: x["name"].lower())
        pages = []
        text = ""
        i = 0
        if as_file:
            max = len(sorted(blacklisted, key=lambda x: len(x["name"]), reverse=True)[0]["name"])
            with open(f"{ctx.guild.id}_blacklist.txt", "w+") as f:
                i = 0
                for bl in blacklisted:
                    i += 1
                    text = f"{i}. " + bl['name']
                    f.write(f"{text:<{max+len(str(len(blacklisted)))+2}} - {bl['reason']}\n")
            await ctx.send(f"**{ctx.guild.name}**'s Player Blacklist", file=discord.File(f"{ctx.guild.id}_blacklist.txt"))
            os.remove(f"{ctx.guild.id}_blacklist.txt")
            return
        raw_pages = self.bot.utils.chunks(blacklisted, 20)
        for raw_page in raw_pages:
            i += 1
            e = discord.Embed(color=discord.Color.random())
            e.set_author(name=f"{ctx.guild.name}'s Player Blacklist | {i}/{len(raw_pages)}", icon_url=ctx.guild.icon or discord.Embed.Empty)
            text = ""
            for bl in raw_page:
                if bl["timeout"]:
                    text += "🕐 "
                text += f"`{bl['name']}` - {bl['reason']}\n"
            e.description = text
            page = {
                "page": i,
                "content": None,
                "embed": e
            }
            pages.append(page)
        paginator = Paginator(ctx, pages, start_end=True)
        await ctx.reply(embed=pages[0]["embed"], view=paginator)

    @blacklist.command(slash_command=True, help="Show info about a blacklisted player")
    async def info(self, ctx, 
        member: typing.Optional[discord.User]=commands.Option(default=None, description="Input a discord user ID, Name or mention"), 
        player_name: TrovePlayer=commands.Option(default=None, description="Input a player name")):
        if player_name:
            all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("name")
            for user in all_users:
                if user.lower().startswith(player_name.lower()):
                    player_name = user
                    break
        if member != None:
            bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"discord": member.id, "server": ctx.guild.id})
        elif player_name != None:
            bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"name": {"$regex": f"(?i)^{player_name}$"}, "server": ctx.guild.id})
        else:
            await ctx.reply("Please define who to look for.", ephemeral=True)
            return
        if not bl:
            await ctx.reply("That player is not blacklisted.")
            return
        added_by = await self.bot.fetch_user(bl["added_by"])
        e = discord.Embed(description=bl["reason"], timestamp=datetime.utcfromtimestamp(bl["added_at"]), color=self.bot.comment)
        e.set_author(name=bl["name"])
        if bl["discord"] is not None:
            blu = await self.bot.fetch_user(bl["discord"])
            e.set_author(name=f"{blu} | IGN: {bl['name']}", icon_url=blu.avatar or discord.Embed.Empty)
        if bl["timeout"] is not None:
            timeout = TimeConverter(bl["timeout"])
            e.add_field(name="Timeout Duration", value=str(timeout))
            e.add_field(name="Timeout End", value=self.bot.utils.format_dt(datetime.utcnow()+timeout.delta, "F"))
        e.set_footer(text=f"Blacklisted by {added_by.display_name} on", icon_url=added_by.avatar or discord.Embed.Empty)
        await ctx.send(embed=e)

    @blacklist.command(slash_command=True, help="Link a discord user to a blacklisted player", name="discord")
    async def _discord(self, ctx, 
        player_name: TrovePlayer=commands.Option(description="Input a player name"),
        user: discord.User=commands.Option(default=None, description="Input a discord user")):
        all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("name")
        for useri in all_users:
            if useri.lower().startswith(player_name.lower()):
                player_name = useri
                break
        bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"name": {"$regex": f"(?i)^{player_name}$"}, "server": ctx.guild.id})
        if not bl:
            await ctx.send("That player is not added to blacklist. You must add it first before linking.")
            return
        if not user:
            unbanned = False
            if bl["discord"]:
                bans = await ctx.guild.bans()
                for ban in bans:
                    if ban.user.id != bl["discord"]:
                        continue
                    try:
                        await ctx.guild.unban(ban.user)
                        unbanned = True
                    except:
                        pass
                    break
            await self.bot.db.database[await self.bl_db_pick(ctx.guild)].update_one({"name": bl["name"], "server": ctx.guild.id}, {"$set":{"discord": None}})
            await ctx.send(f"**{bl['name']}**'s discord has been removed." + (f"\n**{ban.user}** `{ban.user.id}` unbanned from discord server." if unbanned else ""))
            return
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].update_one({"name": bl["name"], "server": ctx.guild.id}, {"$set":{"discord": user.id}})
        banned = False
        try:
            added_by = await self.bot.fetch_user(bl["added_by"])
            await ctx.guild.ban(user, reason=bl["reason"] + f" [Banned by {added_by} - {added_by.id}]")
            banned = True
        except:
            ...
        await ctx.send(f"**{bl['name']}** is now associated with {user}" + (f" and was banned from this server." if banned else ""))

    @blacklist.command(slash_command=True, help="Set a timeout to an existin blacklist entry")
    async def timeout(self, ctx,
        player_name: TrovePlayer=commands.Option(name="player", description="Input a player name"),
        *, timeout: TimeConvert=commands.Option(default=None, description="Amount of time for the timeout")):
        if timeout:
            settings = await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"blacklist": 1})
            if not settings["blacklist"]["channel"]:
                return await ctx.reply(f"You need to set a notification channel to use timeouts. `{ctx.prefix}blacklist channel #MyChannel`")
            # if timeout.seconds < 86400:
            #     return await ctx.reply("Minimum timout is 1 day.", ephemeral=True)
        player = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"name": {"$regex": f"(?i)^{player_name}$"}, "server": ctx.guild.id})
        if player is None:
            return await ctx.send("That player is not in the blacklist.")
        if not timeout.seconds:
            timeout = None
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].update_one({"_id": player["_id"]}, {"$set": {"timeout": timeout.seconds if timeout else timeout}})
        return await ctx.reply(f"Player blacklist will timeout in **{timeout}**" if timeout else "Timeout removed, player blacklist was made permanent.")

    @blacklist.command(slash_command=True, help="Set a channel to be notified when a blacklist timeout ends")
    async def channel(self, ctx, channel: discord.TextChannel=commands.Option(default=None, description="Select a text channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"blacklist.channel": channel.id if channel else channel}})
        if channel:
            await ctx.reply(f"Blacklist timeout notifications set to {channel.mention}")
        else:
            await ctx.reply(f"Blacklist timeout notifications disabled.")

    async def bl_db_pick(self, guild=None):
        data = await self.bot.db.db_servers.find_one({"_id": guild.id})
        if data["PTS mode"] == True:
            return "blacklist_pts"
        elif guild:
            return "blacklist_live"

    @commands.command(slash_command=True, help="Display list of commands usable for club management", aliases=["ccmd"])
    async def club_commands(self, ctx):
        e = discord.Embed(description="Some in-game club commands", color=self.bot.comment)
        e.add_field(name="Rename World", value="`/renameworld <new name>`", inline=False)
        e.add_field(name="Promote/Demote members", value="`/club [pro|de]mote <playername> <clubname>`", inline=False)
        e.add_field(name="Zone Restrict", value="`/zonerestrict <basic/modify/expert/nobody>`", inline=False)
        e.add_field(name="Damage Protection", value="`/club setzonedamageable <0|1>`", inline=False)
        e.add_field(name="Kick", value="`/club kick <playerName> <clubName>`", inline=False)
        e.add_field(name="Block", value="`/club [block/unblock] <clubname> <playername>`", inline=False)
        e.set_author(name="Club Commands", icon_url=ctx.guild.icon)
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(Club(bot))
