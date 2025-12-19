"""Tests for AgentClient

This module contains unit tests for the AgentClient class.
"""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import ModelConfig, ExecutionResult
from src.agent_client import AgentClient, AgentResponse, AgentClientError


class TestAgentClientInitialization:
    """Tests for AgentClient initialization"""
    
    def test_agent_client_creation_with_valid_config(self):
        """Test that AgentClient can be created with valid configuration"""
        model_config = ModelConfig(
            model_name="qwen3:4b",
            api_base="http://localhost:11434",
            timeout=30,
            temperature=0.7,
            max_tokens=2000
        )
        
        tools = [
            {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {
                            "type": "string",
                            "description": "Test parameter"
                        }
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        # This may fail if qwen-agent is not properly installed
        # but we're testing the interface
        try:
            client = AgentClient(model_config, tools)
            assert client.model_config == model_config
            assert client.tools == tools
            assert client.tool_executor is None  # Not registered yet
        except AgentClientError as e:
            # If qwen-agent is not available, that's expected in some test environments
            pytest.skip(f"qwen-agent not available: {e}")
    
    def test_agent_client_stores_configuration(self):
        """Test that AgentClient stores the provided configuration"""
        model_config = ModelConfig(
            model_name="qwen3:4b",
            api_base="http://localhost:11434"
        )
        
        tools = []
        
        try:
            client = AgentClient(model_config, tools)
            assert client.model_config.model_name == "qwen3:4b"
            assert client.model_config.api_base == "http://localhost:11434"
            assert len(client.tools) == 0
        except AgentClientError:
            pytest.skip("qwen-agent not available")


class TestToolExecutorRegistration:
    """Tests for tool executor registration"""
    
    def test_register_tool_executor(self):
        """Test that tool executor can be registered"""
        model_config = ModelConfig(
            model_name="qwen3:4b",
            api_base="http://localhost:11434"
        )
        
        tools = []
        
        try:
            client = AgentClient(model_config, tools)
            
            # Create a mock executor
            def mock_executor(method_name: str, params: dict) -> ExecutionResult:
                return ExecutionResult(
                    success=True,
                    result=f"Executed {method_name} with {params}"
                )
            
            # Register the executor
            client.register_tool_executor(mock_executor)
            
            # Verify it was registered
            assert client.tool_executor is not None
            assert client.tool_executor == mock_executor
            
        except AgentClientError:
            pytest.skip("qwen-agent not available")
    
    def test_executor_can_be_called_after_registration(self):
        """Test that registered executor can be invoked"""
        model_config = ModelConfig(
            model_name="qwen3:4b",
            api_base="http://localhost:11434"
        )
        
        tools = []
        
        try:
            client = AgentClient(model_config, tools)
            
            # Create a mock executor
            call_log = []
            
            def mock_executor(method_name: str, params: dict) -> ExecutionResult:
                call_log.append((method_name, params))
                return ExecutionResult(success=True, result="test result")
            
            client.register_tool_executor(mock_executor)
            
            # Call the executor directly
            result = client.tool_executor("test_method", {"param": "value"})
            
            assert len(call_log) == 1
            assert call_log[0] == ("test_method", {"param": "value"})
            assert result.success is True
            
        except AgentClientError:
            pytest.skip("qwen-agent not available")


class TestAgentResponse:
    """Tests for AgentResponse dataclass"""
    
    def test_agent_response_creation(self):
        """Test AgentResponse can be created"""
        response = AgentResponse(
            success=True,
            response="Test response",
            tool_calls=[{"name": "test", "args": {}}]
        )
        
        assert response.success is True
        assert response.response == "Test response"
        assert len(response.tool_calls) == 1
        assert response.error is None
    
    def test_agent_response_with_error(self):
        """Test AgentResponse with error"""
        response = AgentResponse(
            success=False,
            error="Test error"
        )
        
        assert response.success is False
        assert response.error == "Test error"
        assert response.response == ""
        assert response.tool_calls == []
    
    def test_agent_response_default_tool_calls(self):
        """Test that tool_calls defaults to empty list"""
        response = AgentResponse(success=True)
        assert response.tool_calls == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
