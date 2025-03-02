# brian-discord-bot/cogs/admin.py

import os
import disnake
from disnake.ext import commands
import logging
import config

logger = logging.getLogger('discord_bot')


class Admin(commands.Cog):
    """Administrative commands for server management"""

    def __init__(self, bot):
        self.bot = bot

    # Check if user is an admin or has manage server permissions
    async def cog_slash_command_check(self, inter):
        # Server owner always has permission
        if inter.guild.owner_id == inter.author.id:
            return True
        # Bot owner always has permission
        if inter.author.id in config.OWNER_IDS:
            return True
        # Check for admin permission
        return inter.author.guild_permissions.administrator or inter.author.guild_permissions.manage_guild

    @commands.slash_command()
    async def purge(
        self,
        inter,
        amount: int = commands.Param(
            description="Number of messages to delete", ge=1, le=100),
        user: disnake.User = commands.Param(
            description="Filter by user", default=None)
    ):
        """Delete multiple messages from a channel"""
        # Defer response since this might take time
        await inter.response.defer(ephemeral=True)

        try:
            if user:
                # Delete messages from specific user
                def check(message):
                    return message.author.id == user.id

                deleted = await inter.channel.purge(limit=amount, check=check)
                await inter.edit_original_message(
                    content=f"Deleted {len(deleted)} messages from {user.display_name}."
                )
            else:
                # Delete messages without filter
                deleted = await inter.channel.purge(limit=amount)
                await inter.edit_original_message(
                    content=f"Deleted {len(deleted)} messages."
                )

            logger.info(
                f"{inter.author} purged {len(deleted)} messages in #{inter.channel.name}")

        except disnake.errors.Forbidden:
            await inter.edit_original_message(
                content="I don't have permission to delete messages in this channel."
            )
        except Exception as e:
            logger.error(f"Error in purge command: {e}")
            await inter.edit_original_message(
                content=f"An error occurred: {str(e)}"
            )

    @commands.slash_command()
    async def kick(
        self,
        inter,
        user: disnake.Member = commands.Param(description="User to kick"),
        reason: str = commands.Param(
            description="Reason for kick", default="No reason provided")
    ):
        """Kick a user from the server"""
        if not inter.guild.me.guild_permissions.kick_members:
            return await inter.response.send_message(
                "I don't have permission to kick members!",
                ephemeral=True
            )

        if user.top_role >= inter.author.top_role and inter.author.id != inter.guild.owner_id:
            return await inter.response.send_message(
                "You can't kick someone with a role higher than or equal to yours.",
                ephemeral=True
            )

        if user.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message(
                "I can't kick someone with a role higher than or equal to mine.",
                ephemeral=True
            )

        try:
            await inter.response.defer(ephemeral=True)
            # Send DM to user if possible
            try:
                embed = disnake.Embed(
                    title=f"You've been kicked from {inter.guild.name}",
                    description=f"Reason: {reason}",
                    color=config.ERROR_COLOR
                )
                await user.send(embed=embed)
            except:
                # Can't send DM, continue anyway
                pass

            # Kick the user
            await user.kick(reason=reason)

            # Log the action
            logger.info(f"{inter.author} kicked {user} for: {reason}")

            # Confirm to moderator
            embed = disnake.Embed(
                title="User Kicked",
                description=f"{user.mention} has been kicked\nReason: {reason}",
                color=config.SUCCESS_COLOR
            )
            await inter.edit_original_message(embed=embed)

            # Log to channel if configured
            if config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
                log_channel = inter.guild.get_channel(config.LOG_CHANNEL_ID)
                if log_channel:
                    log_embed = disnake.Embed(
                        title="User Kicked",
                        description=f"**User:** {user.mention} ({user.id})\n**Reason:** {reason}\n**Moderator:** {inter.author.mention}",
                        color=config.INFO_COLOR,
                        timestamp=inter.created_at
                    )
                    log_embed.set_thumbnail(url=user.display_avatar.url)
                    await log_channel.send(embed=log_embed)

        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await inter.edit_original_message(
                content=f"Failed to kick {user.mention}: {str(e)}"
            )

    @commands.slash_command()
    async def ban(
        self,
        inter,
        user: disnake.Member = commands.Param(description="User to ban"),
        reason: str = commands.Param(
            description="Reason for ban", default="No reason provided"),
        delete_days: int = commands.Param(
            description="Days of messages to delete", default=1, ge=0, le=7)
    ):
        """Ban a user from the server"""
        if not inter.guild.me.guild_permissions.ban_members:
            return await inter.response.send_message(
                "I don't have permission to ban members!",
                ephemeral=True
            )

        if user.top_role >= inter.author.top_role and inter.author.id != inter.guild.owner_id:
            return await inter.response.send_message(
                "You can't ban someone with a role higher than or equal to yours.",
                ephemeral=True
            )

        if user.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message(
                "I can't ban someone with a role higher than or equal to mine.",
                ephemeral=True
            )

        try:
            await inter.response.defer(ephemeral=True)
            # Send DM to user if possible
            try:
                embed = disnake.Embed(
                    title=f"You've been banned from {inter.guild.name}",
                    description=f"Reason: {reason}",
                    color=config.ERROR_COLOR
                )
                await user.send(embed=embed)
            except:
                # Can't send DM, continue anyway
                pass

            # Ban the user
            await user.ban(reason=reason, delete_message_days=delete_days)

            # Log the action
            logger.info(f"{inter.author} banned {user} for: {reason}")

            # Confirm to moderator
            embed = disnake.Embed(
                title="User Banned",
                description=f"{user.mention} has been banned\nReason: {reason}",
                color=config.SUCCESS_COLOR
            )
            await inter.edit_original_message(embed=embed)

            # Log to channel if configured
            if config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
                log_channel = inter.guild.get_channel(config.LOG_CHANNEL_ID)
                if log_channel:
                    log_embed = disnake.Embed(
                        title="User Banned",
                        description=f"**User:** {user.mention} ({user.id})\n**Reason:** {reason}\n**Moderator:** {inter.author.mention}\n**Delete Message Days:** {delete_days}",
                        color=config.ERROR_COLOR,
                        timestamp=inter.created_at
                    )
                    log_embed.set_thumbnail(url=user.display_avatar.url)
                    await log_channel.send(embed=log_embed)

        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await inter.edit_original_message(
                content=f"Failed to ban {user.mention}: {str(e)}"
            )

    @commands.slash_command()
    async def timeout(
        self,
        inter,
        user: disnake.Member = commands.Param(description="User to timeout"),
        # Max 28 days (40320 minutes)
        duration: int = commands.Param(
            description="Duration in minutes", ge=1, le=40320),
        reason: str = commands.Param(
            description="Reason for timeout", default="No reason provided")
    ):
        """Timeout a user for a specified duration"""
        if not inter.guild.me.guild_permissions.moderate_members:
            return await inter.response.send_message(
                "I don't have permission to timeout members!",
                ephemeral=True
            )

        if user.top_role >= inter.author.top_role and inter.author.id != inter.guild.owner_id:
            return await inter.response.send_message(
                "You can't timeout someone with a role higher than or equal to yours.",
                ephemeral=True
            )

        if user.top_role >= inter.guild.me.top_role:
            return await inter.response.send_message(
                "I can't timeout someone with a role higher than or equal to mine.",
                ephemeral=True
            )

        try:
            await inter.response.defer(ephemeral=True)

            # Calculate timeout duration
            import datetime
            until = datetime.datetime.now(
                datetime.timezone.utc) + datetime.timedelta(minutes=duration)

            # Timeout the user
            await user.timeout(until=until, reason=reason)

            # Format time for display
            # Convert to seconds for the helper
            time_str = format_timespan(duration * 60)

            # Send confirmation
            embed = disnake.Embed(
                title="User Timed Out",
                description=f"{user.mention} has been timed out for {time_str}\nReason: {reason}",
                color=config.SUCCESS_COLOR
            )
            await inter.edit_original_message(embed=embed)

            # Log to channel if configured
            if config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
                log_channel = inter.guild.get_channel(config.LOG_CHANNEL_ID)
                if log_channel:
                    log_embed = disnake.Embed(
                        title="User Timed Out",
                        description=f"**User:** {user.mention} ({user.id})\n**Duration:** {time_str}\n**Reason:** {reason}\n**Moderator:** {inter.author.mention}",
                        color=config.INFO_COLOR,
                        timestamp=inter.created_at
                    )
                    log_embed.set_thumbnail(url=user.display_avatar.url)
                    await log_channel.send(embed=log_embed)

        except Exception as e:
            logger.error(f"Error in timeout command: {e}")
            await inter.edit_original_message(
                content=f"Failed to timeout {user.mention}: {str(e)}"
            )

    @commands.slash_command()
    async def reload(
        self,
        inter,
        extension: str = commands.Param(
            description="Extension to reload",
            choices=[
                "all",
                "admin",
                "diagnostics",
                "error_handler",
                "fun",
                "staff_listings"
            ]
        )
    ):
        """Reload bot extensions (owner only)"""
        # Check if user is a bot owner
        if inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message(
                "This command is restricted to bot owners.",
                ephemeral=True
            )

        await inter.response.defer(ephemeral=True)

        if extension.lower() == "all":
            # Reload all extensions
            success = []
            failed = []

            # First unload all
            for ext in list(self.bot.extensions):
                try:
                    self.bot.unload_extension(ext)
                except Exception as e:
                    failed.append(f"{ext}: {str(e)}")

            # Then reload from files
            for filename in os.listdir('./cogs'):
                if filename.endswith('.py') and not filename.startswith('_'):
                    ext = f'cogs.{filename[:-3]}'
                    try:
                        self.bot.load_extension(ext)
                        success.append(ext)
                    except Exception as e:
                        failed.append(f"{ext}: {str(e)}")

            # Build response message
            msg = f"Reloaded {len(success)} extension(s)"
            if failed:
                msg += f"\nFailed to reload {len(failed)} extension(s):\n" + \
                    "\n".join(failed)

            await inter.edit_original_message(content=msg)

        else:
            # Reload specific extension
            ext = extension if extension.startswith(
                'cogs.') else f'cogs.{extension}'
            try:
                self.bot.reload_extension(ext)
                await inter.edit_original_message(content=f"Successfully reloaded {ext}")
            except Exception as e:
                await inter.edit_original_message(content=f"Failed to reload {ext}: {str(e)}")

# Helper function to format time spans


def format_timespan(seconds):
    """Format a timespan in seconds to a human-readable string"""
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)

    parts = []
    if days > 0:
        parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not parts:  # Only include seconds if less than a minute
        parts.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts)


def setup(bot):
    bot.add_cog(Admin(bot))
