# brian-discord-bot/data/database.py

import aiosqlite
import os
import logging
import asyncio
from typing import Any, Dict, List, Optional

logger = logging.getLogger('discord_bot')


class Database:
    """Asynchronous SQLite database manager for the Discord bot."""

    def __init__(self, db_path: str = "data/bot.db"):
        """Initialize the database connection.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._connection: Optional[aiosqlite.Connection] = None
        self._setup_lock = asyncio.Lock()

        # Ensure the directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def _get_connection(self) -> aiosqlite.Connection:
        """Get the database connection, creating it if necessary."""
        if self._connection is None:
            self._connection = await aiosqlite.connect(self.db_path)
            # Enable foreign keys
            await self._connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self._connection.row_factory = aiosqlite.Row

        return self._connection

    async def close(self) -> None:
        """Close the database connection."""
        if self._connection is not None:
            await self._connection.close()
            self._connection = None

    async def execute(self, query: str, parameters: tuple = ()) -> None:
        """Execute a query without returning results.

        Args:
            query: SQL query to execute
            parameters: Parameters to use with the query
        """
        conn = await self._get_connection()
        try:
            await conn.execute(query, parameters)
            await conn.commit()
        except Exception as e:
            logger.error(f"Database execute error: {e} - Query: {query}")
            raise

    async def execute_many(self, query: str, parameters_list: List[tuple]) -> None:
        """Execute a query multiple times with different parameters.

        Args:
            query: SQL query to execute
            parameters_list: List of parameter tuples to use with the query
        """
        conn = await self._get_connection()
        try:
            await conn.executemany(query, parameters_list)
            await conn.commit()
        except Exception as e:
            logger.error(f"Database executemany error: {e} - Query: {query}")
            raise

    async def fetchone(self, query: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute a query and fetch one result.

        Args:
            query: SQL query to execute
            parameters: Parameters to use with the query

        Returns:
            A dictionary containing the row data, or None if no results
        """
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(query, parameters)
            row = await cursor.fetchone()
            await cursor.close()

            if row is None:
                return None

            return dict(row)
        except Exception as e:
            logger.error(f"Database fetchone error: {e} - Query: {query}")
            raise

    async def fetchall(self, query: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and fetch all results.

        Args:
            query: SQL query to execute
            parameters: Parameters to use with the query

        Returns:
            A list of dictionaries containing the row data
        """
        conn = await self._get_connection()
        try:
            cursor = await conn.execute(query, parameters)
            rows = await cursor.fetchall()
            await cursor.close()

            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Database fetchall error: {e} - Query: {query}")
            raise

    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name: Name of the table to check

        Returns:
            True if the table exists, False otherwise
        """
        query = """
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """
        result = await self.fetchone(query, (table_name,))
        return result is not None

    async def create_tables(self) -> None:
        """Create all database tables if they don't exist."""
        async with self._setup_lock:
            # Core tables common to multiple features
            # Add more core tables as needed
            pass


# Global database instance
_db: Optional[Database] = None


async def get_db() -> Database:
    """Get or create the global database instance.

    Returns:
        The global Database instance
    """
    global _db
    if _db is None:
        _db = Database()
        await _db.create_tables()
    return _db

# Helper function to initialize the database


async def init_db() -> None:
    """Initialize the database and create tables."""
    db = await get_db()
    await db.create_tables()

    # Initialize models
    await init_models()

    logger.info("Database initialized")


async def init_models() -> None:
    """Initialize all database models.

    This function imports and initializes all model tables.
    Add new models here as they are created.
    """
    # Import models here to avoid circular imports
    from data.models.timed_role_model import TimedRole

    # Initialize model tables
    await TimedRole.create_table()

    # Add more models as needed
    # await SomeOtherModel.create_table()

    logger.info("Database models initialized")
