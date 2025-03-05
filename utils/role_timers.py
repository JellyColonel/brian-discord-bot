# utils/role_timers.py
import logging
import datetime
from data.models.timed_role_model import TimedRole

logger = logging.getLogger('discord_bot')


async def add_timed_role(
    member,
    role,
    duration_seconds,
    added_by,
    reason=None,
    auto_remove=True,
    notify_user=True,
    notify_channel=None,
    notify_roles=None
):
    """Add a role to a member that will be tracked for a specified duration.

    Args:
        member (disnake.Member): The member to add the role to
        role (disnake.Role): The role to add
        duration_seconds (int): Duration in seconds to keep the role
        added_by (disnake.Member): The member who added the role
        reason (str, optional): Reason for adding the role
        auto_remove (bool, optional): Whether to automatically remove the role when it expires
        notify_user (bool, optional): Whether to notify the user when role expires
        notify_channel (disnake.TextChannel, optional): Channel to notify when role expires
        notify_roles (list, optional): List of roles to ping when role expires

    Returns:
        int: ID of the created timed role record

    Raises:
        disnake.Forbidden: If the bot doesn't have permission to add the role
    """

    # Check if this role is already a timed role for this user
    existing_roles = await TimedRole.get_active_roles_for_user(member.id)
    for existing_role in existing_roles:
        if existing_role["role_id"] == role.id:
            raise ValueError(
                f"This member already has '{role.name}' as an active timed role.")

    # Check if the bot can manage this role (hierarchy check)
    if role >= member.guild.me.top_role:
        raise ValueError(
            f"Cannot manage the role '{role.name}' due to role hierarchy. Move the bot's role above this role.")

    # First add the role to the member
    if role not in member.roles:
        await member.add_roles(role, reason=f"Timed role: {reason}")

    # Store in database
    notify_role_ids = [r.id for r in notify_roles] if notify_roles else None
    notify_channel_id = notify_channel.id if notify_channel else None

    timed_role_id = await TimedRole.add_timed_role(
        guild_id=member.guild.id,
        user_id=member.id,
        role_id=role.id,
        duration_seconds=duration_seconds,
        added_by=added_by.id,
        reason=reason,
        auto_remove=auto_remove,
        notify_user=notify_user,
        notify_channel_id=notify_channel_id,
        notify_role_ids=notify_role_ids
    )

    logging_action = "Added timed role" if auto_remove else "Added tracked role"
    logger.info(
        f"{logging_action} {role.name} to {member.display_name} for {format_duration(duration_seconds)}"
    )

    return timed_role_id


async def list_active_timed_roles(member):
    """List all active timed roles for a member.

    Args:
        member (disnake.Member): The member to check

    Returns:
        list: List of active timed role records with additional format data
    """
    active_roles = await TimedRole.get_active_roles_for_user(member.id)

    # Enhance data with formatted times and role names
    for role in active_roles:
        # Add time remaining
        expires_at = role["expires_at"]
        remaining_seconds = expires_at - \
            int(datetime.datetime.now().timestamp())
        role["time_remaining"] = format_duration(remaining_seconds)

        # Add formatted expiration time
        role["expires_at_formatted"] = datetime.datetime.fromtimestamp(
            expires_at
        ).strftime("%Y-%m-%d %H:%M:%S")

        # Try to get the role name
        role_obj = member.guild.get_role(role["role_id"])
        role["role_name"] = role_obj.name if role_obj else f"Unknown Role ({role['role_id']})"

    return active_roles


def format_duration(seconds):
    """Format seconds into a readable duration string.

    Args:
        seconds (int): Duration in seconds

    Returns:
        str: Formatted duration string
    """
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days > 0:
        parts.append(f"{int(days)} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{int(hours)} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{int(minutes)} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not parts:
        parts.append(f"{int(seconds)} second{'s' if seconds != 1 else ''}")

    return ", ".join(parts)


def parse_duration(duration_str):
    """Parse a duration string (like '1d12h30m') into seconds.

    Args:
        duration_str (str): Duration string (e.g., '1d12h30m', '24h', '30m')

    Returns:
        int: Duration in seconds, or 0 if invalid format
    """
    total_seconds = 0
    current_num = ""

    for char in duration_str.lower():
        if char.isdigit():
            current_num += char
        elif char == 'd' and current_num:
            total_seconds += int(current_num) * 86400  # Days
            current_num = ""
        elif char == 'h' and current_num:
            total_seconds += int(current_num) * 3600  # Hours
            current_num = ""
        elif char == 'm' and current_num:
            total_seconds += int(current_num) * 60  # Minutes
            current_num = ""
        elif char == 's' and current_num:
            total_seconds += int(current_num)  # Seconds
            current_num = ""

    # Add any remaining numbers as seconds
    if current_num:
        total_seconds += int(current_num)

    return total_seconds
