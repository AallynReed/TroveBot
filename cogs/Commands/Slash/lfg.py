# Priority: 1
from utils.buttons import Pager, Page
from utils.objects import SlashCommand
from discord.app import Option
from utils.CustomObjects import CEmbed, TimeConverter
from utils.partner import LFGView
from datetime import datetime

class LFGCommand(SlashCommand, name="lfg", description="Find groups to play with."):
    ...

class LFGCreate(SlashCommand, parent=LFGCommand, name="create", description="Create a group."):
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context(ephemeral=True)
        view = LFGView(ctx)
        view.message = await ctx.send(embed=view.build_embed(), view=view)

class LFGList(SlashCommand, parent=LFGCommand, name="list", description="List all groups."):
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context(ephemeral=True)
        lfgs = await ctx.bot.db.db_lfg.find({"expire": {"$gt": datetime.utcnow().timestamp()}, "deleted": False}).to_list(length=999999)
        if not lfgs:
            return await ctx.send("No groups found.")
        lfg_pages = ctx.bot.utils.chunks(lfgs, 5)
        view = Pager(ctx, start_end=True, timeout=180)
        for lfg_page in lfg_pages:
            e = view.make_page()
            e.set_author(name="LFG List", icon_url=ctx.bot.user.avatar)
            for lfg in lfg_page:
                e.add_field(
                    name=f"{lfg['name']}",
                    value=f"by {lfg['player']} | Expires in: {TimeConverter(lfg['expire']-lfg['created_at'])}",
                    inline=False
                )
        await ctx.send(embed=view.selected_page, view=view.start())

    def _build_embed(self, data):
        embed = CEmbed(
            description=data["description"] or "New Group",
            timestamp=datetime.utcfromtimestamp(data["created_at"])
        )
        embed.set_author(name=self.data["name"] or "Empty")
        embed.set_footer(text=f"Created by {self.user.name}", icon_url=self.user.avatar)
        embed.add_field(name="Player", value=self.data["player"] or "Empty")
        embed.add_field(name="Platform", value=self.data["platform"] or "Empty")
        embed.add_field(
            name="Expiration",
            value=str(TimeConverter(self.data["expire"]-self.data["created_at"])) if self.data["expire"] else "No Expiration"
        )
        embed.add_field(name="Requirements", value=self.data["requirements"] or "No Requirements", inline=False)
        return embed 

def setup(bot):
    bot.application_command(LFGCommand)