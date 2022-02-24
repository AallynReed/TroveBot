import json
import re
import urllib.request as urlget
from io import BytesIO

import discord
from discord import app
from discord.ext import commands
from openpyxl import load_workbook
from PIL import Image

from utils.CustomObjects import TimeConverter
from utils.trove import Ally


class ACResponse(app.AutoCompleteResponse):
    def __getitem__(self, x):
        if isinstance(x, slice):
            response = ACResponse()
            for i, (k, v) in enumerate(self.items()):
                step_start = x.start or 0
                if x.start and i < x.start or x.stop and i >= x.stop:
                    continue
                if x.step and (i-step_start)%x.step:
                    continue
                response.add_option(k, v)
            return response
        elif isinstance(x, int):
            return ACResponse([{k: v} for k, v in self.items()][x])
        elif isinstance(x, str):
            return super().__getitem__(x)
        else:
            raise TypeError("slice indices must be integers or None")

class SlashContext():
    def __init__(self, command):
        self.command = command
        self.interaction = command.interaction
        self.channel = self.interaction.channel
        self.author = self.interaction.user
        self.guild = self.interaction.guild
        self.bot = command.client
        self.defer = self.interaction.response.defer
        self.prefix = "/"
        self.on_slash_command()

    def on_slash_command(self):
        self.bot.dispatch("app_slash", self)

    async def send(self, content=None, **kwargs):
        return await self.interaction.followup.send(content=content, **kwargs)

class SlashCommand(app.SlashCommand):
    async def get_context(self, ephemeral=False):
        ctx = SlashContext(self)
        await ctx.defer(ephemeral=ephemeral)
        return ctx

    async def error(self, error):
        if isinstance(error, discord.errors.NotFound) and error.text == "Unknown interaction":
            ...
        else:
            await super().error(error)

class UserCommandContext():
    def __init__(self, command):
        self.command = command
        self.interaction = command.interaction
        self.channel = self.interaction.channel
        self.author = self.interaction.user
        self.guild = self.interaction.guild
        self.bot = command.client
        self.defer = self.interaction.response.defer
        self.prefix = "/"
        self.on_user_command()

    def on_user_command(self):
        self.bot.dispatch("app_user", self)

    async def send(self, content=None, **kwargs):
        return await self.interaction.followup.send(content=content, **kwargs)

class UserCommand(app.UserCommand):
    async def get_context(self):
        ctx = UserCommandContext(self)
        await ctx.defer()
        return ctx

    async def error(self, error):
        if isinstance(error, discord.errors.NotFound) and error.text == "Unknown interaction":
            ...
        else:
            await super().error(error)

