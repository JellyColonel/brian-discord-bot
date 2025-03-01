# Database System Documentation

This document explains how to use the database system in the Majestic Discord Bot.

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

## Using Models

Models provide an organized way to work with specific tables.

### Using Existing Models

Each model has its own methods. For example, the Tag model:

```python
from utils.tag_model import Tag

async def example():
    # Create a tag
    await Tag.create_tag(guild_id, "greeting", "Hello everyone!", creator_id)

    # Get a tag
    tag = await Tag.get_by_name(guild_id, "greeting")

    # Delete a tag
    await Tag.delete_tag(guild_id, "outdated_tag")
```

### Creating New Models

To create a new model for a feature:

1. Create a new file in `data/models/` for your model (e.g., `data/models//reminder_model.py`)
2. Extend the BaseModel class
3. Add your model to `data/database.py` in the `init_models()` function

Example model:

```python
from data.base_model import BaseModel

class Reminder(BaseModel):
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
    async def create_reminder(cls, guild_id, user_id, text, remind_at):
        # Your implementation here
        pass

    # Add more methods as needed
```

Then update `data/database.py`:

```python
async def init_models() -> None:
    # Import models
    from data.models.tag_model import Tag
    from data.models.reminder_model import Reminder  # Add your model here

    # Initialize model tables
    await Tag.create_table()
    await Reminder.create_table()  # Add your model here
```

## Best Practices

1. **Use Models**: Create a model for each major feature that needs data persistence
2. **Keep Queries Simple**: Structure your data well to avoid complex queries
3. **Error Handling**: Always handle potential database errors
4. **Transactions**: For multiple related operations, use transactions
5. **Migration Plan**: If changing table schemas, implement a migration strategy

## Example: Creating a New Feature with Database Support

Let's walk through adding a new feature that uses the database:

1. **Define Your Data Model**:

   - Create `data/models/poll_model.py` for a poll system
   - Define the schema and required methods

2. **Register the Model**:

   - Add it to `init_models()` in `database.py`

3. **Create a Cog**:

   - Create `cogs/polls.py` that uses your model
   - Implement commands to interact with polls

4. **Test Thoroughly**:
   - Test creation, retrieval, updates, and edge cases

## Troubleshooting

If you encounter database issues:

- **Check logs**: Most database errors are logged
- **Validate input**: Ensure data being saved matches expected format
- **Check constraints**: Unique constraints might prevent inserts
- **File permissions**: Ensure bot has write access to database file

For more complex database implementations, consider reviewing the SQLite documentation and the aiosqlite package documentation.
