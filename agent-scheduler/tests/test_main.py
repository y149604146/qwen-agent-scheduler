"""Tests for Agent Scheduler Brain main entry point

This module tests the main application initialization and component integration.
"""

import pytest
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import ModelConfig, DatabaseConfig, MethodMetadata, MethodParameter
from shared.config_loader import ConfigurationError

# Import after path setup
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from main import AgentSchedulerBrain, setup_logging


class TestSetupLogging:
    """Tests for logging configuration"""
    
    def test_setup_logging_console_only(self):
        """Test logging setup with console output only"""
        setup_logging(log_level="INFO", log_file=None)
        
        logger = logging.getLogger()
        assert logger.level == logging.INFO
        assert len(logger.handlers) >= 1
    
    def test_setup_logging_with_file(self):
        """Test logging setup with file output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            setup_logging(log_level="DEBUG", log_file=log_file)
            
            logger = logging.getLogger()
            assert logger.level == logging.DEBUG
            assert os.path.exists(log_file)
            
            # Close all handlers to release file locks (Windows compatibility)
            for handler in logger.handlers[:]:
                handler.close()
                logger.removeHandler(handler)
    
    def test_setup_logging_invalid_level(self):
        """Test logging setup with invalid level defaults to INFO"""
        setup_logging(log_level="INVALID", log_file=None)
        
        logger = logging.getLogger()
        # Should default to INFO when invalid level is provided
        assert logger.level == logging.INFO


class TestAgentSchedulerBrain:
    """Tests for AgentSchedulerBrain main application class"""
    
    @pytest.fixture
    def mock_config_file(self):
        """Create a temporary configuration file"""
        config_content = """
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"
  timeout: 30
  temperature: 0.7
  max_tokens: 2000

