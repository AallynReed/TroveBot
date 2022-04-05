# Priority: 1
import re

import discord
from discord.app import Option
from utils.CustomObjects import CEmbed, Sage
from utils.buttons import MarkHelpful, Pager, PagerButton, SageManage, SageModal
from utils.objects import ACResponse, SlashCommand


class SageCommand(SlashCommand, name="sage", description="Send a sage into chat"):
    name = Option(description="What sage to send?", autocomplete=True)
    async def callback(self):
        await super().callback()
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
        view = MarkHelpful(ctx, sage)
        view.message = await ctx.send(embed=e, view=view)

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused].lower()
        data = self.client.db.db_tags.find(
            {"$and": [
                {"approved": True},
                {"deleted": False},
                {"$or": [
                    {"_id": value}, 
                    {"name": {"$regex": f"(?i)(?:\W|^)({re.escape(value)})"}}, 
                ]}
            ]}
        ).sort([["helpful", -1], ["uses", -1]])
        async for sage in data:
            response.add_option(f'{sage["name"]} | +{len(sage["helpful"])}', sage["_id"])
        return response[:25]

class AddSageCommand(SlashCommand, name="sage_add", description="Create a sage"):
    async def callback(self):
        await super().callback()
        Modal = SageModal(self.client)
        await self.interaction.response.send_modal(Modal)

class UpdateSageCommand(SlashCommand, name="sage_update", description="Update a sage"):
    name = Option(description="What sage to update?", autocomplete=True)
    async def callback(self):
        await super().callback()
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
                    {"name": {"$regex": f"(?i)(?:\W|^)({re.escape(value)})"}}, 
                ]}
            ]}
        ).sort("uses", -1)
        async for sage in data:
            response.add_option(sage["name"], sage["_id"])
        return response[:25]

class ManageSageCommand(SlashCommand, name="sage_manage", description="Manage a sage (Staff only)"):
    name = Option(description="What sage to manage?", default=None, autocomplete=True)
    async def callback(self):
        await super().callback()
        roles = {r.id for r in self.interaction.user.roles}
        roles.update({self.interaction.user.id})
        if not self.client.sage_moderators.intersection(roles):
            return await self.interaction.response.send_message(
                "You can't manage sages",
                ephemeral=True
            )
        sages = []
        if not self.name:
            raw_sages = self.client.db.db_tags.find({"approved": False, "deleted": False}).sort("uses", -1)
            async for raw_sage in raw_sages:
                sages.append(Sage(raw_sage))
            if not sages:
                return await self.interaction.response.send_message(
                    "There are no sages waiting to be approved.",
                    ephemeral=True
                )
        else:
            sage = await self.client.db.db_tags.find_one(
                {"$or": [
                    {"_id": self.name},
                    {"name": {"$regex": f"(?i){re.escape(self.name)}"}}
                ]}
            )
            if not sage:
                return await self.interaction.response.send_message(
                    "There is no tag with that ID or Name",
                    ephemeral=True
                )
            sages.append(Sage(sage))
        ctx = await self.get_context()
        pager = Pager(ctx, start_end=True, timeout=180)
        for sage in sages:
            author = await ctx.bot.try_user(sage.author)
            e = pager.make_page(description=sage.content)
            e.sage = sage
            e.timestamp = sage.creation_date
            e.color = discord.Color.random()
            e.set_author(name=sage.name, icon_url="https://i.imgur.com/2Cjlmwb.png")
            e.set_footer(text=f"{author} | SageID: {sage._id} | Created", icon_url=author.avatar)
            e.set_image(url=sage.image)
        categories = await self.client.db.db_tags.find({"category": {"$ne": None}}).distinct("category")
        if len(pager.pages) == 1:
            page = pager.selected_page
            view = SageManage(ctx, page.sage, categories)
            view.message = await ctx.send(embed=page, view=view)
        else:
            button = PagerButton(label="Manage", row=1, emoji="🛠️", original=False)
            async def new_func(self, _):
                sage_view = SageManage(ctx, self.view.selected_page.sage, categories)
                sage_view.message = self.view.message
                await self.view.message.edit(view=sage_view)
            button.callback = new_func.__get__(button, PagerButton)
            pager = pager.start()
            pager.add_item(button)
            pager.message = await ctx.send(embed=pager.selected_page, view=pager)

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused].lower()
        data = self.client.db.db_tags.find(
            {"$or": [
                {"_id": value}, 
                {"name": {"$regex": f"(?i)(?:\W|^)({re.escape(value)})"}}, 
            ]}
        ).sort("uses", -1)
        async for sage in data:
            response.add_option(f'{sage["name"]} | Uses x{sage["uses"]}', sage["_id"])
        return response[:25]

class IndexSageCommand(SlashCommand, name="sage_index", description="List sages in categories"):
    category = Option(description="Name of the category", autocomplete=True, default=None)
    async def callback(self):
        await super().callback()
        sages = self.client.db.db_tags.find({"category": self.category})
        sages = [Sage(sage) async for sage in sages]
        if not sages:
            return await self.interaction.response.send_message(
                "That category doesn't exist.",
                ephemeral=True
            )
        ctx = await self.get_context(ephemeral=True)
        sage_pages = self.client.utils.chunks(sages, 10)
        pager = Pager(ctx, start_end=True)
        for i, sage_page in enumerate(sage_pages, 1):
            e = pager.make_page()
            e.set_author(name=f"List of sages in \"{self.category}\" ({i}/{len(sage_pages)})")
            e.description = f"\n".join([sage.name for sage in sage_page])
        pager.message = await ctx.send(embed=pager.selected_page, view=pager.start())

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused].lower()
        categories = await self.client.db.db_tags.find(
            {
                "$and": [
                    {"deleted": False},
                    {"category": {"$ne": None}},
                    {"category": {"$regex": f"(?i)(?:\W|^)({re.escape(value)})"}}
                ]
            }).distinct("category")
        for category in categories:
            response.add_option(category, category)
        return response[:25]

def setup(bot):
    bot.application_command(SageCommand)
    bot.application_command(AddSageCommand)
    bot.application_command(UpdateSageCommand)
    bot.application_command(ManageSageCommand)
    bot.application_command(IndexSageCommand)