class TimeConvert(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            converted = TimeConverter(argument)
            return converted
        except:
            raise commands.BadArgument("Invalid input.")

class DictConvert(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            dicti = json.loads(argument)
            return dicti
        except:
            raise commands.BadArgument("Not a valid json text")

class TrovePlayer(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            nick = re.match(r"^([a-z_0-9]{2,19})$", argument, re.IGNORECASE)
            if nick:
                return argument
            raise Exception("No shot.")
        except:
            raise commands.BadArgument("Invalid nickname.")

class ArgumentFinder(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            variables = {
                "build_type": "light",
                "build": None,
                "subclass": None,
                "primordial": False,
                "crystal5": False, 
                "light": 0,
                "cd_count": 0,
                "deface": False,
                "ally": True,
                "mod": False,
                "bardcd": False
            }
            regex = r"(?i)(health|hp|mh|tank|life|coeff|ms|farm)"
            res = re.search(regex, argument)
            if res:
                if res.group(0).lower() in ["health", "hp", "tank", "life", "mh"]:
                    variables["build_type"] = "health"
                if res.group(0).lower() in ["farm", "ms"]:
                    variables["build_type"] = "farm"
                    regex = r"(?i)(?:farm|ms)(?: )([1-3])(?:$| )"
                    resi = re.findall(regex, argument)
                    if resi:
                        if int(resi[0]) > 2:
                            raise Exception("Invalid Build")
                        variables["cd_count"] = int(resi[0])
                if res.group(0).lower() in ["coeff"]:
                    variables["build_type"] = "coeff"
            regex = r"(?i)(prim(?:ordial)?|c(?:rystal)?(?: )?5)"
            res = re.findall(regex, argument)
            if res:
                for group in res:
                    if group.lower() in ["prim", "primordial"]:
                        variables["primordial"] = True
                    if group.lower() in ["crystal5", "crystal 5", "c5", "c 5"]:
                        variables["crystal5"] = True
            regex = r"([0-9]{1})[\/]([0-9]{1})[\/ ]([0-9]{1,2})[\/]([0-9]{1,2})(?:(?: )?[\/+ ](?: )?([0-9]{1})[\/]([0-9]{1})(?:[\/ ]([0-9]{1})[\/ ]([0-9]{1}))?[\/ ]([0-9]{1})[\/]([0-9]{1}))?"
            res = re.findall(regex, argument)
            if res:
                res = self.chunk_builds([int(i) for i in list(res[0]) if i], 2)
                variables["build"] = res
            for i in argument.lower().split(" "):
                try:
                    if i:
                        variables["subclass"] = await GameClass().convert(ctx, i)
                except:
                    pass
                if i.isdigit() and int(i) > 7000:
                    variables["light"] = int(i)
            regex = r"(?i)(?:deface|noface)"
            res = re.findall(regex, argument)
            if res:
                variables["deface"] = True
            regex = r"(?i)(?:mod|game)"
            res = re.findall(regex, argument)
            if res:
                variables["mod"] = True
            regex = r"(?i)(?:noally|nopet)"
            res = re.findall(regex, argument)
            if res:
                variables["ally"] = False
            regex = r"(?i)(?:bardcd|bardbuff|song)"
            res = re.findall(regex, argument)
            if res:
                variables["bardcd"] = True
            return variables
        except:
            raise commands.BadArgument("Invalid build.")

    def chunk_builds(self, lst, n):
        result = []
        if len(lst) in [4, 8]:
            for i in range(0, len(lst), 2):
                result.append(tuple(lst[i:i + 2]))
            if len(lst) == 4:
                result.append((0,0,3))
                result.append((0,0,6))
            if len(lst) == 8:
                y = sum(result[2])
                result[2] = tuple(list(result[2]) + [3-y])
                y = sum(result[3])
                result[3] = tuple(list(result[3]) + [6-y])

        else:
            first_lst = lst[:4]
            for i in range(0, len(first_lst), 2):
                result.append(tuple(first_lst[i:i + 2]))
            first_lst = lst[4:]
            for i in range(0, len(first_lst), 3):
                result.append(tuple(first_lst[i:i + 3]))
        return tuple(result)

class BuildType(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            build_type = None
            regex = r"(?i)(health|hp|mh|tank|life|light|damage|ms|farm|dmg|coeff|dps)"
            res = re.search(regex, argument)
            if res:
                if res.group(0).lower() in ["health", "hp", "tank", "life", "mh"]:
                    build_type = "tank"
                if res.group(0).lower() in ["farm", "ms"]:
                    build_type = "farm"
                if res.group(0).lower() in ["light", "damage", "coeff", "dmg", "dps"]:
                    build_type = "light"
            if not build_type:
                raise Exception("Invalid build type.")
            return build_type
        except:
            raise commands.BadArgument("Invalid build.")
    
    def cconvert(self, argument):
        try:
            build_type = None
            regex = r"(?i)(health|hp|mh|tank|life|light|damage|ms|farm|dmg|coeff|dps)"
            res = re.search(regex, argument)
            if res:
                if res.group(0).lower() in ["health", "hp", "tank", "life", "mh"]:
                    build_type = "tank"
                if res.group(0).lower() in ["farm", "ms"]:
                    build_type = "farm"
                if res.group(0).lower() in ["light", "damage", "coeff", "dmg", "dps"]:
                    build_type = "light"
            if not build_type:
                raise Exception("Invalid build type.")
            return build_type
        except:
            raise commands.BadArgument("Invalid build.")

class GameClass(commands.Converter):
    def __init__(self):
        self.values = Values()
        
    async def convert(self, ctx, argument):
        try:
            for _class in self.values.classes:
                if _class.short.lower() == argument.lower() or _class.name.lower().startswith(argument.lower()):
                    return _class
            raise Exception("Wrong")
        except:
            raise commands.BadArgument("Invalid class.")

    def cconvert(self, argument):
        try:
            classes = self.values.classes
            for _class in classes:
                if _class.short.lower() == argument.lower() or _class.name.lower().startswith(argument.lower()):
                    return _class
            raise Exception("Wrong")
        except:
            raise commands.BadArgument("Invalid class.")

class MemeType(commands.Converter):
    def __init__(self):
        self.values = Values()
        
    async def convert(self, ctx, argument):
        try:
            if argument.lower() in ["biome", "boss", "creature"]:
                return argument.lower()
            raise Exception("Wrong")
        except:
            raise commands.BadArgument("Invalid class.")

class TroveClass():
    def __init__(self, data):
        self.values = Values(False)
        self.name = data[1]
        self.short = data[0]
        self.image = data[2]
        self.subimage = data[3]
        self.get_values()

    def __eq__(self, obj):
        return self.name == obj.name

    def __ne__(self, obj):
        return not self.__eq__(obj)

    def __str__(self):
        return self.name

    def get_values(self):
        for key, _ in self.values.scaling.items():
            if key == self.name:
                for k, v in self.values.scaling[key].items():
                    setattr(self, k, v)

class Values():
    def __init__(self, load_classes=True):
        self._preload(load_classes)

    def _preload(self, load_classes):
        self.gems
        self.dragons
        if load_classes:
            self.classes = self._classes()
        self.gear_builds = json.loads(open("/home/sly/nucleo/data/builds.json", "r").read())
        self._allies_raw = json.loads(open("/home/sly/nucleo/data/allies.json", "r").read())
        self.allies = [Ally(data) for data in self._allies_raw.values()]

    def update_gear_builds(self):
        urlget.urlretrieve("https://docs.google.com/spreadsheets/d/16LhF4_19iEldLQxlmQsrBucpeIQd10CSODtbWrN1xo0/export?format=xlsx&id=16LhF4_19iEldLQxlmQsrBucpeIQd10CSODtbWrN1xo0", 'data/sheets/gear_builds.xlsx')
        wb = load_workbook(filename="data/sheets/gear_builds.xlsx", data_only=True)["Builds"]
        gear = {}
        def text_format(text):
            text = text.strip()
            if text == "MH":
                text = "Maximum Health"
            if text == "MH%":
                text = "Maximum Health%"
            if text == "MD":
                text = "Magic Damage"
            if text == "PD":
                text = "Physical Damage"
            if text == "CD":
                text = "Critical Damage"
            if text == "PP":
                text = "Preference"
            if text == "AS":
                text = "Attack Speed"
            if text == "MS":
                text = "Movement Speed"
            if text == "ER":
                text = "Energy Regeneration"
            if text == "DDV":
                text = "Death-Defying Vial"
            if text == "Conjurer's":
                text = "Conjurer's Crucible Vial"
            if text == "Elysian":
                text = "Elysian Bandolier"
            if text == "LL":
                text = "Lunar Lancer"
            if text == "PC":
                text = "Pirate Captain"
            if text == "Chloro":
                text = "Chloromancer"
            if text == "Freerange":
                text = "Freerange Electrolytic Crystals"
            if text == "Lil Whiptop":
                text = "Lil' Whiptop"
            if text == "Pyrodisk":
                text = "Pyrodisc"
            return text

        for i in range(3, 42):
            row = str(i)
            _class = wb["B"+row].value
            if not _class:
                continue
            if _class not in gear.keys():
                gear[_class] = {}
            types = [["light", "DPS"], ["farm", "Farm"], ["tank", "Tank"]]
            for _type in types:
                if _type[0] not in gear[_class].keys():
                    gear[_class][_type[0]] = {"enabled": False}
            for _type in types:
                if wb["C"+row].value == _type[1]:
                    gear[_class][_type[0]]["enabled"] = True
                    break
            build = gear[_class][_type[0]]
            build["tier"] = int(wb["D"+row].value)
            build["hat"] = [text_format(text) for text in wb["E"+row].value.split("/")]
            build["weapon"] = [text_format(text) for text in wb["F"+row].value.split("/")]
            build["face"] = [text_format(text) for text in wb["G"+row].value.split("/")]
            build["ring"] = [text_format(text) for text in wb["H"+row].value.split("/")]
            build["ally"] = [text_format(text) for text in wb["I"+row].value.split("/")]
            build["banner"] = [text_format(text) for text in wb["J"+row].value.split("/")]
            build["subclass"] = [text_format(text) for text in wb["K"+row].value.split("/")]
            build["flask"] = [text_format(text) for text in wb["L"+row].value.split("/")]
            build["emblem"] = [text_format(text) for text in wb["M"+row].value.split("/")] + [text_format(text) for text in wb["N"+row].value.split("/")]
            build["food"] = [text_format(text) for text in wb["O"+row].value.split("/")]
            build["gems"] = []
            if wb["P"+row].value == "Yes":
                build["gems"].append("Class Gem")
            elif wb["P"+row].value == "PP":
                build["gems"] += [text_format(wb["P"+row].value)]
            build["gems"].append(text_format(wb["Q"+row].value))
            if len(wb["R"+row].value.split(" and ")) > 1:
                build["gems"] += [text_format(i) for i in wb["R"+row].value.split(" and ")]
            else:
                build["gems"] += ["/".join([text_format(i) for i in wb["R"+row].value.split(" or ")])]
            build["gems"].append(wb["S"+row].value + " (Cosmic)")

        json.dump(gear, open("/home/sly/nucleo/data/builds.json", "w+"), indent=4)
        self._preload(False)

    @property
    def gems(self):
       # Light
        self.lesser_base_light = (385, 200)
        self.emp_base_light = (451, 266)
       # Damage
        self.lesser_base_dmg = (5390, 2800)
        self.lesser_base_cd = (77, 40)
        self.emp_base_dmg = (6314, 3724)
        self.emp_base_cd = (90.2, 53.2)
       # Health
        self.lesser_base_health = (19250, 10000)
        self.lesser_base_healthper = (192.5, 100)
        self.emp_base_health = (22550, 13300)
        self.emp_base_healthper = (225.5, 133)

    @property
    def base_light(self):
        items = {
            "hat": 845,
            "face": 845,
            "weapon": 1690,
            "banner": 900,
            "food": 300,
            "mastery": 1000,
            "dragon": 50,
            "ally": 300,
            "ring": 325
        }
        return sum(items.values())

    @property
    def base_damage(self):
        items = {
            "weapon": 14300,
            "face": 4719,
            "ring": 14300,
            "banner": 500
        }
        return sum(items.values())

    @property
    def base_cd(self):
        items = {
            "weapon": 44.2,
            "face": 44.2,
            "hat": 44.2,
            "dunno": 100
        }
        return sum(items.values())

    @property
    def base_mf(self):
        items = {
            "dragons": 2500,
            "dragon_badges": 450,
            "hat": 260,
            "weapon": 260,
            "face": 260,
            "ring": 300,
            "pc": 70,
            "ally": 150,
            "fixture": 200
        }
        return sum(items.values())

    @property
    def dragons(self):
        self.pd_dragons = 6400
        self.md_dragons = 5900
        self.cd_dragons = 80

    @property
    def bonus_dmg(self):
        items = {
            "mastery": 100,
            "club": 15,
            "ally": 20
        }
        return sum(items.values())

    @property
    def base_health(self):
        items = {
            "weapon": 18876,
            "face": 28600,
            "hat": 28600,
            "ring": 14475,
            "dragons": 39000,
            "torch": 10000
        }
        return sum(items.values())

    @property
    def base_healthper(self):
        items = {
            "face": 234,
            "hat": 234,
            "dragons": 117,
            "ally": 15,
            "mastery": 300,
            "fixture": 100
        }
        return sum(items.values())

    def max_pr(self, mastery, pts=False, console=False):
        items = {
            "hat": 1698,
            "weapon": 1698,
            "face": 1698,
            "gems": 24769,
            "dragons": 1620,
            "banner": 350,
            "ring": 1513,
            "ally": 75,
            "class_level": 450,
            "subclass": 90,
            "emblem": 50 * 2,
            "flask": 50,
            "mastery_geode": 5 * 100,
            "mastery_rank": 4 * 500,
            "500_plus_mastery": mastery
        }
        return sum(items.values())

    def _classes(self):
        classes = [
            ["SH", "Shadow Hunter", "https://i.imgur.com/E32gMrC.png", "https://i.imgur.com/HvvIHUK.png"],
            ["IS", "Ice Sage", "https://i.imgur.com/uzTPDbL.png", "https://i.imgur.com/lVXnoD1.png"],
            ["DL", "Dracolyte", "https://i.imgur.com/jQ6M4UG.png", "https://i.imgur.com/qpIjWn1.png"],
            ["CB", "Candy Barbarian", "https://i.imgur.com/OIzAgRD.png", "https://i.imgur.com/Vv3qZg1.png"],
            ["RV", "Revenant", "https://i.imgur.com/dY6GEGx.png", "https://i.imgur.com/ZQ0LzUd.png"],
            ["CM", "Chloromancer", "https://i.imgur.com/YMeZfxb.png", "https://i.imgur.com/FdKga43.png"],
            ["FT", "Fae Trickster", "https://i.imgur.com/gjzUWZD.png", "https://i.imgur.com/njRkhk2.png"],
            ["TR", "Tomb Raiser", "https://i.imgur.com/iJuk7W0.png", "https://i.imgur.com/VjWyI45.png"],
            ["BR", "Boomeranger", "https://i.imgur.com/RzUypVH.png", "https://i.imgur.com/RfKxS11.png"],
            ["KT", "Knight", "https://i.imgur.com/doiHKau.png", "https://i.imgur.com/CASI02e.png"],
            ["VG", "Vanguardian", "https://i.imgur.com/ZzDHxh8.png", "https://i.imgur.com/wlxZlVn.png"],
            ["DT", "Dino Tamer", "https://i.imgur.com/heHb98J.png", "https://i.imgur.com/UXgnvBw.png"],
            ["LL", "Lunar Lancer", "https://i.imgur.com/MocVYYr.png", "https://i.imgur.com/e0hjnQk.png"],
            ["PC", "Pirate Captain", "https://i.imgur.com/lXUABOn.png", "https://i.imgur.com/kofWx3X.png"],
            ["NN", "Neon Ninja", "https://i.imgur.com/k0gqiM2.png", "https://i.imgur.com/M2GRzim.png"],
            ["GS", "Gunslinger", "https://i.imgur.com/8DW31Et.png", "https://i.imgur.com/eOxgSgJ.png"],
            ["BD", "Bard", "https://i.imgur.com/Fiam1k5.png", "https://i.imgur.com/HkwAqzR.png"]
        ]
        return sorted([TroveClass(i) for i in classes], key=lambda x: x.name)

    @property
    def scaling(self):
        return {
            "Boomeranger": {
                "cd": 50,
                "dmg": 3080,
                "health": 6150,
                "healthper": 30,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 10,
                "emoji": "<:c_BR:876846904019943504>"
            },
            "Candy Barbarian": {
                "cd": 50,
                "dmg": 2900,
                "health": 4970,
                "healthper": 20,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 30,
                "emoji": "<:c_CB:876846886462554193>"
            },
            "Chloromancer": {
                "cd": 50,
                "dmg": 2376,
                "health": 4850,
                "healthper": 20,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_CM:876846891747410001>"
            },
            "Dino Tamer": {
                "cd": 50,
                "dmg": 2376,
                "health": 4850,
                "healthper": 20,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_DT:876846922135126036>"
            },
            "Dracolyte": {
                "cd": 75,
                "dmg": 2440,
                "health": 4850,
                "healthper": 20,
                "dmg_type": "MD",
                "infinite_as": True,
                "class_bonus": 0,
                "emoji": "<:c_DL:876846884143116368>"
            },
            "Fae Trickster": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_FT:876846898718339103>"
            },
            "Gunslinger": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_GS:876846930871865385>"
            },
            "Ice Sage": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_IS:876846881311965224>"
            },
            "Bard": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_BD:876846944604024842>"
            },
            "Knight": {
                "cd": 50,
                "dmg": 3202,
                "health": 6150,
                "healthper": 30,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_KT:876846916749656115>"
            },
            "Lunar Lancer": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 30,
                "emoji": "<:c_LL:876846924932718592>"
            },
            "Neon Ninja": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_NN:876846928808259654>"
            },
            "Pirate Captain": {
                "cd": 165,
                "dmg": 2376,
                "health": 4850,
                "healthper": 20,
                "dmg_type": "MD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_PC:876846926841135124>"
            },
            "Revenant": {
                "cd": 50,
                "dmg": 3230,
                "health": 5310,
                "healthper": 45,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_RV:876846888819777547>"
            },
            "Shadow Hunter": {
                "cd": 75,
                "dmg": 2376,
                "health": 4850,
                "healthper": 0,
                "dmg_type": "PD",
                "infinite_as": True,
                "class_bonus": 0,
                "emoji": "<:c_SH:876846872503943170>"
            },
            "Tomb Raiser": {
                "cd": 50,
                "dmg": 2376,
                "health": 4850,
                "healthper": 20,
                "dmg_type": "MD",
                "infinite_as": True,
                "class_bonus": 0,
                "emoji": "<:c_TR:876846901801123850>"
            },
            "Vanguardian": {
                "cd": 75,
                "dmg": 2976,
                "health": 5750,
                "healthper": 20,
                "dmg_type": "PD",
                "infinite_as": False,
                "class_bonus": 0,
                "emoji": "<:c_VG:876846919572394045>"
            }
        }

    async def get_sigil(self, session, pr, totalmr):
        url_mr = ""
        url_pr = ""
        # Mastery
        if 1 <= totalmr <= 9:
            url_mr = "https://i.imgur.com/ytgFQJq.png"
        if 10 <= totalmr <= 29:
            url_mr = "https://i.imgur.com/qFlsroS.png"
        if 30 <= totalmr <= 49:
            url_mr = "https://i.imgur.com/VcnmxYG.png"
        if 50 <= totalmr <= 74:
            url_mr = "https://i.imgur.com/k1uSwAJ.png"
        if 75 <= totalmr <= 99:
            url_mr = "https://i.imgur.com/ST8NDsO.png"
        if 100 <= totalmr <= 149:
            url_mr = "https://i.imgur.com/uWDUKxk.png"
        if 150 <= totalmr <= 199:
            url_mr = "https://i.imgur.com/atceNdE.png"
        if 200 <= totalmr <= 249:
            url_mr = "https://i.imgur.com/WuPD8Vi.png"
        if 250 <= totalmr <= 299:
            url_mr = "https://i.imgur.com/IG4Uncx.png"
        if 300 <= totalmr <= 349:
            url_mr = "https://i.imgur.com/222rH1k.png"
        if 350 <= totalmr <= 399:
            url_mr = "https://i.imgur.com/9hiZXCZ.png"
        if 400 <= totalmr <= 449:
            url_mr = "https://i.imgur.com/ZEAVWDA.png"
        if 450 <= totalmr <= 499:
            url_mr = "https://i.imgur.com/Z7g60mW.png"
        if 500 <= totalmr <= 549:
            url_mr = "https://i.imgur.com/BzJj2lL.png"
        if 550 <= totalmr <= 599:
            url_mr = "https://i.imgur.com/n04blVH.png"
        if 600 <= totalmr <= 649:
            url_mr = "https://i.imgur.com/EufwyxA.png"
        if 650 <= totalmr <= 699:
            url_mr = "https://i.imgur.com/wq5D6Iw.png"
        if 700 <= totalmr <= 749:
            url_mr = "https://i.imgur.com/sYTJNHU.png"
        if 750 <= totalmr <= 799:
            url_mr = "https://i.imgur.com/jpx5SZE.png"
        if 800 <= totalmr:
            url_mr = "https://i.imgur.com/6kS2qH3.png"
        # Power
        if 1 <= pr <= 249:
            url_pr = "https://i.imgur.com/ytgFQJq.png"
        if 250 <= pr <= 549:
            url_pr = "https://i.imgur.com/Lu25aXz.png"
        if 550 <= pr <= 899:
            url_pr = "https://i.imgur.com/BLgFldK.png"
        if 900 <= pr <= 1199:
            url_pr = "https://i.imgur.com/93uU1oA.png"
        if 1200 <= pr <= 2499:
            url_pr = "https://i.imgur.com/AOWt4On.png"
        if 2500 <= pr <= 4999:
            url_pr = "https://i.imgur.com/l6TejUh.png"
        if 5000 <= pr <= 7499:
            url_pr = "https://i.imgur.com/rF0ezqj.png"
        if 7500 <= pr <= 9999:
            url_pr = "https://i.imgur.com/G27zi8j.png"
        if 10000 <= pr <= 14999:
            url_pr = "https://i.imgur.com/cTCm7QK.png"
        if 15000 <= pr <= 19999:
            url_pr = "https://i.imgur.com/9QN4F1W.png"
        if 20000 <= pr <= 24999:
            url_pr = "https://i.imgur.com/FpXg2LU.png"
        if 25000 <= pr <= 29999:
            url_pr = "https://i.imgur.com/E7mqm6F.png"
        if 30000 <= pr <= 34999:
            url_pr = "https://i.imgur.com/x7EqPKj.png"
        if 35000 <= pr <= 39999:
            url_pr = "https://i.imgur.com/cdT2Hub.png"
        if 40000 <= pr:
            url_pr = "https://i.imgur.com/6m6jfYq.png"
        if url_mr and url_pr:
            img1 = await self.get_image(session, url_mr)
            img2 = await self.get_image(session, url_pr)
            img1.paste(img2, (0, 0), img2)
        else:
            if url_mr:
                img1 = await self.get_image(session, url_mr)
            else:
                img1 = await self.get_image(session, url_pr)
        return img1

    async def get_image(self, session, link):
        async with session.get(link) as request:
            return Image.open(BytesIO(await request.read())).convert("RGBA")

class AugmentationStats(commands.Converter):
    async def convert(self, ctx, argument):
        augments = re.split(r"(?![\w: ]|$)", argument.lower())
        output = {"gems": [], "focus": "precise"}
        for raw_gem in augments:
            gem = []
            stats = re.findall(r"(([0-3]):(100|[0-9]{1,2})) ?(rough|precise|superior)?", raw_gem)
            if len(stats) != 3:
                raise Exception("Gems must have 3 stats.")
            boosts = 0
            for stat in stats:
                boosts += int(stat[1])
                gem.append([int(stat[1]), int(stat[2])])
                if stat[-1]:
                    output["focus"] = stat[-1]
            if boosts != 3:
                raise Exception("Gems must have 3 boosts.")
            output["gems"].append(gem)
        return output