database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "test_user"
  password: "test_password"
  pool_size: 5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        yield config_path
        
        # Cleanup
        if os.path.exists(config_path):
            os.unlink(config_path)
    
    @pytest.fixture
    def mock_method_metadata(self):
        """Create sample method metadata"""
        import json
        
        param = MethodParameter(
            name="test_param",
            type="string",
            description="Test parameter",
            required=True
        )
        
        method = MethodMetadata(
            name="test_method",
            description="Test method",
            parameters_json=json.dumps([param.to_dict()]),
            return_type="string",
            module_path="test_module",
            function_name="test_function"
        )
        
        return method
    
    @patch('main.MethodLoader')
    @patch('main.AgentClient')
    @patch('main.MethodExecutor')
    @patch('main.AgentSchedulerAPI')
    def test_initialization_success(
        self,
        mock_api_class,
        mock_executor_class,
        mock_client_class,
        mock_loader_class,
        mock_config_file,
        mock_method_metadata
    ):
        """Test successful initialization of AgentSchedulerBrain"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load_all_methods.return_value = [mock_method_metadata]
        mock_loader.convert_to_qwen_tools.return_value = [
            {
                'name': 'test_method',
                'description': 'Test method',
                'parameters': {}
            }
        ]
        mock_loader_class.return_value = mock_loader
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor
        
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        # Initialize application
        app = AgentSchedulerBrain(config_path=mock_config_file)
        
        # Verify configuration loaded
        assert app.model_config is not None
        assert app.model_config.model_name == "qwen3:4b"
        assert app.db_config is not None
        assert app.db_config.database == "test_db"
        
        # Verify components initialized
        assert app.method_loader is not None
        assert app.method_executor is not None
        assert app.agent_client is not None
        assert app.api is not None
        
        # Verify method loader was called
        mock_loader.load_all_methods.assert_called_once()
        mock_loader.convert_to_qwen_tools.assert_called_once()
        
        # Verify agent client was initialized with tools
        mock_client_class.assert_called_once()
        
        # Verify executor was registered
        mock_client.register_tool_executor.assert_called_once()
        
        # Verify API was configured
        mock_api.set_agent_client.assert_called_once_with(mock_client)
        mock_api.set_method_loader.assert_called_once_with(mock_loader)
    
    def test_initialization_invalid_config(self):
        """Test initialization with invalid configuration file"""
        with pytest.raises(ConfigurationError):
            AgentSchedulerBrain(config_path="nonexistent_file.yaml")
    
    @patch('main.MethodLoader')
    def test_initialization_no_methods(self, mock_loader_class, mock_config_file):
        """Test initialization when no methods are registered"""
        # Setup mock to return empty method list
        mock_loader = Mock()
        mock_loader.load_all_methods.return_value = []
        mock_loader.convert_to_qwen_tools.return_value = []
        mock_loader_class.return_value = mock_loader
        
        with patch('main.AgentClient'), \
             patch('main.MethodExecutor'), \
             patch('main.AgentSchedulerAPI'):
            
            # Should not raise exception, just log warning
            app = AgentSchedulerBrain(config_path=mock_config_file)
            
            assert app.method_loader is not None
            mock_loader.load_all_methods.assert_called_once()
    
    @patch('main.MethodLoader')
    @patch('main.AgentClient')
    @patch('main.MethodExecutor')
    @patch('main.AgentSchedulerAPI')
    def test_execute_method(
        self,
        mock_api_class,
        mock_executor_class,
        mock_client_class,
        mock_loader_class,
        mock_config_file,
        mock_method_metadata
    ):
        """Test method execution through the callback"""
        from shared.models import ExecutionResult
        
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load_all_methods.return_value = [mock_method_metadata]
        mock_loader.convert_to_qwen_tools.return_value = [{'name': 'test_method'}]
        mock_loader_class.return_value = mock_loader
        
        mock_executor = Mock()
        mock_result = ExecutionResult(success=True, result="test_result", execution_time=0.1)
        mock_executor.execute.return_value = mock_result
        mock_executor_class.return_value = mock_executor
        
        mock_client_class.return_value = Mock()
        mock_api_class.return_value = Mock()
        
        # Initialize application
        app = AgentSchedulerBrain(config_path=mock_config_file)
        
        # Execute method through callback
        result = app._execute_method("test_method", {"test_param": "test_value"})
        
        # Verify executor was called
        mock_executor.execute.assert_called_once_with(
            "test_method",
            {"test_param": "test_value"}
        )
        
        # Verify result
        assert result.success is True
        assert result.result == "test_result"
    
    @patch('main.MethodLoader')
    @patch('main.AgentClient')
    @patch('main.MethodExecutor')
    @patch('main.AgentSchedulerAPI')
    def test_execute_method_failure(
        self,
        mock_api_class,
        mock_executor_class,
        mock_client_class,
        mock_loader_class,
        mock_config_file,
        mock_method_metadata
    ):
        """Test method execution failure handling"""
        from shared.models import ExecutionResult
        
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load_all_methods.return_value = [mock_method_metadata]
        mock_loader.convert_to_qwen_tools.return_value = [{'name': 'test_method'}]
        mock_loader_class.return_value = mock_loader
        
        mock_executor = Mock()
        mock_result = ExecutionResult(
            success=False,
            error="Test error",
            execution_time=0.1
        )
        mock_executor.execute.return_value = mock_result
        mock_executor_class.return_value = mock_executor
        
        mock_client_class.return_value = Mock()
        mock_api_class.return_value = Mock()
        
        # Initialize application
        app = AgentSchedulerBrain(config_path=mock_config_file)
        
        # Execute method through callback
        result = app._execute_method("test_method", {"test_param": "test_value"})
        
        # Verify result indicates failure
        assert result.success is False
        assert result.error == "Test error"
    
    @patch('main.MethodLoader')
    @patch('main.AgentClient')
    @patch('main.MethodExecutor')
    @patch('main.AgentSchedulerAPI')
    def test_shutdown(
        self,
        mock_api_class,
        mock_executor_class,
        mock_client_class,
        mock_loader_class,
        mock_config_file,
        mock_method_metadata
    ):
        """Test application shutdown"""
        # Setup mocks
        mock_loader = Mock()
        mock_loader.load_all_methods.return_value = [mock_method_metadata]
        mock_loader.convert_to_qwen_tools.return_value = [{'name': 'test_method'}]
        mock_loader_class.return_value = mock_loader
        
        mock_client_class.return_value = Mock()
        mock_executor_class.return_value = Mock()
        mock_api_class.return_value = Mock()
        
        # Initialize application
        app = AgentSchedulerBrain(config_path=mock_config_file)
        
        # Shutdown
        app.shutdown()
        
        # Verify method loader was closed
        mock_loader.close.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
