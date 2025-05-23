# brian-discord-bot/cogs/staff_listings.py

import disnake
from disnake.ext import commands, tasks
import logging
import config
import re
import asyncio
from utils.helper import clear_channel

from utils.staff_utils import (
    format_member_display,
    find_members_with_role_pattern,
    find_single_member_with_role_pattern,
    get_dept_for_channel as utils_get_dept_for_channel
)

logger = logging.getLogger('discord_bot')


class StaffListings(commands.Cog):
    """Staff listings and organization hierarchy management"""

    def __init__(self, bot):
        self.bot = bot
        self.staff_role_ids = set(config.ROLE_IDS.values())
        self.update_lock = asyncio.Lock()  # Lock to prevent simultaneous updates
        self.permission_errors = set()  # Store channels with permission errors

        # Store enabled state for easy access throughout the class
        self.enabled = config.FEATURES['STAFF_LISTINGS']

        # Start the task only if enabled
        if self.enabled:
            self.update_staff_listings.start()
            logger.info("Staff listings feature is enabled")
        else:
            logger.info("Staff listings feature is disabled")

    def cog_unload(self):
        if self.enabled and self.update_staff_listings.is_running():
            self.update_staff_listings.cancel()

    # Helper method to check if feature is enabled
    async def staff_listings_enabled(self, inter, allow_admin_override=True):
        """Check if staff listings are enabled, with optional admin override"""
        if self.enabled:
            return True

        # Allow admins to still use commands even when feature is disabled
        if allow_admin_override and (
            inter.author.guild_permissions.administrator or
            inter.author.id in config.OWNER_IDS
        ):
            return True

        await inter.response.send_message(
            "Staff listings feature is currently disabled.",
            ephemeral=True
        )
        return False

    @tasks.loop(minutes=30)  # Update every 30 minutes
    async def update_staff_listings(self):
        """Automatically update staff listings"""
        # Skip if feature is disabled
        if not self.enabled:
            return

        logger.info("Updating staff listings...")

        # Get the guild
        guild = self.bot.get_guild(config.SERVER_ID)
        if not guild:
            logger.error("Could not find guild for staff listings update")
            return

        # Clear previous permission errors
        self.permission_errors.clear()

        # Update high staff listings
        await self.update_high_staff_listings(guild)

        # Update department-specific listings
        await self.update_department_listings(guild)

        # Log any permission errors
        if self.permission_errors:
            # Map channel IDs to names for better logging
            channel_names = {}
            for channel_id in self.permission_errors:
                channel = guild.get_channel(channel_id)
                if channel:
                    channel_names[channel_id] = channel.name

            # Log with consolidated format
            error_channels_text = ", ".join([
                f"{get_dept_for_channel(channel_id)}: #{channel_names.get(channel_id, str(channel_id))}"
                for channel_id in self.permission_errors
            ])
            logger.warning(
                f"Staff listings update: Missing permissions in channels: {error_channels_text}")

            # Try to notify in log channel - only if we haven't already tried
            if config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
                try:
                    log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
                    if log_channel and log_channel.id not in self.permission_errors:
                        # Use channel mentions in the Discord message, better for admins
                        channel_mentions = ", ".join(
                            [f"<#{channel_id}>" for channel_id in self.permission_errors])
                        await log_channel.send(
                            f"⚠️ Staff listings could not be updated in some channels due to missing permissions: {channel_mentions}\n"
                            f"Please ensure the bot has the following permissions in these channels:\n"
                            f"- View Channel\n"
                            f"- Read Message History\n"
                            f"- Send Messages\n"
                            f"- Manage Messages (to clean up old listings)"
                        )
                except Exception as e:
                    logger.error(
                        f"Could not send permission error notification: {e}")
        else:
            logger.info("Staff listings updated successfully")

    async def update_high_staff_listings(self, guild):
        """Update the high staff listings channel"""
        # Get the channel
        channel_id = config.HIGH_STAFF_LISTING_CHANNEL_ID
        channel = guild.get_channel(channel_id)
        if not channel:
            logger.error(
                f"Could not find high staff listings channel: {channel_id}")
            return

        try:
            # Clear the channel
            await clear_channel(channel)

            # Create and send all embeds
            await self.send_high_staff_embeds(channel, guild)
            await self.send_department_embeds(channel, guild)

            logger.info("High staff listings updated successfully")
        except disnake.Forbidden:
            # Just add to permission_errors, we'll log everything at once
            self.permission_errors.add(channel_id)
        except Exception as e:
            logger.error(
                f"Error updating high staff listings: {e}", exc_info=True)

    async def update_department_listings(self, guild):
        """Update each department's staff listing channel"""
        for dept in config.DEPARTMENTS:
            # Get department channel
            channel_id = dept.get('channel_id')
            if not channel_id:
                logger.warning(
                    f"No channel ID configured for {dept['short']} department")
                continue

            channel = guild.get_channel(channel_id)
            if not channel:
                logger.error(
                    f"Could not find channel for {dept['short']} department: {channel_id}")
                continue

            try:
                # Clear the channel
                await clear_channel(channel)

                # Create and send department-specific embeds
                await self.send_department_specific_embeds(channel, guild, dept)

                logger.info(
                    f"{dept['short']} department listings updated successfully")
            except disnake.Forbidden:
                # Just add to permission_errors, we'll log everything at once
                self.permission_errors.add(channel_id)
            except Exception as e:
                logger.error(
                    f"Error updating {dept['short']} department listings: {e}", exc_info=True)

    async def send_department_specific_embeds(self, channel, guild, dept):
        """Send the department-specific embeds to the channel"""

        # Embed 1: Department Curator (Заведующий)
        curator_embed = await self.create_department_curator_embed(guild, dept)
        if curator_embed:
            await channel.send(embed=curator_embed)
            await asyncio.sleep(0.5)

        # Embed 2: Department Head (Начальник)
        head_embed = await self.create_department_head_embed(guild, dept)
        if head_embed:
            await channel.send(embed=head_embed)
            await asyncio.sleep(0.5)

        # Embed 3: Deputy Heads (Заместители начальника)
        deputy_embed = await self.create_department_deputy_embed(guild, dept)
        if deputy_embed:
            await channel.send(embed=deputy_embed)
            await asyncio.sleep(0.5)

        # Embed 4: Mid-level staff (Средний состав)
        mid_staff_embed = await self.create_department_mid_staff_embed(guild, dept)
        if mid_staff_embed:
            await channel.send(embed=mid_staff_embed)
            await asyncio.sleep(0.5)

    async def create_department_curator_embed(self, guild, dept):
        """Create embed for department curator (Заведующий)"""
        dept_short = dept['short']
        dept_full = dept['full']

        # Find department curator with "Заведующий {dept_short}" role
        pattern = re.compile(f"Заведующий\\s+{dept_short}")
        dept_curator = find_single_member_with_role_pattern(guild, pattern)

        if not dept_curator:
            logger.warning(f"No department curator found for {dept_short}")
            return None

        # Get management role for color
        management_role_id = config.ROLE_IDS.get('MANAGEMENT_STAFF')
        management_role = guild.get_role(
            management_role_id) if management_role_id else None
        embed_color = management_role.color if management_role else disnake.Color.blurple()

        embed = disnake.Embed(
            title=f"Состав {dept_full}",
            description=f"### Заведующий {dept_short}\n{format_member_display(dept_curator)}",
            color=embed_color
        )

        return embed

    async def create_department_head_embed(self, guild, dept):
        """Create embed for department head (Начальник)"""
        dept_short = dept['short']

        # Find department head with "Начальник {dept_short}" role
        pattern = re.compile(f"Начальник\\s+{dept_short}")
        head = find_single_member_with_role_pattern(guild, pattern)

        if not head:
            logger.warning(f"No department head found for {dept_short}")
            return None

        # Get high staff role for color
        high_staff_role_id = config.ROLE_IDS.get('HIGH_STAFF')
        high_staff_role = guild.get_role(
            high_staff_role_id) if high_staff_role_id else None
        embed_color = high_staff_role.color if high_staff_role else disnake.Color.blurple()

        embed = disnake.Embed(
            title=f"Начальник {dept_short}",
            description=f"{format_member_display(head)}",
            color=embed_color
        )

        return embed

    async def create_department_deputy_embed(self, guild, dept):
        """Create embed for department deputy heads (Заместители начальника)"""
        dept_short = dept['short']

        # Find deputies with "Зам. Начальника {dept_short}" role
        pattern = re.compile(f"Зам\\. Начальника\\s+{dept_short}")
        deputies = find_members_with_role_pattern(guild, pattern)

        if not deputies:
            logger.warning(f"No deputy heads found for {dept_short}")
            return None

        description = ""
        for i, deputy in enumerate(deputies, start=1):
            description += f"{i}. {format_member_display(deputy)}\n"

        # Get high staff role for color (same as department head)
        high_staff_role_id = config.ROLE_IDS.get('HIGH_STAFF')
        high_staff_role = guild.get_role(
            high_staff_role_id) if high_staff_role_id else None
        embed_color = high_staff_role.color if high_staff_role else disnake.Color.blurple()

        embed = disnake.Embed(
            title=f"Заместители начальника {dept_short}",
            description=description,
            color=embed_color
        )

        return embed

    async def create_department_mid_staff_embed(self, guild, dept):
        """Create embed for department mid-level staff (Средний состав)"""
        dept_short = dept['short']

        # Get the department role
        dept_role_id = config.ROLE_IDS.get(f'{dept_short}_DEPARTMENT')
        if not dept_role_id:
            logger.error(f"{dept_short} department role ID not configured")
            return None

        dept_role = guild.get_role(dept_role_id)
        if not dept_role:
            logger.error(
                f"Could not find {dept_short} department role: {dept_role_id}")
            return None

        # Compile patterns for leadership roles
        curator_pattern = re.compile(f"Заведующий\\s+{dept_short}")
        head_pattern = re.compile(f"Начальник\\s+{dept_short}")
        deputy_pattern = re.compile(f"Зам\\. Начальника\\s+{dept_short}")

        curators = find_members_with_role_pattern(guild, curator_pattern)
        heads = find_members_with_role_pattern(guild, head_pattern)
        deputies = find_members_with_role_pattern(guild, deputy_pattern)

        # Combine all leadership members into a set for efficient lookup
        leadership_members = set()
        leadership_members.update(curators)
        leadership_members.update(heads)
        leadership_members.update(deputies)

        # Find all members with department role but without leadership roles
        mid_staff = [
            member for member in dept_role.members if member not in leadership_members]

        # Sort alphabetically
        mid_staff.sort(key=lambda m: m.display_name.lower())

        if not mid_staff:
            logger.warning(f"No mid-level staff found for {dept_short}")
            return None

        description = ""
        for i, member in enumerate(mid_staff, start=1):
            description += f"{i}. {format_member_display(member)}\n"

        embed = disnake.Embed(
            title=f"Средний состав {dept_short}",
            description=description,
            color=dept_role.color
        )

        return embed

    @update_staff_listings.before_loop
    async def before_update_staff_listings(self):
        """Wait for the bot to be ready before starting the task"""
        await self.bot.wait_until_ready()

    async def send_high_staff_embeds(self, channel, guild):
        """Send embeds for high staff positions"""
        # Embed 1: Chief Doctor
        chief_embed = await self.create_chief_doctor_embed(guild)
        if chief_embed:
            await channel.send(embed=chief_embed)
            await asyncio.sleep(0.5)

        # Embed 2: Deputy Chief Doctors
        deputy_embed = await self.create_deputy_chiefs_embed(guild)
        if deputy_embed:
            await channel.send(embed=deputy_embed)
            await asyncio.sleep(0.5)

        # Embed 3: Hospital Managers
        hospital_embed = await self.create_hospital_managers_embed(guild)
        if hospital_embed:
            await channel.send(embed=hospital_embed)
            await asyncio.sleep(0.5)

        # Embed 4: Department Heads
        dept_heads_embed = await self.create_department_heads_embed(guild)
        if dept_heads_embed:
            await channel.send(embed=dept_heads_embed)
            await asyncio.sleep(0.5)

    async def send_department_embeds(self, channel, guild):
        """Send embeds for each department's staff"""
        for dept in config.DEPARTMENTS:
            dept_embed = await self.create_department_staff_embed(guild, dept)
            if dept_embed:
                await channel.send(embed=dept_embed)
                await asyncio.sleep(0.5)  # Small delay to avoid rate limits

    async def create_chief_doctor_embed(self, guild):
        """Create embed for Chief Doctor"""
        role_id = config.ROLE_IDS.get('CHIEF_DOCTOR')
        if not role_id:
            logger.error("Chief Doctor role ID not configured")
            return None

        role = guild.get_role(role_id)
        if not role:
            logger.error(f"Could not find Chief Doctor role: {role_id}")
            return None

        # Find the member with this role
        chief = next((m for m in role.members), None)
        if not chief:
            logger.warning(f"No member found with Chief Doctor role")
            return None

        embed = disnake.Embed(
            title="Старший и руководящий состав",
            description=f"### Главный врач\n{format_member_display(chief)}",
            color=role.color
        )

        return embed

    async def create_deputy_chiefs_embed(self, guild):
        """Create embed for Deputy Chief Doctors"""
        role_id = config.ROLE_IDS.get('DEPUTY_CHIEF_DOCTOR')
        if not role_id:
            logger.error("Deputy Chief Doctor role ID not configured")
            return None

        role = guild.get_role(role_id)
        if not role:
            logger.error(f"Could not find Deputy Chief Doctor role: {role_id}")
            return None

        # Sort members alphabetically by display name
        deputies = sorted(role.members, key=lambda m: m.display_name.lower())

        if not deputies:
            logger.warning(f"No members found with Deputy Chief Doctor role")
            return None

        # Create numbered list
        description = ""
        for i, deputy in enumerate(deputies, start=1):
            description += f"{i}. {format_member_display(deputy)}\n"

        embed = disnake.Embed(
            title="Заместители Главного Врача",
            description=description,
            color=role.color
        )

        return embed

    async def create_hospital_managers_embed(self, guild):
        """Create embed for Hospital Managers"""
        role_id = config.ROLE_IDS.get('HOSPITAL_MANAGER')
        if not role_id:
            logger.error("Hospital Manager role ID not configured")
            return None

        role = guild.get_role(role_id)
        if not role:
            logger.error(f"Could not find Hospital Manager role: {role_id}")
            return None

        # Get the three hospital managers by their IDs
        east_ls_manager = guild.get_member(
            config.HOSPITAL_MANAGERS.get('EAST_LOS_SANTOS'))
        sandy_manager = guild.get_member(
            config.HOSPITAL_MANAGERS.get('SANDY_SHORES'))
        bay_manager = guild.get_member(
            config.HOSPITAL_MANAGERS.get('THE_BAY_CARE'))

        description = ""

        if east_ls_manager:
            description += f"### Заведующий East Los Santos Hospital\n{format_member_display(east_ls_manager)}\n"

        if sandy_manager:
            description += f"### Заведующий Sandy Shores Medical Center\n{format_member_display(sandy_manager)}\n"

        if bay_manager:
            description += f"### Заведующий The Bay Care Center\n{format_member_display(bay_manager)}\n"

        if not description:
            logger.warning("No hospital managers found")
            return None

        embed = disnake.Embed(
            title="Заведующие больницами",
            description=description,
            color=role.color
        )

        return embed

    async def create_department_heads_embed(self, guild):
        """Create embed for Department Heads"""
        management_role_id = config.ROLE_IDS.get('MANAGEMENT_STAFF')
        if not management_role_id:
            logger.error("Management Staff role ID not configured")
            return None

        management_role = guild.get_role(management_role_id)
        if not management_role:
            logger.error(
                f"Could not find Management Staff role: {management_role_id}")
            return None

        # Find all members with roles matching "Заведующий {department}"
        dept_heads = []
        pattern = re.compile(r"Заведующий\s+(.+)")

        # Create a mapping of short to full department names for display
        dept_mapping = {dept['short']: dept['full']
                        for dept in config.DEPARTMENTS}

        # Create a set of hospital curator IDs to exclude them
        hospital_manager_ids = set(config.HOSPITAL_MANAGERS.values())

        for member in guild.members:
            # Skip hospital managers - they should only appear in hospital managers section
            if member.id in hospital_manager_ids:
                continue

            for role in member.roles:
                match = pattern.match(role.name)
                if match:
                    dept_name = match.group(1)
                    dept_heads.append((dept_name, member, role))

        if not dept_heads:
            logger.warning("No department heads found")
            return None

        # Sort by department name
        dept_heads.sort(key=lambda x: x[0])

        description = ""
        for dept_name, member, role in dept_heads:
            description += f"### Заведующий {dept_name}\n{format_member_display(member)}\n"

        embed = disnake.Embed(
            title="Заведующие отделениями",
            description=description,
            color=management_role.color
        )

        return embed

    async def create_department_staff_embed(self, guild, dept_info):
        """Create embed for a specific department's staff"""
        dept_short = dept_info['short']
        dept_full = dept_info['full']

        dept_role_id = config.ROLE_IDS.get(f'{dept_short}_DEPARTMENT')
        if not dept_role_id:
            logger.error(f"{dept_short} department role ID not configured")
            return None

        dept_role = guild.get_role(dept_role_id)
        if not dept_role:
            logger.error(
                f"Could not find {dept_short} department role: {dept_role_id}")
            return None

        # Find department head (Начальник {dept})
        head_pattern = re.compile(f"Начальник\\s+{dept_short}")
        dept_head = None

        # Find deputy heads (Зам. Начальника {dept})
        deputy_pattern = re.compile(f"Зам\\. Начальника\\s+{dept_short}")
        deputies = []

        for member in guild.members:
            for role in member.roles:
                if head_pattern.match(role.name):
                    dept_head = member
                elif deputy_pattern.match(role.name):
                    deputies.append(member)

        # Sort deputies alphabetically
        deputies.sort(key=lambda m: m.display_name.lower())

        description = ""

        if dept_head:
            description += f"### Начальник {dept_short}\n{format_member_display(dept_head)}\n"

        if deputies:
            description += f"### Заместители начальника {dept_short}\n"
            for i, deputy in enumerate(deputies, start=1):
                description += f"{i}. {format_member_display(deputy)}\n"

        if not description:
            logger.warning(f"No staff found for department {dept_short}")
            return None

        embed = disnake.Embed(
            title=f"Старший состав {dept_short}",
            description=description,
            color=dept_role.color
        )

        return embed

    @commands.slash_command()
    async def update_staff(self, inter):
        """Update the staff listings (Admin only)"""
        # Check for admin permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You do not have permission to use this command.", ephemeral=True)

        # Check if feature is enabled (with admin override)
        if not await self.staff_listings_enabled(inter):
            return

        await inter.response.defer(ephemeral=True)

        try:
            # Get guild
            guild = inter.guild

            # Clear previous permission errors
            self.permission_errors.clear()

            # Update high staff listings
            await self.update_high_staff_listings(guild)

            # Update department-specific listings
            await self.update_department_listings(guild)

            # Check for permission errors
            if self.permission_errors:
                # Map channel IDs to names for better display
                channel_mentions = ", ".join(
                    [f"<#{channel_id}>" for channel_id in self.permission_errors])
                await inter.edit_original_message(
                    content=f"⚠️ Staff listings partially updated. Missing permissions in channels: {channel_mentions}\n\n"
                    f"Please ensure I have the following permissions in these channels:\n"
                    f"- View Channel\n"
                    f"- Read Message History\n"
                    f"- Send Messages\n"
                    f"- Manage Messages (to clean up old listings)"
                )
            else:
                await inter.edit_original_message(content="✅ Staff listings have been updated successfully.")
        except Exception as e:
            logger.error(
                f"Error manually updating staff listings: {e}", exc_info=True)
            await inter.edit_original_message(content=f"Error updating staff listings: {str(e)}")

    @commands.slash_command()
    async def update_department_staff(
        self,
        inter,
        department: str = commands.Param(
            description="Department to update (high, HAD, PM, DI, PSED, FD)",
            choices=["high", "HAD", "PM", "DI", "PSED", "FD"]
        )
    ):
        """Update a specific department's staff listing (Admin only)"""
        # Check for admin permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You do not have permission to use this command.", ephemeral=True)

        # Check if feature is enabled (with admin override)
        if not await self.staff_listings_enabled(inter):
            return

        await inter.response.defer(ephemeral=True)

        try:
            # Get guild
            guild = inter.guild

            # Handle high staff listings separately
            if department.lower() == "high":
                # Get high staff listings channel
                channel_id = config.HIGH_STAFF_LISTING_CHANNEL_ID
                if not channel_id:
                    return await inter.edit_original_message(content="No channel ID configured for high staff listings.")

                channel = guild.get_channel(channel_id)
                if not channel:
                    return await inter.edit_original_message(content="Could not find high staff listings channel.")

                try:
                    # Clear the channel
                    await clear_channel(channel)

                    # Send high staff embeds
                    await self.send_high_staff_embeds(channel, guild)
                    await self.send_department_embeds(channel, guild)

                    await inter.edit_original_message(content="✅ High staff listings have been updated successfully.")
                except disnake.Forbidden:
                    await inter.edit_original_message(
                        content=f"⚠️ Could not update high staff listings due to missing permissions in channel <#{channel_id}>.\n\n"
                        f"Please ensure I have the following permissions in this channel:\n"
                        f"- View Channel\n"
                        f"- Read Message History\n"
                        f"- Send Messages\n"
                        f"- Manage Messages (to clean up old listings)"
                    )
                return

            # Find the department info
            dept_info = next(
                (dept for dept in config.DEPARTMENTS if dept['short'] == department), None)
            if not dept_info:
                return await inter.edit_original_message(content=f"Department {department} not found in configuration.")

            # Get department channel
            channel_id = dept_info.get('channel_id')
            if not channel_id:
                return await inter.edit_original_message(content=f"No channel ID configured for {department} department.")

            channel = guild.get_channel(channel_id)
            if not channel:
                return await inter.edit_original_message(content=f"Could not find channel for {department} department.")

            # Clear previous permission errors
            self.permission_errors.clear()

            try:
                # Clear the channel
                await clear_channel(channel)

                # Send department-specific embeds
                await self.send_department_specific_embeds(channel, guild, dept_info)

                await inter.edit_original_message(content=f"✅ {department} department staff listing has been updated successfully.")
            except disnake.Forbidden:
                await inter.edit_original_message(
                    content=f"⚠️ Could not update {department} department staff listing due to missing permissions in channel <#{channel_id}>.\n\n"
                    f"Please ensure I have the following permissions in this channel:\n"
                    f"- View Channel\n"
                    f"- Read Message History\n"
                    f"- Send Messages\n"
                    f"- Manage Messages (to clean up old listings)"
                )
            except Exception as e:
                logger.error(
                    f"Error manually updating department staff listing: {e}", exc_info=True)
                await inter.edit_original_message(content=f"Error updating department staff listing: {str(e)}")
        except Exception as e:
            logger.error(
                f"Error manually updating department staff listing: {e}", exc_info=True)
            await inter.edit_original_message(content=f"Error updating department staff listing: {str(e)}")

    # Add a new admin command to toggle the feature on/off
    @commands.slash_command()
    async def toggle_staff_listings(self, inter):
        """Toggle staff listings feature on/off (Admin only)"""
        # Check for admin permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You do not have permission to use this command.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        # Toggle state
        self.enabled = not self.enabled

        # Start or stop the task as needed
        if self.enabled and not self.update_staff_listings.is_running():
            self.update_staff_listings.start()
            await inter.edit_original_message(content="✅ Staff listings feature has been enabled.")
            logger.info(f"Staff listings feature enabled by {inter.author}")
        elif not self.enabled and self.update_staff_listings.is_running():
            self.update_staff_listings.cancel()
            await inter.edit_original_message(content="⚠️ Staff listings feature has been disabled.")
            logger.info(f"Staff listings feature disabled by {inter.author}")
        else:
            status = "enabled" if self.enabled else "disabled"
            await inter.edit_original_message(content=f"Staff listings feature is already {status}.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        """Listen for members leaving and update staff listings if needed"""
        # Skip if feature is disabled
        if not self.enabled:
            return

        # Check if the member had any staff roles
        member_roles = set(role.id for role in member.roles)
        if any(role_id in self.staff_role_ids for role_id in member_roles):
            # Only update if we're not already updating
            if not self.update_lock.locked():
                async with self.update_lock:
                    logger.info(
                        f"Staff member {member.display_name} left the server, updating listings")
                    await self.update_listings_now()

    async def update_listings_now(self):
        """Update listings immediately (used by event handlers)"""
        # Get the guild
        guild = self.bot.get_guild(config.SERVER_ID)
        if not guild:
            logger.error("Could not find guild for staff listings update")
            return

        # Clear previous permission errors
        self.permission_errors.clear()

        # Update high staff listings
        await self.update_high_staff_listings(guild)

        # Update department-specific listings
        await self.update_department_listings(guild)

        # Log any permission errors - reuse the same logic as the task
        if self.permission_errors:
            # Map channel IDs to names for better logging
            channel_names = {}
            for channel_id in self.permission_errors:
                channel = guild.get_channel(channel_id)
                if channel:
                    channel_names[channel_id] = channel.name

            # Log with consolidated format
            error_channels_text = ", ".join([
                f"{get_dept_for_channel(channel_id)}: #{channel_names.get(channel_id, str(channel_id))}"
                for channel_id in self.permission_errors
            ])
            logger.warning(
                f"Staff listings update: Missing permissions in channels: {error_channels_text}")

            # Try to notify in log channel
            if config.FEATURES['LOGGING'] and config.LOG_CHANNEL_ID:
                try:
                    log_channel = guild.get_channel(config.LOG_CHANNEL_ID)
                    if log_channel and log_channel.id not in self.permission_errors:
                        # Use channel mentions in the Discord message, better for admins
                        channel_mentions = ", ".join(
                            [f"<#{channel_id}>" for channel_id in self.permission_errors])
                        await log_channel.send(
                            f"⚠️ Staff listings could not be updated in some channels due to missing permissions: {channel_mentions}\n"
                            f"Please ensure the bot has the following permissions in these channels:\n"
                            f"- View Channel\n"
                            f"- Read Message History\n"
                            f"- Send Messages\n"
                            f"- Manage Messages (to clean up old listings)"
                        )
                except Exception as e:
                    logger.error(
                        f"Could not send permission error notification: {e}")
        else:
            logger.info("Staff listings updated successfully")


# Helper function to get department name for a channel ID
def get_dept_for_channel(channel_id):
    """Get the department name for a channel ID"""
    return utils_get_dept_for_channel(
        channel_id,
        config.HIGH_STAFF_LISTING_CHANNEL_ID,
        config.DEPARTMENTS
    )


def setup(bot):
    bot.add_cog(StaffListings(bot))
