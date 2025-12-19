"""
Test Environment Configuration

This module provides utilities for configuring and managing the test environment,
including:
- Test-specific model configuration (qwen3:4b)
- Ollama service availability checking
- Test-specific PostgreSQL database configuration
- Test data cleanup utilities

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import os
import logging
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)


@dataclass
class TestModelConfig:
    """Test-specific model configuration for qwen3:4b"""
    model_name: str = "qwen3:4b"
    api_base: str = "http://localhost:11434"
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class TestDatabaseConfig:
    """Test-specific PostgreSQL database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "qwen_agent_test_db"  # Separate test database
    user: str = "postgres"
    password: str = "postgres"
    pool_size: int = 5


class OllamaServiceChecker:
    """Utility class to check Ollama service availability"""
    
    def __init__(self, api_base: str = "http://localhost:11434", timeout: int = 5):
        self.api_base = api_base.rstrip('/')
        self.timeout = timeout
        
    def is_available(self) -> bool:
        """
        Check if Ollama service is available and responding
        
        Returns:
            bool: True if service is available, False otherwise
        """
        if httpx is None:
            logger.warning("httpx not installed, cannot check Ollama availability")
            return False
            
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.api_base}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama service check failed: {e}")
            return False
    
    def is_model_available(self, model_name: str) -> bool:
        """
        Check if a specific model is available in Ollama
        
        Args:
            model_name: Name of the model to check (e.g., "qwen3:4b")
            
        Returns:
            bool: True if model is available, False otherwise
        """
        if httpx is None:
            logger.warning("httpx not installed, cannot check model availability")
            return False
            
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.api_base}/api/tags")
                if response.status_code != 200:
                    return False
                    
                data = response.json()
                models = data.get('models', [])
                return any(model.get('name') == model_name for model in models)
        except Exception as e:
            logger.debug(f"Model availability check failed: {e}")
            return False
    
    def wait_for_service(self, max_wait_seconds: int = 30, check_interval: int = 2) -> bool:
        """
        Wait for Ollama service to become available
        
        Args:
            max_wait_seconds: Maximum time to wait in seconds
            check_interval: Time between checks in seconds
            
        Returns:
            bool: True if service became available, False if timeout
        """
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            if self.is_available():
                return True
            time.sleep(check_interval)
        return False


