import json
import re
from datetime import datetime, timedelta

import discord
from discord.ui import Modal, Select, TextInput

from utils.others import RandomID
from utils.buttons import BaseView
from utils.CustomObjects import CEmbed, TimeConverter

# Bug Report

class BugReportModal(Modal):
    def __init__(self, view, identify=False):
        super().__init__("Bug Report Form")
        self.view = view
        user = self.view.ctx.author
        if identify:
            server_roles = {
                819195729234362378, # PC
                920807897770917959, # PS4
                920807969980051536, # XBOX
                920808044768669717  # Switch
            }
            platforms = {r.id for r in user.roles}.intersection(server_roles)
            platform = user.guild.get_role(list(platforms)[0]).name if platforms else None
            prefill_name = user.display_name
            if not re.match(r"^([a-z_0-9]{2,19})$", prefill_name, re.IGNORECASE):
                prefill_name = None
            items = [
                TextInput(
                    custom_id="trove_name",
                    label="Your in-game name?",
                    style=discord.TextInputStyle.short,
                    min_length=2,
                    max_length=19,
                    value=self.view.data["trove_name"] or prefill_name
                ),
                TextInput(
                    custom_id="platform",
                    label="Your platform?",
                    style=discord.TextInputStyle.short,
                    min_length=2,
                    max_length=12,
                    value=self.view.data["platform"] or platform
                ),
                TextInput(
                    custom_id="exploit",
                    label="Is this bug report an exploit? Y | N",
                    style=discord.TextInputStyle.short,
                    min_length=1,
                    max_length=1,
                    value="Y" if self.view.data["exploit"] else "N"
                )
            ]
        else:
            items = [
                TextInput(
                    custom_id="description",
                    label="Short description of bug",
                    placeholder="e.g. My Charatacter doesn't mount in the Hub",
                    style=discord.TextInputStyle.short,
                    min_length=0,
                    max_length=190,
                    value=self.view.data["description"]
                ),
                TextInput(
                    custom_id="result",
                    label="What were you doing?",
                    placeholder="e.g. Standing around in hub",
                    style=discord.TextInputStyle.long,
                    min_length=30,
                    value=self.view.data["result"]
                ),
                TextInput(
                    custom_id="expected",
                    label="What did you expect to happen?",
                    placeholder="e.g. The mount to come out as usual",
                    style=discord.TextInputStyle.long,
                    min_length=30,
                    value=self.view.data["expected"]
                ),
                TextInput(
                    custom_id="reproduction",
                    label="How can we reproduce this bug?",
                    placeholder="e.g. Go to an Hub World\nTry to mount",
                    style=discord.TextInputStyle.long,
                    min_length=30,
                    value=self.view.data["reproduction"]
                ),
                TextInput(
                    custom_id="media_links",
                    label="Do you have any media? [Max: 10]",
                    placeholder="Only Youtube, Imgur or Twitch Clip URL's are allowed",
                    style=discord.TextInputStyle.long,
                    required=False,
                    value=self.view.data["media_links"]
                )
            ]
        for item in items:
            self.add_item(item)

    async def callback(self, interaction):
        if await self.check_fields(interaction):
            self.view.manage_buttons()
            await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
            await interaction.response.send_message("Successfully filled form.", ephemeral=True)

    async def check_fields(self, interaction):
        try:
            for child in self.children:
                if child.custom_id == "trove_name":
                    nick = re.match(r"^([a-z_0-9]{2,19})$", child.value, re.IGNORECASE)
                    if not nick:
                        raise Exception("Trove In-Game name invalid.")
                    self.view.data[child.custom_id] = child.value
                elif child.custom_id == "exploit":
                    self.view.data[child.custom_id] = child.value.lower() == "y"
                elif child.custom_id == "media_links":
                    yt_regex = r"(?:https?:\/\/)?(?:www\.)?youtu(?:be\.com/watch\?(?:.*?&(?:amp;)?)?v=|\.be/)(?:[\w\-]+)(?:&(?:amp;)?[\w\?=]*)?"
                    imgur_regex = r"(?:https?:\/\/)?(?:i\.)?imgur.com\/(?:(?:gallery\/)(?:\w+)|(?:a\/)(?:\w+)#?)?(?:\w*)"
                    twitch_regex = r"(?:https?:\/\/)(?:www\.)twitch\.tv\/\w+\/clip\/\w+(?:-\w+)?"
                    discord_regex = r"(?:https?:\/\/cdn\.discordapp\.com\/attachments\/[0-9]+\/[0-9]+\/\w+\.[a-z0-9]{1,4})"
                    if child.value:
                        links = set(re.findall(yt_regex, child.value))
                        links.update(set(re.findall(imgur_regex, child.value)))
                        links.update(set(re.findall(twitch_regex, child.value)))
                        links.update(set(re.findall(discord_regex, child.value)))
                        if not links:
                            raise Exception("No valid YouTube, Imgur, Discord or Twitch Clip links were detected in your media input however you can click again to fix these.")
                        self.view.data["media_links"] = list(links)[:10]
                else:
                    self.view.data[child.custom_id] = child.value
        except Exception as e:
            await interaction.response.send_message(str(e), ephemeral=True)
            return False
        return True

