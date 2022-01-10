# Priority: 1
import discord
from discord.ext import commands

from utils.buttons import HelpView
from utils.CustomObjects import CEmbed
from utils.HelpAPI import HelpAPI


class Help(commands.Cog):
    """Help module"""
    def __init__(self, bot):
        self.bot = bot
        self.bot.help = HelpAPI(self.bot.db.database)

    async def get_command(self, commandname, subcommands=None):
        for command in await self.bot.help.get_all_commands():
            if commandname == command.name or commandname in command.aliases:
                if not subcommands:
                    return command
                for subcommand in subcommands:
                    if command.subcommands:
                        for sub in command.subcommands:
                            if sub.name == subcommand or subcommand in sub.aliases:
                                command = sub
                                continue
                    else:
                        return None
                return command
        return None

    @commands.command(slash_command=True, help="Help for all of the released commands on bot.")
    @commands.bot_has_permissions(embed_links=1, add_reactions=1)
    async def help(self, ctx, 
            commandname=commands.Option(default=None, description="Input command to get help on"),
            *, subcommand=commands.Option(default=None, description="Input subcommands to get help on.")):
        if subcommand and not commandname:
            return await ctx.send("You must input a command in order to check for subcommands.", ephemeral=True)
        # if ctx.guild.id in [118027756075220992] and commandname:
        #     commandname = None if commandname.lower() not in ["build", "gear", "search", "findmod", "augment", "coeff", "invite", "communities"] else commandname.lower()
        msg = ""
        page = 1
        prefix = ctx.prefix
        if commandname and not subcommand:
            command = await self.get_command(commandname)
            if command:
                embed=CEmbed(title=command.full_name.capitalize(), colour=discord.Color.random())
                #embed.description += "\n\nNeed help? Want to discuss something about the bot? [`Join support server`](https://trove.slynx.xyz/support)"
                embed.add_field(name="Description", value=command.description, inline=False)
                if commandname in self.bot.all_commands:
                    if self.bot.all_commands[commandname].usage:
                        embed.add_field(name="Usage", value=self.bot.all_commands[commandname].usage, inline=False)
                    embed.add_field(name="Example", value=f'`{command.example.replace("{prefix}", prefix)}`')
                    if command.extra_text:
                        embed.add_field(name="More info", value=command.extra_text, inline=False)  
                    if command.aliases:
                        embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)
                    if command.subcommands:
                        embed.add_field(name="Subcommands", value="`"+"`\n`".join([str(sub) for sub in command.subcommands])+"`", inline=False)
                    return await ctx.send(embed=embed)
            await ctx.send("Invalid command!")
        elif commandname and subcommand:
            subcommands = subcommand.split(" ")
            command = await self.get_command(commandname, subcommands)
            if command:
                embed=CEmbed(title=command.full_name.capitalize(), colour=discord.Color.random())
                #embed.description += "\n\nNeed help? Want to discuss something about the bot? [`Join support server`](https://trove.slynx.xyz/support)"
                embed.add_field(name="Description", value=command.description, inline=False)
                embed.add_field(name="Example", value=f'`{command.example.replace("{prefix}", prefix)}`')
                if command.extra_text:
                    embed.add_field(name="More info", value=command.extra_text, inline=False)  
                if command.aliases:
                    embed.add_field(name="Aliases", value=", ".join(command.aliases), inline=False)

                if command.subcommands:
                    embed.add_field(name="Subcommands", value="`"+"`\n`".join([str(sub) for sub in command.subcommands])+"`", inline=False)
                return await ctx.send(embed=embed)
            await ctx.send("Command not found!")
        elif not commandname and not subcommand:
            commands_list = {}
            x = 0
            for command in await self.bot.help.get_all_commands():
                # if ctx.guild.id in [118027756075220992] and command.name not in ["search", "build", "gear", "findmod", "augment", "coeff", "invite", "communities"]:
                #     continue
                if command.module not in commands_list.keys():
                    commands_list[command.module] = []
                commands_list[command.module].append(command)
                x += 1
            for module in commands_list.keys():
                commands_list[module] = self.bot.utils.chunks(commands_list[module], 10)
                i = 1
                new_pages = []
                for page in commands_list[module]:
                    msg = ""# if ctx.guild.id != 118027756075220992 else "**Trovesaurus has a limited feature set.** To access other features, add the bot to your own server.\n\n"
                    for command in page:
                        msg += f'`{command.name}` - {command.description}\n\n'
                    embed=CEmbed(title=f"Page: {i}/{len(commands_list[module])}",description=msg, colour=discord.Color.random())
                    embed.set_author(name=f"{module.capitalize()} Commands", icon_url=self.bot.user.avatar)
                    embed.description += f"**Want to add the bot to your own server feel free to do so [here]({self.bot.invite})**\nNeed help? Want to discuss something about the bot? [`Join support server`](https://trove.slynx.xyz/support) you can also get help through bot DM's"
                    embed.set_footer(text=f"{prefix}help <command>/<subcommand> for more info on the command.")
                    page = {
                        "content": None,
                        "embed": embed
                    }
                    new_pages.append(page)
                    i += 1
                commands_list[module] = new_pages
            module_descriptions = {
                "automation": "List of commands to manage bot's automation capabilites.",
                "builds": "List of commands to get gem and gear builds.",
                "calculations": "List of commands to calculate stuff easily.",
                "club": "List of commands to manage club.",
                "general": "List of general trove commands.",
                "information": "List of trove informational commands.",
                "miscellaneous": "List of miscellaneous commands.",
                "profiles": "List of commands for profiles system.",
                "settings": "List of commands to change bot's behavior."
            }
            e = CEmbed()
            e.color = discord.Color.random()
            e.set_author(name=f"Help | {x} Total Commands", icon_url=self.bot.user.avatar)
            e.description = "" if ctx.guild.id not in [118027756075220992] else "**Trovesaurus has a limited feature set.** To access other features, add the bot to your own server.\n\n"
            e.description += f"Bot is now on version **{self.bot.version}** check changes with `{ctx.prefix}change_log`\n"
            e.description += "\n**Modules:**\n\n"
            e.description += "\n".join(sorted([f"`{m.capitalize()}`\n{module_descriptions[m]}\n" for m in commands_list.keys()]))
            e.description += f"\n**Want to add the bot to your own server feel free to do so [here]({self.bot.invite})**\nNeed help? Want to discuss something about the bot? [`Join support server`](https://trove.slynx.xyz/support) you can also get help through bot DM's"
            e.set_footer(text=f"{prefix}help <command>/<subcommand> for more info on the command.")
            commands_list["embed"] = e
            view = HelpView(ctx, commands_list)
            view.message = await ctx.reply(embed=commands_list["embed"], view=view)

def setup(bot):
    n = Help(bot)
    bot.add_cog(n)
