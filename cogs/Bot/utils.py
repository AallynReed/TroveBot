# Priority: 8
import base64
import json
import math
import re
from PIL import Image
from io import BytesIO
from datetime import datetime
from typing import Literal, Optional

import discord
from discord.ext import commands


class MD(dict):
    def __str__(self):
        string = ", ".join(
            [
                f'"{k}":{str(type(v).__name__)}'
                for k, v in self.items()
            ]
        )
        return f"<{string}>"
    
    def __repr__(self):
        return self.__str__()

    @property
    def as_str(self):
        return json.dumps(self, indent=4)
        
    def get(self, keys: str):
        keys = keys.split(".")
        value = self
        for key in keys:
            if not key:
                raise ValueError("Malformed Pointer")
            try:
                value = value[key]
            except KeyError:
                return None
        if isinstance(value, dict):
            value = MD(value)
        return value

class Utilities(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.utils = self

 # Trove

    def get_augmentation_cost(self, stat, prefered=None):
        r_augment = [2.500, 1.250, 0.833, 0.625]
        p_augment = [5.000, 2.500, 1.667, 1.250]
        s_augment = [12.500, 6.250, 4.167, 3.125]
        per = int(stat[1])
        focus = [0, 0, 0]
        while per < 100:
            if prefered == "superior" and per + s_augment[int(stat[0])] <= 100:
                per += s_augment[int(stat[0])]
                focus[2] += 1
                continue
            if prefered in ["precise", "superior"] and per + p_augment[int(stat[0])] <= 100:
                per += p_augment[int(stat[0])]
                focus[1] += 1
                continue
            per += r_augment[int(stat[0])]
            focus[0] += 1
        flux = 0
        flux += focus[0] * 1200
        flux += focus[1] * 2000
        flux += focus[2] * 50000
        bb = focus[0] + focus[1] + focus[2]
        hod = focus[0] * 4
        water = focus[1] * 3000
        air = focus[1] * 3000
        fire = focus[1]* 3000
        dd = focus[2] * 30
        ts = focus[2] * 3
        costs = [
            ["<:flux:873290253849489408> Flux", flux],
            ["<:boundb:873290253656555551> Bound Brilliance", bb],
            ["<:hod:873290253895622676> Heart of Darkness", hod],
            ["<:watergd:873290253761413182> Water Gem Dust", water],
            ["<:airgd:873290254029828136> Air Gem Dust", air],
            ["<:firegd:873290254138892408> Fire Gem Dust", fire],
            ["<:diadrag:873290253794963566> Diamond Dragonite", dd],
            ["<:titan_soul:873290253862064138> Titan Soul", ts]]
        return focus, costs
  
    def points_to_mr(self, points, cap=1000):
        i = 1
        while True:
            if i == cap:
                break
            i += 1
            if i <= 5:
                increment = 25
            elif 6 <= i <= 10:
                increment = 50
            elif 11 <= i <= 20:
                increment = 75
            elif 21 <= i <= 300:
                increment = 100
            elif i > 300:
                increment = 150 + math.ceil((i - 300) * 0.5)
            points -= increment
            if points <= 0:
                if points < 0:
                    points += increment
                    i -= 1
                break
        return i, points, increment

    def mr_to_points(self, level):
        points = 0
        i = 1
        while True:
            i += 1
            if i <= 5:
                increment = 25
            elif 6 <= i <= 10:
                increment = 50
            elif 11 <= i <= 20:
                increment = 75
            elif 21 <= i <= 300:
                increment = 100
            elif i > 300:
                increment = 150 + math.ceil((i - 300) * 0.5)
            if i == level+1:
                if i-1 > 300:
                    increment = 150 + math.ceil((i-1 - 300) * 0.5)
                break
            points += increment
        return increment, points

 # Other

    async def give_roles(self, member, roles):
        if isinstance(roles, discord.Role):
            roles = [roles]
        failed = []
        for role in roles:
            if role in member.roles:
                continue
            try:
                await member.add_roles(role)
            except:
                failed.append(role)
        return failed

    async def take_roles(self, member, roles):
        if isinstance(roles, discord.Role):
            roles = [roles]
        failed = []
        for role in roles:
            if role not in member.roles:
                continue
            try:
                await member.remove_roles(role)
            except:
                failed.append(role)
        return failed

    async def url_to_bytes(self, link):
        async with self.bot.AIOSession.get(link) as resp:
            if resp.status == 200:
                bytes = await resp.read()
                bytes = base64.b64encode(bytes)
                return bytes
            else:
                return None

    async def get_command(self, commandname, subcommands=None):
        for command in await self.bot.help.get_all_commands():
            if commandname == command.name or commandname in command.aliases:
                if not subcommands:
                    return command
                for subcommand in subcommands:
                    if command.subcommands:
                        for sub in command.subcommands:
                            if sub.name == subcommand or subcommand in sub.aliases:
                                command = sub
                                continue
                    else:
                        return None
                return command
        return None

    async def get_subcommand_help(self, ctx, bot):
        command_name = str(ctx.command)
        subcommands = command_name.split(" ")
        if subcommands:
            command_db  = await self.bot.db.db_help.find_one({"_id": subcommands[0]})
        else:
            command_db  = await self.bot.db.db_help.find_one({"_id": command_name})
        prefix = ctx.prefix
        if len(subcommands) == 1:
            command_name = bot.all_commands[subcommands[0]]
            command_path = command_db
            description = command_path["description"]
            subcommands = list(command_path["subcommands"])
            example = command_path["example"].replace("{prefix}", prefix)
        elif len(subcommands) == 2:
            command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]]
            command_path = command_db["subcommands"][subcommands[1]]
            description = command_path["description"]
            example = command_path["example"].replace("{prefix}", prefix)
        elif len(subcommands) == 3:
            command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]]
            command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]
            description = command_path["description"]
            example = command_path["example"].replace("{prefix}", prefix)
        elif len(subcommands) == 4:
            command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]].all_commands[subcommands[3]]
            command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]["subcommands"][subcommands[3]]
            description = command_path["description"]
            example = command_path["example"].replace("{prefix}", prefix)
        e=discord.Embed(description=description, colour=discord.Color.random())
        e.set_author(name=f"{str(command_name).capitalize()} Commands", icon_url=ctx.guild.icon)
        if "subcommands" in command_path and command_path["subcommands"]:
            for subcommand in command_path["subcommands"]:
                description = command_path["subcommands"][subcommand]["description"]
                example = command_path["subcommands"][subcommand]["example"].replace("{prefix}", prefix)
                e.add_field(name=f'• {prefix}{command_name} {subcommand}', value=f'{description}\n**Example:** ``{example}``', inline=False)
        return e

    def time_str(self, text, short=True, abbr=False):
        data = []
        w_ratio = 60 * 60 * 24 * 365.25 / 12 / 604800
        t = 0
        t_str = ""
        reg = r"([0-9]+)(?: )?(decade|month|[cywdhms])+"
        if isinstance(text, str):
            data = re.findall(reg, text, re.IGNORECASE)
        if isinstance(text, int) or isinstance(text, float):
            t = text
        for u in data:
            if u[1].lower() == "c":
                t += 604800 * w_ratio * 12 * 100 * int(u[0])
            if u[1] in ["D", "decade"]:
                t += 604800 * w_ratio * 12 * 10 * int(u[0])
                continue
            if u[1].lower() == "y":
                t += 604800 * w_ratio * 12 * int(u[0])
            if u[1] in ["M", "month"]:
                t += 604800 * w_ratio * int(u[0])
                continue
            if u[1].lower() == "w":
                t += 604800 * int(u[0])
            if u[1].lower() == "d":
                t += 86400 * int(u[0])
            if u[1].lower() == "h":
                t += 3600 * int(u[0])
            if u[1] == "m":
                t += 60 * int(u[0])
            if u[1].lower() == "s":
                t += int(u[0])
        if t > 10**13:
            raise Exception("Error")
        c, s = divmod(t, 604800 * w_ratio * 12 * 100)
        D, s = divmod(s, 604800 * w_ratio * 12 * 10)
        y, s = divmod(s, 604800 * w_ratio * 12)
        M, s = divmod(s, 604800 * w_ratio)
        w, s = divmod(s, 604800)
        d, s = divmod(s, 86400)
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        c = int(c)
        D = int(D)
        y = int(y)
        M = int(M)
        w = int(w)
        d = int(d)
        h = int(h)
        m = int(m)
        s = int(s)
        if c >= 1:
            t_str += f"{c}c" if short else f"{c} century"
            if not short and c != 1:
                t_str = t_str[:-1]
                t_str += "ies"
        if D >= 1:
            t_str += " " if t_str != "" else ""
            t_str += f"{D}D" if short else f"{D} decade"
            t_str += "s" if not short and D != 1 else ""
        if y >= 1:
            t_str += " " if t_str != "" else ""
            t_str += f"{y}y" if short else f"{y} year"
            t_str += "s" if not short and y != 1 else ""
        if M >= 1:
            if not (abbr and (D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{M}M" if short else f"{M} month"
                t_str += "s" if not short and M != 1 else ""
        if w >= 1:
            if not (abbr and (D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{w}w" if short else f"{w} week"
                t_str += "s" if not short and w != 1 else ""
        if d >= 1:
            if not (abbr and (y or D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{d}d" if short else f"{d} day"
                t_str += "s" if not short and d != 1 else ""
        if h >= 1:
            if not (abbr and (w or M or y or D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{h}h" if short else f"{h} hour"
                t_str += "s" if not short and h != 1 else ""
        if m >= 1:
            if not (abbr and (d or w or M or y or D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{m}m" if short else f"{m} minute"
                t_str += "s" if not short and m != 1 else ""
        if s >= 1:
            if not (abbr and (h or d or w or M or y or D or c)):
                t_str += " " if t_str != "" else ""
                t_str += f"{s}s" if short else f"{s} second"
                t_str += "s" if not short and s != 1 else ""
        return math.ceil(t), t_str

    def chunks(self, lst, n):
        result = []
        for i in range(0, len(lst), n):
            result.append(lst[i:i + n])
        return result

    def progress_bar(self, total, current, size=20):
        text = "`﴾"
        progress = round(current / total * size)
        text += "=" * progress
        text += " " * (size - progress)
        text += "﴿`"
        return text

    @property
    def emotes(self):
        return {
            "loading": "<a:loading:844624767239192576>",
            "loaded": "<:done:844624767217958922>"
        }

    TimestampStyle = Literal['f', 'F', 'd', 'D', 't', 'T', 'R']

    def format_dt(self, dt: datetime, style: Optional[TimestampStyle] = None):
        if style is None:
            return f'<t:{int(dt.timestamp())}>'
        return f'<t:{int(dt.timestamp())}:{style}>'

    def json(self, data):
        return MD(data)

    async def getch(obj, attr: str, id: int):
        getter = getattr(obj, f'get_{attr}')(id)
        if getter is None:
            try:
                getter = await getattr(obj, f'fetch_{attr}')(id)
            except discord.errors.NotFound:
                ...
        return getter

    async def get_sigil(self, pr, totalmr):
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
        if 800 <= totalmr <= 849:
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
        if url_mr == "" or url_pr == "":
            return False
        image_mr = await (await self.bot.AIOSession.get(url_mr)).read()
        img1 = Image.open(BytesIO(image_mr))
        image_pr = await (await self.bot.AIOSession.get(url_pr)).read()
        img2 = Image.open(BytesIO(image_pr))
        img1.paste(img2, (0, 0), img2)
        data = BytesIO()
        img1.save(data, "PNG")
        data.seek(0)
        return data

    def primes(self, start, end):
        for num in range(2, end+1):
            if num < 2:
                continue
            kill = False
            for n in range(2,int(num/2)+1):
                if num%n==0:
                    kill = True
            if kill:
                continue
            yield num

def setup(bot):
    bot.add_cog(Utilities(bot))
