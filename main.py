from asyncio import sleep
from datetime import datetime
from json import load

import discord
from discord.ext import commands, tasks

from core.database import DatabaseManager
from core.modules import get_modules
from core.objects import Empty, NovaContext

configs = load(open("constants/config/keys.json"))

class Nova(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=self.prefix,
            case_insensitive=True,
            intents=self._get_intents(),
            description="Nova Bot",
            pm_help=None,
            status=discord.Status.dnd,
            activity=discord.Game(f"Starting Up..."),
            chunk_guilds_at_startup=True,
            allowed_mentions=discord.AllowedMentions(replied_user=False)
        )

    def _get_intents(self):
        intents = discord.Intents.all()
        return intents

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or NovaContext)

    async def prefix(self, bot, message):
        await bot.wait_until_ready()
        prefixes = []
        if guild_prefixes := self.db.prefixes["guilds"].get(message.guild.id):
            prefixes.extend(guild_prefixes)
        if user_prefixes := self.db.prefixes["users"].get(message.author.id):
            prefixes.extend(user_prefixes)
        if not prefixes:
            prefixes.append("n?")
        return commands.when_mentioned_or(*prefixes)(self, message)

    async def _set_constants(self):
        self.db = DatabaseManager("Nova")
        metadata = await self.db.get_metadata()
        constants = await self.db.get_constants()
        self.owners = {m.id for m in (await self.application_info()).team.members}
        self.metadata = Empty()
        self.constants = Empty()
        for key, value in metadata.items():
            setattr(self.metadata, key, value)
        for key, value in constants.items():
            setattr(self.constants, key, value)
        setattr(self.constants, "uptime", datetime.utcnow().timestamp())
        setattr(self.constants, "configs", configs)
        self._last_exception = None

    async def _set_trove_constants(self):
        setattr(self.constants, "Trove", Empty())
        setattr(self.constants.Trove, "values", TroveValues())
        setattr(self.constants.Trove, "time", TroveTime())
        setattr(self.constants.Trove, "sheets", {})
        setattr(self.constants.Trove, "daily_data", load(open("constants/trove/data/daily_buffs.json")))
        setattr(self.constants.Trove, "weekly_data", {})

    async def _load_modules(self):
        await self.change_presence(activity=discord.Game(f"Loading Modules..."), status=discord.Status.idle)
        self.modules = get_modules
        for m in self.modules("cogs/"):
            if not m.priority:
                continue
            try:
                self.load_extension(m.load)
            except Exception as e:
                print(e)

    @tasks.loop(seconds=1)         
    async def _status_task(self):
        await self.wait_until_ready()
        statuses = [
            "n?help",
            "slynx.xyz/trovebot",
            f"in {len(self.guilds)} communities",
            f"v{self.version[0]}"
        ]
        for status in statuses:
            await self.change_presence(activity=discord.Activity(name=status, type=discord.ActivityType.playing))
            await sleep(60)

    async def setup(self):
        self.remove_command('help')
        await self._set_constants()
        await self._set_trove_constants()
        await self._load_modules()
        self._status_task.start()
        await super().setup()

# Events

    async def on_ready(self):
        print("Bot connected as " + self.user.name + "#" + self.user.discriminator)
        info = list({m for m in (await self.application_info()).team.members})
        print("Owner: " + str(info[0].name) + "#" + str(info[0].discriminator) + " [" + str(info[0].id) + "]")
        print("Serving " + str(len(self.users)) + " users in " + str(len(self.guilds)) + " guilds!")
        print("===================================================")

Nova().run(configs["Tokens"][0], reconnect=True)
