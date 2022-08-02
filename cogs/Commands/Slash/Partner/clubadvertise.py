# Priority: 1
import re
from datetime import datetime, timedelta
from typing import Literal

from discord.app import Option
from utils.buttons import Page, Pager
from utils.objects import SlashCommand
from utils.partner import ClubAdvertise


class ClubCommand(SlashCommand, name="club", guilds=[118027756075220992]):
    ...

class ClubAdvertiseCommand(SlashCommand, name="advert", description="Advertise your club at Trovesaurus.", parent=ClubCommand):
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context(ephemeral=True)
        advertise_panel = ctx.bot.get_channel(432281532091072513)
        messages = await advertise_panel.history(limit=None, after=datetime.utcnow()-timedelta(days=90)).flatten() # 90
        messages = [
            m for m in messages
            if (m.author.id == ctx.bot.user.id and
                m.embeds and
                m.embeds[0].footer and
                str(ctx.author.id) in m.embeds[0].footer.text
            )
        ]
        view = ClubAdvertise(ctx, advertise_panel, platform=messages[0].embeds[0].fields[0].value if messages else None) 
        view.message = await ctx.send(
            embed=view.build_embed(),
            view=view
        )

class ClubAdvertiseListCommand(SlashCommand, name="list", description="List club advertisements.", parent=ClubCommand):
    platform: Literal["PC", "PS4-NA", "PS4-EU", "Xbox", "Switch"] = Option(description="Pick platform to find clubs for.")
    async def callback(self):
        try:
            await super().callback()
        except:
            return
        ctx = await self.get_context(ephemeral=True)
        advertise_panel = ctx.bot.get_channel(432281532091072513)
        invites = []
        #servers = []
        ads = []
        async for message in advertise_panel.history(limit=None, after=datetime.utcnow()-timedelta(days=90), oldest_first=False):
            if message.author.id == ctx.bot.user.id and message.embeds:
                embed = message.embeds[0]
                if embed.footer and embed.footer.text.startswith("Advertised by"):
                    if embed.fields[0].value == self.platform:
                        ads.append(message)
            elif (platforms := re.findall(f"(?:\W|^)(?:(PC)|(Xbox)|(Switch)|(PS[4-5]?(?: |-)?NA)|(PS[4-5]?(?: |-)?EU))(?:\W|$)", message.content, re.IGNORECASE)):
                platform = None
                if platforms[0][0]:
                    platform = "PC"
                elif platforms[0][1]:
                    platform = "Xbox"
                elif platforms[0][2]:
                    platform = "Switch"
                elif platforms[0][3]:
                    platform = "PS4-NA"
                elif platforms[0][4]:
                    platform = "PS4-EU"
                if platform  != self.platform:
                    continue
                if (matched_invites := re.findall("(?:discord|dsc)\.gg\/([\w-]+)", message.content)) and len(message.content) > 50:
                    invite = matched_invites[0]
                    if invite in invites:
                        continue
                    invites.append(invite)
                    # try:
                    #     invite = await ctx.bot.fetch_invite(invite)
                    #     if invite.guild.id in servers:
                    #         continue
                    #     servers.append(invite.guild.id)
                    # except:
                    #     invite = None
                    ads.append(message)
        view = Pager(ctx, start_end=True)
        for i, ad in enumerate(ads, 1):
            if ad.author.id == ctx.bot.user.id:
                e = Page.from_dict(ad.embeds[0].to_dict())
                e.title = f"Club {i}/{len(ads)}"
                view.add_page(e)
            else:
                invites = re.findall("(?:discord|dsc)\.gg/([\w-]+)", ad.content)
                e = view.make_page(description=ad.content)
                e.timestamp = ad.created_at
                e.title = f"Club {i}/{len(ads)}"
                e.set_footer(text=f"Advertised by {ad.author} ({ad.author.id})")
                #e.add_field(name="Platform", value=self.platform)
                # if invite:
                #     e.set_thumbnail(url=invite.guild.icon)
                #     e.add_field(name="Discord", value=invite.url)
                #     e.add_field(name="Discord Members", value=invite.approximate_member_count)
        if not view.count:
            return await ctx.send("No club advertisements found.")
        view.message = await ctx.send(content=view.selected_page.content, embed=view.selected_page, view=view.start())

def setup(bot):
    bot.application_command(ClubCommand)
