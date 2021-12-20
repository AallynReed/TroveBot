import discord
from pymongo import MongoClient

client = MongoClient()
db = client["sly"]
file = db.help

async def get_subcommand_help(ctx, bot):
    command_name = str(ctx.command)
    subcommands = command_name.split(" ")
    if subcommands:
        command_db  = file.find_one({"_id": subcommands[0]})
    else:
        command_db  = file.find_one({"_id": command_name})

    prefix = ctx.prefix
    if len(subcommands) == 1:
        command_name = bot.all_commands[subcommands[0]]
        command_path = command_db
        description = command_path["description"]
        subcommands = list(command_path["subcommands"])
        example = command_path["example"].replace("{prefix}", prefix)
    elif len(subcommands) == 2:
        command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]]
        command_path = command_db["subcommands"][subcommands[1]]
        description = command_path["description"]
        example = command_path["example"].replace("{prefix}", prefix)
    elif len(subcommands) == 3:
        command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]]
        command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]
        description = command_path["description"]
        example = command_path["example"].replace("{prefix}", prefix)
    elif len(subcommands) == 4:
        command_name = bot.all_commands[subcommands[0]].all_commands[subcommands[1]].all_commands[subcommands[2]].all_commands[subcommands[3]]
        command_path = command_db["subcommands"][subcommands[1]]["subcommands"][subcommands[2]]["subcommands"][subcommands[3]]
        description = command_path["description"]
        example = command_path["example"].replace("{prefix}", prefix)
    e=discord.Embed(description=description, colour=bot.comment)
    e.set_author(name=f"{str(command_name).capitalize()} Commands", icon_url=ctx.guild.icon_url)
    if "subcommands" in command_path and command_path["subcommands"]:
        for subcommand in command_path["subcommands"]:
            description = command_path["subcommands"][subcommand]["description"]
            example = command_path["subcommands"][subcommand]["example"].replace("{prefix}", prefix)
            if str(command_name) == "profile" and str(subcommand) == "help":
                continue
            e.add_field(name=f'• {prefix}{command_name} {subcommand}', value=f'{description}\n**Example:** ``{example}``', inline=False)
    return e
