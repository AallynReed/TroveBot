# Priority: 1
import asyncio
import operator
import re
import json
from typing import Collection

import discord
from discord.ext import commands, tasks

import utils.checks as perms
import pandas as pd
from utils.objects import Values


class LbStats(commands.Converter):
    async def convert(self, ctx, argument):
        operators = ["<", "<=", ">", ">=", "="]
        stats_list = await ctx.bot.db.stats_list()
        arguments = [arg for argument in argument.split("|") for arg in argument.split(",")]
        def check_stat(stat):
            SStat = None
            for Stat in stats_list:
                if not re.match("^"+stat+"$", Stat.split(".")[-1], re.IGNORECASE):
                    continue
                SStat = Stat
                break
            return SStat or None
        data = {}
        for arg in arguments:
            if not arg.replace(" ", ""):
                continue
            match = re.match(r"((?:[a-z]+ ?)+[a-z]+)(?: *)?([<=>]{1,2})?(?: *)?([0-9]+)?", arg.strip(), re.IGNORECASE)
            if not match:
                continue
            stat, condition, value = match.groups()
            stat = check_stat(stat)
            if not stat:
                raise Exception("Invalid Stat.")
            if stat in data.keys():
                raise Exception("Duplicate stat detected.")
            if condition and condition not in operators:
                raise Exception("Invalid Condition.")
            try:
                value = int(value)
            except:
                ...
            data[stat.replace(".", "/")] = {
                "name": stat.split(".")[-1],
                "value": value,
                "condition": condition
            }
        if not data:
            raise Exception("Invalid Input!")
        return data

class Leaderboards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.operators = {
            "<": operator.lt,
            "<=": operator.le,
            ">": operator.gt,
            ">=": operator.ge,
            "=": operator.eq,
        }
        self.values = Values()
        self.auto_roles.start()

    def cog_unload(self):
        self.auto_roles.cancel()

    def test_lb(self):
        lb = [
            ["Sly", 1],
            ["Tom", 2],
            ["Toff", 3],
            ["Nik", 4],
            ["Jhh", 5]
        ]
        dataframe = pd.DataFrame(lb, index=list(range(1, len(lb)+1)),columns=["Player", "Poop Made"])
        return dataframe

    @commands.group(invoke_without_command=True, aliases=["lb"])
    async def leaderboard(self, ctx, leaderboard=None):
        e = discord.Embed()
        e.color = discord.Color.random()
        e.description = "```\n"
        e.description += str(self.test_lb())
        e.description += "\n```"
        await ctx.reply(embed=e)

    @leaderboard.command()
    async def create(self, ctx, role: discord.Role, *, args: LbStats):
        await ctx.send("```json\n" + str(json.dumps(args, indent=4)) + "\n```")
        return
        data = await ctx.get_guild_data(stat_roles=1)
        if data["stat_roles"]["roles"].get(str(role.id)):
            return await ctx.reply(f"{role.mention} already has a configuration set. Use `{ctx.prefix}update`", allowed_mentions=discord.AllowedMentions.none())
        for _, v in args.items():
            if not v["condition"]:
                return await ctx.reply(f"Stats must have a condition.")
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {f"stat_roles.roles.{role.id}": args}})
        await ctx.reply(f"{role.mention} rule is set.", allowed_mentions=discord.AllowedMentions.none())

    @tasks.loop(seconds=300)
    async def auto_roles(self):
        profiles = await self.bot.db.db_profiles.find({"Bot Settings.Server": 1}).to_list(length=9999999)
        for g in self.bot.guilds:
            gdata = await self.bot.db.db_servers.find_one({"_id": g.id, "stat_roles.roles": {"$ne": {}}}, {"stat_roles": 1})
            if not gdata:
                continue
            asyncio.create_task(self.give_guild_roles(g, gdata, profiles))

    async def give_guild_roles(self, guild, gdata, profiles):
        for member in guild.members:
            for profile in profiles:
                if profile["_id"] != member.id:
                    continue
                break
            for role, config in gdata["stat_roles"]["roles"].items():
                role = guild.get_role(int(role))
                if not role:
                    continue
                award = True
                classes = []
                for path, rule in config.items():
                    if "/Class/" not in path:
                        try:
                            value = self.navigate_to_value(profile, path)
                            if not self.operators[rule["condition"]](value, rule["value"]):
                                award = False
                                break
                        except:
                            ...
                    else:
                        for _class, stats in profile["Classes"].items():
                            if self.operators[rule["condition"]](stats[rule["name"]], rule["value"]):
                                if _class not in classes:
                                    classes.append(_class)
                classez = []
                for _class in classes:
                    is_valid = True
                    for _, rule in config.items():
                        if "/Class/" in path:
                            if not self.operators[rule["condition"]](stats[rule["name"]], rule["value"]):
                                is_valid = False
                    if is_valid:
                        classez.append(_class)
                try:
                    if award and classez:
                        await member.add_roles(role)
                    else:
                        await member.remove_roles(role)
                except:
                    ...

    def navigate_to_value(self, data, path):
        for key in path.split("/"):
            data = data[key]
        return data
        
def setup(bot):
    bot.add_cog(Leaderboards(bot))
