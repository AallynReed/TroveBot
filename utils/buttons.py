import asyncio
import re
from copy import copy
from datetime import datetime
from functools import partial
from random import choices
from string import ascii_letters, digits

import discord

from utils.builds import BuildsMaker
from utils.CustomObjects import CEmbed, Dict


class Dummy():
    ...

# Base

class BaseView(discord.ui.View):
    def __init__(self, timeout=120):
        super().__init__(
            timeout=timeout
        )

    async def interaction_check(self, item, interaction: discord.Interaction):
        if self.ctx.author == interaction.user:
            return True
        else:
            await interaction.response.send_message("You can't interact with these buttons as you weren't the one using the command.", ephemeral=True)
            return False

    async def on_timeout(self):
        try:
            await self.message.edit(view=None)
        except:
            pass

## Static

class Confirm(BaseView):
    def __init__(self, ctx, timeout=180):
        super().__init__(
            timeout=timeout
        )
        self.ctx = ctx
        self.value = None

    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = True
        self.stop()

    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.danger)
    async def cancel(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.value = False
        self.stop()

class Traceback(discord.ui.View):
    def __init__(self, ctx, exception, timeout=60):
        super().__init__(
            timeout=timeout
        )
        self.ctx = ctx
        self.exception = exception

    @discord.ui.button(label='Show Traceback', style=discord.ButtonStyle.grey)
    async def show(self, button: discord.ui.Button, interaction: discord.Interaction):
        if len(self.exception) > 2000:
            await interaction.response.send_message(f"```py\n{self.exception[:1990]}```", ephemeral=True)
            await interaction.followup.send(f"```py\n{self.exception[1990:3980]}```", ephemeral=True)
        else:
            await interaction.response.send_message(f"```py\n{self.exception}```", ephemeral=True)

## Dynamic

# Others

class OptionPicker(BaseView):
    def __init__(self, ctx, options):
        super().__init__(
            timeout=60
        )
        self.ctx = ctx
        self.value = None
        for option in options:
            self.add_item(OptionPickerButton(emoji=option["emoji"], text=option["text"]))
        
class OptionPickerButton(discord.ui.Button["OptionPicker"]):
    def __init__(self, emoji, text):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji, label=text)

    async def callback(self, interaction: discord.Interaction):
        self.view.value = self.label
        self.view.stop()

class Paginator(BaseView):
    def __init__(self, ctx, pages, page=0, start_end=False, step_10=False, timeout=120):
        super().__init__(
            timeout=timeout
        )
        self.ctx = ctx
        self.page = page
        self.pages = pages
        self.count = len(pages)
        self.start_end = start_end
        self.step_10 = step_10
        self.add_buttons()

    def add_buttons(self):
        non_page_buttons = [item for item in self.children if not isinstance(item, PaginatorButton)]
        if self.children:
            self.clear_items()
        if not self.count or self.count == 1:
            return
        previous_page = self.page - 1
        if previous_page < 0:
            previous_page = self.count - 1
        self.add_item(PaginatorButton("◀️", previous_page))
        next_page = self.page + 1
        if next_page > self.count - 1:
            next_page = 0
        self.add_item(PaginatorButton("▶️", next_page))
        if self.start_end and self.count > 5:
            if self.page != 0:
                self.add_item(PaginatorButton("⏮️", 0))
        if self.step_10 and self.count > 10:
            previous_10 = self.page - 10
            if previous_10 < 0:
                previous_10 = self.count - (10 - self.page)
            self.add_item(PaginatorButton("⏪", previous_10))
        if self.step_10 and self.count > 10:
            next_10 = self.page + 10
            if next_10 > self.count - 1:
                next_10 = 0 + next_10 - self.count
            self.add_item(PaginatorButton("⏩", next_10))
        if self.start_end and self.count > 5:
            if self.page != self.count - 1:
                self.add_item(PaginatorButton("⏭️", self.count - 1, row=1 if len(self.children) >= 5 else 0))
        for item in non_page_buttons:
            self.add_item(item)

class PaginatorButton(discord.ui.Button["Paginator"]):
    def __init__(self, emoji, page, row=0):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=emoji, row=row)
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        self.pages = self.view.pages
        self.view.page = self.page
        self.view.add_buttons()
        await interaction.message.edit(content=self.pages[self.page].get("content"), embed=self.pages[self.page]["embed"], view=self.view)

# Help View

