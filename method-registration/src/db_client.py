"""Database client for Method Registration System

This module provides the DatabaseWriter class for persisting method metadata
to PostgreSQL database with transaction management and error handling.
"""

import logging
from typing import List, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import DatabaseConfig, MethodMetadata
from shared.db_schema import DatabaseConnection


logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Raised when database operations fail"""
    pass


class DatabaseWriter:
    """Handles writing method metadata to PostgreSQL database
    
    This class provides methods for upserting (insert or update) method
    registrations with proper transaction management and error handling.
    
    Attributes:
        db_connection: DatabaseConnection instance for connection pooling
    """
    
    def __init__(self, db_config: DatabaseConfig):
        """Initialize DatabaseWriter with database configuration
        
        Args:
            db_config: Database configuration object
            
        Raises:
            DatabaseError: If connection initialization fails
        """
        try:
            self.db_connection = DatabaseConnection(db_config)
            self.db_connection.initialize_pool()
            logger.info("DatabaseWriter initialized successfully")
        except psycopg2.Error as e:
            error_msg = f"Failed to initialize database connection: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
    
    def ensure_schema(self) -> None:
        """Create database schema if it doesn't exist
        
        This method creates:
        - The registered_methods table
        - Indexes on name and updated_at columns
        - Trigger function for automatic updated_at updates
        - Trigger to call the function on updates
        
        Raises:
            DatabaseError: If schema creation fails
        """
        try:
            self.db_connection.ensure_schema()
            logger.info("Database schema ensured successfully")
        except psycopg2.Error as e:
            error_msg = f"Failed to ensure database schema: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
    
    def upsert_method(self, method: MethodMetadata) -> None:
        """Insert or update a single method record
        
        If a method with the same name already exists, it will be updated.
        Otherwise, a new record will be inserted.
        
        Args:
            method: MethodMetadata object to insert or update
            
        Raises:
            DatabaseError: If upsert operation fails
        """
        conn = None
        cursor = None
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # Use INSERT ... ON CONFLICT for upsert
            upsert_sql = """
                INSERT INTO registered_methods 
                    (name, description, parameters_json, return_type, module_path, function_name)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (name) 
                DO UPDATE SET
                    description = EXCLUDED.description,
                    parameters_json = EXCLUDED.parameters_json,
                    return_type = EXCLUDED.return_type,
                    module_path = EXCLUDED.module_path,
                    function_name = EXCLUDED.function_name,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """
            
            cursor.execute(
                upsert_sql,
                (
                    method.name,
                    method.description,
                    method.parameters_json,
                    method.return_type,
                    method.module_path,
                    method.function_name
                )
            )
            
            result = cursor.fetchone()
            method_id = result[0] if result else None
            
            conn.commit()
            
            logger.info(f"Successfully upserted method '{method.name}' (id: {method_id})")
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            error_msg = f"Failed to upsert method '{method.name}': {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_connection.return_connection(conn)
    
    def upsert_methods(self, methods: List[MethodMetadata]) -> None:
        """Insert or update multiple method records in a single transaction
        
        All methods are inserted/updated within a single transaction.
        If any operation fails, all changes are rolled back.
        
        Args:
            methods: List of MethodMetadata objects to insert or update
            
        Raises:
            DatabaseError: If batch upsert operation fails
        """
        if not methods:
            logger.warning("upsert_methods called with empty list")
            return
        
        conn = None
        cursor = None
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor()
            
            # Use INSERT ... ON CONFLICT for upsert
            upsert_sql = """
                INSERT INTO registered_methods 
                    (name, description, parameters_json, return_type, module_path, function_name)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s)
                ON CONFLICT (name) 
                DO UPDATE SET
                    description = EXCLUDED.description,
                    parameters_json = EXCLUDED.parameters_json,
                    return_type = EXCLUDED.return_type,
                    module_path = EXCLUDED.module_path,
                    function_name = EXCLUDED.function_name,
                    updated_at = CURRENT_TIMESTAMP;
            """
            
            # Execute batch insert/update
            for method in methods:
                cursor.execute(
                    upsert_sql,
                    (
                        method.name,
                        method.description,
                        method.parameters_json,
                        method.return_type,
                        method.module_path,
                        method.function_name
                    )
                )
            
            conn.commit()
            
            logger.info(f"Successfully upserted {len(methods)} methods")
            
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            error_msg = f"Failed to upsert methods batch: {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_connection.return_connection(conn)
    
    def get_method_by_name(self, method_name: str) -> Optional[MethodMetadata]:
        """Retrieve a method by its name
        
        Args:
            method_name: Name of the method to retrieve
            
        Returns:
            MethodMetadata object if found, None otherwise
            
        Raises:
            DatabaseError: If query fails
        """
        conn = None
        cursor = None
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            select_sql = """
                SELECT id, name, description, parameters_json, return_type, 
                       module_path, function_name, created_at, updated_at
                FROM registered_methods
                WHERE name = %s;
            """
            
            cursor.execute(select_sql, (method_name,))
            row = cursor.fetchone()
            
            if row:
                return MethodMetadata(
                    id=row['id'],
                    name=row['name'],
                    description=row['description'],
                    parameters_json=row['parameters_json'],
                    return_type=row['return_type'],
                    module_path=row['module_path'],
                    function_name=row['function_name'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            return None
            
        except psycopg2.Error as e:
            error_msg = f"Failed to retrieve method '{method_name}': {e}"
            logger.error(error_msg)
            raise DatabaseError(error_msg) from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_connection.return_connection(conn)
    
    def close(self) -> None:
        """Close database connection pool
        
        Should be called when DatabaseWriter is no longer needed.
        """
        self.db_connection.close_pool()
        logger.info("DatabaseWriter closed")
