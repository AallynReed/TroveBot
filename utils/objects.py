import json
import re
import urllib.request as urlget
from datetime import datetime, timedelta
import hashlib
from io import BytesIO
from typing import Literal, Optional

from discord.ext import commands
from openpyxl import load_workbook
from PIL import Image
from pytz import UTC
from utils.trovesaurus import Ally

TimestampStyle = Literal['f', 'F', 'd', 'D', 't', 'T', 'R']

class DictConvert(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            dicti = json.loads(argument)
            return dicti
        except:
            raise Exception("Not a valid json text")

class TrovePlayer(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            nick = re.match(r"^([a-z_0-9]{2,19})$", argument, re.IGNORECASE)
            if nick:
                data = await ctx.bot.db.db_profiles.find_one({"Name": {"$regex": f"(?i)^{argument}$"}})
                if data:
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

class Class():
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
        return sorted([Class(i) for i in classes], key=lambda x: x.name)

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

class TroveTime():
    def __init__(self):
        self.first_weekly_ds = datetime(2020, 3, 23, tzinfo=UTC)
        self.luxion = datetime(2021, 3, 19, tzinfo=UTC)
        self.corruxion = datetime(2021, 3, 12, tzinfo=UTC)
        day = 60 * 60 * 24
        self.week_length = day * 7
        self.dweek_length = day * 14
        self.stay_time = day * 3

    @property
    def now(self):
        return datetime.utcnow().replace(microsecond=0) - timedelta(hours=11)

    @property
    def weekly_time(self):
        time_elapsed = self.now.timestamp() - self.first_weekly_ds.timestamp()
        weeks, _ = divmod(time_elapsed, self.week_length)
        time_split = weeks / 4
        time_find = time_split - int(time_split)
        return int(time_find * 4)

    @property
    def luxion_time(self):
        time_elapsed = self.now.timestamp() - self.luxion.timestamp()
        dweeks, time = divmod(time_elapsed, self.dweek_length)
        return time, dweeks, time_elapsed

    @property
    def is_luxion(self):
        return self.luxion_time[0] < self.stay_time

    @property
    def luxion_start(self):
        if self.is_luxion:
            return self.luxion + timedelta(seconds=self.dweek_length * self.luxion_time[1])
        return self.luxion + timedelta(seconds=self.dweek_length * (self.luxion_time[1] + 1))

    @property
    def luxion_end(self):
        return self.luxion_start + timedelta(seconds=self.stay_time)

    def rw_time(self, dt: datetime):
        return dt + timedelta(hours=11)

    def luxion_start_rwts(self, style: Optional[TimestampStyle]=None):
        start = self.rw_time(self.luxion_start)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'

    def luxion_end_rwts(self, style: Optional[TimestampStyle]=None):
        start = self.rw_time(self.luxion_end)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'
        
    @property
    def corruxion_time(self):
        time_elapsed = self.now.timestamp() - self.corruxion.timestamp()
        dweeks, time = divmod(time_elapsed, self.dweek_length)
        return time, dweeks, time_elapsed

    @property
    def is_corruxion(self):
        return self.corruxion_time[0] < self.stay_time

    @property
    def corruxion_start(self):
        if self.is_corruxion:
            return self.corruxion + timedelta(seconds=self.dweek_length * self.corruxion_time[1])
        return self.corruxion + timedelta(seconds=self.dweek_length * (self.corruxion_time[1] + 1))

    @property
    def corruxion_end(self):
        return self.corruxion_start + timedelta(seconds=self.stay_time)

    def rw_time(self, dt: datetime):
        return dt + timedelta(hours=11)

    def corruxion_start_rwts(self, style: Optional[TimestampStyle]=None):
        start = self.rw_time(self.corruxion_start)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'

    def corruxion_end_rwts(self, style: Optional[TimestampStyle]=None):
        start = self.rw_time(self.corruxion_end)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'

class MetricsConverter():
    def __init__(self, encryption, data=None):
        self._encryption = encryption
        self._raw_data = data
        self._data = None
        self._converted = None
        self._profile = None
        self._regex = r"(?:([a-z 0-9]+) = ([a-z 0-9_\.]+)|\[([a-z 0-9-]+)\])"
    
    def _convert_value(self, value):
        if value.isdigit():
            value = int(value)
        else:
            try:
                value = float(value)
            except ValueError:
                ...
        return value
    
    def _get_hash(self):
        result = re.findall(r"Hash = ([a-z0-9]+)", self._raw_data)
        if not result:
            raise Exception("Hash not found.")
        self._data = self._raw_data.replace(f"Hash = {result[0]}\n", "")
        self._original_hash = result[0]
        self._hash = getattr(hashlib, self._encryption)(self._data.encode()).hexdigest()

    def _validate(self):
        if not self._data:
            self._get_hash()
        return self._hash == self._original_hash
        
    def _extract(self):
        if not self._validate():
            del self._original_hash
            del self._hash
            raise Exception("File was edited.")
        result = re.findall(self._regex, self._data, re.IGNORECASE)
        return result
        
    def convert(self):
        extracted = self._extract()
        data = {}
        current_tab = None
        for key, value, tab in extracted:
            if tab and tab not in data.keys():
                data[tab] = {} if tab != "Clubs" else []
                current_tab = tab
                continue
            value = self._convert_value(value)
            if current_tab and current_tab != "Clubs":
                data[current_tab][key] = value
            elif current_tab:
                data[current_tab].append(str(value))
            else:
                data[key] = value
        self._converted = data
        
    def _make_profile(self):
        if not self._converted:
            self.convert()
        self._profile = self._converted
        
    def get_profile(self):
        if not self._profile:
            self._make_profile()
        return self._profile

class AugmentationStats(commands.Converter):
    async def convert(self, ctx, argument):
        gem_regex = r"(?:([0-3]):([0-9]{1,2})(?:\W|$))"
        focus_regex = r"rough|precise|superior"
        find_focus = re.findall(focus_regex, argument)
        focus = find_focus or "precise"
        if isinstance(focus, list):
            focus = focus[0]
        def adjust_missing(gem):
            for _ in range(3 - len(gem)):
                gem.append(None)
            return gem
        gems_input = []
        for gem in argument.split("+"):
            gem = gem.strip()
            gem = re.findall(gem_regex, gem)
            if not len(gem):
                continue
            if len(gem) > 3:
                raise Exception("Gems can't have more than 3 stats.")
            boosts = 0
            for boost, progress in gem:
                boosts += int(boost)
            if boosts > 3:
                raise Exception("Gems can't have more than 3 boosts.")
            gem = adjust_missing(gem)
            gems_input.append(gem)
        if not gems_input:
            raise Exception("No valid Gem format found.")
        data = {"gems": gems_input, "focus": focus}
        return data