class HelpView(BaseView):
    def __init__(self, ctx, commands, timeout=120):
        super().__init__(
            timeout=timeout
        )
        self.ctx = ctx
        self.commands = commands
        self.category = None
        self.get_buttons()

    async def on_timeout(self):
        #await super().on_timeout()
        try:
            await self.message.delete()
        except:
            pass

    def get_buttons(self):
        if self.children:
            self.clear_items()
        if not self.category:
            for category, pages in sorted(self.commands.items(), key=lambda x: x[0]):
                if category in ["embed"]:
                    continue
                self.add_item(HelpButton(self.ctx, pages, self.children, label=category))
        
class HelpButton(discord.ui.Button["HelpView"]):
    def __init__(self, ctx, pages, children, label, view=None):
        row = divmod(len(children), 5)[0]
        super().__init__(style=discord.ButtonStyle.secondary, label=label.capitalize(), row=row)
        self.help_view = view
        self.ctx = ctx
        self.pages = pages

    async def callback(self, interaction: discord.Interaction):
        if self.label == "Back":
            self.help_view.category = None
            self.help_view.get_buttons()
            return await interaction.response.edit_message(embed=self.help_view.commands["embed"], view=self.help_view)
        else:
            self.view.category = self.label.lower()
            paginator = Paginator(self.ctx, self.pages)
            paginator.add_item(HelpButton(self.ctx, [], [], label="Back", view=self.view))
            await interaction.response.edit_message(embed=self.pages[0]["embed"], view=paginator)
            if await paginator.wait():
                await self.view.on_timeout()

# Gem Tutorial View

class GemTutorial(BaseView):
    def __init__(self, ctx, tabs, topics):
        self.ctx = ctx
        super().__init__(
            timeout=600
        )
        self.initial_menu = tabs["embed"]
        self.selected_tab = None
        self.selected_topic = None
        self.tabs = tabs["tabs"]
        self.topics = topics
        self._setup_buttons(start=True)

    def _setup_buttons(self, start=False):
        if self.children:
            self.clear_items()
        if not self.selected_tab:
            e = self.initial_menu
            for tab in self.tabs.keys():
                self.add_item(GemTutorialButton(label=tab))
        elif self.selected_tab:
            if not self.selected_topic:
                e = CEmbed(color=discord.Color(3092790))
                e.set_author(name=f"Gem Tutorial - {self.selected_tab}")
                e.description = "Select a topic to learn"
            else:
                e = CEmbed.from_dict(self.selected_topic.embed) 
            tab_topics = [t for t in self.topics if t.tab == self.selected_tab]
            self.add_item(GemTutorialTopics(self, tab_topics))
            self.add_item(GemTutorialButton(label="Back"))
            if e.footer.text:
                e.footer.text += " | Last updated"
            else:
                e.set_footer(text="Last updated")
            e.timestamp = self.initial_menu.timestamp
        if not start:
            asyncio.create_task(self.message.edit(embed=e, view=self))

class GemTutorialButton(discord.ui.Button["GemTutorial"]):
    def __init__(self, label):
        super().__init__(style=discord.ButtonStyle.secondary, label=label)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if self.label == "Back":
            self.view.selected_topic = None
            self.view.selected_tab = None
        else:
            self.view.selected_tab = self.label
        self.view._setup_buttons()

class GemTutorialTopics(discord.ui.Select):
    def __init__(self, view, topics):
        select = []
        select.extend([
            discord.SelectOption(label=t.name, default=t == view.selected_topic)
            for t in topics
        ])
        super().__init__(placeholder=f"Pick a topic", options=select)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.selected_topic = [t for t in self.view.topics if self.values[0] == t.name][0]
        self.view._setup_buttons()

# Profiles View

class ProfileView(BaseView):
    def __init__(self, ctx, get_profile, user, classes, server=1):
        super().__init__(
            timeout=120
        )
        self.ctx = ctx
        y = 0
        for i in range(len(classes)):
            _class = classes[i]
            if i in [4, 8, 12, 16]:
                y += 1
            self.add_item(ProfileButton(get_profile, user, _class, server, row=y))

class ProfileButton(discord.ui.Button["ProfileView"]):
    def __init__(self, get_profile, user, _class, server, row):
        super().__init__(style=discord.ButtonStyle.secondary, emoji=_class.emoji, row=row)
        self.user = user
        self.server = server
        self._class = _class
        self.get_profile = get_profile

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view, image = await self.get_profile(self.view.ctx, self.user, self._class, self.server, is_active=self.view.message)
        await self.view.message.edit(view=view, file=image)

