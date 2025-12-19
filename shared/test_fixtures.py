"""
Shared pytest fixtures for test environment setup

This module provides reusable pytest fixtures for:
- Test model configuration
- Test database configuration
- Ollama service checking
- Test data cleanup

These fixtures can be imported and used in both method-registration
and agent-scheduler test suites.
"""

import pytest
import logging
from typing import Generator

from shared.test_config import (
    TestModelConfig,
    TestDatabaseConfig,
    OllamaServiceChecker,
    TestDatabaseManager,
    get_test_model_config,
    get_test_database_config,
    check_test_environment
)

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def test_model_config() -> TestModelConfig:
    """
    Provide test model configuration for the entire test session
    
    Returns:
        TestModelConfig: Configuration for qwen3:4b model
    """
    return get_test_model_config()


@pytest.fixture(scope="session")
def test_db_config() -> TestDatabaseConfig:
    """
    Provide test database configuration for the entire test session
    
    Returns:
        TestDatabaseConfig: Configuration for test PostgreSQL database
    """
    return get_test_database_config()


@pytest.fixture(scope="session")
def ollama_checker(test_model_config: TestModelConfig) -> OllamaServiceChecker:
    """
    Provide Ollama service checker for the entire test session
    
    Args:
        test_model_config: Test model configuration
        
    Returns:
        OllamaServiceChecker: Service checker instance
    """
    return OllamaServiceChecker(
        api_base=test_model_config.api_base,
        timeout=5
    )


@pytest.fixture(scope="session")
def check_ollama_available(ollama_checker: OllamaServiceChecker) -> bool:
    """
    Check if Ollama service is available at session start
    
    Args:
        ollama_checker: Ollama service checker
        
    Returns:
        bool: True if Ollama is available
        
    Raises:
        pytest.skip: If Ollama service is not available
    """
    if not ollama_checker.is_available():
        pytest.skip("Ollama service is not available")
    return True


@pytest.fixture(scope="session")
def check_model_available(
    ollama_checker: OllamaServiceChecker,
    test_model_config: TestModelConfig
) -> bool:
    """
    Check if qwen3:4b model is available at session start
    
    Args:
        ollama_checker: Ollama service checker
        test_model_config: Test model configuration
        
    Returns:
        bool: True if model is available
        
    Raises:
        pytest.skip: If model is not available
    """
    if not ollama_checker.is_available():
        pytest.skip("Ollama service is not available")
    
    if not ollama_checker.is_model_available(test_model_config.model_name):
        pytest.skip(f"Model {test_model_config.model_name} is not available in Ollama")
    
    return True


@pytest.fixture(scope="session")
def db_manager(test_db_config: TestDatabaseConfig) -> TestDatabaseManager:
    """
    Provide database manager for the entire test session
    
    Args:
        test_db_config: Test database configuration
        
    Returns:
        TestDatabaseManager: Database manager instance
    """
    return TestDatabaseManager(test_db_config)


@pytest.fixture(scope="session")
def ensure_test_database(db_manager: TestDatabaseManager) -> Generator[TestDatabaseManager, None, None]:
    """
    Ensure test database exists for the entire test session
    
    This fixture:
    1. Creates the test database if it doesn't exist
    2. Yields the database manager for tests to use
    3. Optionally cleans up after all tests (controlled by env var)
    
    Args:
        db_manager: Database manager instance
        
    Yields:
        TestDatabaseManager: Database manager with ensured database
        
    Raises:
        pytest.skip: If database cannot be created or accessed
    """
    # Ensure database exists
    if not db_manager.ensure_test_database_exists():
        pytest.skip("Could not create or access test database")
    
    # Verify database is accessible
    if not db_manager.is_database_accessible():
        pytest.skip("Test database is not accessible")
    
    yield db_manager
    
    # Optional: Drop database after all tests
    # Controlled by environment variable to prevent accidental data loss
    import os
    if os.getenv('DROP_TEST_DB_AFTER_TESTS', 'false').lower() == 'true':
        logger.info("Dropping test database after test session")
        db_manager.drop_test_database()


@pytest.fixture(scope="function")
def clean_database(ensure_test_database: TestDatabaseManager) -> Generator[TestDatabaseManager, None, None]:
    """
    Clean all tables before and after each test function
    
    This fixture ensures test isolation by cleaning all data
    from the database before and after each test.
    
    Args:
        ensure_test_database: Database manager with ensured database
        
    Yields:
        TestDatabaseManager: Database manager with clean database
    """
    # Clean before test
    ensure_test_database.cleanup_all_tables()
    
    yield ensure_test_database
    
    # Clean after test
    ensure_test_database.cleanup_all_tables()


@pytest.fixture(scope="function")
def clean_database_after(ensure_test_database: TestDatabaseManager) -> Generator[TestDatabaseManager, None, None]:
    """
    Clean all tables only after each test function
    
    Use this fixture when you need to inspect database state
    before the test runs, but want cleanup after.
    
    Args:
        ensure_test_database: Database manager with ensured database
        
    Yields:
        TestDatabaseManager: Database manager
    """
    yield ensure_test_database
    
    # Clean after test
    ensure_test_database.cleanup_all_tables()


@pytest.fixture(scope="session")
def test_environment_status() -> dict:
    """
    Check and report test environment status at session start
    
    Returns:
        dict: Status of test environment components
    """
    status = check_test_environment()
    
    logger.info("Test Environment Status:")
    logger.info(f"  Ollama Available: {status['ollama_available']}")
    logger.info(f"  Model Available: {status['model_available']}")
    logger.info(f"  Database Accessible: {status['database_accessible']}")
    
    return status


@pytest.fixture
def skip_if_no_ollama(check_ollama_available: bool):
    """
    Convenience fixture to skip test if Ollama is not available
    
    Usage:
        def test_something(skip_if_no_ollama):
            # Test will be skipped if Ollama is not available
            pass
    """
    pass


@pytest.fixture
def skip_if_no_model(check_model_available: bool):
    """
    Convenience fixture to skip test if model is not available
    
    Usage:
        def test_something(skip_if_no_model):
            # Test will be skipped if qwen3:4b is not available
            pass
    """
    pass
