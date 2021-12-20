import asyncio

from motor.motor_asyncio import AsyncIOMotorClient
from copy import deepcopy


class Profile():
    def __init__(self, data=None):
        self._data = data

class DB():
    def __init__(self, database):
        self.client = AsyncIOMotorClient()
        self.database = self.client[database]
        asyncio.create_task(self._database_setup())

    async def _database_setup(self):
        await self._setup_collections_shortcuts()

    async def _setup_collections_shortcuts(self):
        collections = await self.database.list_collection_names()
        for collection in collections:
            setattr(self, "db_"+collection, self.database[collection])

class Database(DB):
    def __init__(self, database="trove"):
        super().__init__(database=database)
        asyncio.create_task(self._ensure_database())

    async def _ensure_database(self):
        while True:
            if hasattr(self, "db_bot"):
                bot = await self.db_bot.find_one({"_id": "0511"}, {"_id": 1})
                if not bot:
                    await self.db_bot.insert_one(self._default_bot())
                break
            await asyncio.sleep(1)

    async def database_check(self, server_id=None):
        if server_id:
            data = await self.db_servers.find_one({"_id": server_id})
            if not data:
                new_data = self._default_server(server_id)
                await self.db_servers.insert_one(self._default_server(server_id))
            else:
                new_data = Dict(deepcopy(data)).fix(self._default_server(server_id))
                if new_data != data:
                    await self.db_servers.update_one({"_id": server_id}, {"$set": new_data})
            return new_data

    async def stats_list(self):
        stats = []
        async for doc in self.db_profiles.find({}, {"Bot Settings": 0, "Collected Mastery": 0, "Clubs": 0, "_id": 0}):
            for i in doc["Classes"].keys():
                stats.extend(list(self._return_stat_names(doc["Classes"][i], "Classes.Class.")))
            del doc["Classes"]
            stats.extend(list(self._return_stat_names(doc)))
        return sorted(list(set(stats)))

    def _return_stat_names(self, data: dict, nest=""):
        if isinstance(data, dict):
            for key, value in data.items():
                if key == "Last Update":
                    continue
                if not isinstance(value, (dict, int, float, list)):
                    continue 
                if not nest and isinstance(value, (int, float)):
                    yield key
                if nest:
                    yield nest + key
                for ret in self._return_stat_names(value, nest=nest+key+"."):
                    yield ret

    def _default_bot(self):
        return {
            "_id": "0511",
            "blacklist": [],
            "prefixes": {
                "servers": {},
                "users": {}
            },
            "mastery": {
                "mastery_update": 0,
                "geode_mastery_update": 0,
                "max_live_mastery": 0,
                "max_live_mastery_geode": 0,
                "max_pts_mastery": 0,
                "max_pts_mastery_geode": 0
            },
            "giveaway": [],
            "server_status": {}
        }

    def _default_server(self, server_id):
        return {
            "_id": server_id,
            "locale": "en",
            "PTS mode": False,
            "self_cleanup": False,
            "commands": {
                "list_mode": 0,
                "list": {}
            },
            "leaderboards": {
                "list": []
            },
            "automation": {
                "daily": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "weekly": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "dragon_merchant": {
                    "voice": {
                        "channel": None
                    },
                    "text": {
                        "channel": None,
                        "role": None
                    }
                },
                "nickname": {
                    "toggle": False
                },
                "club": {
                    "name": None,
                    "member_role": None,
                    "member_role_only_profile": False
                }
            },
            "stat_roles": {
                "settings": {},
                "roles": {}
            },
            "clock": {
                "channel": None,
                "format": None,
                "slowmode": 5
            },
            "forums_posts": {},
            "twitch": {
                "channel": None,
                "message": None,
                "channels": [],
                "notified": []
            },
            "blacklist": {
                "channel": None
            }
        }

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