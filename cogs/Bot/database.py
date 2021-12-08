# Priority: 1
import json
import os

from bson.objectid import ObjectId
from discord.ext import commands


class Database(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.backup_directory = "dbbackups"

    @commands.command(hidden=True)
    async def full_backup(self, ctx):
        if ctx.author.id != 565097923025567755:
            return
        databases = ["Slynx", "trove"]
        if not os.path.exists(self.backup_directory):
            os.mkdir(self.backup_directory)
        for database in databases:
            if not os.path.exists(f"{self.backup_directory}/{database}"):
                os.mkdir(f"{self.backup_directory}/{database}")
            collections = await self.bot.db.client[database].list_collection_names()
            for collection in collections:
                data = await self.bot.db.client[database][collection].find({}).to_list(length=99999999)
                _f = f"{self.backup_directory}/{database}/{collection}.json"
                for d in data:
                    if isinstance(d["_id"], ObjectId):
                        d["_id"] = f"ObjectId_{str(d['_id'])}"
                with open(_f, "w+") as f:
                    f.write(str(json.dumps(data)))
                await ctx.send(f"Backed up **{database}/{collection}**")
        await ctx.send("Finished database backups.")

    @commands.command(hidden=True)
    async def fullrestore(self, ctx):
        if ctx.author.id != 565097923025567755:
            return
        if not os.path.exists(self.backup_directory) or not os.listdir(self.backup_directory):
            return await ctx.send("No Backups found!")
        await ctx.send("Restoring...")
        for database in os.listdir(self.backup_directory):
            for collection in os.listdir(f"{self.backup_directory}/{database}"):
                _f = f"{self.backup_directory}/{database}/{collection}"
                data = json.loads(open(_f, "r").read())
                for document in data:
                    if isinstance(document["_id"], str):
                        split_id = document["_id"].split("_")
                        if split_id[0] == "ObjectId":
                            document["_id"] = ObjectId("_".join(split_id[1:]))
                    while True:
                        try:
                            coll = collection.replace(".json", "")
                            try:
                                await self.bot.db.client[database][coll].delete_one({"_id": document["_id"]})
                            except:
                                pass
                            await self.bot.db.client[database][coll].insert_one(document)
                            break
                        except Exception as e:
                            print(e)
                await ctx.send(f"Restored up **{database}/{coll}**")
        await ctx.send("Finished restoring database backups.")

def setup(bot):
    bot.add_cog(Database(bot))
