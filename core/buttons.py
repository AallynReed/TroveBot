import discord

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
