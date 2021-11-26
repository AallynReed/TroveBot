class Command():
    def __init__(self, **data):
        self.extra_text = None
        for dat in data:
            setattr(self, dat, data[dat])
        self.hidden = data["hidden"] if "hidden" in data else False
        self.subcommands = []

    def __str__(self):
        return self.name

    def add_subcommand(self, command):
        self.subcommands.append(command)
    
class Subcommand(Command):
    def __init__(self, **data):
        super().__init__(**data)

class HelpAPI():
    def __init__(self, db):
        self.db = db.help

    async def _get_commands(self):
        return await self.db.find({}).to_list(length=999)

    async def _organize_commands(self, data):
        commands = []
        i = 0
        for command in data:
            cmd = Command(base=command['_id'], name=command['_id'], full_name=command['_id'], **command)
            if "subcommands" in data[i] and data[i]["subcommands"]:
                for subcommand in data[i]["subcommands"]:
                    subcmd = Subcommand(base=command['_id'], name=subcommand, full_name=f"{command['_id']} {subcommand}\n", **data[i]["subcommands"][subcommand])
                    if "subcommands" in data[i]["subcommands"][subcommand] and data[i]["subcommands"][subcommand]["subcommands"]:
                        for subsubcommand in data[i]["subcommands"][subcommand]["subcommands"]:
                            subsubcmd = Subcommand(base=command['_id'], name=subsubcommand, full_name=f"{command['_id']} {subcommand} {subsubcommand}\n", **data[i]["subcommands"][subcommand]["subcommands"][subsubcommand])
                            if "subcommands" in data[i]["subcommands"][subcommand]["subcommands"][subsubcommand] and data[i]["subcommands"][subcommand]["subcommands"][subsubcommand]["subcommands"]:
                                for subsubsubcommand in data[i]["subcommands"][subcommand]["subcommands"][subsubcommand]["subcommands"]:
                                    subsubsubcmd = Subcommand(base=command['_id'], name=subsubsubcommand, full_name=f"{command['_id']} {subcommand} {subsubcommand} {subsubsubcommand}\n", **data[i]["subcommands"][subcommand]["subcommands"][subsubcommand]["subcommands"][subsubsubcommand])
                                    subsubcmd.add_subcommand(subsubsubcmd)
                            subcmd.add_subcommand(subsubcmd)
                    cmd.add_subcommand(subcmd)
            commands.append(cmd)
            i += 1
        return commands

    async def get_command(self, commandname, subcommands=None):
        for command in await self.get_all_commands():
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

    async def get_all_commands(self):
        data = await self._get_commands()
        return await self._organize_commands(data)

    async def get_all_cmd_subcmd(self):
        commands = await self.get_all_commands()
        all_cmd_subcmd = []
        for command in commands:
            all_cmd_subcmd.append(command)
            for subcommand in command.subcommands:
                all_cmd_subcmd.append(subcommand)
                for sub in subcommand.subcommands:
                    all_cmd_subcmd.append(sub)
        return all_cmd_subcmd

    async def get_all_cmd_subcmd_web(self):
        commands = await self.get_all_cmd_subcmd()
        for command in commands:
            command.example = command.example.replace("{prefix}", "n!")
            command.example = command.example.split("\n")
        return commands
        
