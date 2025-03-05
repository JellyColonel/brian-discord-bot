# brian-discord-bot/utils/helper.py
import asyncio
import datetime
import logging
import disnake

logger = logging.getLogger('discord_bot')


async def clear_channel(channel):
    """Clear all messages in a channel

    Args:
        channel: The discord channel to clear

    Raises:
        disnake.Forbidden: If the bot lacks required permissions
        Exception: For other errors during deletion
    """
    try:
        # First try bulk delete for messages less than 14 days old
        messages = await channel.history(limit=100).flatten()
        if not messages:
            return

        # Filter messages by age
        now = datetime.datetime.now(datetime.timezone.utc)
        recent_messages = [msg for msg in messages if (
            now - msg.created_at).days < 14]

        if recent_messages:
            await channel.purge(limit=len(recent_messages))

        # If there are older messages, delete them one by one
        older_messages = [msg for msg in messages if (
            now - msg.created_at).days >= 14]
        for message in older_messages:
            await message.delete()
            await asyncio.sleep(0.5)  # Delay to avoid rate limits

    except disnake.Forbidden:
        # Re-raise the exception to be caught by the calling method
        raise
    except Exception as e:
        logger.error(
            f"Error clearing channel: {e}", exc_info=True)
        raise
