# Priority: 1
import re
from datetime import datetime
from typing import Literal

import discord
from discord import Option
from discord.utils import get
from utils.buttons import Pager
from utils.CustomObjects import TimeConverter
from utils.objects import ACResponse, SlashCommand


class Archive(SlashCommand, name="archive", guilds=[118027756075220992, 834505270075457627]):
    ...

class Open(SlashCommand, name="open", description="Open an archive channel.",parent=Archive):
    channel: discord.TextChannel=Option(description="The archive to open.", autocomplete=True)
    duration: Literal["1 hour", "3 hours", "6 hours", "12 hours"]=Option(
        description="The duration of the archive being open.",
        default="1 hour"
    )
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        if await ctx.bot.db.db_ts_archives.count_documents({"opened_by": ctx.author.id}) >= 3:
            return await ctx.send("You already have 2 open archives, you must close one with `/archive close`.")
        guild = ctx.bot.get_guild(118027756075220992)
        categories = [772434558330601542, 908664374619668510]
        channels = [ch for c in [guild.get_channel(c) for c in categories] for ch in c.text_channels]
        target = guild.default_role
        channel = get(channels, id=int(self.channel))
        if not channel:
            return await ctx.send("No archive found.")
        closed_archives = [a for a in channels if not a.permissions_for(target).view_channel]
        if channel not in closed_archives:
            return await ctx.send("This archive is already open.")
        new_overwrites = channel.overwrites
        new_overwrites[target].view_channel = True
        now = int(datetime.utcnow().timestamp())
        duration = int(TimeConverter(self.duration))
        await channel.edit(overwrites=new_overwrites, reason=f"Opening archive for {ctx.author}.")
        await ctx.bot.db.db_ts_archives.insert_one(
            {
                "_id": channel.id,
                "opened_by": ctx.author.id,
                "opened_at": now,
                "duration": duration,
                "close_at": now + duration

            }
        )
        return await ctx.send(f"Archive {channel.mention} has been opened for {TimeConverter(duration)}.")

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused]
        value = value.lower()
        guild = self.client.get_guild(118027756075220992)
        categories = [772434558330601542, 908664374619668510]
        channels = [ch for c in [guild.get_channel(c) for c in categories] for ch in c.text_channels]
        target = guild.default_role
        for archive in sorted(channels, key=lambda x: -x.created_at.timestamp()):
            if not archive.permissions_for(target).view_channel:
                if archive.permissions_for(guild.me).manage_permissions:
                    if not re.findall(f"(?:\W|^)({re.escape(value)})", archive.name, re.IGNORECASE):
                        continue
                    response.add_option(archive.name, str(archive.id))
        return response[:25]

class Close(SlashCommand, name="close", description="Close an archive channel.", parent=Archive):
    channel: discord.TextChannel=Option(description="The archive to close.", autocomplete=True)
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        guild = ctx.bot.get_guild(118027756075220992)
        categories = [772434558330601542, 908664374619668510]
        channels = [ch for c in [guild.get_channel(c) for c in categories] for ch in c.text_channels]
        channel = get(channels, id=int(self.channel))
        if not channel:
            return await ctx.send("No archive found.")
        archive = await ctx.bot.db.db_ts_archives.find_one({"_id": channel.id})
        if not archive:
            return await ctx.send("That archive isn't open.")
        if ctx.author.id not in [117951235423731712, 565097923025567755]:
            if archive["opened_by"] != ctx.author.id:
                return await ctx.send("You can only close an archive you opened.")
        target = guild.default_role
        await ctx.bot.db.db_ts_archives.delete_one({"_id": channel.id})
        if not channel.permissions_for(target).view_channel:
            return await ctx.send("This archive is already closed.")
        new_overwrites = channel.overwrites
        new_overwrites[target].view_channel = False
        await channel.edit(overwrites=new_overwrites, reason=f"Closing archive, manually, for {ctx.author}.")
        return await ctx.send(f"Archive {channel.mention} has been closed.")

    async def autocomplete(self, options, focused):
        response = ACResponse()
        value = options[focused]
        value = value.lower()
        guild = self.client.get_guild(118027756075220992)
        categories = [772434558330601542, 908664374619668510]
        channels = [ch for c in [guild.get_channel(c) for c in categories] for ch in c.text_channels]
        if self.interaction.user.id in [117951235423731712, 565097923025567755]:
            opened_archives = self.client.db.db_ts_archives.find({})
        else:
            opened_archives = self.client.db.db_ts_archives.find({"opened_by": self.interaction.user.id})
        if not opened_archives:
            return response
        async for archive in opened_archives:
            archive = get(channels, id=archive["_id"])
            if not archive:
                continue
            response.add_option(archive.name, str(archive.id))
        return response[:25]

class List(SlashCommand, name="list", description="List all archive channels.",parent=Archive):
    async def callback(self):
        await super().callback()
        ctx = await self.get_context(ephemeral=True)
        guild = ctx.bot.get_guild(118027756075220992)
        categories = [772434558330601542, 908664374619668510]
        channels = [ch for c in [guild.get_channel(c) for c in categories] for ch in c.text_channels]
        target = guild.default_role
        if not channels:
            return await ctx.send("Looks like something went terribly wrong. Contact developer.")
        archives = [a for a in channels]
        archives.sort(key=lambda x: x.overwrites[target].view_channel, reverse=True)
        view = Pager(ctx, start_end=True)
        pages = ctx.bot.utils.chunks(archives, 10)
        for i, page in enumerate(pages, 1):
            e = view.make_page(color=0x000000)
            e.set_author(name=f"Archives list | {i} of {len(pages)}")
            text = []
            for archive in page:
                if archive.permissions_for(target).view_channel:
                    status = "🟢 **"
                    if (data := await ctx.bot.db.db_ts_archives.find_one({"_id": archive.id})):
                        time = f"<t:{data['close_at']}:R>"
                        status = f"🟡 ({time}) **"
                else:
                    status = "🔴 **"
                text.append(status + archive.mention + "**\n")
            e.description = "".join(text)
            e.set_footer(text="🟢 = open, 🟡 = temporarily open, 🔴 = closed")
        view.message = await ctx.send(embed=view.selected_page, view=view.start())

def setup(bot):
    bot.application_command(Archive)
