# Priority: 1
import re
import typing

import discord
from discord.ext import commands
from simpleeval import simple_eval

from utils.objects import AugmentationStats


class Calculations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=True, help="Show augmentation costs for a set of gems", aliases=["agm", "aug"])
    async def augment(self, ctx, *, augmentation=commands.Option(name="augmentation", description="Input your gem sets to be calculated (2:46 1:25 0:65)")):
        converter = AugmentationStats()
        try:
            augmentation = await converter.convert(ctx, augmentation)
        except Exception as e:
            return await ctx.send(str(e))
        if len(augmentation["gems"]) > 6:
            return await ctx.send("You can only do up to 6 gems at a time.")
        def get_gem_cost(gem):
            gem_cost = {}
            for i in range(len(gem)):
                stat = gem[i]
                if stat:
                    focuses, resources = self.bot.utils.get_augmentation_cost(stat, prefered=augmentation["focus"])
                    gem_cost[f"{i}-{stat[0]}:{stat[1]}"] = [focuses, resources]
                else:
                    gem_cost[str(i)] = None
            return gem_cost
        gems = [get_gem_cost(gem) for gem in augmentation["gems"]]
        e = discord.Embed(description=f"Prefered: **{augmentation['focus'].capitalize()}**", color=self.bot.comment)
        e.set_author(name="Gem Augmentation", icon_url="https://i.imgur.com/st2CWEz.png")
        e.set_image(url="https://i.imgur.com/M5rAxEM.png")
        e.set_footer(text=r"UI rounds values, so costs might not be 100% correct but it's a pretty accurate estimate")
        total_costs = {}
        for i in range(len(gems)):
            gem = gems[i]
            costs = {}
            for stat, value in gem.items():
                if not value:
                    e.add_field(name="----------------", value="\u200b")
                    continue
                stat_focuses = f"<:foc1:873291782732009493>Rough: **{value[0][0]}**"
                stat_focuses += f"\n<:foc2:873291782773940225>Precise: **{value[0][1]}**" if value[0][1] > 0 else ""
                stat_focuses += f"\n<:foc3:873291783025598514>Superior: **{value[0][2]}**" if value[0][2] > 0 else ""
                e.add_field(name=f"----------------\n**<:boost:873291316447047761> {stat[2:]}%**", value=stat_focuses)
                for resource, cost in value[1]:
                    if resource not in total_costs.keys():
                        total_costs[resource] = 0
                    if resource not in costs.keys():
                        costs[resource] = 0
                    costs[resource] += int(cost)
                    total_costs[resource] += int(cost)
            cost_text = ""
            for resource, cost in costs.items():
                if cost > 0:
                    cost_text += f"{resource}: **{cost:,}**\n"
            e.add_field(name=f"**Gem {i+1} Cost**", value=cost_text, inline=False)
        if len(augmentation["gems"]) > 1:
            cost_text = ""
            for resource, cost in total_costs.items():
                if cost > 0:
                    cost_text += f"{resource}: **{cost:,}**\n"
            e.add_field(name=f"---------------------------------------------------\n**Total Cost**", value=cost_text, inline=False)
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Calculate a math expression", aliases=["calc"])
    async def calculate(
        self,
        ctx,
        no_commas: typing.Optional[typing.Literal["true"]]=commands.Option(name="no_commas", default=None, description="Whether to disable commas in the result or not"),
        debug: typing.Optional[typing.Literal["true"]]=commands.Option(name="debug", default=None, description="Whether to show debug info or not"),
        *,
        expression=commands.Option(name="expression", default=None, description="Input an arguments")):
        args = expression
        if not args:
            return await ctx.send("Please give an expression to solve.", delete_after=10)
        def convert(arg):
            value = arg.groups(0)[0]
            return f"({value}/100)"
        curated_args = args.lower().replace("x", "*").replace(":", "/").replace("^", "**")
        curated_args = re.sub(r"((?:[0-9]+)(?:\.[0-9]+)?)%", convert, curated_args)
        try:
            result = simple_eval(curated_args)
        except:
            return await ctx.send("Expression is invalid.")
        if result >= 10**21 or result <= 10**-21:
            res = f"{result:.2e}"
        else:
            res = f"{result}" if no_commas else f"{result:,}"
        e = discord.Embed(title="Result", description=f"**{res}**", color=self.bot.comment)
        if debug:
            e.description += f"\n\nInput Expression: `{args}`" + (f"\nFixed Expression: `{curated_args}`" if args != curated_args else "")
        await ctx.send(embed=e)
    
    @commands.command(
        slash_command=True,
        help="Calculates coefficient given certain values.",
        aliases=["coefficient"]
    )
    async def coeff(
        self, 
        ctx, 
        damage: float=commands.Option(name="damage", description="Input Damage"), 
        crit: float=commands.Option(name="critical_damage", description="Input Critical Damage"),
        critchance: float=commands.Option(name="critical_hit", default=100.0, description="Input Critical Hit"), 
        class_bonus: int=commands.Option(name="class_bonus_damage", default=None, description="Input Damage bonus")
    ):
        if critchance > 100:
            critchance = 100.0
        coeff = round((100 - critchance) * damage / 100 + critchance * (damage * (1 + crit / 100)) / 100)
        e = discord.Embed(color=self.bot.comment)
        e.set_author(name="Coefficient Calculation", icon_url="https://i.imgur.com/sCIbgLX.png")
        e.add_field(name="Damage", value=damage)
        e.add_field(name="Critical Damage", value=f"{crit}%")
        e.add_field(name="Critical Chance", value=f"{critchance}%")
        if class_bonus:
            e.add_field(name="Class Bonus", value=f"{class_bonus}%")
            coeff = round(coeff * (1 + class_bonus / 100))
        e.add_field(name="Coefficient", value=coeff)
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Convert mastery points to mastery level", aliases=["cm", "cmp"])
    async def convert_mastery(self, ctx, 
        points: int=commands.Option(name="mastery_points", description="Input amount of mastery points"), 
        cap: int=commands.Option(name="limit", default=1000, description="Input a level to be max [Default: 1000]")):
        if points > 10000000:
            await ctx.send("Hold on pal, you having too much fun there.")
            return
        level, points, level_left = self.bot.utils.points_to_mr(points, cap)
        await ctx.send(f"Level: **{level}**\nExtra Points: **{points}**\nTo next Level: **{level_left - points if level_left - points >= 0 else 0}**")

    @commands.command(slash_command=True, help="Convert mastery level to mastery points", aliases=["cml"])
    async def convert_mastery_level(self, ctx, 
        level: int=commands.Option(name="mastery_level", description="Input amount of mastery levels")):
        if level > 10000:
            await ctx.send("Hold on pal, you having too much fun there.")
            return
        next_level, points = self.bot.utils.mr_to_points(level)
        await ctx.send(f"Level: **{level}**\nMastery Points: **{points}**\nTo next Level: **{next_level}**")


def setup(bot):
    bot.add_cog(Calculations(bot))
