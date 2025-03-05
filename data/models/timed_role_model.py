# data/models/timed_role_model.py
from data.base_model import BaseModel
import time


class TimedRole(BaseModel):
    """Model for storing timed role assignments."""

    TABLE_NAME = "timed_roles"
    PRIMARY_KEY = "id"

    SCHEMA = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "guild_id": "INTEGER NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "role_id": "INTEGER NOT NULL",
        "expires_at": "INTEGER NOT NULL",
        "added_by": "INTEGER NOT NULL",
        "reason": "TEXT",
        "auto_remove": "INTEGER DEFAULT 1",  # 1 = true, 0 = false
        "notify_user": "INTEGER DEFAULT 1",
        "notify_channel_id": "INTEGER",
        "notify_role_ids": "TEXT"  # Comma-separated list of role IDs to notify
    }

    @classmethod
    async def add_timed_role(cls, guild_id, user_id, role_id, duration_seconds, added_by,
                             reason=None, auto_remove=True, notify_user=True,
                             notify_channel_id=None, notify_role_ids=None):
        """Add a timed role to a user.

        Args:
            guild_id: Discord server ID
            user_id: User to assign role to
            role_id: Role ID to assign
            duration_seconds: How long to keep the role (in seconds)
            added_by: User ID who added the role
            reason: Optional reason for the timed role
            auto_remove: Whether to automatically remove the role when it expires
            notify_user: Whether to notify the user when role expires
            notify_channel_id: Channel ID to send notification when role expires
            notify_role_ids: List of role IDs to ping when role expires

        Returns:
            ID of the created timed role record
        """
        expires_at = int(time.time() + duration_seconds)

        # Convert list of role IDs to comma-separated string
        notify_roles_str = None
        if notify_role_ids:
            notify_roles_str = ",".join(str(role_id)
                                        for role_id in notify_role_ids)

        data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "role_id": role_id,
            "expires_at": expires_at,
            "added_by": added_by,
            "reason": reason,
            "auto_remove": 1 if auto_remove else 0,
            "notify_user": 1 if notify_user else 0,
            "notify_channel_id": notify_channel_id,
            "notify_role_ids": notify_roles_str
        }

        await cls.create(data)

        # Get the ID of the newly created record
        from data.database import get_db
        db = await get_db()
        result = await db.fetchone(
            f"SELECT last_insert_rowid() as id FROM {cls.TABLE_NAME}"
        )
        return result["id"]

    @classmethod
    async def get_expired_roles(cls, current_time=None):
        """Get all timed roles that have expired.

        Args:
            current_time: Current time timestamp (defaults to now)

        Returns:
            List of expired timed role records
        """
        if current_time is None:
            current_time = int(time.time())

        from data.database import get_db
        db = await get_db()
        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        WHERE expires_at <= ?
        """
        return await db.fetchall(query, (current_time,))

    @classmethod
    async def get_active_roles_for_user(cls, user_id):
        """Get all active timed roles for a user.

        Args:
            user_id: Discord user ID

        Returns:
            List of active timed role records
        """
        from data.database import get_db
        db = await get_db()
        current_time = int(time.time())

        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        WHERE user_id = ? AND expires_at > ?
        ORDER BY expires_at ASC
        """
        return await db.fetchall(query, (user_id, current_time))

    @classmethod
    async def remove_timed_role(cls, timed_role_id):
        """Remove a timed role record.

        Args:
            timed_role_id: ID of the timed role record to remove
        """
        await cls.delete(timed_role_id)
