# Priority: 1
import os
import typing
from datetime import datetime

import discord
from discord.ext import commands

import utils.checks as perms


class Club(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(slash_command=True, help="Manage your club's blacklist", aliases=["bl"])
    @perms.has_permissions("administrator")
    async def blacklist(self, ctx):
        ...
    
    @blacklist.command(slash_command=True, help="Add a player to club's blacklist")
    async def add(self, ctx, 
        player_name=commands.Option(name="player", description="Input a player name"), 
        *, reason=commands.Option(name="reason", description="Input a reason to blacklist the user")):
        bl = {
            "_id": player_name.lower(),
            "name": player_name,
            "reason": reason,
            "added_at": datetime.utcnow().timestamp(),
            "discord": None,
            "server": ctx.guild.id,
            "added_by": ctx.author.id
        }
        try:
            all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("_id")
            for user in all_users:
                if player_name.casefold() == user.casefold():
                    await ctx.send("That player was already added to the blacklist.")
                    return
        except:
            pass
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].insert_one(bl)
        await ctx.send(f"**{player_name}** was added to the club's blacklist.\nReason: {reason}")

    @blacklist.command(slash_command=True, help="Remove a player from blacklist", aliases=["rem"])
    async def remove(self, ctx, player_name=commands.Option(name="player", description="Input a player name")):
        all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("_id")
        for useri in all_users:
            if useri.startswith(player_name.lower()):
                player_name = useri
                break
        player = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"_id": player_name.lower(), "server": ctx.guild.id})
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
        blacklisted.sort(key=lambda x: x["name"])
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
        for bl in blacklisted:
            i += 1
            text += f"`{bl['name']}` - {bl['reason']}\n"
            if i == 20:
                pages.append(text)
                text = ""
                i = 0
        if text != "":
            pages.append(text)
        cursor = 0
        await self.paginator(ctx, pages, cursor, f"{ctx.guild.name}'s blacklist")

    @blacklist.command(slash_command=True, help="Show info about a blacklisted player")
    async def info(self, ctx, 
        member: typing.Optional[discord.User]=commands.Option(default=None, description="Input a discord user ID, Name or mention"), 
        player_name=commands.Option(default=None, description="Input a player name")):
        if player_name:
            all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("_id")
            for user in all_users:
                if user.startswith(player_name.lower()):
                    player_name = user
                    break
        if member != None:
            bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"discord": member.id, "server": ctx.guild.id})
        elif player_name != None:
            bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"_id": player_name.lower(), "server": ctx.guild.id})
        else:
            await ctx.send("Please define who to look for.")
            return
        if not bl:
            await ctx.send("That player is not blacklisted.")
            return
        added_by = await self.bot.fetch_user(bl["added_by"])
        e = discord.Embed(description=bl["reason"], timestamp=datetime.utcfromtimestamp(bl["added_at"]), color=self.bot.comment)
        e.set_author(name=bl["name"])
        if bl["discord"] is not None:
            blu = await self.bot.fetch_user(bl["discord"])
            e.set_author(name=f"{blu} | IGN: {bl['name']}", icon_url=blu.avatar)
        e.set_footer(text=f"Blacklisted by {added_by.display_name} on", icon_url=added_by.avatar)
        await ctx.send(embed=e)

    @blacklist.command(slash_command=True, help="Link a discord user to a blacklisted player", name="discord")
    async def _discord(self, ctx, 
        player_name=commands.Option(description="Input a player name"),
        user: discord.User=commands.Option(default=None, description="Input a discord user")):
        all_users = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find({"server": ctx.guild.id}).distinct("_id")
        for useri in all_users:
            if useri.startswith(player_name.lower()):
                player_name = useri
                break
        bl = await self.bot.db.database[await self.bl_db_pick(ctx.guild)].find_one({"_id": player_name.lower(), "server": ctx.guild.id})
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
            await self.bot.db.database[await self.bl_db_pick(ctx.guild)].update_one({"_id": player_name.lower(), "server": ctx.guild.id}, {"$set":{"discord": None}})
            await ctx.send(f"**{bl['name']}**'s discord has been removed." + (f"\n**{ban.user}** `{ban.user.id}` unbanned from discord server." if unbanned else ""))
            return
        await self.bot.db.database[await self.bl_db_pick(ctx.guild)].update_one({"_id": player_name.lower(), "server": ctx.guild.id}, {"$set":{"discord": user.id}})
        banned = False
        try:
            added_by = await self.bot.fetch_user(bl["added_by"])
            await ctx.guild.ban(user, reason=bl["reason"] + f" [Banned by {added_by} - {added_by.id}]")
            banned = True
        except:
            ...
        await ctx.send(f"**{bl['name']}** is now associated with {user}" + (f" and was banned from this server." if banned else ""))

    async def bl_db_pick(self, guild=None):
        data = await self.bot.db.db_servers.find_one({"_id": guild.id})
        if data["PTS mode"] == True:
            return "blacklist_pts"
        elif guild:
            return "blacklist_live"

    async def paginator(self, ctx, pages, cursor, title):
        e = discord.Embed(description=pages[cursor], color=self.bot.comment)
        e.set_author(name=title.replace("{cursor}", str(cursor + 1)).replace("{total_pages}", str(len(pages))))
        sent = await ctx.send(embed=e)
        if len(pages) == 1:
            return
        await sent.add_reaction("◀️")
        await sent.add_reaction("▶️")

        def check(reaction, user):
            return user == ctx.author and reaction.message.id == sent.id and str(reaction.emoji) in ["◀️", "▶️"]

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", check=check, timeout=60)
            except:
                try:
                    await sent.clear_reactions()
                except:
                    break
                break
            if str(reaction.emoji) == "◀️":
                cursor -= 1
                if cursor < 0:
                    cursor = len(pages) - 1
            if str(reaction.emoji) == "▶️":
                cursor += 1
                if cursor > len(pages) - 1:
                    cursor = 0
            e = discord.Embed(description=pages[cursor], color=self.bot.comment, timestamp=datetime.utcfromtimestamp(1613722651))
            e.set_author(name=title.replace("{cursor}", str(cursor + 1)).replace("{total_pages}", str(len(pages))))
            e.set_footer(text="Last Updated on")
            try:
                await sent.edit(embed=e)
            except:
                pass
            try:
                await reaction.remove(ctx.author)
            except:
                pass
            
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