class BugReportView(BaseView):
    def __init__(self, ctx):
        super().__init__(timeout=900)
        self.ctx = ctx
        user = ctx.author
        self.data = {
            "user": {
                "id": user.id,
                "avatar_url": str(user.avatar.replace(format="webp") if user.avatar else user.default_avatar),
                "name": user.name,
                "nickname": user.nick,
                "discriminator": user.discriminator,
                "display_name": str(user)
            },
            "trove_name": None,
            "platform": None,
            "exploit": False,
            "description": None,
            "result": None,
            "expected": None,
            "reproduction": None,
            "media_links": [],
            "message_id": None,
            "message_jump": None
        }

    def manage_buttons(self):
        if self.data["trove_name"] and self.data["platform"]:
            self.identify.style = discord.ButtonStyle.success
            self.report_form.disabled = False
        if (self.data["description"] and
            self.data["result"] and
            self.data["expected"] and
            self.data["reproduction"]):
            self.report_form.style = discord.ButtonStyle.success
        if (self.identify.style == discord.ButtonStyle.success and
            self.report_form.style == discord.ButtonStyle.success):
            self.submit.disabled = False

    @discord.ui.button(label='Identification', style=discord.ButtonStyle.secondary)
    async def identify(self, _, interaction):
        await interaction.response.send_modal(BugReportModal(self, True))

    @discord.ui.button(label='Report Form', style=discord.ButtonStyle.secondary, disabled=True)
    async def report_form(self, _, interaction):
        await interaction.response.send_modal(BugReportModal(self))

    def build_embed(self):
        description = self.data["description"] or "Empty"
        expected = self.data["expected"] or "Empty"
        result = self.data["result"] or "Empty"
        repro = self.data["reproduction"] or "Empty"
        media_links = self.data["media_links"] or ["Empty"]
        e = CEmbed(color=discord.Color.random(), timestamp=datetime.utcnow())
        e.set_author(name=f"Bug report by {self.ctx.author}", icon_url=self.ctx.author.avatar)
        e.description = "**Context**\n" + (description if len(description) <= 1024 else description[:1024-45] + "...\n**[Text visually redacted due to size]**")
        e.add_field(name="Trove IGN", value=self.data["trove_name"] or "Empty")
        e.add_field(name="Platform", value=self.data["platform"] or "Empty")
        e.add_field(
            name="Expected",
            value=expected if len(expected) <= 1024 else expected[:1024-45] + "...\n**[Text visually redacted due to size]**",
            inline=False)
        e.add_field(
            name="Observed",
            value=result if len(result) <= 1024 else result[:1024-45] + "...\n**[Text visually redacted due to size]**",
            inline=False)
        e.add_field(
            name="Reproduction Steps",
            value=repro if len(repro) <= 1024 else repro[:1024-45] + "...\n**[Text visually redacted due to size]**",
            inline=False)
        e.add_field(name="Media", value="\n".join(media_links), inline=False)
        e.set_footer(text="Reported via Bot")
        return e

    @discord.ui.button(label='Submit', style=discord.ButtonStyle.primary, disabled=True, row=1)
    async def submit(self, _, interaction):
        final_e = self.build_embed()
        if not self.data["exploit"]:
            report = await self.ctx.bot.get_channel(812354696320647238).send(embed=final_e)
            self.data["message_id"] = report.id
            self.data["message_jump"] = report.jump_url
        async with self.ctx.bot.AIOSession.post(
            "https://trovesaurus.com/discord/issues",
            data={"payload": json.dumps(self.data),
            "Token": self.ctx.bot.keys["Trovesaurus"]["Token"]}) as request:
            if request.status == 200:
                if not self.data["exploit"]:
                    final_e.add_field(name="\u200b", value=f"[View on Trovesaurus Issue Tracker]({await request.text()})")
                    await report.edit(embed=final_e)
                await interaction.response.send_message(
                    f"Your bug report was submitted to Trovesaurus.",
                    ephemeral=True
                )
            else:
                if not self.data["exploit"]:
                    await report.delete(silent=True)
                await interaction.response.send_message(
                    f"Bug report wasn't submitted, an error occured.",
                    ephemeral=True
                )
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, row=1)
    async def cancel(self, _, interaction):
        await self.message.delete(silent=True)
        await interaction.response.send_message(
            f"Your bug report was cancelled.",
            ephemeral=True
        )
        self.stop()