# Gear Builds View

class BuildsOptions(discord.ui.Select):
    def __init__(self, view, row=1):
        self.ctx = view.ctx
        self._class = view._class
        select = [discord.SelectOption(label=k.capitalize(), description=v["description"], emoji=self.get_emote(k), default=k == view.build_type) for k, v in view.all_gears[view._class].items()]
        super().__init__(placeholder="Pick a build type (Required)", options=select, row=row)

    def get_emote(self, build_type):
        emotes = {
            "light": "<:Light:880134289906368543>",
            "coeff":"<:Coeff:880134290011209758>",
            "farm":"<:Farm:880134290040565812>",
            "tank": "<:Tank:880134290128633906>"
        }
        return emotes[build_type]

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view.build_type = self.values[0].lower()
        self.view.setup_buttons()
        await self.view.message.edit(content=None, embed=self.view.build["embed"], view=self.view)

class BuildClassOptions(discord.ui.Select):
    def __init__(self, view, row=0):
        select = []
        select.extend([
            discord.SelectOption(label=c.name, emoji=c.emoji, default=c.name == view._class)
            for c in view.classes
        ])
        super().__init__(placeholder=f"Pick a class (Required)", options=select, row=row)
    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.view._class = self.values[0]
        if self.view.build_type and self.view.build_type not in self.view.all_gears[self.view._class].keys():
            self.view.build_type = None
        self.view.setup_buttons()
        await self.view.message.edit(
            content=f"Pick a build type for **{self.view._class}**" if not self.view.build_type else None,
            embed=self.view.build["embed"] if self.view.build else None,
            view=self.view
        )

class BuildsPickView(BaseView):
    def __init__(self, ctx, _class, build_type, all_gears):
        super().__init__(
            timeout=300
        )
        self.ctx = ctx
        self.build_type = build_type
        self.all_gears = all_gears
        self.build = None
        self._class = _class.name if _class else None
        self.classes = self.classes = ctx.bot.Trove.values.classes
        self.setup_buttons()

    def setup_buttons(self):
        if self.children:
            self.clear_items()
        self.build = None
        if self.build_type:
            self.build = self.all_gears[self._class][self.build_type]
        self.add_item(BuildClassOptions(self))
        if self._class:
            self.add_item(BuildsOptions(self))

    async def on_timeout(self):
        await super().on_timeout()
        ctx = self.ctx
        if ctx.guild.id == 118027756075220992 and self.build_type:
            try:
                await ctx.message.delete()
            except:
                pass
            try:
                channel = self.message.channel
                message = await channel.fetch_message(self.message.id)
                await message.edit(content=f"{ctx.author.mention} used `{ctx.prefix}gear` for **{self._class} {self.build_type.capitalize()} General build** automatically hidden after 5 minutes. Click the 👁️ to show\nYou may also follow this link <{self.build['link']}> for this build.", suppress=True)
                await message.add_reaction("👁️")
                # await self.message.edit(content=f"{ctx.author.mention} used `{ctx.prefix}gear` for **{self._class} {self.build_type.capitalize()} General build** automatically hidden after 5 minutes. Click the 👁️ to show\nYou may also follow this link <{self.build['link']}> for this build.", suppress=True)
                # await self.message.add_reaction("👁️")
            except:
                return
        elif not self.build_type:
            try:
                await ctx.message.delete()
            except:
                pass
            try:
                await self.message.delete()
            except:
                pass

# Gem Builds View

class GemBaseButton(discord.ui.Button["GemBuildsView"]):
    async def no_concurrent(self, interaction):
        value = self.view.waiting_input
        if value:
            await interaction.response.send_message("You can't activate 2 inputs at the same time, please finish first input.", ephemeral=True)
            return value
        return value

