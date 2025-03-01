# brian-discord-bot/data/models.py

from typing import Any, Dict, List, Optional
import logging
from data.database import get_db

logger = logging.getLogger('discord_bot')

class BaseModel:
    """Base model class for database operations.
    
    This provides common operations for database models and should be
    subclassed by specific feature models.
    """
    
    # Table name - must be set by subclasses
    TABLE_NAME = None
    
    # Primary key column name - can be overridden by subclasses
    PRIMARY_KEY = "id"
    
    # Schema definition - must be set by subclasses
    # Format: {"column_name": "column_type [constraints]"}
    SCHEMA = {}
    
    @classmethod
    async def create_table(cls) -> None:
        """Create the table if it doesn't exist."""
        if cls.TABLE_NAME is None or not cls.SCHEMA:
            raise NotImplementedError("Model must define TABLE_NAME and SCHEMA")
        
        db = await get_db()
        
        # Build the schema from the SCHEMA dict
        columns = []
        for column_name, column_def in cls.SCHEMA.items():
            columns.append(f"{column_name} {column_def}")
        
        query = f"""
        CREATE TABLE IF NOT EXISTS {cls.TABLE_NAME} (
            {", ".join(columns)}
        )
        """
        
        await db.execute(query)
        logger.debug(f"Created table: {cls.TABLE_NAME}")
    
    @classmethod
    async def get_by_id(cls, id_value: Any) -> Optional[Dict[str, Any]]:
        """Get a record by its primary key.
        
        Args:
            id_value: The primary key value to look up
            
        Returns:
            Dict containing the record, or None if not found
        """
        db = await get_db()
        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        WHERE {cls.PRIMARY_KEY} = ?
        """
        return await db.fetchone(query, (id_value,))
    
    @classmethod
    async def get_all(cls) -> List[Dict[str, Any]]:
        """Get all records from the table.
        
        Returns:
            List of dictionaries containing all records
        """
        db = await get_db()
        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        """
        return await db.fetchall(query)
    
    @classmethod
    async def create(cls, data: Dict[str, Any]) -> None:
        """Insert a new record.
        
        Args:
            data: Dictionary of column_name: value pairs
        """
        db = await get_db()
        
        columns = list(data.keys())
        placeholders = ", ".join(["?"] * len(columns))
        values = tuple(data.values())
        
        query = f"""
        INSERT INTO {cls.TABLE_NAME} ({", ".join(columns)})
        VALUES ({placeholders})
        """
        
        await db.execute(query, values)
    
    @classmethod
    async def update(cls, id_value: Any, data: Dict[str, Any]) -> None:
        """Update a record by its primary key.
        
        Args:
            id_value: The primary key value to update
            data: Dictionary of column_name: value pairs to update
        """
        db = await get_db()
        
        set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
        values = tuple(data.values()) + (id_value,)
        
        query = f"""
        UPDATE {cls.TABLE_NAME}
        SET {set_clause}
        WHERE {cls.PRIMARY_KEY} = ?
        """
        
        await db.execute(query, values)
    
    @classmethod
    async def delete(cls, id_value: Any) -> None:
        """Delete a record by its primary key.
        
        Args:
            id_value: The primary key value to delete
        """
        db = await get_db()
        query = f"""
        DELETE FROM {cls.TABLE_NAME}
        WHERE {cls.PRIMARY_KEY} = ?
        """
        await db.execute(query, (id_value,))
    
    @classmethod
    async def find(cls, conditions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find records that match specific conditions.
        
        Args:
            conditions: Dictionary of column_name: value pairs to match
            
        Returns:
            List of matching records
        """
        db = await get_db()
        
        where_clauses = " AND ".join([f"{key} = ?" for key in conditions.keys()])
        values = tuple(conditions.values())
        
        query = f"""
        SELECT * FROM {cls.TABLE_NAME}
        WHERE {where_clauses}
        """
        
        return await db.fetchall(query, values)
