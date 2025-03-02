# brian-discord-bot/cogs/error_handler.py

import disnake
from disnake.ext import commands
import logging
import traceback
import sys
import config

logger = logging.getLogger('discord_bot')


class ErrorHandler(commands.Cog):
    """Global error handling for the bot"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_slash_command_error(self, inter, error):
        """Handle errors from slash commands"""

        # If the command has its own error handler, let it handle the error
        if hasattr(inter.application_command, 'on_error'):
            return

        # Get the original error if it's wrapped
        error = getattr(error, 'original', error)

        if isinstance(error, commands.CommandOnCooldown):
            # Handle cooldown
            seconds = round(error.retry_after)
            message = f"This command is on cooldown. Please try again in {seconds} seconds."
            await inter.response.send_message(message, ephemeral=True)

        elif isinstance(error, commands.NoPrivateMessage):
            # Handle commands that can't be used in DMs
            await inter.response.send_message("This command cannot be used in private messages.", ephemeral=True)

        elif isinstance(error, commands.MissingPermissions):
            # Handle missing user permissions
            await inter.response.send_message(f"You don't have the required permissions to use this command: {error}", ephemeral=True)

        elif isinstance(error, commands.BotMissingPermissions):
            # Handle missing bot permissions
            await inter.response.send_message(f"I don't have the required permissions to execute this command: {error}", ephemeral=True)

        elif isinstance(error, disnake.Forbidden):
            # Handle Discord 403 Forbidden errors
            await inter.response.send_message("I don't have permission to perform this action. Please check my role permissions.", ephemeral=True)
            logger.error(
                f"Permission error in command {inter.application_command.name}: {error}")

        elif isinstance(error, disnake.NotFound):
            # Handle Discord 404 Not Found errors
            await inter.response.send_message("The requested resource was not found. This could be a channel, message, or user that no longer exists.", ephemeral=True)

        elif isinstance(error, commands.CheckFailure):
            # Handle check failures (other than permissions)
            await inter.response.send_message("You don't have permission to use this command.", ephemeral=True)

        else:
            # Log the error
            logger.error(f"Unhandled command error: {error}")
            logger.error(traceback.format_exception(
                type(error), error, error.__traceback__))

            # For unhandled errors, send a generic message with error details
            if hasattr(inter, 'response') and not inter.response.is_done():
                await inter.response.send_message(
                    "An error occurred while executing this command. The error has been logged.",
                    ephemeral=True
                )

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs):
        """Handle non-command errors"""
        # Log the error
        error_type, error, error_traceback = sys.exc_info()

        logger.error(f"Error in event {event}: {error}")
        logger.error(''.join(traceback.format_exception(
            error_type, error, error_traceback)))

        # If it's a permission error, try to notify a configured log channel
        if isinstance(error, disnake.Forbidden) and config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
            try:
                log_channel = self.bot.get_channel(config.LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(f"Permission error in event `{event}`: I don't have the required permissions.")
            except:
                # If we can't send to log channel, just continue
                pass


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
