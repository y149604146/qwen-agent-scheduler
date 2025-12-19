# Test Environment Configuration

This document describes the test environment configuration for the qwen-agent-scheduler project.

## Overview

The test environment configuration provides utilities for:

1. **Test Model Configuration** - Configure qwen3:4b model for testing
2. **Ollama Service Checking** - Verify Ollama service availability
3. **Test Database Configuration** - Configure separate test PostgreSQL database
4. **Test Data Cleanup** - Ensure test isolation by cleaning up data

## Requirements

The test environment configuration addresses the following requirements:

- **Requirement 9.1**: Configure tests to use qwen3:4b model
- **Requirement 9.2**: Implement Ollama service availability checking
- **Requirement 9.3**: Configure test-specific PostgreSQL database
- **Requirement 9.4**: Verify test database accessibility
- **Requirement 9.5**: Implement test data cleanup logic

## Components

### 1. Test Configuration Classes

#### TestModelConfig

Configures the qwen3:4b model for testing:

```python
from shared.test_config import TestModelConfig

config = TestModelConfig(
    model_name="qwen3:4b",
    api_base="http://localhost:11434",
    timeout=30,
    temperature=0.7,
    max_tokens=2000
)
```

#### TestDatabaseConfig

Configures a separate test database:

```python
from shared.test_config import TestDatabaseConfig

config = TestDatabaseConfig(
    host="localhost",
    port=5432,
    database="qwen_agent_test_db",  # Separate from production
    user="postgres",
    password="postgres",
    pool_size=5
)
```

### 2. Service Checking

#### OllamaServiceChecker

Checks if Ollama service is available:

```python
from shared.test_config import OllamaServiceChecker

checker = OllamaServiceChecker(
    api_base="http://localhost:11434",
    timeout=5
)

# Check if service is running
if checker.is_available():
    print("Ollama is running")
    
    # Check if specific model is available
    if checker.is_model_available("qwen3:4b"):
        print("qwen3:4b model is available")

# Wait for service to become available
if checker.wait_for_service(max_wait_seconds=30):
    print("Service is now available")
```

### 3. Database Management

#### TestDatabaseManager

Manages test database lifecycle:

```python
from shared.test_config import TestDatabaseManager, get_test_database_config

config = get_test_database_config()
manager = TestDatabaseManager(config)

# Ensure test database exists
manager.ensure_test_database_exists()

# Check if database is accessible
if manager.is_database_accessible():
    print("Database is accessible")

# Clean up all tables (for test isolation)
manager.cleanup_all_tables()

# Clean up specific table
manager.cleanup_table("registered_methods")

# Drop test database (use with caution!)
manager.drop_test_database()
```

## Pytest Fixtures

The test environment provides reusable pytest fixtures:

### Session-Scoped Fixtures

These fixtures are created once per test session:

- `test_model_config` - Provides TestModelConfig
- `test_db_config` - Provides TestDatabaseConfig
- `ollama_checker` - Provides OllamaServiceChecker
- `db_manager` - Provides TestDatabaseManager
- `ensure_test_database` - Ensures test database exists
- `test_environment_status` - Reports environment status

### Function-Scoped Fixtures

These fixtures are created for each test function:

- `clean_database` - Cleans database before and after test
- `clean_database_after` - Cleans database only after test

### Skip Fixtures

These fixtures skip tests if services are unavailable:

- `skip_if_no_ollama` - Skip if Ollama is not running
- `skip_if_no_model` - Skip if qwen3:4b is not available

## Usage in Tests

### Basic Usage

```python
import pytest

def test_something(test_model_config, test_db_config):
    """Test using test configurations"""
    assert test_model_config.model_name == "qwen3:4b"
    assert test_db_config.database == "qwen_agent_test_db"
```

### Skip if Service Unavailable

```python
def test_with_ollama(skip_if_no_ollama):
    """This test will be skipped if Ollama is not available"""
    # Test code that requires Ollama
    pass

def test_with_model(skip_if_no_model):
    """This test will be skipped if qwen3:4b is not available"""
    # Test code that requires the model
    pass
```

### Database Cleanup

```python
def test_with_clean_database(clean_database):
    """Database is cleaned before and after this test"""
    # Test code that modifies database
    # Database will be automatically cleaned after test
    pass

def test_with_cleanup_after(clean_database_after):
    """Database is cleaned only after this test"""
    # Test code that needs to inspect existing data
    # Database will be cleaned after test
    pass
```

### Integration Tests

