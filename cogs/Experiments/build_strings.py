# Priority: 1
import re
import discord
from discord.ext import commands
from json import dumps
from zlib import compress, decompress
from binascii import hexlify, unhexlify


class BuildStrings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx):
        data = {'_class': 'Chloromancer', 'build_type': 'farm', 'build': ((0, 9), (11, 7), (3, 0, 0), (1, 3, 2)), 'subclass': 'Dino Tamer', 'primordial': False, 'crystal5': False, 'light': 8000, 'cd_count': 0, 'deface': False, 'ally': {'name': 'Orchian', 'type': 'farm', 'damage': 'MD', 'stats': {'Damage': 25, 'Light': 400}}, 'mod': False, 'bardcd': False, 'food': True, 'filter': None}
        Compressed = self.CompressBuild(data)
        await ctx.send(Compressed)
        await ctx.send(self.DecompressBuild(Compressed))

    def CompressBuild(self, data):
        string = self.DataToString(data)
        compressed = compress(string.encode("utf-8"), 9)
        return hexlify(compressed).decode("utf-8")

    def DecompressBuild(self, string):
        compressed = unhexlify(string.encode("utf-8"))
        string = decompress(compressed).decode("utf-8")
        return self.StringToData(string)

    def DataToString(self, data, level=0):
        string = ""
        if isinstance(data, dict):
            if level: string += "{"
            for vbit in data.values():
                if len(string) > 1:
                    string += ";" if level == 0 else ("#" if level == 1 else "$")
                string += self.DataToString(vbit, level+1)
            if level: string += "}"
        elif isinstance(data, tuple):
            if string:
                string += ";"
            string += str(data).replace(" ", "")
        else:
            if string:
                string += ";"
            string += str(data)
        return string

    def StringToData(self, string):
        keys = [
            '_class',
            'build_type',
            'build',
            'subclass',
            'primordial',
            'crystal5',
            'light',
            'cd_count',
            'deface',
            'ally',
            'mod',
            'bardcd',
            'food',
            'filter'
        ]
        values = string.split(";")
        rebuilt_dict = {keys[i]:values[i] for i in range(len(values))}
        for k, v in rebuilt_dict.items():
            if v in ["True", "False", "None"] or v.startswith("(("):
                rebuilt_dict[k] = eval(v)
            if v.isdigit():
                rebuilt_dict[k] = int(v)
            if v.startswith("{"):
                ally_keys = ["name", "type", "damage", "stats"]
                values = v.replace("{", "").replace("}", "").split("#")
                rebuilt_ally = {ally_keys[i]:values[i] for i in range(len(values))}
                stats = rebuilt_ally["stats"].replace("{", "").replace("}", "").split("$")
                stat_keys = ["Damage", "Light"]
                rebuilt_ally["stats"] = {stat_keys[i]:stats[i] for i in range(len(stats))}
                rebuilt_dict[k] = rebuilt_ally
        return f"```json\n{dumps(rebuilt_dict, indent=4)}```"

def setup(bot):
    bot.add_cog(BuildStrings(bot))