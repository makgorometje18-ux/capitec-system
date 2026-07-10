"""
Database Module - Handles SQLite database operations.
"""

import sqlite3
from pathlib import Path
from typing import Any, List, Optional, Tuple
from datetime import datetime

from src.utils.logger import get_logger


class Database:
    """
    Manages SQLite database operations for the application.
    
    Provides methods to execute queries, manage connections,
    and initialize the database schema.
    """

    def __init__(self, db_path: str = 'database/cdrs.db') -> None:
        """
        Initialize the database connection.
        
        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self.logger = get_logger()
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize()

    def _initialize(self) -> None:
        """
        Initialize the database.
        
        Creates the database directory if it doesn't exist
        and initializes the schema.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connect()
        self._initialize_schema()

    def connect(self) -> None:
        """
        Connect to the SQLite database.
        
        Creates a new connection if one doesn't exist.
        """
        try:
            if self.connection is None:
                self.connection = sqlite3.connect(str(self.db_path))
                self.connection.row_factory = sqlite3.Row
                # Enable foreign keys
                self.connection.execute("PRAGMA foreign_keys = ON")
                self.logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            raise

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("Database connection closed")

    def _initialize_schema(self) -> None:
        """Initialize database schema from schema.sql."""
        schema_path = Path('database/schema.sql')
        
        if not schema_path.exists():
            self.logger.warning(f"Schema file not found: {schema_path}")
            return
        
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            cursor = self.connection.cursor()
            cursor.executescript(schema_sql)
            self.connection.commit()
            self.logger.info("Database schema initialized successfully")
        except sqlite3.Error as e:
            self.logger.error(f"Error initializing schema: {e}")
            raise

    def execute(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Execute a SQL query without returning results.
        
        Args:
            query: SQL query to execute.
            params: Query parameters.
        """
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            self.logger.debug(f"Query executed: {query}")
        except sqlite3.Error as e:
            self.logger.error(f"Query execution error: {e}")
            self.connection.rollback()
            raise

    def query(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> List[Tuple[Any, ...]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            query: SQL SELECT query.
            params: Query parameters.
            
        Returns:
            List of result tuples.
        """
        if not self.connection:
            raise RuntimeError("Database connection not established")
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            self.logger.debug(f"Query executed, {len(results)} rows returned")
            return results
        except sqlite3.Error as e:
            self.logger.error(f"Query execution error: {e}")
            raise

    def query_one(self, query: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Tuple[Any, ...]]:
        """
        Execute a SELECT query and return a single result.
        
        Args:
            query: SQL SELECT query.
            params: Query parameters.
            
        Returns:
            Single result tuple or None if not found.
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except sqlite3.Error as e:
            self.logger.error(f"Query execution error: {e}")
            raise

    def insert(self, table: str, data: dict) -> int:
        """
        Insert a row into a table.
        
        Args:
            table: Table name.
            data: Dictionary of column names and values.
            
        Returns:
            ID of the inserted row.
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(data.values()))
            self.connection.commit()
            self.logger.debug(f"Row inserted into {table}")
            return cursor.lastrowid
        except sqlite3.Error as e:
            self.logger.error(f"Insert error: {e}")
            self.connection.rollback()
            raise

    def update(self, table: str, data: dict, where: str, where_params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Update rows in a table.
        
        Args:
            table: Table name.
            data: Dictionary of columns to update.
            where: WHERE clause (without WHERE keyword).
            where_params: Parameters for WHERE clause.
        """
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(data.values())
        if where_params:
            params = params + where_params
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            self.connection.commit()
            self.logger.debug(f"Rows updated in {table}")
        except sqlite3.Error as e:
            self.logger.error(f"Update error: {e}")
            self.connection.rollback()
            raise

    def delete(self, table: str, where: str, where_params: Optional[Tuple[Any, ...]] = None) -> None:
        """
        Delete rows from a table.
        
        Args:
            table: Table name.
            where: WHERE clause (without WHERE keyword).
            where_params: Parameters for WHERE clause.
        """
        query = f"DELETE FROM {table} WHERE {where}"
        
        try:
            cursor = self.connection.cursor()
            if where_params:
                cursor.execute(query, where_params)
            else:
                cursor.execute(query)
            self.connection.commit()
            self.logger.debug(f"Rows deleted from {table}")
        except sqlite3.Error as e:
            self.logger.error(f"Delete error: {e}")
            self.connection.rollback()
            raise

    def close(self) -> None:
        """Close the database connection."""
        self.disconnect()


# Global database instance
_db_instance: Optional[Database] = None


def get_database() -> Database:
    """
    Get the global database instance.
    
    Returns:
        Database: The database instance.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance
