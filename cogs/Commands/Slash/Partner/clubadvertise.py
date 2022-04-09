# Priority: 1
from utils.objects import SlashCommand
from utils.partner import ClubAdvertise


class ClubAdvertiseCommand(SlashCommand, name="club_advertise", description="Advertise your clubs at Trovesaurus.", guilds=[118027756075220992]):
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        view = ClubAdvertise(ctx, ctx.bot.get_channel(941107547287482398))
        view.message = await ctx.send(
            embed=view.build_embed(),
            view=view
        )

def setup(bot):
    bot.application_command(ClubAdvertiseCommand)