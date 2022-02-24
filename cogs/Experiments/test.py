# Priority: 1
import discord
from discord import AuditLogAction
from discord.ext import commands


class ModEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def can_view_audit_logs(self, member):
        return member.guild_permissions.view_audit_log

    @commands.Cog.listener("on_member_ban")
    async def _member_ban(self, guild: discord.Guild, member):
        if not self.can_view_audit_logs(guild.me):
            return
        async for log in guild.audit_logs(limit=100, action=AuditLogAction.ban):
            if log.target.id == member.id:
                self.bot.dispatch("mod_member_ban", guild, member, log.user, log)
                break

    @commands.Cog.listener("on_member_unban")
    async def _member_unban(self, guild, member):
        if not self.can_view_audit_logs(guild.me):
            return
        async for log in guild.audit_logs(limit=100, action=AuditLogAction.unban):
            if log.target.id == member.id:
                self.bot.dispatch("mod_member_unban", guild, member, log.user, log)
                break

    @commands.Cog.listener("on_mod_member_ban")
    async def _mod_member_ban(self, guild, member, mod, log):
        ...

    @commands.Cog.listener("on_mod_member_unban")
    async def _mod_member_unban(self, guild, member, mod, log):
        ...

def setup(bot):
    bot.add_cog(ModEvents(bot))
