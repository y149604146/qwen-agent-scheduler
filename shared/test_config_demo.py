"""
Demo script for test environment configuration

This script demonstrates how to use the test configuration utilities
to check and manage the test environment.

Usage:
    python shared/test_config_demo.py
"""

import logging
from test_config import (
    get_test_model_config,
    get_test_database_config,
    OllamaServiceChecker,
    TestDatabaseManager,
    check_test_environment
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main demo function"""
    
    print("=" * 60)
    print("Test Environment Configuration Demo")
    print("=" * 60)
    print()
    
    # 1. Get test configurations
    print("1. Loading test configurations...")
    model_config = get_test_model_config()
    db_config = get_test_database_config()
    
    print(f"   Model: {model_config.model_name}")
    print(f"   Ollama API: {model_config.api_base}")
    print(f"   Database: {db_config.database} on {db_config.host}:{db_config.port}")
    print()
    
    # 2. Check Ollama service
    print("2. Checking Ollama service...")
    ollama_checker = OllamaServiceChecker(
        api_base=model_config.api_base,
        timeout=5
    )
    
    ollama_available = ollama_checker.is_available()
    print(f"   Ollama service available: {ollama_available}")
    
    if ollama_available:
        model_available = ollama_checker.is_model_available(model_config.model_name)
        print(f"   Model {model_config.model_name} available: {model_available}")
    else:
        print(f"   Cannot check model availability (service not running)")
    print()
    
    # 3. Check database
    print("3. Checking test database...")
    db_manager = TestDatabaseManager(db_config)
    
    db_accessible = db_manager.is_database_accessible()
    print(f"   Database accessible: {db_accessible}")
    
    if not db_accessible:
        print("   Attempting to create test database...")
        if db_manager.ensure_test_database_exists():
            print("   Test database created successfully")
            db_accessible = db_manager.is_database_accessible()
            print(f"   Database accessible now: {db_accessible}")
        else:
            print("   Failed to create test database")
    print()
    
    # 4. Overall environment check
    print("4. Overall test environment status...")
    status = check_test_environment()
    
    print(f"   Ollama Available: {status['ollama_available']}")
    print(f"   Model Available: {status['model_available']}")
    print(f"   Database Accessible: {status['database_accessible']}")
    print()
    
    # 5. Summary
    print("=" * 60)
    all_ready = all(status.values())
    if all_ready:
        print("✓ Test environment is fully configured and ready!")
    else:
        print("✗ Test environment has issues:")
        if not status['ollama_available']:
            print("  - Ollama service is not running")
            print("    Start it with: ollama serve")
        if not status['model_available']:
            print(f"  - Model {model_config.model_name} is not available")
            print(f"    Pull it with: ollama pull {model_config.model_name}")
        if not status['database_accessible']:
            print("  - PostgreSQL database is not accessible")
            print("    Ensure PostgreSQL is running and credentials are correct")
    print("=" * 60)
    
    return 0 if all_ready else 1


if __name__ == '__main__':
    exit(main())
