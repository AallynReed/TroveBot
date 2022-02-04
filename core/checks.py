from discord.ext import commands


def has_permissions(*perms):
    def predicate(ctx):
        setattr(ctx.command, "permissions",", ".join(perms))
        if ctx.author.id in ctx.bot.owners:
            return True
        else:
            return all(getattr(ctx.author.guild_permissions, perm, None) for perm in perms)
    return commands.check(predicate)

def admins():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.admin_ids:
            return True
        return False
    return commands.check(predicate)

def owners():
    def predicate(ctx):
        if ctx.author.id in ctx.bot.owners:
            return True
        return False
    return commands.check(predicate)

class CloneCheckError(Exception):
    ...

def is_clone(f):
    def check(*args):
        if not args:
            raise CloneCheckError("No Arguments Given")
        if not isinstance(args[0], commands.Cog):
            raise CloneCheckError("Argument is not a cog")
        return f(*args)
    return check
