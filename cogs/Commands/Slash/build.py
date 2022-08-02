# Priority: 1
from discord.app import Option
from utils.buttons import GemBuildsView
from utils.objects import ACResponse, SlashCommand


class BuildCommand(SlashCommand, name="build", description="Show gem builds for a class."):
    build_id = Option(description="Load your's or someone's saved build", default=None, autocomplete=True)
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context()
        build_id = self.build_id
        build = None
        build_data = None
        if build_id:
            builds_data = await ctx.bot.db.db_users.find_one({"builds.saved": {"$elemMatch": {"code": build_id}}}, {"builds.saved": 1})
            if builds_data:
                for build_data in builds_data["builds"]["saved"]:
                    if build_data["code"] != build_id:
                        continue
                    if build_data["creator"] != ctx.author.id and not build_data["public"]:
                        return await ctx.send(f"This build is not public.", ephemeral=True)
                    build = build_data["config"]
                    break
                build_data["views"] += 1
                await ctx.bot.db.db_users.update_one({"_id": build_data["creator"], "builds.saved.code": build_id}, {f"$inc": {"builds.saved.$.views": 1}})
                creator = await ctx.bot.try_user(build_data['creator'])
            else:
                return await ctx.send(f"Build ID doesn't correspond to any build in database.\nThis command takes no arguments like class or type, it's just `/build`", delete_after=15, ephemeral=True)
        view = GemBuildsView(ctx, build_data=build_data)
        view.message = await ctx.send(
            content="Builds will only be calculated once all **Required** fields are filled in." if not build else f"Loaded **{build_data['code']}** by {creator.mention}",
            view=view)
    
    async def autocomplete(self, options, focused: str):
        response = ACResponse()
        value = options[focused]
        value = value.lower()
        if not hasattr(self, "builds_cache"):
            self.builds_cache = await self.client.db.db_users.find({}, {"builds.saved": 1}).distinct("builds.saved")
        for build in sorted(self.builds_cache, key=lambda x: (int(x["public"]), x["code"])):
            if value and value.lower() not in build["code"]:
                continue
            if self.interaction.user.id == build["creator"]:
                response.add_option(name=f"🔒 {build['code']}" + (f" | {build['name']}" if build.get("name") else ""), value=build["code"])
            elif build["public"]:
                response.add_option(name=f"🌐 {build['code']}" + (f" | {build['name']}" if build.get("name") else ""), value=build["code"])
        return response[:25]

def setup(bot):
    bot.application_command(BuildCommand)