class TestDatabaseManager:
    """Utility class to manage test database lifecycle"""
    
    def __init__(self, config: TestDatabaseConfig):
        self.config = config
        
    def _get_connection_params(self, database: Optional[str] = None) -> Dict[str, Any]:
        """Get connection parameters for psycopg2"""
        return {
            'host': self.config.host,
            'port': self.config.port,
            'database': database or self.config.database,
            'user': self.config.user,
            'password': self.config.password
        }
    
    def ensure_test_database_exists(self) -> bool:
        """
        Ensure the test database exists, create it if it doesn't
        
        Returns:
            bool: True if database exists or was created successfully
        """
        try:
            # Connect to postgres database to create test database
            conn = psycopg2.connect(**self._get_connection_params('postgres'))
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Check if database exists
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config.database,)
            )
            exists = cursor.fetchone() is not None
            
            if not exists:
                # Create database
                cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.config.database)
                    )
                )
                logger.info(f"Created test database: {self.config.database}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to ensure test database exists: {e}")
            return False
    
    def drop_test_database(self) -> bool:
        """
        Drop the test database (use with caution!)
        
        Returns:
            bool: True if database was dropped successfully
        """
        try:
            # Connect to postgres database to drop test database
            conn = psycopg2.connect(**self._get_connection_params('postgres'))
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Terminate existing connections
            cursor.execute(
                """
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = %s
                AND pid <> pg_backend_pid()
                """,
                (self.config.database,)
            )
            
            # Drop database
            cursor.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(
                    sql.Identifier(self.config.database)
                )
            )
            logger.info(f"Dropped test database: {self.config.database}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop test database: {e}")
            return False
    
    def cleanup_all_tables(self) -> bool:
        """
        Clean up all data from test database tables
        
        Returns:
            bool: True if cleanup was successful
        """
        try:
            conn = psycopg2.connect(**self._get_connection_params())
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute(
                """
                SELECT tablename FROM pg_tables
                WHERE schemaname = 'public'
                """
            )
            tables = cursor.fetchall()
            
            # Truncate all tables
            for (table_name,) in tables:
                cursor.execute(
                    sql.SQL("TRUNCATE TABLE {} CASCADE").format(
                        sql.Identifier(table_name)
                    )
                )
                logger.debug(f"Truncated table: {table_name}")
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup tables: {e}")
            return False
    
    def cleanup_table(self, table_name: str) -> bool:
        """
        Clean up data from a specific table
        
        Args:
            table_name: Name of the table to clean
            
        Returns:
            bool: True if cleanup was successful
        """
        try:
            conn = psycopg2.connect(**self._get_connection_params())
            cursor = conn.cursor()
            
            cursor.execute(
                sql.SQL("TRUNCATE TABLE {} CASCADE").format(
                    sql.Identifier(table_name)
                )
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            logger.debug(f"Cleaned up table: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup table {table_name}: {e}")
            return False
    
    def is_database_accessible(self) -> bool:
        """
        Check if the test database is accessible
        
        Returns:
            bool: True if database is accessible
        """
        try:
            conn = psycopg2.connect(**self._get_connection_params())
            conn.close()
            return True
        except Exception as e:
            logger.debug(f"Database not accessible: {e}")
            return False


def get_test_model_config() -> TestModelConfig:
    """
    Get test model configuration, with environment variable overrides
    
    Environment variables:
    - TEST_MODEL_NAME: Override model name
    - TEST_OLLAMA_API_BASE: Override Ollama API base URL
    
    Returns:
        TestModelConfig: Test model configuration
    """
    return TestModelConfig(
        model_name=os.getenv('TEST_MODEL_NAME', 'qwen3:4b'),
        api_base=os.getenv('TEST_OLLAMA_API_BASE', 'http://localhost:11434'),
        timeout=int(os.getenv('TEST_MODEL_TIMEOUT', '30')),
        temperature=float(os.getenv('TEST_MODEL_TEMPERATURE', '0.7')),
        max_tokens=int(os.getenv('TEST_MODEL_MAX_TOKENS', '2000'))
    )


def get_test_database_config() -> TestDatabaseConfig:
    """
    Get test database configuration, with environment variable overrides
    
    Environment variables:
    - TEST_DB_HOST: Override database host
    - TEST_DB_PORT: Override database port
    - TEST_DB_NAME: Override database name
    - TEST_DB_USER: Override database user
    - TEST_DB_PASSWORD: Override database password
    
    Returns:
        TestDatabaseConfig: Test database configuration
    """
    return TestDatabaseConfig(
        host=os.getenv('TEST_DB_HOST', 'localhost'),
        port=int(os.getenv('TEST_DB_PORT', '5432')),
        database=os.getenv('TEST_DB_NAME', 'test_db'),
        user=os.getenv('TEST_DB_USER', 'yuanyuan'),
        password=os.getenv('TEST_DB_PASSWORD', '666666'),
        pool_size=int(os.getenv('TEST_DB_POOL_SIZE', '5'))
    )


def check_test_environment() -> Dict[str, bool]:
    """
    Check the entire test environment and return status
    
    Returns:
        Dict with status of each component:
        - ollama_available: Ollama service is running
        - model_available: qwen3:4b model is available
        - database_accessible: Test database is accessible
    """
    model_config = get_test_model_config()
    db_config = get_test_database_config()
    
    ollama_checker = OllamaServiceChecker(
        api_base=model_config.api_base,
        timeout=5
    )
    db_manager = TestDatabaseManager(db_config)
    
    status = {
        'ollama_available': ollama_checker.is_available(),
        'model_available': False,
        'database_accessible': db_manager.is_database_accessible()
    }
    
    if status['ollama_available']:
        status['model_available'] = ollama_checker.is_model_available(
            model_config.model_name
        )
    
    return status