class GemBuildsButton(GemBaseButton):
    def __init__(self, view, text, emoji, row=0):
        disabled = not (view.build_arguments._class and view.build_arguments.build_type)
        super().__init__(label=text, disabled=disabled, emoji=emoji, row=row)
        self.build_view = view

    def GenerateCode(self, length):
        return "".join(choices(ascii_letters+digits, k=length))

    async def callback(self, interaction: discord.Interaction):
        if str(self.emoji) == "📤":
            time = int(datetime.utcnow().timestamp())
            args = self.view.build_arguments
            data = {
                "code":         self.GenerateCode(8),
                "creator":      self.view.ctx.author.id,
                "name":         None,
                "description":  f"{args.build_type.capitalize()} build for {args._class}",
                "public":       False,
                "views":        0,
                "likes":        [],
                "created_at":   time,
                "last_updated": time,
                "config":       self.view.build_arguments.__dict__
            }
            await self.view.ctx.bot.db.db_users.update_one({"_id": data["creator"]}, {"$push": {"builds.saved": data}})
            await interaction.response.send_message(f"Build was saved with ID -> **{data['code']}**\nCheck out `{self.view.ctx.prefix}builds list`", ephemeral=True)
        elif str(self.emoji) == "📥":
            time = int(datetime.utcnow().timestamp())
            self.view.build_data["config"] = copy(self.view.build_arguments.__dict__)
            self.view.build_data["last_updated"] = time
            await self.view.ctx.bot.db.db_users.update_one(
                {
                    "_id": self.view.ctx.author.id,
                    "builds.saved.code": self.view.build_data["code"]
                },
                {
                    f"$set": {
                        "builds.saved.$.config": self.view.build_data["config"],
                        "builds.saved.$.last_updated": self.view.build_data["last_updated"]
                    }
                }
            )
            await interaction.response.send_message(f"Build with ID **{self.view.build_data['code']}** was updated.", ephemeral=True)
            self.view.setup_buttons()
        elif str(self.emoji) == "✏️":
            self.build_view.timeout = self.build_view.original_timeout
            await interaction.response.edit_message(view=self.build_view)
            self.view.stop()
        elif not await self.no_concurrent(interaction):
            self.view.setup_buttons(True)

class GemBuildsToggle(GemBaseButton):
    def __init__(self, view, field, label, invert, emoji=None, disabled=False, row=0):
        super().__init__(label=label, disabled=disabled, row=row, emoji=emoji)
        self.field = field
        self.raw_value = getattr(view.build_arguments, field)
        self.value = not self.raw_value if invert else self.raw_value
        self._set_style()

    def _set_style(self):
        if self.value:
            self.style = discord.ButtonStyle.green
        else:
            self.style = discord.ButtonStyle.grey

    async def callback(self, interaction: discord.Interaction):
        if not await self.no_concurrent(interaction):
            await interaction.response.defer()
            setattr(self.view.build_arguments, self.field, not self.raw_value)
            self.view.setup_buttons()

