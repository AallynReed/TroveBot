# Priority: 4
import asyncio
from datetime import datetime, timedelta

from discord.ext import commands, tasks
from discord.utils import _bytes_to_base64_data, get


class PartnerTasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.archive_task.start()
        self.create_events.start()

    def cog_unload(self):
        self.archive_task.cancel()
        self.create_events.cancel()

    @tasks.loop(seconds=15)
    async def archive_task(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow().timestamp()
        to_close = self.bot.db.db_ts_archives.find({"close_at": {"$lte": now}})
        if not to_close:
            return
        guild = self.bot.get_guild(118027756075220992)
        category = guild.get_channel(772434558330601542)
        target = guild.default_role
        async for archive_data in to_close:
            channel = get(category.text_channels, id=int(archive_data["_id"]))
            if not channel:
                continue
            new_overwrites = channel.overwrites
            new_overwrites[target].view_channel = False
            await self.bot.db.db_ts_archives.delete_one({"_id": channel.id})
            await channel.edit(overwrites=new_overwrites, reason="Closing archive after time limit was reached.")

    @tasks.loop(seconds=15)
    async def create_events(self):
        await self.bot.wait_until_ready()
        now = datetime.utcnow() + timedelta(seconds=60)
        events = await self.bot.http.get_scheduled_events(118027756075220992, False)
        events = [e["name"] for e in events]
        request = await self.bot.AIOSession.get("https://trovesaurus.com/calendar/feed")
        calendar = await request.json()
        for event in calendar:
            name = event["name"]
            category = event["category"]
            event_name = f"{category}: {name}"
            start = datetime.utcfromtimestamp(int(event["startdate"]))
            if start < now:
                start = now
            end = datetime.utcfromtimestamp(int(event["enddate"]))
            if (image_url := event["image"] or event["icon"]):
                image_request = await self.bot.AIOSession.get(image_url.replace("\\", ""))
                image = await image_request.read()
            else:
                image = None
            location = event.get("location", event["url"])
            if location.startswith("#"):
                location = get(self.bot.get_guild(118027756075220992).text_channels, name=location.strip()[1:])
                if location:
                    location = location.mention
            location = location
            if event_name not in events:
                print(event_name)
                await self.bot.http.create_guild_scheduled_event(
                    118027756075220992,
                    channel_id=None,
                    name=event_name,
                    description=event["url"],
                    scheduled_start_time=start.isoformat(),
                    scheduled_end_time=end.isoformat(),
                    entity_type=3,
                    privacy_level=2,
                    entity_metadata={"location": location},
                    image=_bytes_to_base64_data(image),
                )
        await asyncio.sleep(300)

def setup(bot):
    bot.add_cog(PartnerTasks(bot))
