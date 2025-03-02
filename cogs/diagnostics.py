# brian-discord-bot/cogs/diagnostics.py

import disnake
from disnake.ext import commands
import logging
import config
import platform
from datetime import datetime

logger = logging.getLogger('discord_bot')


class Diagnostics(commands.Cog):
    """Bot diagnostics and permission checking tools"""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now()

    @commands.slash_command()
    async def check_permissions(
        self,
        inter,
        channel: disnake.TextChannel = commands.Param(
            description="Channel to check permissions in",
            default=None
        )
    ):
        """Check the bot's permissions in a channel (Admin only)"""
        # Check for admin permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You do not have permission to use this command.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        # If no channel is specified, use the current channel
        if channel is None:
            channel = inter.channel

        # Get bot's permissions in the channel
        bot_member = inter.guild.get_member(self.bot.user.id)
        permissions = channel.permissions_for(bot_member)

        # Create an embed for the permission report
        embed = disnake.Embed(
            title=f"Bot Permissions in #{channel.name}",
            description="A check of my permissions in this channel:",
            color=disnake.Color.blue()
        )

        # Check crucial permissions
        crucial_permissions = {
            "View Channel": permissions.view_channel,
            "Send Messages": permissions.send_messages,
            "Embed Links": permissions.embed_links,
            "Read Message History": permissions.read_message_history,
            "Manage Messages": permissions.manage_messages
        }

        # Add crucial permissions to embed
        for perm_name, has_perm in crucial_permissions.items():
            status = "✅" if has_perm else "❌"
            embed.add_field(
                name=f"{status} {perm_name}",
                value="Required for staff listings" if not has_perm else "Granted",
                inline=False
            )

        # Check if there are any missing crucial permissions
        missing_perms = [
            p for p, has in crucial_permissions.items() if not has]
        if missing_perms:
            embed.color = disnake.Color.red()
            embed.add_field(
                name="⚠️ Warning",
                value=f"The bot is missing {len(missing_perms)} crucial permissions in this channel. "
                f"Staff listings and other features may not work correctly.",
                inline=False
            )
        else:
            embed.color = disnake.Color.green()
            embed.add_field(
                name="✅ All Good",
                value="The bot has all necessary permissions in this channel.",
                inline=False
            )

        await inter.edit_original_message(embed=embed)

    @commands.slash_command()
    async def check_all_channels(self, inter):
        """Check the bot's permissions in all staff listing channels (Admin only)"""
        # Check for admin permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You do not have permission to use this command.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        # Get all channel IDs to check
        channels_to_check = []

        # Add high staff listing channel
        if config.HIGH_STAFF_LISTING_CHANNEL_ID:
            channels_to_check.append(config.HIGH_STAFF_LISTING_CHANNEL_ID)

        # Add department channels
        for dept in config.DEPARTMENTS:
            if dept.get('channel_id'):
                channels_to_check.append(dept['channel_id'])

        # Get bot member
        bot_member = inter.guild.get_member(self.bot.user.id)

        # Create embed for results
        embed = disnake.Embed(
            title="Staff Listing Channels Permission Check",
            description="Checking permissions in all configured staff listing channels:",
            color=disnake.Color.blue()
        )

        all_ok = True

        # Check each channel
        for channel_id in channels_to_check:
            channel = inter.guild.get_channel(channel_id)
            if not channel:
                embed.add_field(
                    name=f"❌ Unknown Channel: {channel_id}",
                    value="This channel ID is configured but the channel was not found.",
                    inline=False
                )
                all_ok = False
                continue

            # Get permissions
            perms = channel.permissions_for(bot_member)

            # Check for required permissions
            missing = []
            if not perms.view_channel:
                missing.append("View Channel")
            if not perms.send_messages:
                missing.append("Send Messages")
            if not perms.embed_links:
                missing.append("Embed Links")
            if not perms.read_message_history:
                missing.append("Read Message History")
            if not perms.manage_messages:
                missing.append("Manage Messages")

            if missing:
                embed.add_field(
                    name=f"❌ #{channel.name}",
                    value=f"Missing permissions: {', '.join(missing)}",
                    inline=False
                )
                all_ok = False
            else:
                embed.add_field(
                    name=f"✅ #{channel.name}",
                    value="All required permissions granted",
                    inline=False
                )

        if all_ok:
            embed.color = disnake.Color.green()
            embed.description = "✅ All configured staff listing channels have the required permissions!"
        else:
            embed.color = disnake.Color.red()
            embed.description = "⚠️ Some channels have missing permissions. Staff listings may not work correctly."

        await inter.edit_original_message(embed=embed)

    @commands.slash_command()
    async def botinfo(self, inter):
        """Display information about the bot and its status"""
        await inter.response.defer(ephemeral=False)

        # Calculate uptime
        uptime_delta = datetime.now() - self.start_time
        days = uptime_delta.days
        hours, remainder = divmod(uptime_delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        # Get system info
        python_version = platform.python_version()
        disnake_version = disnake.__version__
        os_info = f"{platform.system()} {platform.release()}"

        # Get bot stats
        guild_count = len(self.bot.guilds)
        user_count = sum(g.member_count for g in self.bot.guilds)
        channel_count = sum(len(g.channels) for g in self.bot.guilds)

        # Create embed
        embed = disnake.Embed(
            title=f"{self.bot.user.name} Info",
            description="Bot status and system information",
            color=config.EMBED_COLOR
        )

        # Add bot information
        embed.add_field(name="Bot Version", value="1.0.0", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(
            name="Ping", value=f"{round(self.bot.latency * 1000)}ms", inline=True)

        # Add system information
        embed.add_field(name="Python Version",
                        value=python_version, inline=True)
        embed.add_field(name="Disnake Version",
                        value=disnake_version, inline=True)
        embed.add_field(name="Operating System", value=os_info, inline=True)

        # Add statistics
        embed.add_field(name="Servers", value=str(guild_count), inline=True)
        embed.add_field(name="Users", value=str(user_count), inline=True)
        embed.add_field(name="Channels", value=str(channel_count), inline=True)

        # Set footer
        embed.set_footer(
            text=f"Requested by {inter.author.display_name}", icon_url=inter.author.display_avatar.url)

        # Set thumbnail
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        await inter.edit_original_message(embed=embed)


def setup(bot):
    bot.add_cog(Diagnostics(bot))