# Looking for group

class LFGModal(Modal):
    def __init__(self, view):
        super().__init__("Create a new Group Listing")
        self.view = view
        prefill_name = view.user.display_name
        if not re.match(r"^([a-z_0-9]{2,19})$", prefill_name, re.IGNORECASE):
            prefill_name = None
        items = [
            TextInput(
                custom_id="player",
                label="Your in-game nickname",
                style=discord.TextInputStyle.short,
                min_length=2,
                max_length=19,
                value=view.data["player"] or prefill_name
            ),
            TextInput(
                custom_id="name",
                label="Group Name",
                style=discord.TextInputStyle.short,
                min_length=6,
                max_length=32,
                value=view.data["name"]
            ),
            TextInput(
                custom_id="description",
                label="Group Description",
                style=discord.TextInputStyle.long,
                min_length=6,
                max_length=1024,
                placeholder="Describe what you want this group to do.\nJust play\nFarm Delves\nBuild a club\netc...",
                value=view.data["description"]
            ),
            TextInput(
                custom_id="requirements",
                label="Group Requirements",
                style=discord.TextInputStyle.long,
                max_length=300,
                value=view.data["requirements"],
                placeholder="Power Rank: 36000+\nLevel 30+\nLight: 8000+\nMad Skillz at not dying\netc...",
                required=False
            ),
            TextInput(
                custom_id="expire",
                label="Group Expiration",
                style=discord.TextInputStyle.short,
                max_length=64,
                value=str(TimeConverter(view.data["expire"]-view.data["created_at"])) if view.data["expire"] else None,
                placeholder="1 hour | 1 day | 1 week",
                required=False
            )
        ]
        for item in items:
            self.add_item(item)

    async def callback(self, interaction):
        for child in self.children:
            if child.custom_id == "player":
                nick = re.match(r"^([a-z_0-9]{2,19})$", child.value, re.IGNORECASE)
                if not nick:
                    return await self.interaction.response.send_message(
                        "Trove In-Game name invalid.",
                        ephemeral=True
                    )
            self.view.data[child.custom_id] = child.value
            if child.custom_id == "expire":
                time = int(TimeConverter(child.value))
                if not time > 0:
                    return await interaction.response.send_message(
                        "Expiration time invalid.",
                        ephemeral=True
                    )
                elif time > 2629800 :
                    return await interaction.response.send_message(
                        "Expiration time must be up to a month.",
                        ephemeral=True
                    )
                self.view.data[child.custom_id] = self.view.data["created_at"] + time
        self.view.manage_buttons()
        await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        await interaction.response.send_message(
            "LFG form filled successfully.",
            ephemeral=True
        )

