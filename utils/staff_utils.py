# utils/staff_utils.py
import re
import disnake
import logging

logger = logging.getLogger('discord_bot')


def format_member_display(member: disnake.Member) -> str:
    """Format member display with mention, name and ID, removing the PREFIX"""
    display_name = member.display_name

    # First, handle the [PREFIX] [Name] [ID] format
    bracket_pattern = re.compile(
        r'^\s*\[[^\]]+\]\s*(\[[^\]]+\]\s*\[[^\]]+\])$')
    bracket_match = bracket_pattern.match(display_name)
    if bracket_match:
        clean_name = bracket_match.group(1).strip()
        return f"{member.mention} - {clean_name}"

    # Handle PREFIX | Name | ID format (or with / as separator)
    # Find the first separator
    separators = ['|', '/', '[']
    first_sep_idx = -1
    for sep in separators:
        idx = display_name.find(sep)
        if idx != -1 and (first_sep_idx == -1 or idx < first_sep_idx):
            first_sep_idx = idx

    # If we found a separator, try to extract the name and ID part
    if first_sep_idx != -1:
        # Everything after the first separator
        remaining = display_name[first_sep_idx:].strip()

        # Remove the separator itself if it's at the beginning
        if remaining and remaining[0] in '|/[':
            remaining = remaining[1:].strip()

        # Check if there are more separators in the remaining text
        has_more_separators = False
        for sep in separators:
            if sep in remaining:
                has_more_separators = True
                break

        # If there are more separators, this is likely the Name | ID part
        if has_more_separators:
            return f"{member.mention} - {remaining}"

    # Fallback if patterns don't match
    return f"{member.mention} - {display_name}"


def find_members_with_role_pattern(guild, pattern):
    """Find all members with roles matching a specific regex pattern"""
    members = []
    regex = re.compile(pattern)

    for member in guild.members:
        for role in member.roles:
            if regex.match(role.name):
                members.append(member)
                break

    return sorted(members, key=lambda m: m.display_name.lower())


def find_single_member_with_role_pattern(guild, pattern):
    """Find a single member with a role matching a specific regex pattern"""
    regex = re.compile(pattern)

    for member in guild.members:
        for role in member.roles:
            if regex.match(role.name):
                return member

    return None


def get_dept_for_channel(channel_id, high_staff_channel_id, departments):
    """Get the department name for a channel ID"""
    if channel_id == high_staff_channel_id:
        return "HIGH STAFF"

    for dept in departments:
        if dept.get('channel_id') == channel_id:
            return dept.get('short', 'UNKNOWN')

    return "UNKNOWN"
