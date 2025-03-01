# Database System Documentation

This document explains how to use the database system in the Discord Bot.

## Overview

The bot uses SQLite with an asynchronous wrapper (`aiosqlite`) for database operations. This provides:

- Persistent storage across bot restarts
- Support for multiple servers/guilds
- Easy-to-use API for CRUD operations
- Model system for organizing data

## Basic Usage

### Getting a Database Connection

```python
from data.database import get_db

async def my_function():
    db = await get_db()
    # Now use the db object for queries
```

### Direct Query Methods

The database manager provides these methods:

- `execute(query, parameters)` - Run a query without returning results (INSERT, UPDATE, DELETE)
- `execute_many(query, parameters_list)` - Run many similar queries at once
- `fetchone(query, parameters)` - Get a single result as a dictionary
- `fetchall(query, parameters)` - Get all results as a list of dictionaries

## Creating and Using Models

Models provide an organized way to work with specific database tables.

### Creating a New Model

To create a new model for a feature:

1. **Create a new file** in `data/models/` for your model (e.g., `data/models/reminder_model.py`)
2. **Extend the BaseModel class** from `data.base_model`
3. **Define your schema** using the SCHEMA dictionary
4. **Add model-specific methods** to interact with your data
5. **Register your model** in `data/database.py` in the `init_models()` function

Here's a complete example of creating a reminder feature:

#### 1. Create the model file: `data/models/reminder_model.py`

```python
from data.base_model import BaseModel
import time

class Reminder(BaseModel):
    """Model for storing user reminders."""

    TABLE_NAME = "reminders"
    PRIMARY_KEY = "id"

    SCHEMA = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "guild_id": "INTEGER NOT NULL",
        "user_id": "INTEGER NOT NULL",
        "reminder_text": "TEXT NOT NULL",
        "remind_at": "INTEGER NOT NULL",
        "created_at": "INTEGER NOT NULL"
    }

    @classmethod
    async def create_reminder(cls, guild_id, user_id, text, remind_at_timestamp):
        """Create a new reminder.

        Args:
            guild_id: Discord server ID
            user_id: Discord user ID
            text: Reminder message
            remind_at_timestamp: Unix timestamp for when to send reminder

        Returns:
            The ID of the created reminder
        """
        current_time = int(time.time())
        data = {
            "guild_id": guild_id,
            "user_id": user_id,
            "reminder_text": text,
            "remind_at": remind_at_timestamp,
            "created_at": current_time
        }

        await cls.create(data)

        # Get the ID of the newly created reminder
        db = await get_db()
        result = await db.fetchone(
            f"SELECT last_insert_rowid() as id FROM {cls.TABLE_NAME}"
        )
        return result["id"]

    @classmethod
    async def get_pending_reminders(cls, current_time=None):
        """Get all reminders that are due.

        Args:
            current_time: Current unix timestamp, defaults to now

        Returns:
            List of due reminder dictionaries
        """
        if current_time is None:
            current_time = int(time.time())

        db = await get_db()
        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        WHERE remind_at <= ?
        ORDER BY remind_at ASC
        """
        return await db.fetchall(query, (current_time,))

    @classmethod
    async def delete_reminder(cls, reminder_id):
        """Delete a reminder by ID.

        Args:
            reminder_id: The ID of the reminder to delete
        """
        await cls.delete(reminder_id)

    @classmethod
    async def get_user_reminders(cls, user_id):
        """Get all reminders for a specific user.

        Args:
            user_id: Discord user ID

        Returns:
            List of reminder dictionaries
        """
        return await cls.find({"user_id": user_id})
```

#### 2. Register your model in `data/database.py`

```python
async def init_models() -> None:
    """Initialize all database models."""
    # Import models here to avoid circular imports
    from data.models.reminder_model import Reminder

    # Initialize model tables
    await Reminder.create_table()

    logger.info("Database models initialized")
```

#### 3. Create a cog to use your model: `cogs/reminders.py`

