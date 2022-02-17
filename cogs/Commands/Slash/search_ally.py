# Priority: 1
import re

import discord
from discord import app
from utils.buttons import Pager
from utils.objects import SlashCommand


class SearchAllyCommand(SlashCommand, name="search_ally", description="Search for an ally name or stats/abilities"):
    stat = app.Option(default=None, description="Search for an ally through stat", autocomplete=True)
    ability = app.Option(default=None, description="Search for an ally through ability", autocomplete=True)
    name = app.Option(default=None, description="Search for an ally through name", autocomplete=True)
    async def callback(self):
        ctx = await self.get_context()
        allies = list(filter(self.filter_allies, ctx.bot.Trove.values.allies))
        if self.name:
            allies.sort(key=lambda x: x.name)
        elif self.stat:
            def sorter(item: tuple, negative=False):
                for stat, raw_value in item.stats.items():
                    value = raw_value
                    if stat.lower() != self.stat.lower():
                        continue
                    if isinstance(value, str):
                        value = value.replace("%", "")
                    if stat.lower() in ["incoming damage"]:
                        value = -(float(value))
                    else:
                        value = float(value)
                    if isinstance(raw_value, str) and "%" in raw_value:
                        value = value * 1000
                    return (value, len(item.abilities))
            allies.sort(key=lambda x: sorter(x), reverse=True)
        view = Pager(ctx, start_end=True)
        paged_results = ctx.bot.utils.chunks(allies, 6)
        for raw_page in paged_results:
            e = view.make_page()
            e.set_author(name=f"Page {paged_results.index(raw_page)+1} of {len(paged_results)}")
            e.description = ""
            e.color = discord.Color.random()
            for ally in raw_page:
                e.description += f"[**{ally.name}**]({ally.url})" + ("\nStats: " + " | ".join([f"**{stat}={value}**" for stat, value in ally.stats.items()]) if ally.stats else "") + ("\nAbilities: " + "\n".join(ally.abilities) if ally.abilities else "") + "\n\n"
        if not view.count:
            return await ctx.send(f"No allies found. Use `{ctx.prefix}feedback <my feedback>` to send a missing or wrong ally.")
        view.message = await view.selected_page.send(ctx.send, view=view.start())

    def filter_allies(self, item):
        return (
            self.name.lower() == item.name.lower() if self.name else True and
            self.stat.lower() in [s.lower() for s in item.stats] if self.stat else True and
            self.ability.lower() in [a.lower() for a in item.abilities] if self.ability else True
        )
        
    async def autocomplete(self, options, focused):
        response = app.AutoCompleteResponse()
        value = options[focused]
        value = value.lower()
        self.allies = self.client.Trove.values.allies
        for autofill in await getattr(self, f"autocomplete_{focused}")(value):
            response.add_option(autofill, autofill)
        return response[:25]

    async def autocomplete_stat(self, value):
        stats = {}
        for ally in self.allies:
            for stat in ally.stats:
                if stat not in stats:
                    stats[stat] = 0
                stats[stat] += 1
        if value is None:
            return stats
        return [s for s, _ in sorted(list(stats.items()), key=lambda x: -x[1]) if re.findall(f"(?:\W|^)({re.escape(value)})", s.lower())]

    async def autocomplete_ability(self, value):
        abilities = {}
        for ally in self.allies:
            for ability in ally.abilities:
                if ability not in abilities:
                    abilities[ability] = 0
                abilities[ability] += 1
        if value is None:
            return abilities
        return [a for a, _ in sorted(list(abilities.items()), key=lambda x: -x[1]) if re.findall(f"(?:\W|^)({re.escape(value)})", a.lower())]

    async def autocomplete_name(self, value):
        names = []
        for ally in self.allies:
            if ally.name not in names:
                names.append(ally.name)
        if value is None:
            return names
        names.sort()
        return [n for n in names if re.findall(f"(?:\W|^)({re.escape(value)})", n.lower()) and not n.startswith("@")]

def setup(bot):
    bot.application_command(SearchAllyCommand)
