"""
Tests for test environment configuration

This test file verifies that the test environment configuration
works correctly, including:
- Model configuration
- Database configuration
- Ollama service checking
- Test data cleanup

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest
import os
from unittest.mock import Mock, patch
from shared.test_config import (
    TestModelConfig,
    TestDatabaseConfig,
    OllamaServiceChecker,
    TestDatabaseManager,
    get_test_model_config,
    get_test_database_config,
    check_test_environment
)


class TestTestModelConfig:
    """Tests for TestModelConfig"""
    
    def test_default_model_config(self):
        """Test default model configuration values"""
        config = TestModelConfig()
        assert config.model_name == "qwen3:4b"
        assert config.api_base == "http://localhost:11434"
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
    
    def test_custom_model_config(self):
        """Test custom model configuration values"""
        config = TestModelConfig(
            model_name="qwen2:7b",
            api_base="http://custom:8080",
            timeout=60,
            temperature=0.5,
            max_tokens=1000
        )
        assert config.model_name == "qwen2:7b"
        assert config.api_base == "http://custom:8080"
        assert config.timeout == 60
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestTestDatabaseConfig:
    """Tests for TestDatabaseConfig"""
    
    def test_default_database_config(self):
        """Test default database configuration values"""
        config = TestDatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "qwen_agent_test_db"
        assert config.user == "postgres"
        assert config.password == "postgres"
        assert config.pool_size == 5
    
    def test_custom_database_config(self):
        """Test custom database configuration values"""
        config = TestDatabaseConfig(
            host="testhost",
            port=5433,
            database="custom_test_db",
            user="testuser",
            password="testpass",
            pool_size=10
        )
        assert config.host == "testhost"
        assert config.port == 5433
        assert config.database == "custom_test_db"
        assert config.user == "testuser"
        assert config.password == "testpass"
        assert config.pool_size == 10


class TestOllamaServiceChecker:
    """Tests for OllamaServiceChecker"""
    
    def test_checker_initialization(self):
        """Test OllamaServiceChecker initialization"""
        checker = OllamaServiceChecker(
            api_base="http://localhost:11434",
            timeout=5
        )
        assert checker.api_base == "http://localhost:11434"
        assert checker.timeout == 5
    
    def test_api_base_trailing_slash_removed(self):
        """Test that trailing slash is removed from api_base"""
        checker = OllamaServiceChecker(api_base="http://localhost:11434/")
        assert checker.api_base == "http://localhost:11434"
    
    @patch('shared.test_config.httpx')
    def test_is_available_success(self, mock_httpx):
        """Test is_available returns True when service responds"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get = Mock(return_value=mock_response)
        mock_httpx.Client = Mock(return_value=mock_client)
        
        checker = OllamaServiceChecker()
        assert checker.is_available() is True
    
    @patch('shared.test_config.httpx')
    def test_is_available_failure(self, mock_httpx):
        """Test is_available returns False when service doesn't respond"""
        mock_client = Mock()
        mock_client.__enter__ = Mock(side_effect=Exception("Connection failed"))
        mock_client.__exit__ = Mock(return_value=False)
        mock_httpx.Client = Mock(return_value=mock_client)
        
        checker = OllamaServiceChecker()
        assert checker.is_available() is False
    
    @patch('shared.test_config.httpx')
    def test_is_model_available_success(self, mock_httpx):
        """Test is_model_available returns True when model exists"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json = Mock(return_value={
            'models': [
                {'name': 'qwen3:4b'},
                {'name': 'qwen2:7b'}
            ]
        })
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get = Mock(return_value=mock_response)
        mock_httpx.Client = Mock(return_value=mock_client)
        
        checker = OllamaServiceChecker()
        assert checker.is_model_available('qwen3:4b') is True
        assert checker.is_model_available('qwen2:7b') is True
        assert checker.is_model_available('nonexistent:1b') is False
    
    @patch('shared.test_config.httpx')
    def test_wait_for_service_success(self, mock_httpx):
        """Test wait_for_service returns True when service becomes available"""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get = Mock(return_value=mock_response)
        mock_httpx.Client = Mock(return_value=mock_client)
        
        checker = OllamaServiceChecker()
        assert checker.wait_for_service(max_wait_seconds=5, check_interval=1) is True
    
    @patch('shared.test_config.httpx')
    @patch('shared.test_config.time.sleep')
    def test_wait_for_service_timeout(self, mock_sleep, mock_httpx):
        """Test wait_for_service returns False on timeout"""
        mock_client = Mock()
        mock_client.__enter__ = Mock(side_effect=Exception("Connection failed"))
        mock_client.__exit__ = Mock(return_value=False)
        mock_httpx.Client = Mock(return_value=mock_client)
        
        checker = OllamaServiceChecker()
        # Use very short timeout for test
        assert checker.wait_for_service(max_wait_seconds=0.1, check_interval=0.05) is False


class TestGetConfigFunctions:
    """Tests for get_test_*_config functions"""
    
    def test_get_test_model_config_defaults(self):
        """Test get_test_model_config returns correct defaults"""
        config = get_test_model_config()
        assert config.model_name == "qwen3:4b"
        assert config.api_base == "http://localhost:11434"
    
    def test_get_test_model_config_env_override(self):
        """Test get_test_model_config respects environment variables"""
        with patch.dict(os.environ, {
            'TEST_MODEL_NAME': 'custom:model',
            'TEST_OLLAMA_API_BASE': 'http://custom:9999'
        }):
            config = get_test_model_config()
            assert config.model_name == 'custom:model'
            assert config.api_base == 'http://custom:9999'
    
    def test_get_test_database_config_defaults(self):
        """Test get_test_database_config returns correct defaults"""
        config = get_test_database_config()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.database == "qwen_agent_test_db"
    
    def test_get_test_database_config_env_override(self):
        """Test get_test_database_config respects environment variables"""
        with patch.dict(os.environ, {
            'TEST_DB_HOST': 'testhost',
            'TEST_DB_PORT': '5433',
            'TEST_DB_NAME': 'custom_db'
        }):
            config = get_test_database_config()
            assert config.host == 'testhost'
            assert config.port == 5433
            assert config.database == 'custom_db'


class TestCheckTestEnvironment:
    """Tests for check_test_environment function"""
    
    @patch('shared.test_config.OllamaServiceChecker')
    @patch('shared.test_config.TestDatabaseManager')
    def test_check_test_environment_all_available(self, mock_db_manager_class, mock_checker_class):
        """Test check_test_environment when all services are available"""
        mock_checker = Mock()
        mock_checker.is_available = Mock(return_value=True)
        mock_checker.is_model_available = Mock(return_value=True)
        mock_checker_class.return_value = mock_checker
        
        mock_db_manager = Mock()
        mock_db_manager.is_database_accessible = Mock(return_value=True)
        mock_db_manager_class.return_value = mock_db_manager
        
        status = check_test_environment()
        
        assert status['ollama_available'] is True
        assert status['model_available'] is True
        assert status['database_accessible'] is True
    
    @patch('shared.test_config.OllamaServiceChecker')
    @patch('shared.test_config.TestDatabaseManager')
    def test_check_test_environment_ollama_unavailable(self, mock_db_manager_class, mock_checker_class):
        """Test check_test_environment when Ollama is unavailable"""
        mock_checker = Mock()
        mock_checker.is_available = Mock(return_value=False)
        mock_checker_class.return_value = mock_checker
        
        mock_db_manager = Mock()
        mock_db_manager.is_database_accessible = Mock(return_value=True)
        mock_db_manager_class.return_value = mock_db_manager
        
        status = check_test_environment()
        
        assert status['ollama_available'] is False
        assert status['model_available'] is False
        assert status['database_accessible'] is True


# Integration tests that require actual services
# These are marked as integration tests and will be skipped if services are not available

@pytest.mark.integration
class TestOllamaServiceCheckerIntegration:
    """Integration tests for OllamaServiceChecker with real service"""
    
    def test_check_real_ollama_service(self, skip_if_no_ollama):
        """Test checking real Ollama service"""
        checker = OllamaServiceChecker()
        assert checker.is_available() is True
    
    def test_check_real_model_availability(self, skip_if_no_model):
        """Test checking real model availability"""
        checker = OllamaServiceChecker()
        assert checker.is_model_available('qwen3:4b') is True


@pytest.mark.integration
class TestDatabaseManagerIntegration:
    """Integration tests for TestDatabaseManager with real database"""
    
    def test_ensure_database_exists(self, db_manager):
        """Test ensuring test database exists"""
        assert db_manager.ensure_test_database_exists() is True
    
    def test_database_is_accessible(self, ensure_test_database):
        """Test that test database is accessible"""
        assert ensure_test_database.is_database_accessible() is True
    
    def test_cleanup_all_tables(self, clean_database):
        """Test cleaning up all tables"""
        # This test uses the clean_database fixture which already
        # performs cleanup, so we just verify it doesn't raise errors
        assert clean_database.cleanup_all_tables() is True
