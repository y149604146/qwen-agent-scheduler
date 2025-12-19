"""Tests for MethodExecutor class

This module tests the method execution functionality including:
- Parameter validation
- Type conversion
- Method execution
- Error handling
- Timeout control
"""

import pytest
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import MethodMetadata, MethodParameter, ExecutionResult

# Import from agent-scheduler
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.executor import MethodExecutor, MethodExecutorError


@pytest.fixture
def sample_methods():
    """Create sample methods for testing"""
    methods = {}
    
    # Method 1: add_numbers - simple integer addition
    add_params = [
        MethodParameter(name="a", type="int", description="First number", required=True),
        MethodParameter(name="b", type="int", description="Second number", required=True)
    ]
    methods["add_numbers"] = MethodMetadata(
        name="add_numbers",
        description="Add two numbers",
        parameters_json=json.dumps([p.to_dict() for p in add_params]),
        return_type="int",
        module_path="workspace.tools.test_tools",
        function_name="add_numbers"
    )
    
    # Method 2: greet - string with optional parameter
    greet_params = [
        MethodParameter(name="name", type="string", description="Name to greet", required=True),
        MethodParameter(name="greeting", type="string", description="Greeting word", 
                       required=False, default="Hello")
    ]
    methods["greet"] = MethodMetadata(
        name="greet",
        description="Generate greeting",
        parameters_json=json.dumps([p.to_dict() for p in greet_params]),
        return_type="string",
        module_path="workspace.tools.test_tools",
        function_name="greet"
    )
    
    # Method 3: divide - can raise exception
    divide_params = [
        MethodParameter(name="numerator", type="float", description="Numerator", required=True),
        MethodParameter(name="denominator", type="float", description="Denominator", required=True)
    ]
    methods["divide"] = MethodMetadata(
        name="divide",
        description="Divide two numbers",
        parameters_json=json.dumps([p.to_dict() for p in divide_params]),
        return_type="float",
        module_path="workspace.tools.test_tools",
        function_name="divide"
    )
    
    # Method 4: process_data - dict parameter
    process_params = [
        MethodParameter(name="data", type="dict", description="Data to process", required=True)
    ]
    methods["process_data"] = MethodMetadata(
        name="process_data",
        description="Process data",
        parameters_json=json.dumps([p.to_dict() for p in process_params]),
        return_type="dict",
        module_path="workspace.tools.test_tools",
        function_name="process_data"
    )
    
    # Method 5: list_items - list parameter
    list_params = [
        MethodParameter(name="items", type="list", description="List of items", required=True)
    ]
    methods["list_items"] = MethodMetadata(
        name="list_items",
        description="Count items",
        parameters_json=json.dumps([p.to_dict() for p in list_params]),
        return_type="int",
        module_path="workspace.tools.test_tools",
        function_name="list_items"
    )
    
    return methods


@pytest.fixture
def executor(sample_methods):
    """Create MethodExecutor instance for testing"""
    return MethodExecutor(sample_methods, default_timeout=5)


def test_executor_initialization(sample_methods):
    """Test MethodExecutor can be initialized"""
    executor = MethodExecutor(sample_methods)
    assert executor is not None
    assert len(executor.methods) == len(sample_methods)
    assert executor.default_timeout == 30


def test_validate_params_valid(executor):
    """Test parameter validation with valid parameters"""
    is_valid, error = executor.validate_params("add_numbers", {"a": 5, "b": 3})
    assert is_valid is True
    assert error is None


def test_validate_params_missing_required(executor):
    """Test parameter validation detects missing required parameters"""
    is_valid, error = executor.validate_params("add_numbers", {"a": 5})
    assert is_valid is False
    assert "Required parameter 'b' is missing" in error


def test_validate_params_unknown_parameter(executor):
    """Test parameter validation detects unknown parameters"""
    is_valid, error = executor.validate_params("add_numbers", {"a": 5, "b": 3, "c": 10})
    assert is_valid is False
    assert "Unknown parameter 'c'" in error


def test_validate_params_optional_parameter_missing(executor):
    """Test validation passes when optional parameter is missing"""
    is_valid, error = executor.validate_params("greet", {"name": "Alice"})
    assert is_valid is True
    assert error is None


def test_validate_params_method_not_found(executor):
    """Test validation fails for non-existent method"""
    is_valid, error = executor.validate_params("nonexistent", {})
    assert is_valid is False
    assert "Method 'nonexistent' not found" in error


def test_execute_simple_method(executor):
    """Test executing a simple method with valid parameters"""
    result = executor.execute("add_numbers", {"a": 5, "b": 3})
    
    assert isinstance(result, ExecutionResult)
    assert result.success is True
    assert result.result == 8
    assert result.error is None
    assert result.execution_time > 0


def test_execute_with_type_conversion(executor):
    """Test execution with automatic type conversion"""
    # Pass strings that should be converted to integers
    result = executor.execute("add_numbers", {"a": "5", "b": "3"})
    
    assert result.success is True
    assert result.result == 8


def test_execute_with_optional_parameter_default(executor):
    """Test execution uses default value for optional parameter"""
    result = executor.execute("greet", {"name": "Alice"})
    
    assert result.success is True
    assert result.result == "Hello, Alice!"


