import re
from datetime import timedelta

from discord import Embed
from discord.embeds import EmptyEmbed
from discord.ext import commands


class Empty():
    ...

class NovaContext(commands.Context):
    ...

class CEmbed(Embed):
    def set_author(self, *, name, url=EmptyEmbed, icon_url=EmptyEmbed):
        return super().set_author(name=name, url=url, icon_url=icon_url or Embed.Empty)

    def set_footer(self: Embed, *, text = EmptyEmbed, icon_url = EmptyEmbed):
        return super().set_footer(text=text, icon_url=icon_url or Embed.Empty)

    def set_thumbnail(self, *, url):
        return super().set_thumbnail(url=url or Embed.Empty)

    def set_image(self, *, url):
        return super().set_image(url=url or Embed.Empty)

class TimeConverter():
    def __init__(self, input, fuzzy=True):
        self.fuzzy = fuzzy
        if isinstance(input, (int, float)) or input.isdigit():
            self.seconds = int(input)
        elif isinstance(input, str):
            parts = self._get_time_parts(input)
            result = self._parts_to_int(parts)
            self.seconds = result
        else:
            raise ValueError("Wrong Input")
        self._seconds = self.seconds
        self.delta = timedelta(seconds=self.seconds)

    @property
    def _periods(self):
        periods = {}
        periods["year"] = 31557600 if self.fuzzy else 31536000
        periods["month"] = 2629800 if self.fuzzy else 2592000
        periods["week"] = 604800
        periods["day"] = 86400
        periods["hour"] = 3600
        periods["minute"] = 60
        periods["second"] = 1
        return periods

    def _get_time_parts(self, input):
        regex = r"((?!0)[0-9]+) ?(?:(y(?:ears?)?)|(months?)|(w(?:eeks?)?)|(d(?:ays?)?)|(h(?:ours?)?)|(m(?:inutes?)?)|(s(?:econds?)?))"
        result = re.findall(regex, input, re.IGNORECASE)
        if not result:
            raise ValueError("No time parts detected.")
        return result

    def _parts_to_int(self, parts):
        seconds = 0
        for part in parts:
            broken_part = part[1:]
            for i in range(len(broken_part)):
                if broken_part[i]:
                    seconds += int(part[0]) * list(self._periods.values())[i]
        return seconds

    def _naturaldelta(self):
        strings = []
        used_units = []
        for name, value in self._periods.items():
            if self._seconds < value:
                continue
            if len(used_units) == 3:
                break
            used_units.append(name)
            time, self._seconds = divmod(self._seconds, value)
            strings.append(f"{time} {name}" + ("s" if time != 1 else ""))
        return strings
            
    def __str__(self):
        return ", ".join(self._naturaldelta())

    def __int__(self):
        return self.seconds

class Dict(dict):
    def __init__(self, data: dict):
        super().__init__(data)
        self._data = data
        self._default = None

    def fix(self, default: dict=None):
        if not default and not self.default:
            raise Exception("No defaut was set!")
        elif default:
            self._set_default(default)
        default_keys, target_keys, diff = self._get_diff()
        diff = diff.copy()
        diff = self._remove_excess(diff, self._get_max_length(default_keys))
        self._build_missing(diff)
        return self._data

    def _set_default(self, default: dict):
        self._default = default

    def _get_diff(self):
        default = set(self._get_nested_keys(self._default))
        target = set(self._get_nested_keys(self._data))
        diff = list(default - target)
        return default, target, diff

    def _get_nested_keys(self, data: dict, nest=""):
        if isinstance(data, dict):
            for key, value in data.items():
                yield nest + key if nest else key
                for ret in self._get_nested_keys(value, nest=nest+key+"."):
                    yield ret

    def _get_max_length(self, default_keys):
        i = 1
        for x in default_keys:
            split = len(x.split("."))
            if split > i:
                i = split
        return i

    def _build_missing(self, diff):
        for i in diff:
            split = i.split(".")
            navigate = self._default
            current = self._data
            for key in split:
                navigate = navigate[key]
                if key == split[-1]:
                    current[key] = navigate
                elif key not in current:
                    current[key] = {}
                current = current[key]

    def _remove_excess(self, diff, max): 
        for x in range(max):
            for i in diff:
                try:
                    split = i.split(".")
                    _split = ".".join([split[y] for y in range(x)])
                    if i != _split and "." in i and _split in diff and i in diff:
                        diff.remove(i)
                except:
                    pass
        return diff
