import os
import re

class Module():
    def __init__(self, data):
        for k, v in data.items():
            setattr(self, k, v)

    def __str__(self):
        return self.name.capitalize()

    def __repr__(self):
        return self.name.capitalize()

    def __eq__(self, target):
        return isinstance(target, Module) and self.path == target.path

    def __ne__(self, target):
        return not self.__eq__(target)

def get_metadata(path):
    regex = r"^# ?priority ?[:=] ?([0-9]*)$"
    with open(path, "r") as _file:
        raw = _file.read()
        size = len(raw)
        lines = raw.splitlines()
        if lines and lines[0].startswith("#"):
            match = re.match(regex, lines[0], re.IGNORECASE)
            if match:
                return size, int(match.groups()[0])
    return size,  0

def get_modules(path, sort=True):
    modules = []
    for _file in os.listdir(path):
        if os.path.isfile(path+_file) and _file.endswith(".py"):
            module = {
                "name": ".".join(_file.split(".")[:-1]),
                "path": path+_file,
                "tree": "/".join(path.split("/")[1:]) or None
            }
            module["load"] = ".".join(module["path"].split("/")).replace(".py", "")
            size, priority = get_metadata(module["path"])
            module["size"] = size
            module["priority"] = priority
            modules.append(Module(module))
        elif os.path.isdir(path+_file):
            for i in get_modules(path+_file+"/", False):
                modules.append(i)
    if sort:
        modules.sort(key=lambda x: -x.priority)
    return modules

def get_loaded_modules(bot, modules):
    raw_loaded = [c.__module__.split(".")[-1] for c in bot.cogs.values()]
    loaded = [m for m in modules for c in raw_loaded if m.name == c]
    return loaded