class GemBuildsInput(GemBaseButton):
    def __init__(self, view, field, label, hint, emoji=None, disabled=False, row=0):
        super().__init__(disabled=disabled, row=row, emoji=emoji)
        self.build_view = view
        self.field = field
        self.hint = hint + " or `cancel` to stop input."
        self.value = getattr(view.build_arguments, field)
        if self.field == "build":
            self.label = label + (f" ({self.build_text(self.value)})" if self.value else "")
        else:
            self.label = label + (f" ({self.value})" if self.value else "")
        self._set_style()

    def _set_style(self):
        if self.value:
            self.style = discord.ButtonStyle.green
        else:
            self.style = discord.ButtonStyle.grey

    async def callback(self, interaction: discord.Interaction):
        if not await self.no_concurrent(interaction):
            if self.value and self.field in ["build", "filter"]:
                value = None
            elif self.value and self.field in ["light", "ally", "cd_count"]:
                value = 0
            else:
                self.view.waiting_input = True
                await interaction.response.send_message(self.hint, ephemeral=True)
                self.interaction = interaction
                try:
                    message = await self.view.ctx.bot.wait_for("message", check=getattr(self, f"check_{self.field}"), timeout=60)
                except asyncio.TimeoutError:
                    self.view.waiting_input = False
                    return await interaction.followup.send(f"You took to long to respond, action cancelled.", ephemeral=True)
                if message.content.lower() == "cancel":
                    self.view.waiting_input = False
                    return await interaction.followup.send(f"You've cancelled input.", ephemeral=True)
                if self.field == "build":
                    value = self.validate_build(message.content)
                elif self.field == "filter":
                    value = self.validate_build_part(message.content)
                else:
                    value = int(message.content)
            setattr(self.view.build_arguments, self.field, value)
            self.view.setup_buttons()
            self.view.waiting_input = False

    def check_light(self, message):
        if self.view.ctx.author == message.author and self.view.ctx.channel == message.channel:
            if (message.content.isdigit() and 1 <= int(message.content) <= 15000) or message.content.lower() == "cancel":
                asyncio.create_task(self.delete_msg(message))
                return True
            asyncio.create_task(self.delete_msg(message, True))
        return False

    def check_ally(self, message):
        if self.view.ctx.author == message.author and self.view.ctx.channel == message.channel:
            if (message.content.isdigit() and 1 <= int(message.content) <= 300) or message.content.lower() == "cancel":
                asyncio.create_task(self.delete_msg(message))
                return True
            asyncio.create_task(self.delete_msg(message, True))
        return False

    def check_cd_count(self, message):
        if self.view.ctx.author == message.author and self.view.ctx.channel == message.channel:
            if (message.content.isdigit() and int(message.content) in list(range(1, 4))) or message.content.lower() == "cancel":
                asyncio.create_task(self.delete_msg(message))
                return True
            asyncio.create_task(self.delete_msg(message, True))
        return False

    def check_build(self, message):
        if self.view.ctx.author == message.author and self.view.ctx.channel == message.channel:
            if self.validate_build(message.content) or message.content.lower() == "cancel":
                asyncio.create_task(self.delete_msg(message))
                return True
            asyncio.create_task(self.delete_msg(message, True))
        return False

    def check_filter(self, message):
        if self.view.ctx.author == message.author and self.view.ctx.channel == message.channel:
            if self.validate_build_part(message.content) or message.content.lower() == "cancel":
                asyncio.create_task(self.delete_msg(message))
                return True
            asyncio.create_task(self.delete_msg(message, True))
        return False

    async def delete_msg(self, message, wrong=False):
        try:
            await message.delete()
        except:
            pass
        # if wrong:
        #     await self.interaction.followup.send(f"Invalid input\n{self.hint}", ephemeral=True)

    def validate_build(self, argument):
        regex = r"([0-9]{1})[\/]([0-9]{1})[\/ ]([0-9]{1,2})[\/]([0-9]{1,2})(?:(?: )?[\/+ ](?: )?([0-9]{1})[\/]([0-9]{1})(?:[\/ ]([0-9]{1})[\/ ]([0-9]{1}))?[\/ ]([0-9]{1})[\/]([0-9]{1}))?"
        res = re.findall(regex, argument)
        if res:
            res = self.chunk_builds([int(i) for i in list(res[0]) if i])
            if self.is_valid_build(res):
                return res
        return False

    def validate_build_part(self, text):
        regex = r"([0-9]{1,2})\/([0-9]{1,2})(?:\/([0-6]{1}))?"
        result = re.findall(regex, text)
        if not result:
            return False
        result = tuple(int(i) for i in result[0] if i)
        total = sum(result)
        if len(result) == 2 and total not in [9, 18]:
            return False
        if len(result) == 3 and total not in [3, 6]:
            return False
        return "/".join([str(r) for r in result])

    def is_valid_build(self, build):
        if sum(build[0]) != 9:
            return False
        if sum(build[1]) != 18:
            return False
        if sum(build[2]) != 3:
            return False
        if sum(build[3]) != 6:
            return False
        return True

    def chunk_builds(self, lst):
        result = []
        if len(lst) in [4, 8]:
            for i in range(0, len(lst), 2):
                result.append(list(lst[i:i + 2]))
            if len(lst) == 4:
                result.append([0,0,3])
                result.append([0,0,6])
            if len(lst) == 8:
                y = sum(result[2])
                result[2] = list(list(result[2]) + [3-y])
                y = sum(result[3])
                result[3] = list(list(result[3]) + [6-y])

        else:
            first_lst = lst[:4]
            for i in range(0, len(first_lst), 2):
                result.append(list(first_lst[i:i + 2]))
            first_lst = lst[4:]
            for i in range(0, len(first_lst), 3):
                result.append(list(first_lst[i:i + 3]))
        return result

    def build_text(self, b):
        build = []
        [build.extend(i) for i in b]
        light = self.build_view.build_arguments.light
        build_type = self.build_view.build_arguments.build_type
        if not light or (light and build_type in ["coeff", "health"]):
            del build[6]
            del build[8]
        if not light and build_type not in ["coeff", "health"]:
            build = build[:4]
        text = ""
        text += f"{'/'.join([str(i) for i in build][:4]): <8}"
        if len(build) == 8:
            text += " + " + "/".join([str(i) for i in build][4:])
        elif len(build) == 10:
            text += " + " + "/".join([str(i) for i in build][4:7]) + " " + "/".join([str(i) for i in build][7:10])
        return text.strip()

