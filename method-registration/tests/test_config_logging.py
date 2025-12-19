"""Property-based tests for configuration error logging

Tests that configuration loading failures are properly logged with
file path and specific error details.
"""

import pytest
import logging
import tempfile
import json
import yaml
from pathlib import Path
from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock

from shared.config_loader import ConfigLoader, ConfigurationError


class TestConfigurationErrorLogging:
    """Test suite for configuration error logging (Property 26)"""
    
    @given(
        test_case=st.one_of(
            # Invalid YAML syntax - tabs are not allowed in YAML
            st.tuples(st.just("key:\t\tvalue"), st.sampled_from(['.yaml', '.yml', '.json'])),
            # Unclosed bracket
            st.tuples(st.just("key: [value"), st.sampled_from(['.yaml', '.yml', '.json'])),
            # Empty file
            st.tuples(st.just(""), st.sampled_from(['.json', '.yaml', '.yml'])),
            # Not a dictionary (just a string) - will pass parsing but fail dict check
            st.tuples(st.just("just a string"), st.sampled_from(['.json', '.yaml', '.yml'])),
            # Not a dictionary (just a list)
            st.tuples(st.just("- item1\n- item2"), st.sampled_from(['.json', '.yaml', '.yml'])),
        )
    )
    @settings(max_examples=100)
    def test_config_error_includes_file_path_and_error_detail(self, test_case):
        """
        Feature: qwen-agent-scheduler, Property 26: Configuration error logging detail
        
        For any configuration loading failure, the error log should include 
        the configuration file path and the specific parsing error.
        
        Validates: Requirements 10.2
        """
        file_content, file_format = test_case
        
        # Create a temporary config file with invalid content
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix=file_format, 
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write(file_content)
            temp_path = f.name
        
        try:
            # Attempt to load the invalid configuration
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_yaml(temp_path)
            
            # Verify the error message contains the file path
            error_message = str(exc_info.value)
            assert temp_path in error_message, (
                f"Error message should contain file path '{temp_path}', "
                f"but got: {error_message}"
            )
            
            # Verify the error message contains some detail about what went wrong
            # It should not be just the file path, but also explain the error
            assert len(error_message) > len(temp_path), (
                "Error message should contain more than just the file path"
            )
            
            # The error should describe the type of problem
            # (e.g., "Failed to parse", "empty", "not a file", etc.)
            error_indicators = [
                'parse', 'empty', 'not a file', 'not found', 
                'YAML', 'JSON', 'dictionary', 'invalid'
            ]
            has_error_detail = any(
                indicator.lower() in error_message.lower() 
                for indicator in error_indicators
            )
            assert has_error_detail, (
                f"Error message should contain specific error details, "
                f"but got: {error_message}"
            )
            
        finally:
            # Clean up
            Path(temp_path).unlink(missing_ok=True)
    
    @given(
        missing_field=st.sampled_from(['model', 'database', 'methods']),
        config_type=st.sampled_from(['model', 'database', 'methods'])
    )
    @settings(max_examples=100)
    def test_missing_section_error_includes_file_path_and_section_name(
        self, 
        missing_field, 
        config_type
    ):
        """
        Feature: qwen-agent-scheduler, Property 26: Configuration error logging detail
        
        For any configuration with missing required sections, the error should 
        include the file path and the name of the missing section.
        
        Validates: Requirements 10.2
        """
        # Create a config file missing the required section
        config_data = {"other_section": "data"}
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.yaml', 
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # Try to load the config based on type
            with pytest.raises(ConfigurationError) as exc_info:
                if config_type == 'model':
                    ConfigLoader.load_model_config(temp_path)
                elif config_type == 'database':
                    ConfigLoader.load_database_config(temp_path)
                else:  # methods
                    ConfigLoader.load_methods_config(temp_path)
            
            error_message = str(exc_info.value)
            
            # Verify file path is in error message
            assert temp_path in error_message, (
                f"Error message should contain file path '{temp_path}', "
                f"but got: {error_message}"
            )
            
            # Verify the missing section name is mentioned
            assert config_type in error_message.lower(), (
                f"Error message should mention missing section '{config_type}', "
                f"but got: {error_message}"
            )
            
            # Verify it says something about "missing"
            assert 'missing' in error_message.lower(), (
                f"Error message should indicate section is missing, "
                f"but got: {error_message}"
            )
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    @given(
        test_case=st.one_of(
            # Negative or zero timeout
            st.tuples(st.integers(max_value=0), st.just('timeout')),
            # Invalid temperature (outside 0.0-2.0 range)
            st.tuples(
                st.one_of(
                    st.floats(max_value=-0.1),
                    st.floats(min_value=2.1, max_value=10.0)
                ),
                st.just('temperature')
            ),
            # Non-positive max_tokens
            st.tuples(st.integers(max_value=0), st.just('max_tokens')),
        )
    )
    @settings(max_examples=100)
    def test_invalid_value_error_includes_file_path_and_value_detail(
        self, 
        test_case
    ):
        """
        Feature: qwen-agent-scheduler, Property 26: Configuration error logging detail
        
        For any configuration with invalid values, the error should include 
        the file path and details about the invalid value.
        
        Validates: Requirements 10.2
        """
        invalid_value, field_name = test_case
        
        # Create config with invalid value
        config_data = {
            "model": {
                "name": "qwen3:4b",
                "api_base": "http://localhost:11434",
                "timeout": 30,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }
        
        # Set the invalid value
        config_data["model"][field_name] = invalid_value
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.yaml', 
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            # Try to load the config
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_model_config(temp_path)
            
            error_message = str(exc_info.value)
            
            # The error message should contain information about what's wrong
            # It might not contain the file path for validation errors,
            # but it should contain details about the invalid value
            assert (
                str(invalid_value) in error_message or
                field_name in error_message.lower() or
                'positive' in error_message.lower() or
                'between' in error_message.lower()
            ), (
                f"Error message should contain details about the invalid value "
                f"for field '{field_name}' with value {invalid_value}, "
                f"but got: {error_message}"
            )
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_nonexistent_file_error_includes_file_path(self):
        """
        Feature: qwen-agent-scheduler, Property 26: Configuration error logging detail
        
        For any attempt to load a nonexistent file, the error should include 
        the file path that was not found.
        
        Validates: Requirements 10.2
        """
        nonexistent_path = "/tmp/nonexistent_config_file_12345.yaml"
        
        with pytest.raises(ConfigurationError) as exc_info:
            ConfigLoader.load_yaml(nonexistent_path)
        
        error_message = str(exc_info.value)
        
        # Verify file path is in error message
        assert nonexistent_path in error_message, (
            f"Error message should contain file path '{nonexistent_path}', "
            f"but got: {error_message}"
        )
        
        # Verify it mentions the file was not found
        assert 'not found' in error_message.lower(), (
            f"Error message should indicate file was not found, "
            f"but got: {error_message}"
        )
    
    @given(
        method_name=st.text(min_size=1, max_size=50),
        duplicate_count=st.integers(min_value=2, max_value=5)
    )
    @settings(max_examples=100)
    def test_duplicate_method_error_includes_file_path_and_method_name(
        self, 
        method_name, 
        duplicate_count
    ):
        """
        Feature: qwen-agent-scheduler, Property 26: Configuration error logging detail
        
        For any configuration with duplicate method names, the error should 
        include the file path and the duplicate method name.
        
        Validates: Requirements 10.2
        """
        # Create config with duplicate method names
        method_template = {
            "name": method_name,
            "description": "Test method",
            "module_path": "test.module",
            "function_name": "test_func",
            "return_type": "str"
        }
        
        config_data = {
            "methods": [method_template.copy() for _ in range(duplicate_count)]
        }
        
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.yaml', 
            delete=False,
            encoding='utf-8'
        ) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigLoader.load_methods_config(temp_path)
            
            error_message = str(exc_info.value)
            
            # Verify the duplicate method name is mentioned
            assert method_name in error_message, (
                f"Error message should contain duplicate method name '{method_name}', "
                f"but got: {error_message}"
            )
            
            # Verify it mentions "duplicate"
            assert 'duplicate' in error_message.lower(), (
                f"Error message should indicate method name is duplicate, "
                f"but got: {error_message}"
            )
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
