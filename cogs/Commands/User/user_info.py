# Priority: 1
import discord
from discord.app import UserCommand
from utils.CustomObjects import CEmbed


class UserInfo(UserCommand, name="User Info"):
    async def callback(self):
        user = await self.target.upgrade(banner=True, presences=True)
        badges = {
            "bug_hunter": "<:bug_hunter:864159464630124575>",
            "bug_hunter_level_2": "<:bug_hunter_level_2:864159465112993822>",
            #"discord_certified_moderator": "<:certified_moderator:864159465448407050>",
            "early_supporter": "<:early_supporter:864159465556148224>",
            "early_verified_bot_developer": "<:verified_developer:864159466592796732>",
            "hypesquad": "<:hypesquad:864159465724837919>",
            "hypesquad_balance": "<:hypesquad_balance:864159466072047631>",
            "hypesquad_bravery": "<:hypesquad_bravery:864159466299719760>",
            "hypesquad_brilliance": "<:hypesquad_brilliance:864159466433019964>",
            "partner": "<:partner:864159466513236028>",
            "staff": "<:staff:864166002484969502>",
            "verified_bot_developer": "<:verified_developer:864159466592796732>"
        }
        e = CEmbed()
        e.color = user.accent_color or user.color
        e.set_author(name=str(user) + (" 🤖" if user.bot else ""), icon_url=user.avatar)
        e.set_footer(text=f"UUID: {user.id}")
        e.add_field(name="Created at", value=f"{self.client.utils.format_dt(user.created_at, 'f')}\n{self.client.utils.format_dt(user.created_at, 'R')}")
        flags = list(set([e for b, e in badges.items() if getattr(user.public_flags, b)]))
        if flags:
            e.add_field(name="Badges", value=''.join(flags))
        if len(e.fields)%3:
            for _ in range(3-len(e.fields)%3):
                e.add_field(name="\u200b", value="\u200b")
        if isinstance(user, discord.Member):
            if not user.bot:
                for activity in user.activities:
                    if isinstance(activity, discord.Spotify):
                        e.add_field(name="Spotify", value=f"[**{activity.title}**](https://open.spotify.com/track/{activity.track_id})\nby __{''.join(activity.artists)}__\non {activity.album}")
                        e.set_thumbnail(url=activity.album_cover_url)
                    if activity.type is discord.ActivityType.playing or isinstance(activity, discord.Game):
                        e.add_field(name="Game", value=f"Started playing **{activity.name}**\n{self.client.utils.format_dt(activity.start, 'R') if activity.start else ''}")
                        if "large_image_url" in dir(activity) and activity.large_image_url:
                            e.set_thumbnail(url=activity.large_image_url)
                    if activity.type is discord.ActivityType.streaming or isinstance(activity, discord.Streaming):
                        e.add_field(name="Stream", value=f"Started streaming {activity.game}\non {activity.platform} at [**{activity.twitch_name}**]({activity.url})")
                        if "large_image_url" in dir(activity) and activity.large_image_url:
                            e.set_thumbnail(url=activity.large_image_url)
                    if isinstance(activity, discord.CustomActivity):
                        e.add_field(name="Custom Status", value=f"{activity.emoji if activity.emoji else ''} {activity.name if activity.name else ''}")
            if len(e.fields)%3:
                for _ in range(3-len(e.fields)%3):
                    e.add_field(name="\u200b", value="\u200b")
            if str(user.web_status) != "offline":
                e.add_field(name="Web Status", value=str(user.web_status).capitalize())
            e.add_field(name="Desktop Status", value=str(user.desktop_status).capitalize())
            if str(user.mobile_status) != "offline":
                e.add_field(name="Mobile Status", value=str(user.mobile_status).capitalize())
            if len(e.fields)%3:
                for _ in range(3-len(e.fields)%3):
                    e.add_field(name="\u200b", value="\u200b")
            if user.guild == user.guild:
                e.timestamp = user.joined_at
                e.set_footer(text=e.footer.text+" | Joined")
                if user.nick:
                    e.add_field(name="Nickname", value=user.nick)
                e.add_field(name="Boosting since", value=f"{self.client.utils.format_dt(user.premium_since, 'f')}\n{self.client.utils.format_dt(user.premium_since, 'R')}" if user.premium_since else "Not Boosting")
            if len(e.fields) in [2, 5, 8, 11, 14]:
                e.add_field(name="\u200b", value="\u200b")
        await self.interaction.response.send_message(embed=e, ephemeral=True)

def setup(bot):
    bot.application_command(UserInfo)