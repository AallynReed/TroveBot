# Priority: 1
import discord
from discord.ext import commands

from utils.CustomObjects import CEmbed


class Colors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(slash_command=True, help="Pick a color role to use.")
    @commands.bot_has_permissions(manage_roles=True)
    async def color(self, ctx, role: int=commands.Option(description="Pick a role number")):
        index = role-1
        all_roles = sorted(ctx.guild.roles, key=lambda x: -x.position)
        color_roles = [r for r in all_roles if r.name.startswith("🎨")]
        author: discord.Member = ctx.author
        user_roles = [r for r in ctx.author.roles if r in color_roles]
        if color_roles[0].position >= ctx.guild.me.roles[-1].position:
            return await ctx.reply("I can't manage some roles.", ephemeral=True)
        if role == 0:
            if not user_roles:
                return await ctx.reply("You don't have any color role to remove.", ephemeral=True)
            try:
                await author.remove_roles(*user_roles)
            except:
                return await ctx.reply("Failed to remove color roles.", ephemeral=True)
            return await ctx.reply("All color roles were removed.")
        elif index not in list(range(len(color_roles))):
            return await ctx.send("There's no such role with that index.")
        else:
            try:
                selected_role = color_roles[index]
                await author.remove_roles(*user_roles)
                await author.add_roles(selected_role)
            except:
                return await ctx.reply("Failed to add color role.", ephemeral=True)
            await ctx.reply(f"{selected_role.mention} is now your color.", ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @commands.command(slash_command=True, help="List all color roles.")
    async def colors(self, ctx):
        all_roles = sorted(ctx.guild.roles, key=lambda x: -x.position)
        color_roles = [r for r in all_roles if r.name.startswith("🎨")]
        user_roles = [r for r in ctx.author.roles if r in color_roles]
        e = CEmbed(description="")
        e.set_author(name="Role Colors", icon_url=ctx.guild.icon)
        e.set_footer(text=f"{ctx.prefix}color <ColorNumber> | ⭐ is your current color.")
        if user_roles:
            e.color = user_roles[0].color
        else:
            e.color = 0x2f3136
        i = 1
        if color_roles:
            for role in color_roles:
                if role not in user_roles:
                    text = f"\n`{str(i)+'.':<3}`{role.mention}"
                else:
                    text = f"\n`{str(i)+'.':<3}`**{role.mention}** ⭐"
                e.description += text
                i += 1
        else:
            e.description += "No color roles found"
        await ctx.reply(embed=e, ephemeral=True)


def setup(bot):
    bot.add_cog(Colors(bot))