class GemBuildsOption(discord.ui.Select):
    async def no_concurrent(self, interaction):
        value = self.view.waiting_input
        if value:
            await interaction.response.send_message("You can't activate 2 inputs at the same time, please finish first input.", ephemeral=True)
            return value
        return value

class GemBuildTypeOptions(GemBuildsOption):
    def __init__(self, view, options, row=0):
        descriptions = {
            "light": "These builds aim at best DPS for deeper Delves.",
            "farm": "These builds aim at best farming by tuning values for speed.",
            "coeff": "These builds aim at most damage Ubers and ST's.",
            "health": "These builds aim at most amount of health for tanking."
        }
        select = [
            discord.SelectOption(label=t.capitalize(), description=descriptions[t], emoji=self.get_emote(t))
            for t in options
        ]
        super().__init__(placeholder=f"Pick a build type (Required)", options=select, row=row)

    def get_emote(self, build_type):
        emotes = {
            "light": "<:Light:880134289906368543>",
            "coeff":"<:Coeff:880134290011209758>",
            "farm":"<:Farm:880134290040565812>",
            "health": "<:Tank:880134290128633906>"
        }
        return emotes[build_type]

    async def callback(self, interaction: discord.Interaction):
        if not await self.no_concurrent(interaction):
            await interaction.response.defer()
            self.view.build_arguments.build_type = self.values[0].lower()
            if self.values[0].lower() == "farm":
                self.view.build_arguments.cd_count = 0
                if not self.view.build_arguments.light:
                    self.view.build_arguments.light = 8000
            _class = [c for c in self.view.classes if c.name == self.view.build_arguments._class][0]
            if not self.view.build_arguments.ally:
                if self.values[0].lower() == "farm":
                    if _class.dmg_type == "MD":
                        self.view.build_arguments.ally = self.view.allies["Orchian"]
                    elif _class.dmg_type == "PD":
                        self.view.build_arguments.ally = self.view.allies["Animated Jug"]
                if self.values[0].lower() == "coeff":
                    if _class.dmg_type == "MD":
                        self.view.build_arguments.ally = self.view.allies["Orchian"]
                    elif _class.dmg_type == "PD":
                        self.view.build_arguments.ally = self.view.allies["Chester Eggington the Third"]
                if self.values[0].lower() == "light":
                    if _class.dmg_type == "MD":
                        self.view.build_arguments.ally = self.view.allies["Puck"]
                    elif _class.dmg_type == "PD":
                        self.view.build_arguments.ally = self.view.allies["Earnie"]
            self.view.setup_buttons()

class ClassOptions(GemBuildsOption):
    def __init__(self, view, options, something, extra, row=0):
        select = []
        if something == "subclass" and view.build_arguments.subclass:
            select.append(discord.SelectOption(label="None"))
        select.extend([
            discord.SelectOption(label=c.name, emoji=c.emoji, default=c.name == view.build_arguments._class if something == "class" else c.name == view.build_arguments.subclass)
            for c in options
            if (c.name != view.build_arguments._class and something != "class") or (c.name != view.build_arguments.subclass and something != "subclass")
        ])
        super().__init__(placeholder=f"Pick a {something} {extra}", options=select, row=row)
        self.something = something
    
    async def callback(self, interaction: discord.Interaction):
        if not await self.no_concurrent(interaction):
            await interaction.response.defer()
            if self.something == "class":
                self.view.build_arguments._class = self.values[0]
            elif self.something == "subclass":
                if self.values[0] == "None":
                    self.view.build_arguments.subclass = None
                else:
                    self.view.build_arguments.subclass = self.values[0]
            self.view.setup_buttons()

class AllyOptions(GemBuildsOption):
    def __init__(self, view, row=0):
        select = []
        if view.build_arguments.ally:
            select.append(discord.SelectOption(label="None"))
        select.extend([
            discord.SelectOption(label=c["name"], default=c == view.build_arguments.ally)
            for c in view.allies.values()
        ])
        super().__init__(placeholder=f"Pick an ally", options=select, row=row)
    
    async def callback(self, interaction: discord.Interaction):
        if not await self.no_concurrent(interaction):
            if self.values[0] == "None":
                self.view.build_arguments.ally = None
            else:
                self.view.build_arguments.ally = self.view.allies[self.values[0]]
            self.view.setup_buttons()

