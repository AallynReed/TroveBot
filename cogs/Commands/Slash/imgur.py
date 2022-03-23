# Priority: 1
import discord
from discord.app import Option
from utils.CustomObjects import CEmbed
from utils.objects import SlashCommand


class ImgurUploadCommand(SlashCommand, name="imgur_upload", description="Upload images to imgur."):
    image: discord.Attachment = Option(description="Upload an image to send to imgur.")
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        contents = await self.image.read()
        response = await ctx.bot.AIOSession.post(
            "https://api.imgur.com/3/image",
            headers={"Authorization": f'Client-ID {ctx.bot.keys["Imgur"]["ClientID"]}'},
            data={"image": contents},
        )
        json_response = await response.json()
        if error := json_response["data"].get("error"):
            return await ctx.send(f"An error occured while uploading: **{error['message']}**")
        link = json_response["data"]["link"]
        e = CEmbed(description=f"You imgur link: {link}", color=ctx.author.color)
        e.set_image(url=link)
        await ctx.send(embed=e)

def setup(bot):
    bot.application_command(ImgurUploadCommand)