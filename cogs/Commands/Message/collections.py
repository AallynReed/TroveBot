# Priority: 1
import discord
from discord.app import Option
from utils.buttons import Page, Pager
from utils.CustomObjects import CEmbed
from utils.objects import MessageCommand, SlashCommand


class CollectionMessageCommand(MessageCommand, name="Collection Board"):
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        collected = await self.bot.db.db_message_collections.find_one(
            {
                "message": self.message.id,
                "saved_by": self.interaction.user.id
            }
        )
        if collected:
            await self.bot.db.db_message_collections.delete_one(
                {
                    "message": self.message.id,
                    "saved_by": self.interaction.user.id
                }
            )
            return await ctx.send(
                "You removed this message from your Collection Board."
            )
        await self.bot.db.db_message_collections.insert_one(
            {
                "guild": self.message.guild.id,
                "channel": self.message.channel.id,
                "author": self.message.author.id,
                "message": self.message.id,
                "saved_by": self.interaction.user.id,
                "content": self.message.content,
                "snippet": (self.message.content[:40] + ("..." if len(self.message.content) > 40 else "")) if self.message.content else "",
                "media": [attachment.url for attachment in self.message.attachments],
                "jump": self.message.jump_url,
            }
        )
        await ctx.send("You saved this message to your Collection Board.")

class CollectionSlashCommand(SlashCommand, name="collection"):
    ...

class CollectionListCommand(SlashCommand, name="list", description="List your Collection Board", parent=CollectionSlashCommand):
    channel: discord.TextChannel=Option(default=None, description="Filter list by channel.")
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        if not self.channel:
            query = {"saved_by": self.interaction.user.id}
        else:
            query = {
                "saved_by": self.interaction.user.id,
                "channel": self.channel.id
            }
        collection = await self.bot.db.db_message_collections.find(query)
        if not collection:
            return await ctx.send("You have no messages in your Collection Board.")
        view = Pager(ctx, start_end=True,  step_10=True)
        pages = ctx.bot.utils.chunks(collection, 4)
        for i, page in enumerate(pages, 1):
            async def create_page(bot, page):
                e = CEmbed(description="")
                e.title = f"Page {i}/{len(pages)}"
                e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar)
                for message in page:
                    author = bot.get_user(message["author"]) or await bot.fetch_user(message["author"])
                    e.description += f"[Message]({message['jump']}) by {author.mention} `{author}`\n"
                    e.description += f"{message['snippet']}\n"
                    e.description += f" | ".join([f"[Attachment {i}]({url})" for i, url in enumerate(message['media'], 1)])
                    e.description += "\n\n"
                page = Page.from_dict(e)
            view.add_dynamic_page(create_page, page)
        await ctx.send(embed=view.selected_page, view=await view.dynamic_start())       

def setup(bot):
    bot.application_command(CollectionMessageCommand)
    bot.application_command(CollectionSlashCommand)
