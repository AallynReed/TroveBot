# Priority: 1
from io import BytesIO
from json import dumps
from math import floor

import discord
from utils.buttons import ProfileView
from utils.objects import GameClass, UserCommand


class ProfileUserCommand(UserCommand):
    async def _profile(self, ctx, user, _class, server=1, is_active=False):
        data = await ctx.bot.db.db_profiles.find_one({"discord_id": user.id, "Bot Settings.Server": server}, {"Collected Mastery": 0, "Stats": 0})
        if not data:
            return await ctx.send(f"No profile found for **{user}**" + (f"\nUse `{ctx.prefix}profile request` to learn how to submit one." if user == ctx.author else ""))
        _class = _class or GameClass().cconvert(data["Bot Settings"]["Primary"])
        if _class.name not in data["Classes"].keys():
            await ctx.send(f"**{user}** hasn't submitted that class yet.")
        if isinstance(user, discord.Member):
            avatar = user.display_avatar
        else:
            avatar = user.avatar if user.avatar else user.default_avatar
        stats = data["Classes"][_class.name]
        classes = [c for c in ctx.bot.Trove.values.classes if c.name in data["Classes"].keys() and c.name != _class.name]
        try:
            subclass = GameClass().cconvert(stats["Subclass"])
        except:
            subclass = None
        db_bot = (await ctx.bot.db.db_bot.find_one({"_id": "0511"}, {"mastery": 1}))["mastery"]
        max_live_mastery = db_bot["max_live_mastery"]
        percentage = floor(data["Trove Mastery Points"] / max_live_mastery * 1000)/10
        percentage = percentage if percentage - int(percentage) else int(percentage)
        try:
            data = {
                "Token": "TkT8qs9lviaI3wyCQdTD",
                "User": str(user),
                "Nick": data["Name"],
                "Class": _class.image,
                "Subclass": subclass.subimage if subclass else None,
                "Avatar": str(avatar.replace(format="png", size=256).url),
                "Power Rank": int(stats["Power Rank"]),
                "Level": stats["Level"],
                "Prestige Level": stats["Prestige Level"],
                "Trove Mastery": data["Trove Mastery"],
                "Trove Percentage": percentage,
                "Geode Mastery": data["Geode Mastery"],
                "Total Mastery": data["Total Mastery"],
                "Physical Damage": stats["Physical Damage"],
                "Magic Damage": stats["Magic Damage"],
                "Maximum Health": stats["Maximum Health"],
                "Maximum Energy": stats["Maximum Energy"],
                "Health Regen": stats["Health Regen"],
                "Energy Regen": stats["Energy Regen"],
                "Movement Speed": stats["Movement Speed"],
                "Attack Speed": stats["Attack Speed"],
                "Jump": stats["Jump"],
                "Critical Hit": stats["Critical Hit"],
                "Critical Damage": stats["Critical Damage"],
                "Magic Find": stats["Magic Find"],
                "Light": stats["Light"],
                "Coefficient": stats["Coefficient"],
                "Clubs": data["Clubs"],
                "Hidden": data["Bot Settings"]["Hidden Clubs"],
                "Server": server
            }
        except:
            return await ctx.send(f"**{user}**'s profile for **{_class.name}** is outdated", delete_after=10, ephemeral=True)
        try:
            request = await ctx.bot.AIOSession.post("https://trove.slynx.xyz/profiles/image", data=str(dumps(data)))
        except:
            return await ctx.send("Can't get profile right now, try again later.")
        img = discord.File(BytesIO(await request.read()), filename="image.png")
        view = ProfileView(ctx, self._profile, user, classes, server)
        if is_active:
            view.message = is_active
            return view, img
        view.message = await ctx.send(file=img, view=view if classes else None)

class LiveProfileUserCommand(ProfileUserCommand, name="Trove Profile"):
    async def callback(self):
        ctx = await self.get_context()
        user = self.target
        await self._profile(ctx, user, _class=None, server=1, is_active=False)

class PTSProfileUserCommand(ProfileUserCommand, name="Trove Profile PTS"):
    async def callback(self):
        ctx = await self.get_context()
        user = self.target
        await self._profile(ctx, user, _class=None, server=0, is_active=False)

def setup(bot):
    bot.application_command(LiveProfileUserCommand)
    bot.application_command(PTSProfileUserCommand)