class LFGView(BaseView):
    def __init__(self, ctx):
        super().__init__(timeout=600)
        self.ctx = ctx
        self.user = ctx.author
        self.data = {
            "_id": RandomID(8),
            "player": None,
            "creator": self.user.id,
            "name": None,
            "description": None,
            "platform": None,
            "requirements": None,
            "expire": None,
            "deleted": False,
            "created_at": int(datetime.utcnow().timestamp()),
        }
        self.manage_buttons()
    
    def manage_buttons(self):
        required = [
            "player",
            "name",
            "description",
            "platform"
        ]
        for required_field in required:
            if required_field is None:
                self.submit.disabled = True
        for item in self.children:
            if isinstance(item, LFGPlatformSelect):
                self.remove_item(item)
        self.add_item(LFGPlatformSelect(self))
    
    def build_embed(self):
        embed = CEmbed(
            description=self.data["description"] or "New Group",
            timestamp=datetime.utcfromtimestamp(self.data["created_at"])
        )
        embed.set_author(name=self.data["name"] or "Empty")
        embed.set_footer(text=f"Created by {self.user.name}", icon_url=self.user.avatar)
        embed.add_field(name="Player", value=self.data["player"] or "Empty")
        embed.add_field(name="Platform", value=self.data["platform"] or "Empty")
        embed.add_field(
            name="Expiration",
            value=str(TimeConverter(self.data["expire"]-self.data["created_at"])) if self.data["expire"] else "No Expiration"
        )
        embed.add_field(name="Requirements", value=self.data["requirements"] or "No Requirements", inline=False)
        return embed        

    @discord.ui.button(label='Fill details', style=discord.ButtonStyle.primary, row=0)
    async def fill(self, _, interaction):
        modal = LFGModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Create', style=discord.ButtonStyle.success, row=2)
    async def submit(self, _, interaction):
        await self.ctx.bot.db.db_lfg.insert_one(self.data)
        self.ctx.bot.dispatch("lfg_create", self.data)
        await interaction.response.send_message(
            f"LFG created with ID **{self.data['_id']}**, it'll now show in the LFG listing",
            ephemeral=True
        )
        self.stop()
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, _, interaction):
        await self.message.delete(silent=True)
        await interaction.response.send_message(
            f"Your LFG creation was cancelled.",
            ephemeral=True
        )
        self.stop()

class LFGPlatformSelect(Select):
    def __init__(self, view):
        platforms = [
            "PC",
            "Xbox",
            "PS4-EU",
            "PS4-NA",
            "Switch"
        ]
        options = [
            discord.SelectOption(label=platform, default=platform==view.data["platform"])
            for platform in platforms
        ]
        super().__init__(placeholder="Pick a platform", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        platform = self.values[0]
        self.view.data["platform"] = platform
        self.view.manage_buttons()
        await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        await interaction.response.send_message(f'Platform changed to **{platform}**.', ephemeral=True)

# Club Adventures

def calculate_adventure_time(tier: int):
    return round(-0.416667*tier**3+4.14286*tier**2-15.6548*tier+23.9857)*3600

class ClubAdventuresView(BaseView):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.data = {
            "creator": {
                "id": ctx.author.id,
                "name": str(ctx.author)
            },
            "server": ctx.guild.id,
            "club": None,
            "adventure": None,
            "platform": None,
            "time": None
        }
        self.manage_buttons()

    def manage_buttons(self):
        if self.data["club"]:
            self.fill.label = self.data["club"] + " | " + str(TimeConverter(self.data["time"]))
            self.fill.style = discord.ButtonStyle.success
        self.fill.disabled = not bool(self.data["adventure"])
        if not (
            self.data["club"] is None or 
            self.data["adventure"] is None or 
            self.data["platform"] is None or 
            self.data["time"] is None):
            self.submit.disabled = False
        for item in self.children:
            if isinstance(item, ClubAdventurePicker):
                self.remove_item(item)
        self.add_item(ClubAdventurePicker(self))
        for item in self.children:
            if isinstance(item, ClubAdventuresPlatformSelect):
                self.remove_item(item)
        self.add_item(ClubAdventuresPlatformSelect(self))

    @discord.ui.button(label='Club Name', style=discord.ButtonStyle.secondary, row=2, disabled=True)
    async def fill(self, _, interaction):
        modal = ClubAdventuresModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Create', style=discord.ButtonStyle.success, row=3, disabled=True)
    async def submit(self, _, interaction):
        self.data["adventure"] = self.data["adventure"][2:]
        request = await self.ctx.bot.AIOSession.post(
            "https://trovesaurus.com/clubadventures",
            data={"payload": json.dumps(self.data),
            "Token": self.ctx.bot.keys["Trovesaurus"]["Token"]}
        )
        if request.status == 400:
            return await interaction.response.send_message(
                f"There was an error connecting to the Trovesaurus API, please try again later.\nError: **{await request.text()}**",
            )
        await interaction.response.send_message(
            f"Club adventure submitted to Trovesaurus.",
            ephemeral=True
        )
        self.stop()
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, row=3)
    async def cancel(self, _, interaction):
        await self.message.delete(silent=True)
        await interaction.response.send_message(
            f"Your Club Adventure form was cancelled.",
            ephemeral=True
        )
        self.stop()

