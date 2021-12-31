import hashlib
import re
from datetime import datetime, timedelta
from typing import Literal, Optional

from discord import Embed
from discord.embeds import EmptyEmbed
from pytz import UTC

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
            raise ValueError("No time parts detected")
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
            if self.seconds < value:
                continue
            if len(used_units) == 3:
                break
            used_units.append(name)
            time, self.seconds = divmod(self.seconds, value)
            strings.append(f"{time} {name}" + ("s" if time != 1 else ""))
        return strings
            
    def __str__(self):
        return ", ".join(self._naturaldelta())

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
