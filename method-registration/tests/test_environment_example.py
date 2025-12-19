"""
Example tests demonstrating test environment configuration usage

This file shows how to use the test environment configuration
fixtures in actual tests.

Requirements: 9.1, 9.2, 9.3, 9.4, 9.5
"""

import pytest


class TestEnvironmentConfigurationExamples:
    """Examples of using test environment configuration"""
    
    def test_using_model_config(self, test_model_config):
        """Example: Using test model configuration"""
        # Test model configuration is automatically provided
        assert test_model_config.model_name == "qwen3:4b"
        assert test_model_config.api_base == "http://localhost:11434"
        assert test_model_config.timeout == 30
    
    def test_using_database_config(self, test_db_config):
        """Example: Using test database configuration"""
        # Test database configuration is automatically provided
        assert test_db_config.database == "qwen_agent_test_db"
        assert test_db_config.host == "localhost"
        assert test_db_config.port == 5432
    
    def test_checking_ollama_service(self, ollama_checker):
        """Example: Checking if Ollama service is available"""
        # This test will run regardless of Ollama availability
        # but you can check the status
        is_available = ollama_checker.is_available()
        # Test passes either way, just demonstrates the check
        assert isinstance(is_available, bool)
    
    @pytest.mark.integration
    def test_requiring_ollama(self, skip_if_no_ollama):
        """Example: Test that requires Ollama to be running"""
        # This test will be skipped if Ollama is not available
        # If we get here, Ollama is definitely running
        assert True
    
    @pytest.mark.integration
    def test_requiring_model(self, skip_if_no_model):
        """Example: Test that requires qwen3:4b model"""
        # This test will be skipped if model is not available
        # If we get here, qwen3:4b is definitely available
        assert True
    
    @pytest.mark.integration
    def test_with_database_cleanup(self, clean_database):
        """Example: Test with automatic database cleanup"""
        # Database is cleaned before this test runs
        # Database will be cleaned after this test completes
        # This ensures test isolation
        
        # You can safely modify database here
        # knowing it will be cleaned up
        assert clean_database.is_database_accessible()
    
    def test_environment_status(self, test_environment_status):
        """Example: Checking overall environment status"""
        # Get status of all environment components
        assert 'ollama_available' in test_environment_status
        assert 'model_available' in test_environment_status
        assert 'database_accessible' in test_environment_status
        
        # Status values are booleans
        assert isinstance(test_environment_status['ollama_available'], bool)


class TestSkippingBehavior:
    """Examples of test skipping based on service availability"""
    
    def test_always_runs(self):
        """This test always runs"""
        assert True
    
    @pytest.mark.integration
    def test_skipped_if_no_ollama(self, skip_if_no_ollama):
        """This test is skipped if Ollama is not available"""
        # If this test runs, Ollama is available
        assert True
    
    @pytest.mark.integration
    def test_skipped_if_no_model(self, skip_if_no_model):
        """This test is skipped if qwen3:4b is not available"""
        # If this test runs, the model is available
        assert True
    
    @pytest.mark.integration
    def test_requires_both(self, skip_if_no_ollama, skip_if_no_model):
        """This test requires both Ollama and the model"""
        # If this test runs, both are available
        assert True


class TestDatabaseManagement:
    """Examples of database management in tests"""
    
    @pytest.mark.integration
    def test_database_manager(self, db_manager):
        """Example: Using database manager directly"""
        # Check if database is accessible
        is_accessible = db_manager.is_database_accessible()
        assert isinstance(is_accessible, bool)
    
    @pytest.mark.integration
    def test_with_ensured_database(self, ensure_test_database):
        """Example: Test with ensured database"""
        # Database is guaranteed to exist
        assert ensure_test_database.is_database_accessible()
    
    @pytest.mark.integration
    def test_with_clean_database_before_and_after(self, clean_database):
        """Example: Database cleaned before and after test"""
        # Database is clean at start
        # Do your test operations
        # Database will be cleaned at end
        assert clean_database.is_database_accessible()
    
    @pytest.mark.integration
    def test_with_clean_database_after_only(self, clean_database_after):
        """Example: Database cleaned only after test"""
        # Database may have existing data
        # Do your test operations
        # Database will be cleaned at end
        assert clean_database_after.is_database_accessible()
