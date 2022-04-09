# Priority: 1
from utils.objects import SlashCommand
from utils.partner import ClubAdventuresView


class ClubAdventures(
        SlashCommand,
        name="club_adventures",
        description="Send club adventures to trovesaurus"
    ):
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        view = ClubAdventuresView(ctx)
        view.message = await ctx.send(view=view)

def setup(bot):
    bot.application_command(ClubAdventures)
