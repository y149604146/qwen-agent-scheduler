"""
Pytest configuration for Method Registration System tests

This file makes shared test fixtures available to all tests
in the method-registration project.
"""

import sys
import os

# Add parent directories to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all shared fixtures
from shared.test_fixtures import (
    test_model_config,
    test_db_config,
    ollama_checker,
    check_ollama_available,
    check_model_available,
    db_manager,
    ensure_test_database,
    clean_database,
    clean_database_after,
    test_environment_status,
    skip_if_no_ollama,
    skip_if_no_model
)

# Make fixtures available
__all__ = [
    'test_model_config',
    'test_db_config',
    'ollama_checker',
    'check_ollama_available',
    'check_model_available',
    'db_manager',
    'ensure_test_database',
    'clean_database',
    'clean_database_after',
    'test_environment_status',
    'skip_if_no_ollama',
    'skip_if_no_model'
]
