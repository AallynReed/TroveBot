import hashlib
import re
from datetime import datetime, timedelta
from typing import Literal, Optional

from colors import color
from discord import Embed
from discord.embeds import EmptyEmbed
from pytz import UTC

from utils.others import RandomID

_TimestampStyle = Literal['f', 'F', 'd', 'D', 't', 'T', 'R']

class CEmbed(Embed):
    def set_author(self, *, name, url=EmptyEmbed, icon_url=EmptyEmbed):
        return super().set_author(name=name, url=url, icon_url=icon_url or Embed.Empty)

    def set_footer(self: Embed, *, text = EmptyEmbed, icon_url = EmptyEmbed):
        return super().set_footer(text=text, icon_url=icon_url or Embed.Empty)

    def set_thumbnail(self, *, url):
        return super().set_thumbnail(url=url or Embed.Empty)

    def set_image(self, *, url):
        return super().set_image(url=url or Embed.Empty)

class Sage:
    def __init__(self, data=None, **kwargs):
        self.sanity(data or kwargs)

    def sanity(self, data):
        fields = [
            "name",
            "content",
            "author"
        ]
        missing = [f for f in fields if f not in data.keys()]
        if missing:
            raise ValueError(", ".join(missing) + " fields are missing to build a sage")
        data["_id"] = data.get("_id")
        if not data["_id"]:
            data["_id"] = RandomID()
        data["approved"] = data.get("approved", False)
        data["deleted"] = data.get("deleted", False)
        data["created_at"] = data.get("created_at", datetime.utcnow().timestamp())
        data["image"] = data.get("image", None)
        data["uses"] = data.get("uses", 0)
        self.__dict__.update(data)

    def use(self):
        self.uses += 1

    @property
    def data(self):
        return self.__dict__

    @property
    def creation_date(self):
        return datetime.utcfromtimestamp(self.created_at)

class TimeConverter():
    def __init__(self, input, fuzzy=True):
        self.fuzzy = fuzzy
        if isinstance(input, timedelta):
            self.seconds = input.total_seconds()
        elif isinstance(input, (int, float)):
            self.seconds = int(input)
        elif isinstance(input, str):
            if input.isdigit():
                self.seconds = int(input)
            else:
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

    def get_weekly_time(self, time):
        time_elapsed = time.timestamp() - self.first_weekly_ds.timestamp()
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

    def luxion_start_rwts(self, style: Optional[_TimestampStyle]=None):
        start = self.rw_time(self.luxion_start)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'

    def luxion_end_rwts(self, style: Optional[_TimestampStyle]=None):
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

    def corruxion_start_rwts(self, style: Optional[_TimestampStyle]=None):
        start = self.rw_time(self.corruxion_start)
        if style is None:
            return f'<t:{int(start.timestamp())}>'
        return f'<t:{int(start.timestamp())}:{style}>'

    def corruxion_end_rwts(self, style: Optional[_TimestampStyle]=None):
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

class Colorize():
    def __init__(self, text: str, clean=False):
        self.text = text
        self.clean = clean
        self.CBRegex = r"(?i)(?s)(```.*?```)"
        self.PointerRegex = r"(§([ubi]*)?(?:\$([0-7]))?(?:\#([0-7]))?<(?:%(.*?)%|~(.*?)~)>)"
        self.colorize()

    @property
    def Colors(self):
        return {
        "0": "black",
        "1": "red",
        "2": "green",
        "3": "yellow",
        "4": "blue",
        "5": "magenta",
        "6": "cyan",
        "7": "white",
    }

    def colorize(self):
        codeblocks = re.findall(self.CBRegex, self.text)
        if codeblocks:
            for codeblock in codeblocks:
                parsed = re.sub(self.PointerRegex, self.parsecolors if not self.clean else self.clean_formatting, codeblock, flags=re.MULTILINE)
                self.text = self.text.replace(codeblock, parsed)

    def parsecolors(self, match):
        groups = match.groups()
        text = groups[4] or groups[5]
        text = re.sub(self.PointerRegex, self.parsecolors, text, re.MULTILINE).replace("[0m", "")
        formats = groups[1].lower()
        formatting = {
            "underline": "u" in formats,
            "bold": "b" in formats,
            "italic": "i" in formats # Not Supported by discord
        }
        style = None if not sum(formatting.values()) else "+".join([f for f, v in formatting.items() if v])
        fgc = self.Colors[groups[2]] if groups[2] else None
        bgc = self.Colors[groups[3]] if groups[3] else None
        return color(text, fg=fgc, bg=bgc, style=style)

    def clean_formatting(self, match):
        groups = match.groups()
        return groups[4] or groups[5]

    def __str__(self):
        return self.text
    
    def __repr__(self):
        return self.__str__()

class Dict(dict):
    def __init__(self, data: dict):
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
