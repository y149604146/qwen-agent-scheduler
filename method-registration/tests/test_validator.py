"""Tests for MetadataValidator

This module contains unit tests for the MetadataValidator class.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared import MethodConfig, MethodParameter, ValidationResult
from src.validator import MetadataValidator


class TestMetadataValidator:
    """Test suite for MetadataValidator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.validator = MetadataValidator()
    
    def test_valid_method_passes_validation(self):
        """Test that a valid method configuration passes validation"""
        method = MethodConfig(
            name="get_weather",
            description="Get weather information for a city",
            parameters=[
                MethodParameter(
                    name="city",
                    type="string",
                    description="Name of the city",
                    required=True
                )
            ],
            return_type="dict",
            module_path="tools.weather",
            function_name="get_weather"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.method_name == "get_weather"
    
    def test_method_with_no_parameters_passes_validation(self):
        """Test that a method with no parameters is valid"""
        method = MethodConfig(
            name="get_time",
            description="Get current time",
            parameters=[],
            return_type="string",
            module_path="tools.time",
            function_name="get_time"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is True
        assert len(result.errors) == 0
    
    def test_empty_method_name_fails_validation(self):
        """Test that empty method name fails validation"""
        method = MethodConfig(
            name="",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("name is required" in error.lower() for error in result.errors)
    
    def test_short_method_name_fails_validation(self):
        """Test that method name shorter than 2 characters fails"""
        method = MethodConfig(
            name="a",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("too short" in error.lower() for error in result.errors)
    
    def test_long_method_name_fails_validation(self):
        """Test that method name longer than 100 characters fails"""
        method = MethodConfig(
            name="a" * 101,
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("too long" in error.lower() for error in result.errors)
    
    def test_invalid_method_name_with_spaces_fails(self):
        """Test that method name with spaces fails validation"""
        method = MethodConfig(
            name="get weather",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("not a valid python identifier" in error.lower() for error in result.errors)
    
    def test_invalid_method_name_starting_with_digit_fails(self):
        """Test that method name starting with digit fails validation"""
        method = MethodConfig(
            name="1get_weather",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("not a valid python identifier" in error.lower() for error in result.errors)
    
    def test_method_name_with_special_characters_fails(self):
        """Test that method name with special characters fails validation"""
        method = MethodConfig(
            name="get-weather",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("not a valid python identifier" in error.lower() for error in result.errors)
    
    def test_python_keyword_as_method_name_fails(self):
        """Test that Python keywords cannot be used as method names"""
        method = MethodConfig(
            name="class",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("not a valid python identifier" in error.lower() for error in result.errors)
    
    def test_empty_description_fails_validation(self):
        """Test that empty description fails validation"""
        method = MethodConfig(
            name="test_method",
            description="",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("description is required" in error.lower() for error in result.errors)
    
    def test_long_description_fails_validation(self):
        """Test that description longer than 1000 characters fails"""
        method = MethodConfig(
            name="test_method",
            description="a" * 1001,
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("description is too long" in error.lower() for error in result.errors)
    
    def test_empty_module_path_fails_validation(self):
        """Test that empty module path fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("module path is required" in error.lower() for error in result.errors)
    
    def test_invalid_module_path_fails_validation(self):
        """Test that invalid module path fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test-module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("module path" in error.lower() and "not valid" in error.lower() 
                   for error in result.errors)
    
    def test_empty_function_name_fails_validation(self):
        """Test that empty function name fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name=""
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("function name is required" in error.lower() for error in result.errors)
    
    def test_invalid_function_name_fails_validation(self):
        """Test that invalid function name fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="None",
            module_path="test.module",
            function_name="test-func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("function name" in error.lower() and "not a valid python identifier" in error.lower() 
                   for error in result.errors)
    
    def test_empty_return_type_fails_validation(self):
        """Test that empty return type fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("return type is required" in error.lower() for error in result.errors)
    
    def test_invalid_return_type_fails_validation(self):
        """Test that invalid return type fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[],
            return_type="InvalidType",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("return type" in error.lower() and "not a recognized" in error.lower() 
                   for error in result.errors)
    
    def test_parameter_missing_name_fails_validation(self):
        """Test that parameter without name fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[
                MethodParameter(
                    name="",
                    type="string",
                    description="Test parameter"
                )
            ],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("missing required field 'name'" in error.lower() for error in result.errors)
    
    def test_parameter_missing_type_fails_validation(self):
        """Test that parameter without type fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="",
                    description="Test parameter"
                )
            ],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("missing required field 'type'" in error.lower() for error in result.errors)
    
    def test_parameter_missing_description_fails_validation(self):
        """Test that parameter without description fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="string",
                    description=""
                )
            ],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("missing required field 'description'" in error.lower() for error in result.errors)
    
    def test_parameter_with_invalid_type_fails_validation(self):
        """Test that parameter with invalid type fails validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="InvalidType",
                    description="Test parameter"
                )
            ],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("has invalid type" in error.lower() for error in result.errors)
    
    def test_duplicate_parameter_names_fails_validation(self):
        """Test that duplicate parameter names fail validation"""
        method = MethodConfig(
            name="test_method",
            description="Test method",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="string",
                    description="First parameter"
                ),
                MethodParameter(
                    name="param1",
                    type="int",
                    description="Duplicate parameter"
                )
            ],
            return_type="None",
            module_path="test.module",
            function_name="test_func"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is False
        assert any("duplicate parameter name" in error.lower() for error in result.errors)
    
    def test_validate_methods_returns_results_for_all_methods(self):
        """Test that validate_methods returns result for each method"""
        methods = [
            MethodConfig(
                name="method1",
                description="First method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="method1"
            ),
            MethodConfig(
                name="method2",
                description="Second method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="method2"
            )
        ]
        
        results = self.validator.validate_methods(methods)
        
        assert len(results) == 2
        assert all(isinstance(r, ValidationResult) for r in results)
    
    def test_validate_methods_detects_duplicate_method_names(self):
        """Test that validate_methods detects duplicate method names"""
        methods = [
            MethodConfig(
                name="duplicate_method",
                description="First method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="method1"
            ),
            MethodConfig(
                name="duplicate_method",
                description="Second method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="method2"
            )
        ]
        
        results = self.validator.validate_methods(methods)
        
        # Both methods should have errors about duplicate names
        assert all(not r.valid for r in results)
        assert all(
            any("duplicate method name" in error.lower() for error in r.errors)
            for r in results
        )
    
    def test_validate_methods_with_mixed_valid_and_invalid(self):
        """Test validate_methods with mix of valid and invalid methods"""
        methods = [
            MethodConfig(
                name="valid_method",
                description="Valid method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="valid_method"
            ),
            MethodConfig(
                name="",  # Invalid: empty name
                description="Invalid method",
                parameters=[],
                return_type="None",
                module_path="test.module",
                function_name="invalid_method"
            )
        ]
        
        results = self.validator.validate_methods(methods)
        
        assert len(results) == 2
        assert results[0].valid is True
        assert results[1].valid is False
    
    def test_all_valid_python_types_accepted(self):
        """Test that all valid Python types are accepted"""
        valid_types = [
            'string', 'str', 'int', 'integer', 'float', 'bool', 'boolean',
            'dict', 'dictionary', 'list', 'array', 'tuple', 'set',
            'None', 'NoneType', 'Any', 'bytes', 'bytearray'
        ]
        
        for type_str in valid_types:
            method = MethodConfig(
                name="test_method",
                description="Test method",
                parameters=[],
                return_type=type_str,
                module_path="test.module",
                function_name="test_func"
            )
            
            result = self.validator.validate_method(method)
            
            assert result.valid is True, f"Type '{type_str}' should be valid but validation failed"
    
    def test_valid_module_paths_accepted(self):
        """Test that various valid module paths are accepted"""
        valid_paths = [
            "module",
            "package.module",
            "package.subpackage.module",
            "my_package.my_module"
        ]
        
        for path in valid_paths:
            method = MethodConfig(
                name="test_method",
                description="Test method",
                parameters=[],
                return_type="None",
                module_path=path,
                function_name="test_func"
            )
            
            result = self.validator.validate_method(method)
            
            assert result.valid is True, f"Module path '{path}' should be valid but validation failed"
    
    def test_method_with_multiple_parameters_validates_correctly(self):
        """Test method with multiple parameters"""
        method = MethodConfig(
            name="complex_method",
            description="Method with multiple parameters",
            parameters=[
                MethodParameter(
                    name="param1",
                    type="string",
                    description="First parameter",
                    required=True
                ),
                MethodParameter(
                    name="param2",
                    type="int",
                    description="Second parameter",
                    required=False,
                    default=0
                ),
                MethodParameter(
                    name="param3",
                    type="bool",
                    description="Third parameter",
                    required=True
                )
            ],
            return_type="dict",
            module_path="tools.complex",
            function_name="complex_method"
        )
        
        result = self.validator.validate_method(method)
        
        assert result.valid is True
        assert len(result.errors) == 0