```python
@pytest.mark.integration
def test_integration(skip_if_no_ollama, skip_if_no_model, clean_database):
    """Full integration test with all services"""
    # This test requires Ollama, model, and clean database
    pass
```

## Environment Variables

You can override default configurations using environment variables:

### Model Configuration

- `TEST_MODEL_NAME` - Override model name (default: "qwen3:4b")
- `TEST_OLLAMA_API_BASE` - Override Ollama API URL (default: "http://localhost:11434")
- `TEST_MODEL_TIMEOUT` - Override timeout (default: 30)
- `TEST_MODEL_TEMPERATURE` - Override temperature (default: 0.7)
- `TEST_MODEL_MAX_TOKENS` - Override max tokens (default: 2000)

### Database Configuration

- `TEST_DB_HOST` - Override database host (default: "localhost")
- `TEST_DB_PORT` - Override database port (default: 5432)
- `TEST_DB_NAME` - Override database name (default: "qwen_agent_test_db")
- `TEST_DB_USER` - Override database user (default: "postgres")
- `TEST_DB_PASSWORD` - Override database password (default: "postgres")
- `TEST_DB_POOL_SIZE` - Override pool size (default: 5)

### Test Behavior

- `DROP_TEST_DB_AFTER_TESTS` - Drop test database after all tests (default: "false")

### Example

```bash
# Run tests with custom configuration
export TEST_MODEL_NAME="qwen2:7b"
export TEST_DB_NAME="my_test_db"
pytest
```

## Checking Test Environment

Before running tests, you can check if the test environment is properly configured:

```bash
# Run the demo script
python shared/test_config_demo.py
```

This will check:
- Ollama service availability
- Model availability
- Database accessibility

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r shared/requirements.txt
```

### 2. Start Ollama Service

```bash
ollama serve
```

### 3. Pull qwen3:4b Model

```bash
ollama pull qwen3:4b
```

### 4. Setup PostgreSQL

Ensure PostgreSQL is running and create test database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Create test database
CREATE DATABASE qwen_agent_test_db;
```

Or let the test framework create it automatically:

```python
from shared.test_config import TestDatabaseManager, get_test_database_config

manager = TestDatabaseManager(get_test_database_config())
manager.ensure_test_database_exists()
```

### 5. Verify Setup

```bash
python shared/test_config_demo.py
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Only Integration Tests

```bash
pytest -m integration
```

### Run Only Property-Based Tests

```bash
pytest -m property
```

### Skip Slow Tests

```bash
pytest -m "not slow"
```

## Test Isolation

The test environment ensures test isolation through:

1. **Separate Test Database** - Uses `qwen_agent_test_db` instead of production database
2. **Automatic Cleanup** - `clean_database` fixture cleans all tables between tests
3. **Transaction Rollback** - Database operations can use transactions that rollback on test completion

## Troubleshooting

### Ollama Service Not Available

```
Error: Ollama service is not available
```

**Solution**: Start Ollama service:
```bash
ollama serve
```

### Model Not Available

```
Error: Model qwen3:4b is not available in Ollama
```

**Solution**: Pull the model:
```bash
ollama pull qwen3:4b
```

### Database Connection Failed

```
Error: Test database is not accessible
```

**Solutions**:
1. Ensure PostgreSQL is running
2. Check database credentials in configuration
3. Verify database exists or let framework create it

### Tests Skipped

If tests are being skipped, check the skip reason:
- "Ollama service is not available" - Start Ollama
- "Model qwen3:4b is not available" - Pull the model
- "Test database is not accessible" - Fix database connection

## Best Practices

1. **Use Fixtures** - Always use provided fixtures instead of creating configurations manually
2. **Clean Database** - Use `clean_database` fixture for tests that modify database
3. **Skip Appropriately** - Use skip fixtures for tests that require external services
4. **Mark Tests** - Mark integration tests with `@pytest.mark.integration`
5. **Environment Variables** - Use environment variables for CI/CD configurations
6. **Separate Database** - Never use production database for tests

## CI/CD Integration

For CI/CD pipelines, you can:

1. Use Docker Compose to start services:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: qwen_agent_test_db
  
  ollama:
    image: ollama/ollama
    volumes:
      - ./models:/root/.ollama
```

2. Set environment variables in CI:
```yaml
env:
  TEST_DB_HOST: postgres
  TEST_OLLAMA_API_BASE: http://ollama:11434
```

3. Pull model before tests:
```bash
docker exec ollama ollama pull qwen3:4b
```

4. Run tests:
```bash
pytest -m "not slow"
```
