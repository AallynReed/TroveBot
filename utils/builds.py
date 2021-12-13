import itertools
from datetime import datetime

import discord

from utils.objects import GameClass


class Dummy():
    ...

class BuildsMaker():
    def __init__(self, ctx):
        self.ctx = ctx
        self.values = ctx.bot.Trove.values

    def _add_arguments(self, arguments):
        self.arguments = Dummy()
        for name, value in arguments.items():
            setattr(self.arguments, name, value)
        self._convert_values()
        self._sanity_check()

    def _convert_values(self):
        self.arguments._class = GameClass().cconvert(self.arguments._class)
        if self.arguments.subclass:
            self.arguments.subclass = GameClass().cconvert(self.arguments.subclass)

    def _sanity_check(self):
        # Make sure dumb people don't do shit
        # that would want to make you quit Trove
        if self.arguments.subclass and self.arguments._class == self.arguments.subclass:
            self.arguments.subclass = None
        if self.arguments._class.infinite_as:
            self.arguments.cd_count = 3

    def _get_builds(self):
        if self.arguments.build_type == "health":
            light = 0
            base_damage = self.get_value("base_health")
            critical_damage = self.get_value("base_healthper")
            base_damage += self.arguments._class.health
            critical_damage += self.arguments._class.healthper
            if self.arguments.subclass and self.arguments.subclass.short == "CM":
                critical_damage += 60
            if self.arguments.crystal5:
                base_damage += 17290
                critical_damage += 104
        else:
            light = self.get_value("base_light")
            base_damage = self.get_value("base_damage")
            critical_damage = self.get_value("base_cd")
            bonus_damage = self.get_value("bonus_dmg")
            base_damage += self.arguments._class.dmg
            critical_damage += self.arguments._class.cd
            if self.arguments._class.dmg_type == "PD":
                base_damage += self.pd_dragons
                if self.arguments.subclass and self.arguments.subclass.short in ["LL"]:
                    base_damage += 750
            elif self.arguments._class.dmg_type == "MD":
                base_damage += self.md_dragons
                if self.arguments.subclass and self.arguments.subclass.short in ["SH", "IS"]:
                    base_damage += 750
            if self.arguments.subclass and self.arguments.subclass.short in ["GS"]:
                bonus_damage += 5.5
            critical_damage += self.cd_dragons
            if not self.arguments.deface:
                base_damage += 4719
            if self.arguments.subclass and self.arguments.subclass.short in ["BR", "BD"]:
                critical_damage += 20
            if self.arguments.build_type == "farm":
                critical_damage -= 44.2 * (3 - self.arguments.cd_count)
            if self.arguments.bardcd:
                bonus_damage += 45
                critical_damage += 45
            if self.arguments.ally:
                light += self.arguments.ally["stats"]["Light"]
                if not self.arguments.ally["damage"] or self.arguments.ally["damage"] == self.arguments._class.dmg_type:
                    bonus_damage += self.arguments.ally["stats"]["Damage"]
            if self.arguments.crystal5:
                base_damage += 6916
                critical_damage += 3.75
                light += 780
        builds = []
        builder = self._generate_combinations(coeff=self.arguments.build_type in ["health", "coeff"], light=self.arguments.light)
        for build in builder:
            gem_damage, gem_critical_damage, gem_light = self._get_gem_build_stats(build, prim=self.arguments.primordial, health=self.arguments.build_type=="health")
            build_damage = base_damage + gem_damage
            build_critical = critical_damage + gem_critical_damage
            build_light = light + gem_light
            if self.arguments.build_type != "health":
                if self.arguments._class.short in ["LL", "CB"]:
                    build_damage *= 1.3
                if self.arguments._class.short in ["BR"]:
                    build_damage *= 1.1
                final_damage = build_damage * (1 + bonus_damage / 100)
            else:
                final_damage = build_damage
            coefficient = round(final_damage * (1 + build_critical / 100))
            mod_coefficient = 0 #int(round(final_damage) * (1 + round(build_critical, 1) / 100))
            stats = {}
            if self.arguments.build_type != "health":
                stats["Light"] = round(build_light, 2)
                stats["Gem Damage"] = round(gem_damage, 2)
                stats["Gem Critical Damage"] = round(gem_critical_damage, 2)
                stats["Base Damage"] = round(build_damage, 2)
                stats["Damage"] = round(final_damage, 2)
                stats["Critical Damage"] = round(build_critical, 2)
                stats["Coefficient"] = coefficient
                #stats["Mod Coefficient"] = mod_coefficient
            else:
                stats["Gem Health"] = round(gem_damage, 2)
                stats["Gem Health %"] = round(gem_critical_damage, 2)
                stats["Base Health"] = round(base_damage, 2)
                stats["Health %"] = round(build_critical, 2)
                stats["Health"] = coefficient
            build_stats = [coefficient, build, build_light, mod_coefficient, stats]
            builds.append(build_stats)
        builds.sort(key=lambda x: [abs(x[2]-self.arguments.light),-x[0]])
        return builds

    def _run_builder(self):
        return self._get_builds()

    def get_pages(self, arguments):
        self._add_arguments(arguments)
        _class = self.arguments._class
        build_type = self.arguments.build_type
        cd_count = self.arguments.cd_count
        subclass = self.arguments.subclass
        light = self.arguments.light
        bardcd = self.arguments.bardcd
        primordial = self.arguments.primordial
        crystal5 = self.arguments.crystal5
        mod = self.arguments.mod
        ally = self.arguments.ally
        last_updated = datetime.utcfromtimestamp(1637821955)
        builds = self._run_builder()
        if self.arguments.build:
            for build in builds:
                if build[1] != self.arguments.build:
                    continue
                boosts = []
                [boosts.extend(i) for i in build[1]]
                if not light or (light and build_type in ["coeff", "health"]):
                    del boosts[6]
                    del boosts[8]
                if not light and build_type not in ["coeff", "health"]:
                    boosts = boosts[:4]
                build_text = "/".join([str(i) for i in boosts][:4]) + (" + " + "/".join([str(i) for i in boosts][4:]) if len(boosts) > 4 else "")
                e = discord.Embed(description=f"Detailed info about **{build_text}**\nWant more stats? **Use this [tool](https://slynx.xyz/trove/class_builder)**", color=0x008000, timestamp=last_updated)
                e.set_author(name=f"Rank #{builds.index(build) + 1}", icon_url=_class.image)
                for stat, value in build[4].items():
                    e.add_field(name=stat, value=value)
                if builds.index(build) + 1 > 1:
                    e.add_field(name=f"#1 {'Coeff' if build_type != 'health' else 'Health'} Difference", value=-(builds[0][0] - build[0]))
                    if light and build_type not in ["health", "coeff"]:
                        e.add_field(name=f"#1 Light Difference", value=round(-(builds[0][2]-build[2]), 2))
                    e.add_field(name="\u200b", value="\u200b")
                return [{"content": None, "embed": e}]
        pages = []
        i = 0
        builds = self.chunks(builds[:100], 10)
        for page in builds:
            e = discord.Embed(color=0x008000, timestamp=last_updated)
            e.set_footer(text="Values on masterchat's spreadsheet and coefficient mod lack accuracy due to the use of rounded values, bot is more accurate since it doesn't use rounding. | Last updated on")
            e.description = (
                "\n**Type** " + build_type.capitalize() + (" (DPS)" if build_type == "light" else "") + 
                "\n**Ally** " + (ally["name"] if ally else "❌") +
                (f"\n**Gear CD Count** {cd_count}" if build_type == "farm" else "") + 
                "\n**Subclass** " + (subclass.name if subclass else "❌") + ("" if not subclass or subclass.short != "GS" else " **(Mid Air bonus applied)**") + 
                "\n**Food** " + "Freerange Electrolytic Crystals" +
                "\n**Force Light** " + (str(light) if light else "❌") + 
                "\n**Bard Battle Song** " + ("✅" if bardcd else "❌") + 
                ("\n**Cosmic Primordial** ✅" if primordial else "") + 
                ("\n**Crystal 5** ✅" if crystal5 else ""))
            e.description += "\n\n`👍` Cheap\n`💸` Expensive"
            e.description += ("\n\nElemental Format: `DMG/CD/DMG/CD`\nCosmic Format: `DMG/CD/<LIGHT> DMG/CD/<LIGHT>`" if build_type != 'health' else "\n\nFormat: `HP/HP%/HP/HP%`") + "\n```"
            x = i * 10
            for b in page:
                x += 1
                boosts = []
                [boosts.extend(i) for i in b[1]]
                if not light or (light and build_type in ["coeff", "health"]):
                    del boosts[6]
                    del boosts[8]
                if not light and build_type not in ["coeff", "health"]:
                    boosts = boosts[:4]
                text = f"{str(x) + '.': <4}{self.build_text(boosts)} --> {b[0]}" + (f" [{b[3]}]" if build_type != "health" and mod else "") + (f" | {b[2]} Light" if build_type not in ["coeff", "health"] else "")
                build_rolls = b[1]
                if (3 <= build_rolls[0][0] <= 6 and
                    3 <= build_rolls[0][1] <= 6 and 
                    6 <= build_rolls[1][0] <= 12 and 
                    6 <= build_rolls[1][1] <= 12):
                    text += " 👍\n"
                else:
                    text += " 💸\n"
                e.description += text
            e.description += f"```\nLearn more about builds with `{self.ctx.prefix}help build`"
            e.set_author(name=f"Top 100 Gem Builds for {_class.name} | Page {i+1} of {len(builds)}", icon_url=_class.image)
            page = {
                "page": i,
                "content": None,
                "embed": e
            }
            i += 1
            pages.append(page)
        return pages



  # Values

    def get_value(self, attr: str):
        return sum(getattr(self, attr).values())

    @property
    def base_light(self):
        return {
            "Hat": 845,
            "Face": 845,
            "Weapon": 1690,
            "Banner": 900,
            "Food": 300,
            "Mastery": 1000,
            "Dragon": 50,
            "Ring": 325
        }

    @property
    def base_damage(self):
        return {
            "Weapon": 14300,
            "Ring": 14300,
            "Banner": 500
        }

    @property
    def base_cd(self):
        return {
            "Weapon": 44.2,
            "Face": 44.2,
            "Hat": 44.2,
            "Club": 100
        }

    @property
    def pd_dragons(self):
        return 6400

    @property
    def md_dragons(self):
        return 5900

    @property
    def cd_dragons(self):
        return 80

    @property
    def bonus_dmg(self):
        return {
            "mastery": 500*0.2,
            "club": 15
        }

    @property
    def base_health(self):
        return {
            "Weapon": 18876,
            "Face": 28600,
            "Hat": 28600,
            "Ring": 14475,
            "Dragons": 39000,
            "Torch": 10000
        }

    @property
    def base_healthper(self):
        return {
            "Face": 234,
            "Hat": 234,
            "Dragons": 117,
            "Ally": 15,
            "Mastery": 300,
            "Fixture": 100
        }

  # Helper

    def chunks(self, lst, n):
        result = []
        for i in range(0, len(lst), n):
            result.append(lst[i:i + n])
        return result

    def build_text(self, build):
        text = ""
        text += f"{'/'.join([str(i) for i in build][:4]): <8}"
        if len(build) == 8:
            text += " + " + "/".join([str(i) for i in build][4:])
        elif len(build) == 10:
            text += " + " + "/".join([str(i) for i in build][4:7]) + " " + "/".join([str(i) for i in build][7:10])
        return text

    def _generate_combinations(self, coeff=False, light=False):
        tuples1 = []
        for i in range(10):
            tuples1.append((i, 9 - i))
        tuples2 = []
        for i in range(19):
            tuples2.append((i, 18 - i))
        tuples3 = []
        for x in range(4):
            for y in range(4):
                for z in range(4):
                    if x + y + z != 3: 
                        continue
                    if coeff and x + y != 3:
                        continue
                    if not light and not coeff and z != 3:
                        continue
                    tuples3.append((x, y, z))
        tuples4 = []
        for x in range(7):
            for y in range(7):
                for z in range(7):
                    if x + y + z != 6:
                        continue
                    if coeff and x + y != 6:
                        continue
                    if not light and not coeff and z != 6:
                        continue
                    tuples4.append((x, y, z))
        return itertools.product(tuples1, tuples2, tuples3, tuples4)
    
    def _get_gem_build_stats(self, build, prim=False, health=False):
        lesser_base_light = self.values.lesser_base_light
        lesser_base_dmg = self.values.lesser_base_dmg if not health else self.values.lesser_base_health
        lesser_base_cd = self.values.lesser_base_cd if not health else self.values.lesser_base_healthper
        emp_base_light = self.values.emp_base_light
        emp_base_dmg = self.values.emp_base_dmg if not health else self.values.emp_base_health
        emp_base_cd = self.values.emp_base_cd if not health else self.values.emp_base_healthper
        gem_light = 2 * lesser_base_light[0] + emp_base_light[0]
        cosmic_gem_dmg = 2 * lesser_base_dmg[0] + emp_base_dmg[0]
        cosmic_gem_cd = 2 * lesser_base_cd[0] + emp_base_cd[0]
        gem_light += emp_base_light[1] * build[2][2] + lesser_base_light[1] * build[3][2]
        cosmic_gem_dmg += emp_base_dmg[1] * build[2][0] + lesser_base_dmg[1] * build[3][0]
        cosmic_gem_cd += emp_base_cd[1] * build[2][1] + lesser_base_cd[1] * build[3][1]
        gem_dmg = 6 * lesser_base_dmg[0] + 3 * emp_base_dmg[0]
        gem_cd = 6 * lesser_base_cd[0] + 3 * emp_base_cd[0]
        gem_dmg += emp_base_dmg[1] * build[0][0] + lesser_base_dmg[1] * build[1][0]
        gem_cd += emp_base_cd[1] * build[0][1] + lesser_base_cd[1] * build[1][1]
        if prim:
            gem_light = gem_light * 1.1 
            gem_dmg = (gem_dmg + cosmic_gem_dmg) * 1.1
            gem_cd = (gem_cd + cosmic_gem_cd) * 1.1
        else:
            gem_dmg = gem_dmg * 1.1 + cosmic_gem_dmg
            gem_cd = gem_cd * 1.1 + cosmic_gem_cd
        return gem_dmg, gem_cd, gem_light
