# Priority: 1
import discord
from discord.ext import commands, tasks
from datetime import datetime
import re

import utils.checks as perms


class Automation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.auto_nickname.start()
        self.auto_club_member_role.start()

    def cog_unload(self):
        self.auto_nickname.stop()
        self.auto_club_member_role.stop()

    @tasks.loop(seconds=60)
    async def auto_nickname(self):
        data = await self.bot.db.db_servers.find({"automation.nickname.toggle": True}, {"PTS mode": 1, "automation": 1}).to_list(length=999999)
        if not data:
            return
        profiles = await self.bot.db.db_profiles.find({"Bot Settings.Server": 1}, {"Name": 1, "discord_id": 1}).to_list(length=999999)
        profiles_ids = await self.bot.db.db_profiles.find({"Bot Settings.Server": 1}).distinct("discord_id")
        pts_profiles = await self.bot.db.db_profiles.find({"Bot Settings.Server": 0}, {"Name": 1, "discord_id": 1}).to_list(length=999999)
        pts_profiles_ids = await self.bot.db.db_profiles.find({"Bot Settings.Server": 0}).distinct("discord_id")
        for server in data:
            settings = server["automation"]["nickname"]
            guild = self.bot.get_guild(server["_id"])
            if not guild:
                continue
            if server["PTS mode"]:
                profs_ids = pts_profiles_ids
                profs = pts_profiles
            else:
                profs_ids = profiles_ids
                profs = profiles
            members = [m for m in guild.members if m.id in profs_ids]
            for member in members:
                for profile in profs:
                    if member.id != profile["discord_id"]:
                        continue
                    if member.guild.owner == member:
                        continue
                    if not re.match(f"^{profile['Name']}(?:$| .*)", member.display_name):
                        new_name = profile["Name"]
                        if member.nick:
                            get_extras = re.findall(f"[a-z0-9_]($| .*)", member.nick)
                            if get_extras:
                                new_name = profile["Name"] + get_extras[0]
                        try:
                            await member.edit(nick=new_name)
                        except:
                            pass

    @tasks.loop(seconds=60)
    async def auto_club_member_role(self):
        servers = self.bot.db.db_servers.find({"automation.club.name": {"$ne": None}, "automation.club.member_role": {"$ne": None}}, {"automation": 1, "PTS mode": 1})
        async for server in servers:
            guild = self.bot.get_guild(server["_id"])
            if not guild:
                continue
            role = guild.get_role(server["automation"]["club"]["member_role"])
            if role:
                profiles = await self.bot.db.db_profiles.find({"Bot Settings.Server": int(not server["PTS mode"])}).distinct("discord_id")
                club = await self.bot.db.db_profiles.find({"Bot Settings.Server": int(not server["PTS mode"]), "Clubs": {"$all": [server["automation"]["club"]["name"]]}}).distinct("discord_id")
                for member in guild.members:
                    if member.id in club:
                        await self.bot.utils.give_roles(member, role)
                    else:
                        if server["automation"]["club"]["member_role_only_profile"] and member.id in profiles:
                            await self.bot.utils.take_roles(member, role)

    @commands.group(slash_command=True, help="Command group for bot automation related commands", aliases=["auto"])
    @perms.has_permissions("manage_guild")
    async def automation(self, _):
        ...

    @automation.command(slash_command=True, help="Display current settings of automation command")
    @commands.bot_has_permissions(embed_links=1)
    async def settings(self, ctx):
        data = {
            "automation": 1,
            "clock": 1,
            "PTS mode": 1
        }
        data = await ctx.get_guild_data(**data)
        auto = data["automation"]
        e = discord.Embed()
        e.set_author(name=await ctx.locale("auto_settings_embed_author_name"), icon_url=self.bot.user.avatar)
        e.add_field(name="\u200b", value=await ctx.locale("auto_settings_embed_dailies_field_title"),inline=False)
        channel = self.bot.get_channel(auto["daily"]["text"]["channel"])
        voice = self.bot.get_channel(auto["daily"]["voice"]["channel"])
        role = self.bot.get_channel(auto["daily"]["text"]["role"])
        e.add_field(name=await ctx.locale("auto_settings_embed_dailies_field_text_title"), value=channel.mention if channel else await ctx.locale("auto_settings_embed_dailies_field_text_disabled"))
        e.add_field(name=await ctx.locale("auto_settings_embed_dailies_field_role_title"), value=role.mention if role else await ctx.locale("auto_settings_embed_dailies_field_role_disabled"))
        e.add_field(name=await ctx.locale("auto_settings_embed_dailies_field_voice_title"), value=voice.mention if voice else await ctx.locale("auto_settings_embed_dailies_field_voice_disabled"))
        e.add_field(name="\u200b", value=await ctx.locale("auto_settings_embed_weeklies_field_title") ,inline=False)
        channel = self.bot.get_channel(auto["weekly"]["text"]["channel"])
        voice = self.bot.get_channel(auto["weekly"]["voice"]["channel"])
        role = self.bot.get_channel(auto["weekly"]["text"]["role"])
        e.add_field(name=await ctx.locale("auto_settings_embed_weeklies_field_text_title"), value=channel.mention if channel else await ctx.locale("auto_settings_embed_weeklies_field_text_disabled"))
        e.add_field(name=await ctx.locale("auto_settings_embed_weeklies_field_role_title"), value=role.mention if role else await ctx.locale("auto_settings_embed_weeklies_field_role_disabled"))
        e.add_field(name=await ctx.locale("auto_settings_embed_weeklies_field_voice_title"), value=voice.mention if voice else await ctx.locale("auto_settings_embed_weeklies_field_voice_disabled"))
        e.add_field(name="\u200b", value=await ctx.locale("auto_settings_embed_clock_field_title"),inline=False)
        channel = self.bot.get_channel(data["clock"]["channel"])
        e.add_field(name=await ctx.locale("auto_settings_embed_clock_field_channel_title"), value=channel.mention if channel else await ctx.locale("auto_settings_embed_clock_field_channel_disabled"))
        e.add_field(name=await ctx.locale("auto_settings_embed_clock_field_format_title"), value=data["clock"]["format"] or "`⌛{hour24}:{minute}`")
        e.add_field(name="\u200b", value="\u200b")
        e.add_field(name="👤 Profile Auto Nickname", value=data["PTS mode"], inline=False)
        await ctx.reply(embed=e)

  # Resets

    @automation.group(slash_command=True, help="Automation subcommand group for reset messages")
    async def resets(self, _):
        ...

    @resets.command(slash_command=True, help="Reset subcommand for daily resets in text channels", aliases=["dt"])
    async def daily_text(self, ctx, channel: discord.TextChannel=commands.Option(name="text_channel", default=None, description="Select a text channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.daily.text.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_resets_daily_text_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_resets_daily_text_off"))

    @resets.command(slash_command=True, help="Reset subcommand for daily resets in voice channels", aliases=["dv"])
    async def daily_voice(self, ctx, channel: discord.VoiceChannel=commands.Option(name="voice_channel", default=None, description="Select a voice channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.daily.voice.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_resets_daily_voice_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_resets_daily_voice_off"))

    @resets.command(slash_command=True, help="Reset subcommand for weekly resets in text channels", aliases=["wt"])
    async def weekly_text(self, ctx, channel: discord.TextChannel=commands.Option(name="text_channel", default=None, description="Select a text channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.weekly.text.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_resets_weekly_text_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_resets_weekly_text_off"))

    @resets.command(slash_command=True, help="Reset subcommand for weekly resets in voice channels", aliases=["wv"])
    async def weekly_voice(self, ctx, channel: discord.VoiceChannel=commands.Option(name="voice_channel", default=None, description="Select a voice channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.weekly.voice.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_resets_weekly_voice_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_resets_weekly_voice_off"))

    @resets.command(slash_command=True, help="Reset subcommand for mentioning a role when posting daily resets", aliases=["dm"])
    async def daily_mention(self, ctx, role: discord.Role=commands.Option(name="role", default=None, description="Select a role")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.daily.text.role": role.id if role else role}})
        if role:
            return await ctx.reply((await ctx.locale("auto_resets_daily_mention_on")).format(role.mention), allowed_mentions=discord.AllowedMentions.none())
        else:
            return await ctx.reply(await ctx.locale("auto_resets_daily_mention_off"))

    @resets.command(slash_command=True, help="Reset subcommand for mentioning a role when posting weekly resets", aliases=["wm"])
    async def weekly_mention(self, ctx, role: discord.Role=commands.Option(name="role", default=None, description="Select a role")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.weekly.text.role": role.id if role else role}})
        if role:
            return await ctx.reply((await ctx.locale("auto_resets_weekly_mention_on")).format(role.mention), allowed_mentions=discord.AllowedMentions.none())
        else:
            return await ctx.reply(await ctx.locale("auto_resets_weekly_mention_off"))

    @automation.group(slash_command=True, aliases=["dragon", "dm"], help="Automation subcommand group for dragon merchant messages")
    async def dragon_merchant(self, _):
        ...

    @dragon_merchant.command(slash_command=True, name="voice", help="Dragon Merchant subcommand for voice channel")
    async def _voice(self, ctx, channel: discord.VoiceChannel=commands.Option(default=None, description="Select a voice channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.dragon_merchant.voice.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_dragon_merchant_voice_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_dragon_merchant_voice_off"))

    @dragon_merchant.command(slash_command=True, name="text", help="Dragon Merchant subcommand for text channel")
    async def _text(self, ctx, channel: discord.TextChannel=commands.Option(default=None, description="Select a text channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.dragon_merchant.text.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply("Dragon Merchant posts are now enabled and will be sent to {}".format(channel.mention))
        else:
            return await ctx.reply("Dragon Merchant posts are now disabled.")

    @dragon_merchant.command(slash_command=True, name="mention", help="Dragon Merchant subcommand for mentioning a role when posting dragon merchant messages")
    async def dragon_mention(self, ctx, role: discord.Role=commands.Option(name="role", default=None, description="Select a role")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.dragon_merchant.text.role": role.id if role else role}})
        if role:
            return await ctx.reply("Dragon Merchants posts will now mention {}".format(role.mention), allowed_mentions=discord.AllowedMentions.none())
        else:
            return await ctx.reply("Dragon Merchants posts will not mention anymore.")

  # Clock

    @automation.group(slash_command=True, help="Automation subcommand group for clock channel")
    async def clock(self, _):
        ...

    @clock.command(slash_command=True, help="Select a voice channel for clock")
    async def channel(self, ctx, channel: discord.VoiceChannel=commands.Option(name="voice_channel", default=None, description="Select a voice channel")):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"clock.channel": channel.id if channel else channel}})
        if channel:
            return await ctx.reply((await ctx.locale("auto_clock_channel_on")).format(channel.mention))
        else:
            return await ctx.reply(await ctx.locale("auto_clock_channel_off"))

    @clock.command(slash_command=True, name="format", help="Select a format for clock")
    async def _format(self, ctx, *, _format=commands.Option(name="format", default=None, description="Provide a clock format")):
        if _format and  len(_format) > 100:
            return await ctx.reply(await ctx.locale("auto_clock_format_max_characters"))
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"clock.format": _format}})
        await ctx.reply(await ctx.locale("auto_clock_format_success").format(_format if _format else 'default'))

    @automation.group(slash_command=True, help="Automation subcommand group for club related commands")
    async def club(self, ctx):
        ...

    @club.command(slash_command=True, help="Set a club name to look for in profiles")
    async def name(self, ctx, name=None):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.club.name": name}})
        if name:
            return await ctx.reply("Club name set to `{}`".format(name))
        else:
            return await ctx.reply("Club name reset.")

    @club.command(slash_command=True, help="Set a role to give to users whose profile has the club name in their clubs")
    async def member_role(self, ctx, role: discord.Role=None):
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.club.member_role": role.id}})
        if role:
            return await ctx.reply("Club member role set to {}".format(role.mention), allowed_mentions=discord.AllowedMentions.none())
        else:
            return await ctx.reply("Club member role reset.")

    @club.command(slash_command=True, help="Manage role only in people with a profile (avoids taking from current users)")
    async def member_role_profile_only(self, ctx):
        data = await self.bot.db.db_servers.find_one({"_id": ctx.guild.id}, {"automation": 1})
        value = not data["automation"]["club"]["member_role_only_profile"]
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.club.member_role_only_profile": value}})
        if value:
            return await ctx.reply("Club member role will be taken from people without profile and not in club. **[Enabled]**")
        else:
            return await ctx.reply("Club member role will only be given and not taken from people with profile. **[Disabled]**")

    @automation.command(slash_command=True, help="Manage whether to change people's nicknames based on profiles", aliases=["nick"])
    async def nickname(self, ctx):
        data = await ctx.get_guild_data(automation=1)
        value = not data["automation"]["nickname"]["toggle"]
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"automation.nickname.toggle": value}})
        await ctx.reply(f"Nickname automation set to **{value}**")
    
    @commands.group(slash_command=True, help="Automation subcommand group for automated trove related posts")
    async def posts(self, ctx):
        ...

    @posts.command(slash_command=True, help="Select a channel for PTS Patch Notes to be posted in", aliases=["ppn"])
    async def pts_patch_notes(self, ctx, channel: discord.TextChannel):
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links and perms.view_channel):
            return await ctx.send(f"I require `View Channel` and `Send Messages` and `Embed Links` permissions in {channel.mention} to enable this feature in that channel.")
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"forums_posts.pts.channel": channel.id}})
        await ctx.reply(f"PTS Patch Notes will now be posted in {channel.mention} very shortly.")

    @posts.command(slash_command=True, help="Select a channel for PTS User Posts to be posted in", aliases=["pup"])
    async def pts_user_posts(self, ctx, channel: discord.TextChannel):
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links and perms.view_channel):
            return await ctx.send(f"I require `View Channel` and `Send Messages` and `Embed Links` permissions in {channel.mention} to enable this feature in that channel.")
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"forums_posts.ptsposts.channel": channel.id}})
        await ctx.reply(f"PTS Posts will now be posted in {channel.mention} very shortly.")

    # @posts.command(slash_commmand=True, aliases=["dtp"])
    # async def dev_tracker_posts(self, ctx, channel: discord.TextChannel):
    #     perms = channel.permissions_for(ctx.guild.me)
    #     if not (perms.send_messages and perms.embed_links and perms.view_channel):
    #         return await ctx.send(f"I require `View Channel` and `Send Messages` and `Embed Links` permissions in {channel.mention} to enable this feature in that channel.")
    #     await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"forums_posts.devtracker.channel": channel.id}})
    #     await ctx.reply(f"Dev Tracker posts will now be posted in {channel.mention} very shortly.")
    
    @posts.command(slash_command=True, help="Select a channel for PC Live Patch Notes to be posted in", aliases=["lpn"])
    async def live_patch_notes(self, ctx, channel: discord.TextChannel):
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links and perms.view_channel):
            return await ctx.send(f"I require `View Channel` and `Send Messages` and `Embed Links` permissions in {channel.mention} to enable this feature in that channel.")
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"forums_posts.livepatches.channel": channel.id}})
        await ctx.reply(f"Live Patch Notes will now be posted in {channel.mention} very shortly.")

    @posts.command(slash_command=True, help="Select a channel for Console Patch Notes to be posted in", aliases=["cpn"])
    async def console_patch_notes(self, ctx, channel: discord.TextChannel):
        perms = channel.permissions_for(ctx.guild.me)
        if not (perms.send_messages and perms.embed_links and perms.view_channel):
            return await ctx.send(f"I require `View Channel` and `Send Messages` and `Embed Links` permissions in {channel.mention} to enable this feature in that channel.")
        await self.bot.db.db_servers.update_one({"_id": ctx.guild.id}, {"$set": {"forums_posts.consolepatches.channel": channel.id}})
        await ctx.reply(f"Console Patch Notes will now be posted in {channel.mention} very shortly.")
    
    @posts.command(slash_command=True, help="Select a post to be reposted with it's ID")
    async def repost(self, ctx, post_id: int, channel: discord.TextChannel=commands.Option(name="text_channel", default=None, description="Select a channel to send to")):
        forum_post = await self.bot.db.db_forums.find_one({"_id": post_id})
        channel = channel or ctx.channel
        e = discord.Embed()
        e.color = discord.Color.random()
        e.set_author(name=forum_post["author"])
        e.timestamp = datetime.utcfromtimestamp(forum_post["created_at"])
        e.title = forum_post["title"]
        e.url = forum_post["link"]
        e.set_footer(text=forum_post["_id"])
        add = f"[Dark Mode Page](https://slynx.xyz/trove/posts/{forum_post['_id']})"
        e.description = forum_post["content"].strip() + f"\n\n{add}"
        if len(e.description) > 2048:
            e.description = f"Post is too big to show in discord, check it out at {add}"
        await channel.send(embed=e)
        if ctx.channel != channel:
            await ctx.reply(f"Post sent to {channel.mention}")
        
def setup(bot):
    bot.add_cog(Automation(bot))
