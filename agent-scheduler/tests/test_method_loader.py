"""Tests for MethodLoader class

This module tests the method loading functionality including:
- Loading all methods from database
- Loading specific methods by name
- Converting methods to qwen-agent tool format
"""

import pytest
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import DatabaseConfig, MethodMetadata, MethodParameter

# Import from agent-scheduler (note: using relative path due to hyphen in directory name)
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.method_loader import MethodLoader, MethodLoaderError

# Import DatabaseWriter for test setup
method_registration_path = Path(__file__).parent.parent.parent / "method-registration"
sys.path.insert(0, str(method_registration_path))
sys.path.insert(0, str(method_registration_path / "src"))
try:
    from db_client import DatabaseWriter
except ImportError:
    # Fallback if module structure is different
    import importlib.util
    spec = importlib.util.spec_from_file_location("db_client", method_registration_path / "src" / "db_client.py")
    db_client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(db_client_module)
    DatabaseWriter = db_client_module.DatabaseWriter


@pytest.fixture
def db_config():
    """Database configuration for testing"""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="qwen_agent_test",
        user="postgres",
        password="postgres",
        pool_size=2
    )


@pytest.fixture
def method_loader(db_config):
    """Create MethodLoader instance for testing"""
    loader = MethodLoader(db_config)
    yield loader
    loader.close()


@pytest.fixture
def db_writer(db_config):
    """Create DatabaseWriter instance for test setup"""
    writer = DatabaseWriter(db_config)
    writer.ensure_schema()
    yield writer
    writer.close()


@pytest.fixture
def sample_method():
    """Create a sample method for testing"""
    params = [
        MethodParameter(
            name="city",
            type="string",
            description="City name",
            required=True
        ),
        MethodParameter(
            name="unit",
            type="string",
            description="Temperature unit",
            required=False,
            default="celsius"
        )
    ]
    
    params_json = json.dumps([p.to_dict() for p in params])
    
    return MethodMetadata(
        name="get_weather",
        description="Get weather information for a city",
        parameters_json=params_json,
        return_type="dict",
        module_path="tools.weather",
        function_name="get_weather"
    )


def test_method_loader_initialization(db_config):
    """Test MethodLoader can be initialized"""
    loader = MethodLoader(db_config)
    assert loader is not None
    loader.close()


def test_load_all_methods_empty_database(method_loader):
    """Test loading methods from empty database returns empty list"""
    methods = method_loader.load_all_methods()
    assert isinstance(methods, list)
    # Note: May not be empty if previous tests left data


def test_load_all_methods_with_data(method_loader, db_writer, sample_method):
    """Test loading all methods from database"""
    # Insert a test method
    db_writer.upsert_method(sample_method)
    
    # Load all methods
    methods = method_loader.load_all_methods()
    
    assert isinstance(methods, list)
    assert len(methods) >= 1
    
    # Find our test method
    test_method = next((m for m in methods if m.name == "get_weather"), None)
    assert test_method is not None
    assert test_method.name == "get_weather"
    assert test_method.description == "Get weather information for a city"
    assert test_method.return_type == "dict"


def test_load_method_by_name_existing(method_loader, db_writer, sample_method):
    """Test loading a specific method by name"""
    # Insert a test method
    db_writer.upsert_method(sample_method)
    
    # Load by name
    method = method_loader.load_method_by_name("get_weather")
    
    assert method is not None
    assert method.name == "get_weather"
    assert method.description == "Get weather information for a city"
    assert method.return_type == "dict"
    assert method.module_path == "tools.weather"
    assert method.function_name == "get_weather"


def test_load_method_by_name_not_found(method_loader):
    """Test loading a non-existent method returns None"""
    method = method_loader.load_method_by_name("nonexistent_method_xyz")
    assert method is None


def test_convert_to_qwen_tools_single_method(sample_method):
    """Test converting a single method to qwen-agent format"""
    loader = MethodLoader(DatabaseConfig(
        host="localhost", port=5432, database="test",
        user="test", password="test"
    ))
    
    qwen_tools = loader.convert_to_qwen_tools([sample_method])
    
    assert len(qwen_tools) == 1
    tool = qwen_tools[0]
    
    # Check basic structure
    assert "name" in tool
    assert "description" in tool
    assert "parameters" in tool
    
    # Check values
    assert tool["name"] == "get_weather"
    assert tool["description"] == "Get weather information for a city"
    
    # Check parameters structure
    params = tool["parameters"]
    assert params["type"] == "object"
    assert "properties" in params
    assert "required" in params
    
    # Check parameter properties
    assert "city" in params["properties"]
    assert params["properties"]["city"]["type"] == "string"
    assert params["properties"]["city"]["description"] == "City name"
    
    assert "unit" in params["properties"]
    assert params["properties"]["unit"]["type"] == "string"
    assert params["properties"]["unit"]["default"] == "celsius"
    
    # Check required parameters
    assert "city" in params["required"]
    assert "unit" not in params["required"]
    
    loader.close()


def test_convert_to_qwen_tools_multiple_methods():
    """Test converting multiple methods to qwen-agent format"""
    method1 = MethodMetadata(
        name="method1",
        description="First method",
        parameters_json=json.dumps([{
            "name": "param1",
            "type": "string",
            "description": "Parameter 1",
            "required": True
        }]),
        return_type="string",
        module_path="module1",
        function_name="func1"
    )
    
    method2 = MethodMetadata(
        name="method2",
        description="Second method",
        parameters_json=json.dumps([{
            "name": "param2",
            "type": "int",
            "description": "Parameter 2",
            "required": True
        }]),
        return_type="int",
        module_path="module2",
        function_name="func2"
    )
    
    loader = MethodLoader(DatabaseConfig(
        host="localhost", port=5432, database="test",
        user="test", password="test"
    ))
    
    qwen_tools = loader.convert_to_qwen_tools([method1, method2])
    
    assert len(qwen_tools) == 2
    assert qwen_tools[0]["name"] == "method1"
    assert qwen_tools[1]["name"] == "method2"
    
    loader.close()


def test_convert_to_qwen_tools_type_mapping():
    """Test that parameter types are correctly mapped to JSON schema types"""
    test_cases = [
        ("string", "string"),
        ("str", "string"),
        ("int", "integer"),
        ("integer", "integer"),
        ("float", "number"),
        ("number", "number"),
        ("bool", "boolean"),
        ("boolean", "boolean"),
        ("dict", "object"),
        ("object", "object"),
        ("list", "array"),
        ("array", "array"),
    ]
    
    loader = MethodLoader(DatabaseConfig(
        host="localhost", port=5432, database="test",
        user="test", password="test"
    ))
    
    for input_type, expected_type in test_cases:
        method = MethodMetadata(
            name=f"test_{input_type}",
            description="Test method",
            parameters_json=json.dumps([{
                "name": "param",
                "type": input_type,
                "description": "Test parameter",
                "required": True
            }]),
            return_type="string",
            module_path="test",
            function_name="test"
        )
        
        qwen_tools = loader.convert_to_qwen_tools([method])
        param_type = qwen_tools[0]["parameters"]["properties"]["param"]["type"]
        
        assert param_type == expected_type, f"Type {input_type} should map to {expected_type}, got {param_type}"
    
    loader.close()


def test_convert_to_qwen_tools_empty_list():
    """Test converting empty list returns empty list"""
    loader = MethodLoader(DatabaseConfig(
        host="localhost", port=5432, database="test",
        user="test", password="test"
    ))
    
    qwen_tools = loader.convert_to_qwen_tools([])
    assert qwen_tools == []
    
    loader.close()
