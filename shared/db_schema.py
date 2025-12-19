"""Database schema and connection management for qwen-agent-scheduler

This module defines the PostgreSQL schema and provides utilities
for database connection and initialization.
"""

import logging
from typing import Optional
import psycopg2
from psycopg2 import pool, sql
from psycopg2.extras import RealDictCursor

from .models import DatabaseConfig

logger = logging.getLogger(__name__)


# SQL for creating the registered_methods table
CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS registered_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    parameters_json JSONB NOT NULL,
    return_type VARCHAR(50) NOT NULL,
    module_path VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

# SQL for creating indexes
CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_method_name ON registered_methods(name);",
    "CREATE INDEX IF NOT EXISTS idx_updated_at ON registered_methods(updated_at);"
]

# SQL for creating the trigger function
CREATE_TRIGGER_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
"""

# SQL for creating the trigger
CREATE_TRIGGER_SQL = """
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'update_registered_methods_updated_at'
    ) THEN
        CREATE TRIGGER update_registered_methods_updated_at 
            BEFORE UPDATE ON registered_methods 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END
$$;
"""


class DatabaseConnection:
    """Manages PostgreSQL database connections and schema initialization
    
    This class provides connection pooling and schema management utilities.
    """
    
    def __init__(self, config: DatabaseConfig):
        """Initialize database connection manager
        
        Args:
            config: Database configuration
        """
        self.config = config
        self._pool: Optional[pool.SimpleConnectionPool] = None
        
    def initialize_pool(self) -> None:
        """Initialize the connection pool"""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.config.pool_size,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password
            )
            logger.info(f"Database connection pool initialized (size: {self.config.pool_size})")
        except psycopg2.Error as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool
        
        Returns:
            A database connection
            
        Raises:
            RuntimeError: If pool is not initialized
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized. Call initialize_pool() first.")
        return self._pool.getconn()
    
    def return_connection(self, conn) -> None:
        """Return a connection to the pool
        
        Args:
            conn: Connection to return
        """
        if self._pool is not None:
            self._pool.putconn(conn)
    
    def close_pool(self) -> None:
        """Close all connections in the pool"""
        if self._pool is not None:
            self._pool.closeall()
            logger.info("Database connection pool closed")
    
    def ensure_schema(self) -> None:
        """Create database schema if it doesn't exist
        
        This method creates:
        - The registered_methods table
        - Indexes on name and updated_at columns
        - Trigger function for automatic updated_at updates
        - Trigger to call the function on updates
        
        Raises:
            psycopg2.Error: If schema creation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Create table
            logger.info("Creating registered_methods table if not exists...")
            cursor.execute(CREATE_TABLE_SQL)
            
            # Create indexes
            logger.info("Creating indexes...")
            for index_sql in CREATE_INDEXES_SQL:
                cursor.execute(index_sql)
            
            # Create trigger function
            logger.info("Creating trigger function...")
            cursor.execute(CREATE_TRIGGER_FUNCTION_SQL)
            
            # Create trigger
            logger.info("Creating trigger...")
            cursor.execute(CREATE_TRIGGER_SQL)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to initialize database schema: {e}")
            raise
        finally:
            if conn:
                cursor.close()
                self.return_connection(conn)
    
    def test_connection(self) -> bool:
        """Test if database connection is working
        
        Returns:
            True if connection successful, False otherwise
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            logger.info("Database connection test successful")
            return True
        except psycopg2.Error as e:
            logger.error(f"Database connection test failed: {e}")
            return False
        finally:
            if conn:
                self.return_connection(conn)


def create_database_connection(config: DatabaseConfig) -> DatabaseConnection:
    """Factory function to create and initialize a database connection
    
    Args:
        config: Database configuration
        
    Returns:
        Initialized DatabaseConnection instance
        
    Raises:
        psycopg2.Error: If connection or schema initialization fails
    """
    db_conn = DatabaseConnection(config)
    db_conn.initialize_pool()
    db_conn.ensure_schema()
    return db_conn