class ClubAdventuresModal(Modal):
    def __init__(self, view):
        super().__init__("Advertise a club adventure.")
        self.view = view
        items = [
            TextInput(
                custom_id="club",
                label="Club",
                style=discord.TextInputStyle.short,
                min_length=2,
                max_length=24,
                placeholder="Enter the name of the club",
                value=view.data["club"]
            ),
            TextInput(
                custom_id="time",
                label="Time left (Optional)",
                style=discord.TextInputStyle.short,
                min_length=2,
                max_length=32,
                placeholder="Enter the time left in the adventure",
                value=str(TimeConverter(view.data["time"]))
            )
        ]
        for item in items:
            self.add_item(item)

    async def callback(self, interaction):
        for child in self.children:
            if child.custom_id == "time":
                time = int(TimeConverter(child.value))
                if not time:
                    continue
                elif time > calculate_adventure_time(int(self.view.data["adventure"][0])):
                    return await interaction.response.send_message(
                        f"The time left is too long for the adventure.",
                        ephemeral=True
                    )
                self.view.data["time"] = time
            else:
                self.view.data[child.custom_id] = child.value
        self.view.manage_buttons()
        await interaction.response.send_message(
            f"Club name changed to **{self.view.data['club']}** and time set to **{TimeConverter(self.view.data['time'])}**.",
            ephemeral=True
        )
        await self.view.message.edit(view=self.view)

class ClubAdventurePicker(Select):
    def __init__(self, view):
        adventures = [
            "4:Trigger Magic Find",
            "3:Collect a Chaos Chest",
            "3:Collect Water Gem Boxes",
            "3:Collect Fire Gem Boxes",
            "3:Collect Cosmic Gem Boxes",
            "3:Collect Air Gem Boxes",
            "2:Defeat Radiant Giants",
            "2:Defeat 3 Delve Bosses",
            "2:Deal Damage or Win in Bomber Royale",
            # "1:Defeat Dungeon Bosses In Treasure Isles or the Lost Isles",
            # "1:Defeat Dungeon Bosses In Neon City",
            # "1:Defeat Dungeon Bosses In Jurassic Jungle",
            # "1:Defeat Dungeon Bosses In Forbidden Spires",
            # "1:Defeat Dungeon Bosses In Dragonfire Peaks",
            # "1:Defeat Dungeon Bosses In Cursed Vale",
            # "0:Go Fishing",
            # "0:Defeat Dungeon Bosses In Permafrost",
            # "0:Defeat Dungeon Bosses In Medieval Highlands",
            # "0:Defeat Dungeon Bosses In Fae Forest",
            # "0:Defeat Dungeon Bosses In Desert Frontier",
            # "0:Defeat Dungeon Bosses In Candoria"
        ]
        options = [
            discord.SelectOption(label=adventure[2:], value=adventure, default=adventure==view.data["adventure"])
            for adventure in adventures
        ]
        super().__init__(placeholder="Pick an adventure", options=options, row=0)

    async def callback(self, interaction):
        adventure = self.values[0]
        self.view.data["adventure"] = adventure
        value = int(adventure[0])
        time = calculate_adventure_time(value)
        if not self.view.data.get("time") or self.view.data.get("time") > time:
            self.view.data["time"] = time
        self.view.manage_buttons()
        await self.view.message.edit(view=self.view)
        await interaction.response.send_message(
            f"Adventure changed to **{adventure[2:]}**.",
            ephemeral=True
        )

