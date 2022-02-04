from asyncio import create_task, sleep
from json import load

from motor.motor_asyncio import AsyncIOMotorClient


class DatabaseManager():
    def __init__(self, database):
        self.ready = False
        self.client = AsyncIOMotorClient()
        self.database = self.client["Nova"]
        self.collections = [
            "bot",
            "users",
            "guilds",
            "members"
        ]
        self.prefixes = {"guilds": {}, "users": {}}
        create_task(self._ensure_database())

    async def wait_until_ready(self):
        while not self.ready:
            await sleep(0.1)
        return

    async def _ensure_database(self):
        await self._ensure_collections()
        self._load_defaults()
        self.ready = True

    async def _ensure_collections(self):
        collections = await self.database.list_collection_names()
        for collection in self.collections:
            if collection not in collections:
                await self.database.create_collection(collection)
            setattr(self, "db_"+collection, self.database[collection])

    def _load_defaults(self):
        for collection in self.collections:
            try:
                setattr(self, f"_default_{collection}", load(open(f"constants/database/defaults/{collection}.json")))
            except:
                ...

    async def load_prefixes(self):
        async for guild in self.db_guilds.find({"prefixes": {"$ne": []}}, {"prefixes": 1}):
            self.prefixes["guilds"][guild["_id"]] = guild["prefixes"]
        async for user in self.db_users.find({"prefixes": {"$ne": []}}, {"prefixes": 1}):
            self.prefixes["users"][user["_id"]] = user["prefixes"]

    async def database_check(self, guild_id, user_id):
        ...

    @property
    async def get_metadata(self):
        await self.wait_until_ready()
        data = await self.db_bot.find_one({"_id": "0511"}, {"metadata": 1})
        return data["metadata"]

