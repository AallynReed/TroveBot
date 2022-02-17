# Priority: 1
import discord
from discord import AuditLogAction
from discord.ext import commands
from utils.buttons import Pager


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

    @commands.command(slash_command=True, message_command=True, help="Look for keywords in previous patch notes")
    async def pager(self, ctx,
        _filter=commands.Option(name="filter", default=None, description="Filter posts to find keywords in."),
        keywords=commands.Option(default="and", description="Filter posts by keywords, keywords separated with ;")
    ):
        keywords = keywords.split(";")
        kws = "` `".join(keywords)
        found_posts = []
        async for post in self.bot.db.db_forums.find({}):
            if _filter and _filter != post["type"]:
                continue
            if not (content := post.get("content")):
                continue
            posti = [kw for kw in keywords if kw.lower() not in content.lower()]
            if not posti:
                found_posts.append(post)
        if not found_posts:
            return await ctx.send(f"No posts matching keywords `{kws}` were found.", ephemeral=True)
        found_posts.sort(key=lambda x: -x["created_at"])
        raw_pages = self.bot.utils.chunks(found_posts, 4)
        view = Pager(ctx, start_end=True, step_10=True)
        for i, raw_page in enumerate(raw_pages, 1):
            e = view.make_page(content=f"Page {i}", description=f"Posts for `{kws}`")
            e.set_author(name=f"Forum Posts Search [{i}/{len(raw_pages)}]")
            for post in raw_page:
                e.add_field(name=f"[{post['_id']}] {post['title']}", value=f"[Check out here](https://trove.slynx.xyz/posts/{post['_id']}/)\nBy {post['author']}\nPosted on <t:{int(post['created_at'])}:D>\n[Forums Link]({post['link']})\n\u200b", inline=False)
        view.message = await view.selected_page.send(ctx.send, view=view.start())

def setup(bot):
    bot.add_cog(ModEvents(bot))