class ClubAdventuresPlatformSelect(Select):
    def __init__(self, view):
        platforms = [
            "PC",
            "Xbox",
            "PS4-EU",
            "PS4-NA",
            "Switch"
        ]
        options = [
            discord.SelectOption(label=platform, default=platform==view.data["platform"])
            for platform in platforms
        ]
        super().__init__(placeholder="Pick a platform", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        platform = self.values[0]
        self.view.data["platform"] = platform
        self.view.manage_buttons()
        await self.view.message.edit(view=self.view)
        await interaction.response.send_message(
            f'Platform changed to **{platform}**.',
            ephemeral=True
        )

# Club Advertise

class ClubAdvertise(BaseView):
    def __init__(self, ctx, channel):
        super().__init__()
        self.ctx = ctx
        self.channel = channel
        self.data = {
            "club": None,
            "description": None,
            "invite": None,
            "platform": None
        }
        self.manage_buttons()
    
    def manage_buttons(self):
        if self.data["club"] and self.data["description"] and self.data["invite"]:
            self.fill.label = "Edit advertisement"
            self.fill.style = discord.ButtonStyle.success
        if all([v for k, v in self.data.items() if k not in ["platform"]]):
            self.submit.disabled = False
        for item in self.children:
            if isinstance(item, ClubAdvertisePlatformSelect):
                self.remove_item(item)
        self.add_item(ClubAdvertisePlatformSelect(self))

    def build_embed(self):
        embed = CEmbed()
        embed.title = self.data["club"] or "No club name set."
        embed.description = self.data["description"] or "No description set."
        embed.timestamp = datetime.utcnow()
        #embed.set_author(name="Club Advertisement")
        embed.add_field(name="Platform", value=self.data["platform"] or "No platform set.")
        embed.add_field(name="Discord", value=self.data['invite'] or "No invite set.")
        embed.set_footer(text=f"Advertised by {self.ctx.author} ({self.ctx.author.id})", icon_url=self.ctx.author.avatar)
        return embed

    @discord.ui.button(label='Fill advertisement', style=discord.ButtonStyle.secondary, row=0)
    async def fill(self, _, interaction):
        modal = ClubAdvertiseModal(self)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label='Submit', style=discord.ButtonStyle.success, row=2, disabled=True)
    async def submit(self, _, interaction):
        await interaction.response.defer(ephemeral=True)
        async for m in self.channel.history(limit=1000, after=datetime.utcnow()-timedelta(seconds=604800)):
            if m.author.id != self.ctx.bot.user.id:
                continue
            if (m.embeds and
                m.embeds[0].title and
                m.embeds[0].title.lower() == self.data["club"].lower() and
                m.embeds[0].fields[0].value == self.data["platform"]):
                return await interaction.followup.send(
                    "You can only submit one advertisement per week.",
                    ephemeral=True
                )
        await self.channel.send(embed=self.build_embed())
        await interaction.followup.send(
            f"Club advertisement submitted.",
            ephemeral=True
        )
        self.stop()
    
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger, row=2)
    async def cancel(self, _, interaction):
        await self.message.delete(silent=True)
        await interaction.response.send_message(
            f"Your Club Advertisement form was cancelled.",
            ephemeral=True
        )
        self.stop()

class ClubAdvertiseModal(Modal):
    def __init__(self, view):
        super().__init__("Advertise your club.")
        self.view = view
        items = [
            TextInput(
                custom_id="club",
                label="Club Name",
                style=discord.TextInputStyle.short,
                min_length=2,
                max_length=24,
                placeholder="Enter the name of the club",
                value=self.view.data["club"]
            ),
            TextInput(
                custom_id="description",
                label="Description",
                style=discord.TextInputStyle.short,
                min_length=20,
                max_length=200,
                placeholder="Enter a description of the club",
                value=self.view.data["description"]
            ),
            TextInput(
                custom_id="invite",
                label="Discord Invite Link",
                style=discord.TextInputStyle.short,
                max_length=48,
                placeholder="Enter a discord invite link",
                value=self.view.data["invite"]
            )
        ]
        for item in items:
            self.add_item(item)

    async def callback(self, interaction):
        for child in self.children:
            if child.custom_id == "invite":
                try:
                    invite = (await self.view.ctx.bot.fetch_invite(child.value))
                    if invite.max_age or invite.max_uses:
                        return await interaction.response.send_message(
                            "The invite link can't expire nor have limited uses.",
                            ephemeral=True
                        )
                    self.view.data["invite"] = invite.url
                except:
                    return await interaction.response.send_message(
                        "Invalid invite link.",
                        ephemeral=True
                    )
            else:
                self.view.data[child.custom_id] = child.value.strip()
        self.view.manage_buttons()
        await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        return await interaction.response.send_message(
            "Club advertisement filled.",
            ephemeral=True
        )

class ClubAdvertisePlatformSelect(Select):
    def __init__(self, view):
        platforms = [
            "PC",
            "Xbox",
            "PS4-EU",
            "PS4-NA",
            "Switch"
        ]
        options = [
            discord.SelectOption(label=platform, default=platform==view.data["platform"])
            for platform in platforms
        ]
        super().__init__(placeholder="Pick a platform", options=options, row=1)

    async def callback(self, interaction):
        platform = self.values[0]
        self.view.data["platform"] = platform
        self.view.manage_buttons()
        await self.view.message.edit(embed=self.view.build_embed(), view=self.view)
        await interaction.response.send_message(
            f'Platform changed to **{platform}**.',
            ephemeral=True
        )