```python
import disnake
from disnake.ext import commands, tasks
import datetime
import time

from data.models.reminder_model import Reminder

class Reminders(commands.Cog):
    """Set reminders for yourself or others"""

    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        """Check for due reminders every 30 seconds"""
        current_time = int(time.time())
        due_reminders = await Reminder.get_pending_reminders(current_time)

        for reminder in due_reminders:
            try:
                # Get the user and guild
                guild = self.bot.get_guild(reminder["guild_id"])
                if not guild:
                    continue

                user = guild.get_member(reminder["user_id"])
                if not user:
                    continue

                # Send the reminder
                embed = disnake.Embed(
                    title="Reminder",
                    description=reminder["reminder_text"],
                    color=disnake.Color.blue()
                )
                embed.set_footer(text=f"Reminder set on {datetime.datetime.fromtimestamp(reminder['created_at'])}")

                try:
                    await user.send(embed=embed)
                except:
                    # If we can't DM, try to find a common channel
                    for channel in guild.text_channels:
                        if channel.permissions_for(guild.me).send_messages and channel.permissions_for(user).read_messages:
                            await channel.send(f"{user.mention} I have a reminder for you:", embed=embed)
                            break

                # Delete the reminder after sending
                await Reminder.delete_reminder(reminder["id"])

            except Exception as e:
                print(f"Error processing reminder {reminder['id']}: {e}")

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()

    @commands.slash_command()
    async def remind(
        self,
        inter,
        time: str = commands.Param(description="Time format: 1h30m, 2d, etc."),
        reminder: str = commands.Param(description="What to remind you about")
    ):
        """Set a reminder for yourself"""
        seconds = parse_time(time)

        if seconds <= 0:
            return await inter.response.send_message("Invalid time format. Use 1h30m, 2d, etc.", ephemeral=True)

        remind_at = int(datetime.datetime.now().timestamp() + seconds)

        # Create the reminder
        reminder_id = await Reminder.create_reminder(
            inter.guild.id,
            inter.author.id,
            reminder,
            remind_at
        )

        # Send confirmation
        remind_time = datetime.datetime.fromtimestamp(remind_at)
        await inter.response.send_message(
            f"✅ I'll remind you about: **{reminder}**\nTime: {remind_time.strftime('%Y-%m-%d %H:%M:%S')}",
            ephemeral=True
        )

    @commands.slash_command()
    async def reminders(self, inter):
        """List all your active reminders"""
        user_reminders = await Reminder.get_user_reminders(inter.author.id)

        if not user_reminders:
            return await inter.response.send_message("You don't have any active reminders.", ephemeral=True)

        embed = disnake.Embed(
            title="Your Reminders",
            color=disnake.Color.blue()
        )

        for reminder in user_reminders:
            remind_time = datetime.datetime.fromtimestamp(reminder["remind_at"])
            embed.add_field(
                name=f"ID: {reminder['id']} - {remind_time.strftime('%Y-%m-%d %H:%M:%S')}",
                value=reminder["reminder_text"][:1024],
                inline=False
            )

        await inter.response.send_message(embed=embed, ephemeral=True)

    @commands.slash_command()
    async def cancel_reminder(
        self,
        inter,
        reminder_id: int = commands.Param(description="ID of the reminder to cancel")
    ):
        """Cancel a specific reminder"""
        # Check if the reminder exists and belongs to the user
        reminder = await Reminder.get_by_id(reminder_id)

        if not reminder or reminder["user_id"] != inter.author.id:
            return await inter.response.send_message("Reminder not found or doesn't belong to you.", ephemeral=True)

        await Reminder.delete_reminder(reminder_id)
        await inter.response.send_message(f"✅ Reminder #{reminder_id} canceled.", ephemeral=True)

# Helper function to parse time strings like "1h30m"
def parse_time(time_str):
    total_seconds = 0
    current_num = ""

    for char in time_str.lower():
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

def setup(bot):
    bot.add_cog(Reminders(bot))
```

### Model Design Best Practices

When creating database models for your bot:

1. **Define clear responsibilities** - Each model should handle a specific type of data
2. **Use descriptive column names** - Make your schema self-documenting
3. **Include validation** - Validate data before saving to the database
4. **Implement convenience methods** - Add methods for common operations
5. **Consider relationships** - Think about how models relate to each other
6. **Add comments** - Document complex logic within your model

### Using the BaseModel Class Effectively

The BaseModel class provides these core methods:

- `create_table()` - Creates the table from your SCHEMA
- `get_by_id(id_value)` - Retrieves a record by its primary key
- `get_all()` - Gets all records from the table
- `create(data)` - Inserts a new record
- `update(id_value, data)` - Updates an existing record
- `delete(id_value)` - Deletes a record
- `find(conditions)` - Finds records matching specific conditions

Extend these with your own model-specific methods to create a clean API for your feature.

## Transactions

For operations that involve multiple database changes, use transactions to ensure data integrity:

```python
db = await get_db()
conn = await db._get_connection()

try:
    await conn.execute("BEGIN TRANSACTION")

    # Multiple database operations...
    await conn.execute("INSERT INTO table1 VALUES (?, ?)", values1)
    await conn.execute("UPDATE table2 SET column = ? WHERE id = ?", values2)

    await conn.execute("COMMIT")
except Exception as e:
    await conn.execute("ROLLBACK")
    raise e
```

## Troubleshooting

If you encounter database issues:

- **Check logs**: Most database errors are logged
- **Validate input**: Ensure data being saved matches expected format
- **Check constraints**: Unique constraints might prevent inserts
- **File permissions**: Ensure bot has write access to database file

For more complex database implementations, consider reviewing the SQLite documentation and the aiosqlite package documentation.
