# Priority: 1
from utils.objects import MessageCommand
from googletrans import Translator

class TranslateCommand(MessageCommand, name="translate"):
    def __init__(self) -> None:
        super().__init__()

    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        if not self.message.content:
            return await ctx.send("No text to translate.")
        if not hasattr(ctx.bot, "translator"):
            ctx.bot.translator = Translator()
        translated = ctx.bot.translator.translate(
            self.message.content, dest="en"
        )
        return await ctx.send(translated.text)

def setup(bot):
    bot.application_command(TranslateCommand)
