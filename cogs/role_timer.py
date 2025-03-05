# cogs/role_timer.py
import disnake
from disnake.ext import commands, tasks
import logging
import time
import datetime
from datetime import datetime, time
from data.models.timed_role_model import TimedRole
from utils.role_timers import format_duration, parse_duration
import config

logger = logging.getLogger('discord_bot')


class RoleTimer(commands.Cog):
    """Role timer system to assign temporary roles"""

    def __init__(self, bot):
        self.bot = bot
        # Don't start the task immediately - we'll start it properly in on_ready
        self.daily_check_task = None

    def cog_unload(self):
        self.check_timed_roles.cancel()

    @tasks.loop(minutes=30)  # Run every 30 minutes
    async def role_check_task(self):
        """Check for and process expired timed roles"""
        logger.info("Running scheduled timed roles check")
        await self.check_timed_roles()

    @role_check_task.before_loop
    async def before_role_check_task(self):
        """Wait until the bot is ready before starting the task"""
        await self.bot.wait_until_ready()
        logger.info("Starting role check task loop (checking every 30 minutes)")

    async def check_timed_roles(self):
        """Check for and process expired timed roles"""
        try:
            current_time = int(time.time())  # Using the time module

            # Get all timed roles (both expired and active)
            from data.database import get_db
            db = await get_db()
            query = f"""
            SELECT * FROM {TimedRole.TABLE_NAME}
            """
            all_timed_roles = await db.fetchall(query)

            expired_roles = [
                r for r in all_timed_roles if r["expires_at"] <= current_time]
            logger.info(f"Found {len(expired_roles)} expired timed roles")

            # Also check for roles that might have been manually removed
            active_roles = [
                r for r in all_timed_roles if r["expires_at"] > current_time]
            logger.info(
                f"Checking {len(active_roles)} active timed roles for manual removal")

            # Process expired roles
            for record in expired_roles:
                await self._process_expired_role(record)

            # Check for manually removed roles
            for record in active_roles:
                # Get the guild, member, and role
                guild = self.bot.get_guild(record["guild_id"])
                if not guild:
                    continue  # Skip if guild not found

                member = guild.get_member(record["user_id"])
                if not member:
                    continue  # Skip if member not found

                role = guild.get_role(record["role_id"])
                if not role:
                    # Role doesn't exist anymore, remove from tracking
                    logger.info(
                        f"Role {record['role_id']} no longer exists, removing timed role record")
                    await TimedRole.remove_timed_role(record["id"])
                    continue

                # Check if the role has been manually removed
                if role not in member.roles:
                    logger.info(
                        f"Role {role.name} has been manually removed from {member.display_name}, removing timed role record")
                    await TimedRole.remove_timed_role(record["id"])

        except Exception as e:
            logger.error(
                f"Error in check_timed_roles task: {e}", exc_info=True)

    async def _process_expired_role(self, record):
        """Process a single expired role record"""
        try:
            # Get the guild, member, and role
            guild = self.bot.get_guild(record["guild_id"])
            if not guild:
                logger.warning(
                    f"Guild {record['guild_id']} not found for timed role {record['id']}")
                await TimedRole.remove_timed_role(record["id"])
                return

            member = guild.get_member(record["user_id"])
            role = guild.get_role(record["role_id"])

            # Skip if member no longer in guild
            if not member:
                logger.info(
                    f"Member {record['user_id']} no longer in guild, removing timed role {record['id']}")
                await TimedRole.remove_timed_role(record["id"])
                return

            # Skip if role no longer exists
            if not role:
                logger.warning(
                    f"Role {record['role_id']} no longer exists, removing timed role {record['id']}")
                await TimedRole.remove_timed_role(record["id"])
                return

            # Check if the role is actually assigned to the member
            has_role = role in member.roles

            # Remove the role if auto_remove is enabled and they still have it
            if record["auto_remove"] and has_role:
                try:
                    await member.remove_roles(role, reason="Timed role expired")
                    logger.info(
                        f"Removed timed role {role.name} from {member.display_name}")
                except disnake.Forbidden:
                    logger.error(
                        f"Forbidden: Unable to remove {role.name} from {member.display_name}")
                    # Continue processing even if role removal fails

            # Notify the user if enabled
            if record["notify_user"]:
                try:
                    embed = disnake.Embed(
                        title="Role Expired",
                        description=f"Your role **{role.name}** has " +
                        ("been removed." if record["auto_remove"] and has_role
                         else "expired."),
                        color=config.INFO_COLOR
                    )

                    if record["reason"]:
                        embed.add_field(name="Reason", value=record["reason"])

                    await member.send(embed=embed)
                    logger.info(
                        f"Successfully notified {member.display_name} about expired role {role.name}")
                except disnake.Forbidden:
                    logger.warning(
                        f"Cannot DM user {member.display_name} ({member.id}) about expired role: DMs closed")
                    # If we have a notification channel, add a note about failed DM there
                    if record["notify_channel_id"]:
                        try:
                            channel = guild.get_channel(
                                record["notify_channel_id"])
                            if channel and channel.permissions_for(guild.me).send_messages:
                                await channel.send(f"⚠️ Note: Could not send DM to {member.mention} about role expiration.")
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning(
                        f"Failed to notify user {member.id} about expired role: {e}")

            # Notify channel if specified
            if record["notify_channel_id"]:
                await self._send_expiry_notification(guild, member, role, record, has_role)

            # Remove the record from the database
            await TimedRole.remove_timed_role(record["id"])

        except Exception as e:
            logger.error(
                f"Error processing timed role {record['id']}: {e}", exc_info=True)

    async def _send_expiry_notification(self, guild, member, role, record, has_role):
        """Send a notification to the configured channel about role expiry"""
        try:
            channel = guild.get_channel(record["notify_channel_id"])
            if not channel or not channel.permissions_for(guild.me).send_messages:
                return

            # Prepare mentions
            mentions = []

            # Add role mentions
            if record["notify_role_ids"]:
                role_ids = [int(id)
                            for id in record["notify_role_ids"].split(",")]
                for role_id in role_ids:
                    notify_role = guild.get_role(role_id)
                    if notify_role:
                        mentions.append(notify_role.mention)

            # Create notification embed
            removed_text = ""
            if record["auto_remove"]:
                if has_role:
                    removed_text = "and has been removed"
                else:
                    removed_text = "but was already manually removed"

            embed = disnake.Embed(
                title="Timed Role Expired",
                description=f"Role **{role.name}** for {member.mention} has expired {removed_text}.",
                color=config.INFO_COLOR,
                timestamp=datetime.now()
            )

            if record["reason"]:
                embed.add_field(name="Reason", value=record["reason"])

            # Get the name of who added the role
            added_by_member = guild.get_member(record["added_by"])
            added_by_name = added_by_member.display_name if added_by_member else f"User ID: {record['added_by']}"
            embed.add_field(name="Added By", value=added_by_name)

            # Send the notification
            content = " ".join(mentions) if mentions else None
            await channel.send(content=content, embed=embed)
        except Exception as e:
            logger.error(
                f"Error sending expiry notification: {e}", exc_info=True)

    @commands.slash_command()
    async def timedrole(self, inter):
        """Base command for timed role management"""
        pass

    @timedrole.sub_command()
    async def list(
        self,
        inter,
        member: disnake.Member = commands.Param(
            description="Member to check timed roles for")
    ):
        """List all active timed roles for a member"""
        await inter.response.defer(ephemeral=True)

        try:
            from utils.role_timers import list_active_timed_roles

            active_roles = await list_active_timed_roles(member)

            if not active_roles:
                return await inter.edit_original_message(content=f"{member.display_name} has no active timed roles.")

            # Create embed
            embed = disnake.Embed(
                title=f"Timed Roles for {member.display_name}",
                description=f"Found {len(active_roles)} active timed role(s)",
                color=config.INFO_COLOR
            )

            for role in active_roles:
                # Try to get who added the role
                added_by_member = inter.guild.get_member(role["added_by"])
                added_by_name = added_by_member.display_name if added_by_member else f"User ID: {role['added_by']}"

                value = f"**Expires:** {role['expires_at_formatted']}\n"
                value += f"**Time Remaining:** {role['time_remaining']}\n"
                value += f"**Added By:** {added_by_name}\n"

                if role["reason"]:
                    value += f"**Reason:** {role['reason']}\n"

                embed.add_field(
                    name=role["role_name"],
                    value=value,
                    inline=False
                )

            await inter.edit_original_message(embed=embed)

        except Exception as e:
            logger.error(f"Error listing timed roles: {e}", exc_info=True)
            await inter.edit_original_message(content=f"An error occurred: {str(e)}")

    @timedrole.sub_command()
    async def check_expired(self, inter):
        """Manually check for and process expired timed roles (Admin only)"""
        # Check permissions
        if not inter.author.guild_permissions.administrator and inter.author.id not in config.OWNER_IDS:
            return await inter.response.send_message("You don't have permission to run this command.", ephemeral=True)

        await inter.response.defer(ephemeral=True)

        try:
            # Run the check
            start_time = time.time()  # From the time module
            await self.check_timed_roles()
            elapsed = time.time() - start_time

            await inter.edit_original_message(content=f"✅ Expired timed roles check completed in {elapsed:.2f} seconds.")
        except Exception as e:
            logger.error(f"Error in manual check: {e}", exc_info=True)
            await inter.edit_original_message(content=f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(RoleTimer(bot))
