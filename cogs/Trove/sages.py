# Priority: 1
import re

import utils.checks as perms
from discord.ext import commands


class Sages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @perms.admins()
    async def sage_id(self, ctx, *, sage):
        sage = await self.bot.db.db_tags.find_one({"name": {"$regex": f"(?i){re.escape(sage)}"}})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage.")
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}`")

    @commands.command()
    @perms.admins()
    async def sage_remove(self, ctx, sage_id):
        sage = await self.bot.db.db_tags.find_one({"_id": sage_id, "deleted": False})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage or it's already deleted.")
        await self.bot.db.db_tags.update_one({"_id": sage_id}, {"$set": {"deleted": True}})
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}` was deleted.")

    @commands.command()
    @perms.admins()
    async def sage_recover(self, ctx, sage_id):
        sage = await self.bot.db.db_tags.find_one({"_id": sage_id, "deleted": True})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage or it's not deleted.")
        await self.bot.db.db_tags.update_one({"_id": sage_id}, {"$set": {"deleted": False}})
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}` was recovered.")

    @commands.command()
    @perms.admins()
    async def sage_approve(self, ctx, sage_id):
        sage = await self.bot.db.db_tags.find_one({"_id": sage_id, "approved": False})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage or it's already approved.")
        await self.bot.db.db_tags.update_one({"_id": sage_id}, {"$set": {"approved": True}})
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}` was approved.")
        
    @commands.command()
    @perms.admins()
    async def sage_deny(self, ctx, sage_id):
        sage = await self.bot.db.db_tags.find_one({"_id": sage_id, "approved": True})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage or it's already denied.")
        await self.bot.db.db_tags.update_one({"_id": sage_id}, {"$set": {"approved": False}})
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}` was denied.")

    @commands.command()
    @perms.admins()
    async def sage_delete(self, ctx, sage_id):
        sage = await self.bot.db.db_tags.find_one({"_id": sage_id, "deleted": True})
        if not sage:
            return await ctx.send("That ID doesn't correspond to an existing sage or it's not deleted yet.")
        await self.bot.db.db_tags.delete_one({"_id": sage_id})
        await ctx.send(f"Sage **{sage['name']}** with ID `{sage['_id']}` was permanently deleted.")

def setup(bot):
    bot.add_cog(Sages(bot))