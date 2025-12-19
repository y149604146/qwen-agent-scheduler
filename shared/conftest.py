"""
Pytest configuration for shared module tests

This file makes test fixtures available for tests in the shared directory.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import all fixtures from test_fixtures
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
