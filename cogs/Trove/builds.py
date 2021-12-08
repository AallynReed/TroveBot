# Priority: 1
import asyncio
import itertools
import os
from datetime import datetime
from functools import partial
import string

import discord
from discord.ext import commands
from openpyxl import Workbook, utils
from openpyxl.styles import Font, PatternFill, Alignment
from utils.buttons import BuildsPickView, GemBuildsView
from utils.objects import ArgumentFinder, BuildType, GameClass, Values


class Builds(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.values = Values()
        self.last_updated = 1638985903

    @commands.command(slash_command=True, help="Show current Meta for different game situations.")
    @commands.bot_has_permissions(embed_links=1)
    async def meta(self, ctx):
        e = discord.Embed(color=0x0000ff, timestamp=datetime.utcfromtimestamp(self.last_updated))
        e.set_author(name="Meta", icon_url=self.bot.user.avatar.url)
        e.description = "Here are the game's Meta classes for each activity."
        e.add_field(name="Farming (Adventure/Topside)", value="Physical: <:c_NN:876846928808259654> **Neon Ninja**\nMagic: <:c_DT:876846922135126036> **Dino Tamer** or <:c_BD:876846944604024842> **Bard**", inline=False)
        e.add_field(name="DPS (Single Target)", value="Magic: <:c_CM:876846891747410001> **Chloromancer**", inline=False)
        e.add_field(name="Delve Path (Delve Dusk - | Below Depth ~129)", value="Magic: <:c_TR:876846901801123850> **Tomb Raiser**", inline=False)
        e.add_field(name="Delve Path (Delve Dusk + | Above Depth ~129)", value="Magic: <:c_IS:876846881311965224> **Ice Sage**", inline=False)
        e.set_footer(text="Last updated")
        await ctx.send(embed=e)

    @commands.command(slash_command=True, help="Show gear for a class")
    @commands.cooldown(1, 120, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=1)
    async def gear(
        self,
        ctx,
        _class: GameClass=commands.Option(name="class", default=None, description="Input class name"),
        *,
        build_type: BuildType=commands.Option(name="build_type", default=None, description="Input build type [Farm | DPS | Health]")
    ):
        page = None
        all_gears = self.get_all_gear_pages(ctx)
        if build_type:
            if not self.bot.Trove.values.gear_builds[_class.name][build_type]["enabled"]:
                build_type = None
            else:
                try:
                    page = all_gears[_class.name][build_type]
                except:
                    pass
        view = BuildsPickView(ctx, _class, build_type, all_gears)
        if not _class:
            content = f"Pick a **class** to get builds for."
        elif not build_type:
            content = f"Pick a build type for **{_class}**"        
        else:
            content = None
        view.message = await ctx.send(content, embed=page["embed"] if page else None, view=view)

    def get_all_gear_pages(self, ctx, ):
        all_gears = {}
        for _class in self.bot.Trove.values.classes:
            if _class.name not in all_gears.keys():
                all_gears[_class.name] = {}
            for k, v in self.get_gear_page(ctx, _class).items():
                all_gears[_class.name][k] = v
        return all_gears

    def get_gear_page(self, ctx, _class):
        build_types = ["light", "farm", "tank"]
        builds = {}
        for build_type in build_types:
            class_build = self.values.gear_builds[_class.name][build_type]
            if not class_build["enabled"]:
                continue
            if build_type == "light":
                build_type = "dps"
                build = "DPS"
            elif build_type == "tank":
                build = "Tanking"
            if build_type == "farm":
                build = "Farming"
            trovesaurus = f"https://trovesaurus.com/builds/{_class.name.replace(' ', '%20')}/{build_type}"
            #tiers = ["<:Star5:841015868930523176>", "<:Star4:841015868863283240>", "<:Star3:841015868716220447>", "<:Star2:841015868854501376>", "<:Star1:841015868993175592>"]
            e = discord.Embed(description=f"**Check on [Trovesaurus]({trovesaurus})**",color=discord.Color.random(), timestamp=datetime.utcfromtimestamp(self.last_updated))
            e.description += f"\n\nRating: " + '<:Star:841018551087530024>' * (6-class_build['tier']) + '<:StarOutline:841018551418880010>' * (class_build['tier'] - 1)
            e.set_author(name=f"In depth {build_type} build for {_class.name}", icon_url=_class.image)
            e.add_field(name="<:hat:834512699585069086>Hat", value=self.readable_stats(class_build["hat"]))
            e.add_field(name="<:sword:834512699593064518>Weapon", value=self.readable_stats(class_build["weapon"]))
            e.add_field(name="<:face:834512699441938442>Face", value=self.readable_stats(class_build["face"]))
            e.add_field(name="<:banner:834512699391475742>Banner", value=self.readable_stats(class_build["banner"], False))
            e.add_field(name="<:ring:834512699383218226>Ring", value=self.readable_stats(class_build["ring"], False))
            e.add_field(name="<:food:834512699424505886>Food", value=self.readable_stats(class_build["food"], False))
            e.add_field(name="<:flask:834512699479687228>Flask", value=self.readable_stats(class_build["flask"], False, or_split=True))
            e.add_field(name="<:emblem:834512699332755536>Emblems", value=self.readable_stats(class_build["emblem"], False))
            e.add_field(name="<:qubesly:834512699361853530>Ally", value=self.readable_stats(class_build["ally"], False, True))
            e.add_field(name="<:blue_emp_gem:834506349433585735>Gem Abilities", value=self.readable_stats(class_build["gems"], False))
            e.add_field(name="<:subclass:834512699576025119>Subclass", value=self.readable_stats(class_build["subclass"], False, or_split=True))
            e.add_field(name="\u200b", value="Note: These builds are subjective, contact Sly#0511 for suggestions.\nThanks to **Nikstar** for putting these builds together.", inline=False)
            e.set_footer(text=f"For gem builds use {ctx.prefix}build {_class.short} {build_type} | Last updated on")
            if build_type == "dps":
                build_type = "light"
            builds[build_type.lower()] = {
                "description": f"Build aimed at improving {build}",
                "embed": e,
                "link": trovesaurus
            }
        return builds

    @commands.command(slash_command=True, aliases=["builds", "gem", "gems"], help="Show gem builds for a class.")
    @commands.cooldown(1, 180, commands.BucketType.user)
    @commands.bot_has_permissions(embed_links=1)
    async def build(self, ctx):
        view = GemBuildsView(ctx)
        view.message = await ctx.send(content="Builds will only be calculated once all **Required** fields are filled in.", view=view)

    @commands.command(aliases=["gu"], hidden=True)
    async def gear_update(self, ctx):
        if ctx.author.id not in [565097923025567755,237634733264207872]:
            return
        self.values.update_gear_builds()
        await ctx.send("Updated gear builds.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if self.bot.get_user(payload.user_id).bot:
            return
        if str(payload.emoji) != "👁️":
            return
        channel = self.bot.get_channel(payload.channel_id)
        try:
            msg = await channel.fetch_message(payload.message_id)
        except:
            return
        if msg.author.id == self.bot.user.id and msg.flags.suppress_embeds:
            content = msg.content
            try:
                await msg.edit(content=None, view=None, suppress=False)
                await msg.clear_reaction("👁️")
            except:
                pass
            await asyncio.sleep(300)
            try:
                await msg.edit(content=content, view=None, suppress=True)
                await msg.add_reaction("👁️")
            except:
                pass

    def readable_stats(self, stats, num=True, fixed=False, or_split=False):
        text = ""
        if not or_split:
            text += "```\n"
            if not fixed:
                for i in range(len(stats)):
                    if num:
                        text += f"{i+1}. "
                    else:
                        text += "● "
                    stat_text = stats[i]
                    # if stat_text == 'Explosive Epilogue':
                    #     stat_text == 'Explosive Epi.'
                    # if stat_text == "Freerange Electrolytic Crystals":
                    #     stat_text = "Freerange Elec. Cryst."
                    # stat_text.replace(" Vial", "")
                    text += f"{stat_text}\n"
            else:
                text += "/".join(["● "+i for i in stats])
            text += "```"
        else:
            text += "```css\n"
            text += "\n#or\n".join(["● "+i for i in stats])
            text += "\n```"

        return text

    @commands.command(hidden=True)
    async def ea(self, ctx):
        stats = []
        for ally in self.bot.Trove.values.allies:
            for stat, _ in ally.stats.items():
                if stat not in stats:
                    stats.append(stat)
        stats.sort()
        letters = string.ascii_uppercase
        stats = {stats[i]: letters[i+1] for i in range(len(stats))}
        def adjust_width(ws):
            def is_merged_horizontally(cell):
                cell_coor = cell.coordinate
                if cell_coor not in ws.merged_cells:
                    return False
                for rng in ws.merged_cells.ranges:
                    if cell_coor in rng and len(list(rng.cols)) > 1:
                        return True
                return False

            for col_number, col in enumerate(ws.columns, start=1):
                col_letter = utils.get_column_letter(col_number)

                max_length = max(len(str(cell.value or "")) for cell in col if not is_merged_horizontally(cell))
                adjusted_width = (max_length + 2) * 1
                ws.column_dimensions[col_letter].width = adjusted_width
        wb = Workbook()
        wb.remove_sheet(wb.active)
        ws = wb.create_sheet(title="Allies")
        ws["A1"] = "Name"
        for stat, collumn in stats.items():
            ws[f"{collumn}1"] = stat
        allies = sorted(self.bot.Trove.values.allies, key=lambda x: x.name.lower())
        fill = PatternFill(start_color='00000000',
                            end_color='00000000',
                            fill_type='solid')
        font = Font(color='00747474')
        for i in range(len(allies)):
            ally = allies[i]
            row = i + 2
            ws[f"A{row}"] = ally.name
            for stat, value in ally.stats.items():
                collumn = stats[stat]
                ws[f"{collumn}{row}"] = str(value)
            for i in range(len(stats.keys())+1):
                collumn = letters[i]
                ws[f"{collumn}{row}"].fill = fill
                ws[f"{collumn}{row}"].font = font
                ws[f"{collumn}{row}"].alignment = Alignment(horizontal='center')
        adjust_width(ws)
        for i in range(len(allies)):
            row = i + 2
            ally = discord.utils.get(allies, name=ws[f"A{row}"].value)
            ws[f"A{row}"] = f'=HYPERLINK("{ally.url}", "{ally.name}")'
        _file = "cache/allies.xlsx"
        wb.save(_file)
        await ctx.send(file=discord.File(_file))
        os.remove(_file)

def setup(bot):
    bot.add_cog(Builds(bot))