class GemBuildsView(BaseView):
    def __init__(self, ctx, build_data=None, timeout=300):
        super().__init__(
            timeout=timeout
        )
        self.original_timeout = timeout
        self.ctx = ctx
        self.build_data = build_data
        self._base_arguments(build_data["config"] if build_data else None)
        self.builds_maker = BuildsMaker(ctx)
        self.waiting_input = False
        self.classes = ctx.bot.Trove.values.classes
        self.setup_buttons(just_started=not bool(build_data))

    async def on_timeout(self):
        await super().on_timeout()
        ctx = self.ctx
        if ctx.guild.id == 118027756075220992:
            try:
                await ctx.message.delete()
            except:
                pass
            try:
                channel = self.message.channel
                message = await channel.fetch_message(self.message.id)
                await message.edit(content=f"{ctx.author.mention} used `{ctx.prefix}build` for **{self.build_arguments._class} {self.build_arguments.build_type.capitalize()} Gem build** automatically hidden after 5 minutes. Click the 👁️ to show.", suppress=True, view=None)
                await message.add_reaction("👁️")
                # await self.message.edit(content=f"{ctx.author.mention} used `{ctx.prefix}build` for **{self.build_arguments._class} {self.build_arguments.build_type.capitalize()} Gem build** automatically hidden after 5 minutes. Click the 👁️ to show.", suppress=True, view=None)
                # await self.message.add_reaction("👁️")
            except:
                pass

    def setup_buttons(self, paginate=False, just_started=False):
        if self.children:
            self.clear_items()
        classes = [c for c in self.classes]
        if not self.build_arguments._class or not self.build_arguments.build_type:
            self.add_item(ClassOptions(self, classes, "class", "(Required)", row=0))
        if self.build_arguments._class:
            types = ["light", "farm", "coeff", "health"]
            build_types = []
            for bt in types:
                t = bt
                if bt == "coeff":
                    t = "light"
                if bt == "health":
                    t = "tank"
                build_types.append(bt)
            if not self.build_arguments.build_type:
                self.add_item(GemBuildTypeOptions(self, build_types, row=1))
        if self.build_arguments._class and self.build_arguments.build_type:
            self.add_item(ClassOptions(self, classes, "subclass", "(Optional)", row=0))
            if self.build_arguments.build_type != "health":
                self.add_item(AllyOptions(self, row=1))
            self.add_item(GemBuildsInput(self, "light", "Light", "Type a value for light limit between 1 and 15000", disabled=self.build_arguments.build_type=="health", row=2))
            self.add_item(GemBuildsToggle(self, "deface", "Face Damage", True, disabled=self.build_arguments.build_type=="health", row=2))
            self.add_item(GemBuildsToggle(self, "bardcd", "Bard Song", False, disabled=self.build_arguments.build_type=="health", row=2))
            self.add_item(GemBuildsToggle(self, "food", "Food", False, disabled=self.build_arguments.build_type in ["health", "coeff"], row=2))
            _class = [c for c in classes if c.name == self.build_arguments._class]
            if (_class and _class[0].infinite_as) or self.build_arguments.build_type in ["health", "coeff"]:
                self.add_item(GemBuildsInput(self, "cd_count", "Gear CD", "Type a value for amount of Critical Damage stats to have in gear between 1 and 3", disabled=True, row=2))
            else:
                self.add_item(GemBuildsInput(self, "cd_count", "Gear CD", "Type a value for amount of Critical Damage stats to have in gear between 1 and 3", row=2))
            self.add_item(GemBuildsInput(self, "build", "Build", "Type a valid build to get detailed stats of. Example: `0/9/15/3`", disabled=bool(self.build_arguments.filter), row=3))
            self.add_item(GemBuildsInput(self, "filter", "Filter", "Type a valid build part to filter builds list. Example: `0/9` or `0/0/3`", disabled=bool(self.build_arguments.build), row=3))
            #self.add_item(GemBuildsToggle(self, "mod", "Mod Coeff", False, disabled=self.build_arguments.build_type=="health", row=3)) # Mod
            self.add_item(GemBuildsToggle(self, "primordial", "Cosmic Primordial", False, row=3))
            self.add_item(GemBuildsToggle(self, "crystal5", "Crystal 5", False, row=3))
            if not self.build_arguments.build:
                self.add_item(GemBuildsButton(self, "Page Mode", "📑", row=3))
            if not getattr(self, "build_data"):
                self.add_item(GemBuildsButton(self, "Save Build", "📤", row=4))
            elif self.build_data and self.ctx.author.id == self.build_data["creator"]:
                if self.build_arguments.__dict__ != self.build_data["config"]:
                    self.add_item(GemBuildsButton(self, f"Update Build ({self.build_data['code']})", "📥", row=4))
        if not just_started:
            asyncio.create_task(self.update_message(paginate, bool(self.build_arguments.build_type)))
        
    async def update_message(self, paginate, fetch_builds=False):
        if paginate:
            arguments = self.build_arguments.__dict__
            func = partial(self.builds_maker.get_pages, arguments)
            pages = await self.ctx.bot.loop.run_in_executor(None, func)
            self.pages = pages
            paginator = Paginator(self.ctx, self.pages, start_end=True, timeout=self.timeout)
            paginator.message = self.message
            paginator.add_item(GemBuildsButton(self, "Edit Mode", "✏️", row=0))
            await self.message.edit(content=None, embed=self.pages[0]["embed"], view=paginator)
            self.timeout = None
            if await paginator.wait():
                await self.on_timeout()
        else:
            if fetch_builds:
                arguments = {
                    attr: getattr(self.build_arguments, attr)
                    for attr in dir(self.build_arguments)
                    if not attr.startswith("__")
                }
                func = partial(self.builds_maker.get_pages, arguments)
                pages = await self.ctx.bot.loop.run_in_executor(None, func)
                self.pages = pages
                while not hasattr(self, "message"):
                    await asyncio.sleep(0.1)
                await self.message.edit(content=self.message.content if hasattr(self, "build_data") and self.build_data else None, embed=self.pages[0]["embed"], view=self)
            else:
                await self.message.edit(view=self)

    def _base_arguments(self, arguments):
        build_arguments = {
            "_class": None,
            "build_type": None,
            "build": None,
            "subclass": None,
            "primordial": False,
            "crystal5": False,
            "light": 0,
            "cd_count": 3,
            "deface": False,
            "ally": None,
            "mod": False,
            "bardcd": False,
            "food": True,
            "filter": None
        }
        if arguments:
            build_arguments = Dict(arguments).fix(build_arguments)
        self.build_arguments = Dummy()
        for k, v in build_arguments.items():
            setattr(self.build_arguments, k, v)

    @property
    def allies(self):
        return {
            "Orchian": {
                "name": "Orchian",
                "type": "farm",
                "damage": "MD",
                "stats": {
                    "Damage": 25,
                    "Light": 400
                }
            },
            "Aevyr": {
                "name": "Aevyr",
                "type": "farm",
                "damage": "MD",
                "stats": {
                    "Damage": 20,
                    "Light": 300
                }
            },
            "Puck": {
                "name": "Puck",
                "type": "light",
                "damage": "MD",
                "stats": {
                    "Damage": 20,
                    "Light": 300
                }
            },
            "Earnie": {
                "name": "Earnie",
                "type": "dps",
                "damage": "PD",
                "stats": {
                    "Damage": 25,
                    "Light": 400
                }
            },
            "Animated Jug": {
                "name": "Animated Jug",
                "type": "farm",
                "damage": "PD",
                "stats": {
                    "Damage": 20,
                    "Light": 300
                }
            },
            "Jingles": {
                "name": "Jingles",
                "type": "farm",
                "damage": "PD",
                "stats": {
                    "Damage": 20,
                    "Light": 300
                }
            },
            "Chester Eggington the Third": {
                "name": "Chester Eggington the Third",
                "type": "farm",
                "damage": "PD",
                "stats": {
                    "Damage": 30,
                    "Light": 0
                }
            },
            "Lil Luckbeast": {
                "name": "Lil Luckbeast",
                "type": "farm",
                "damage": None,
                "stats": {
                    "Damage": 0,
                    "Light": 0
                }
            },
            "Clownish Kicker": {
                "name": "Clownish Kicker",
                "type": "farm",
                "damage": None,
                "stats": {
                    "Damage": 0,
                    "Light": 0
                }
            }
        }
