# Priority: 1
from utils.objects import SlashCommand
from utils.partner import BugReportView

class ReportBug(
        SlashCommand,
        name="reportbug",
        description="Report an ingame bug to developers.",
        guilds=[118027756075220992]
    ):
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context(ephemeral=True)
        view = BugReportView(ctx)
        view.message = await ctx.send(embed=view.build_embed(), view=view)

def setup(bot):
    bot.application_command(ReportBug)