def test_execute_with_optional_parameter_provided(executor):
    """Test execution with optional parameter provided"""
    result = executor.execute("greet", {"name": "Bob", "greeting": "Hi"})
    
    assert result.success is True
    assert result.result == "Hi, Bob!"


def test_execute_method_raises_exception(executor):
    """Test execution handles exceptions from method"""
    result = executor.execute("divide", {"numerator": 10.0, "denominator": 0.0})
    
    assert result.success is False
    assert result.error is not None
    assert "ZeroDivisionError" in result.error or "division by zero" in result.error.lower()


def test_execute_invalid_parameters(executor):
    """Test execution fails with invalid parameters"""
    result = executor.execute("add_numbers", {"a": 5})  # Missing 'b'
    
    assert result.success is False
    assert "Parameter validation failed" in result.error


def test_execute_type_conversion_failure(executor):
    """Test execution fails when type conversion is impossible"""
    result = executor.execute("add_numbers", {"a": "not_a_number", "b": 3})
    
    assert result.success is False
    assert "Parameter preparation failed" in result.error


def test_execute_method_not_found(executor):
    """Test execution fails for non-existent method"""
    result = executor.execute("nonexistent_method", {})
    
    assert result.success is False
    assert "Method 'nonexistent_method' not found" in result.error


def test_execute_with_dict_parameter(executor):
    """Test execution with dictionary parameter"""
    test_data = {"key1": "value1", "key2": "value2"}
    result = executor.execute("process_data", {"data": test_data})
    
    assert result.success is True
    assert isinstance(result.result, dict)
    assert result.result["processed"] is True
    assert result.result["item_count"] == 2


def test_execute_with_list_parameter(executor):
    """Test execution with list parameter"""
    test_list = [1, 2, 3, 4, 5]
    result = executor.execute("list_items", {"items": test_list})
    
    assert result.success is True
    assert result.result == 5


def test_type_conversion_string(executor):
    """Test type conversion for string type"""
    value = executor._convert_type(123, "string")
    assert value == "123"
    assert isinstance(value, str)


def test_type_conversion_int(executor):
    """Test type conversion for integer type"""
    value = executor._convert_type("42", "int")
    assert value == 42
    assert isinstance(value, int)


def test_type_conversion_float(executor):
    """Test type conversion for float type"""
    value = executor._convert_type("3.14", "float")
    assert value == 3.14
    assert isinstance(value, float)


def test_type_conversion_bool_from_string(executor):
    """Test type conversion for boolean from string"""
    assert executor._convert_type("true", "bool") is True
    assert executor._convert_type("false", "bool") is False
    assert executor._convert_type("1", "bool") is True
    assert executor._convert_type("0", "bool") is False


def test_type_conversion_dict_from_json(executor):
    """Test type conversion for dict from JSON string"""
    json_str = '{"key": "value"}'
    value = executor._convert_type(json_str, "dict")
    assert isinstance(value, dict)
    assert value["key"] == "value"


def test_type_conversion_list_from_json(executor):
    """Test type conversion for list from JSON string"""
    json_str = '[1, 2, 3]'
    value = executor._convert_type(json_str, "list")
    assert isinstance(value, list)
    assert value == [1, 2, 3]


def test_type_conversion_invalid(executor):
    """Test type conversion raises error for invalid conversion"""
    with pytest.raises(ValueError):
        executor._convert_type("not_a_number", "int")


def test_method_caching(executor):
    """Test that methods are cached after first load"""
    # Execute method first time
    result1 = executor.execute("add_numbers", {"a": 1, "b": 2})
    assert result1.success is True
    
    # Check method is in cache
    assert "add_numbers" in executor._method_cache
    
    # Execute again - should use cached version
    result2 = executor.execute("add_numbers", {"a": 3, "b": 4})
    assert result2.success is True
    assert result2.result == 7


def test_execute_with_custom_timeout(executor):
    """Test execution with custom timeout parameter"""
    # This test just verifies the timeout parameter is accepted
    # Actual timeout testing is platform-dependent
    result = executor.execute("add_numbers", {"a": 1, "b": 2}, timeout=10)
    assert result.success is True


def test_load_method_module_not_found():
    """Test loading method from non-existent module"""
    bad_method = MethodMetadata(
        name="bad_method",
        description="Bad method",
        parameters_json="[]",
        return_type="string",
        module_path="nonexistent.module",
        function_name="some_function"
    )
    
    executor = MethodExecutor({"bad_method": bad_method})
    result = executor.execute("bad_method", {})
    
    assert result.success is False
    assert "Failed to import module" in result.error or "Failed to load method" in result.error


def test_load_method_function_not_found():
    """Test loading non-existent function from valid module"""
    bad_method = MethodMetadata(
        name="bad_method",
        description="Bad method",
        parameters_json="[]",
        return_type="string",
        module_path="workspace.tools.test_tools",
        function_name="nonexistent_function"
    )
    
    executor = MethodExecutor({"bad_method": bad_method})
    result = executor.execute("bad_method", {})
    
    assert result.success is False
    assert "not found" in result.error.lower()
