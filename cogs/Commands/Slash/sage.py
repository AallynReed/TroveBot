# Priority: 1
import re

import discord
from discord.app import Option
from utils.CustomObjects import CEmbed, Sage
from utils.buttons import SageModal
from utils.objects import ACResponse, SlashCommand


class SageCommand(SlashCommand, name="sage", description="Send a sage into chat"):
    name = Option(description="What sage to send?", autocomplete=True)
    async def callback(self):
        data = await self.client.db.db_tags.find_one(
            {
                "$and": [
                    {"approved": True},
                    {"deleted": False},
                    {"$or": [
                        {"_id": self.name},
                        {"name": {"$regex": f"(?i){re.escape(self.name)}"}}
                    ]}
                ]
            }
        )
        ctx = await self.get_context(ephemeral=data is None)
        if not data:
            return await ctx.send(f"No sage with name `{self.name}` was found.")
        sage = Sage(data)
        sage.use()
        author = await ctx.bot.try_user(sage.author)
        e = CEmbed(description=sage.content)
        e.timestamp = sage.creation_date
        e.color = discord.Color.random()
        e.set_author(name=sage.name, icon_url="https://i.imgur.com/2Cjlmwb.png")
        e.set_footer(text=f"{author} | SageID: {sage._id} | Created", icon_url=author.avatar)
        e.set_image(url=sage.image)
        await self.client.db.db_tags.update_one({"_id": sage._id}, {"$set": sage.data})
        await ctx.send(embed=e)

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused].lower()
        data = self.client.db.db_tags.find(
            {"$and": [
                {"approved": True},
                {"deleted": False},
                {"$or": [
                    {"_id": value}, 
                    {"name": {"$regex": f"(?:\W|^)({re.escape(value)})"}}, 
                ]}
            ]}
        ).sort("uses", -1)
        async for sage in data:
            response.add_option(sage["name"], sage["_id"])
        return response[:25]

class AddSageCommand(SlashCommand, name="add_sage", description="Create a sage"):
    async def callback(self):
        Modal = SageModal(self.client)
        await self.interaction.response.send_modal(Modal)

class UpdateSageCommand(SlashCommand, name="update_sage", description="Update a sage"):
    name = Option(description="What sage to update?", autocomplete=True)
    async def callback(self):
        data = await self.client.db.db_tags.find_one(
            {
                "$and": [
                    {"author": self.interaction.user.id},
                    {"deleted": False},
                    {"$or": [
                        {"_id": self.name},
                        {"name": {"$regex": f"(?i){re.escape(self.name)}"}}
                    ]}
                ]
            }
        )
        if not data:
            return await self.interaction.send_message(
                f"No sage with name `{self.name}` was found.",
                ephemeral=True
            )
        sage = Sage(data)
        Modal = SageModal(self.client, sage.name, sage.content, sage.image, update=sage)
        await self.interaction.response.send_modal(Modal)

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused].lower()
        data = self.client.db.db_tags.find(
            {"$and": [
                {"author": self.interaction.user.id},
                {"deleted": False},
                {"$or": [
                    {"_id": value}, 
                    {"name": {"$regex": f"(?:\W|^)({re.escape(value)})"}}, 
                ]}
            ]}
        ).sort("uses", -1)
        async for sage in data:
            response.add_option(sage["name"], sage["_id"])
        return response[:25]

def setup(bot):
    bot.application_command(SageCommand)
    bot.application_command(AddSageCommand)
    bot.application_command(UpdateSageCommand)
