"""Integration tests for ConfigParser and MetadataValidator

This module tests the integration between configuration parsing
and metadata validation.
"""

import pytest
from pathlib import Path
import tempfile
import json

from src.config_parser import ConfigParser
from src.validator import MetadataValidator


class TestConfigParserValidatorIntegration:
    """Integration tests for ConfigParser and MetadataValidator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = ConfigParser()
        self.validator = MetadataValidator()
    
    def test_valid_config_passes_validation(self):
        """Test that methods loaded from valid config pass validation"""
        # Create a temporary config file
        config_data = {
            "methods": [
                {
                    "name": "get_weather",
                    "description": "Get weather information for a city",
                    "module_path": "tools.weather",
                    "function_name": "get_weather",
                    "parameters": [
                        {
                            "name": "city",
                            "type": "string",
                            "description": "Name of the city",
                            "required": True
                        },
                        {
                            "name": "unit",
                            "type": "string",
                            "description": "Temperature unit",
                            "required": False,
                            "default": "celsius"
                        }
                    ],
                    "return_type": "dict"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Load methods from config
            methods = self.parser.load_methods_config(config_path)
            
            # Validate all methods
            results = self.validator.validate_methods(methods)
            
            # All should be valid
            assert len(results) == 1
            assert results[0].valid is True
            assert len(results[0].errors) == 0
        finally:
            Path(config_path).unlink()
    
    def test_invalid_config_fails_validation(self):
        """Test that methods with invalid data fail validation"""
        # Create a config with invalid method name
        config_data = {
            "methods": [
                {
                    "name": "get-weather",  # Invalid: contains hyphen
                    "description": "Get weather information",
                    "module_path": "tools.weather",
                    "function_name": "get_weather",
                    "parameters": [],
                    "return_type": "dict"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Load methods from config
            methods = self.parser.load_methods_config(config_path)
            
            # Validate all methods
            results = self.validator.validate_methods(methods)
            
            # Should fail validation
            assert len(results) == 1
            assert results[0].valid is False
            assert any("not a valid python identifier" in error.lower() 
                      for error in results[0].errors)
        finally:
            Path(config_path).unlink()
    
    def test_multiple_methods_with_duplicate_names_detected(self):
        """Test that duplicate method names are detected during parsing"""
        from shared import ConfigurationError
        
        config_data = {
            "methods": [
                {
                    "name": "calculate",
                    "description": "First calculate method",
                    "module_path": "tools.math",
                    "function_name": "calculate1",
                    "parameters": [],
                    "return_type": "float"
                },
                {
                    "name": "calculate",  # Duplicate name
                    "description": "Second calculate method",
                    "module_path": "tools.math",
                    "function_name": "calculate2",
                    "parameters": [],
                    "return_type": "int"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # ConfigParser should detect duplicate names during loading
            with pytest.raises(ConfigurationError) as exc_info:
                methods = self.parser.load_methods_config(config_path)
            
            assert "duplicate method name" in str(exc_info.value).lower()
        finally:
            Path(config_path).unlink()
    
    def test_method_with_invalid_parameter_type_fails(self):
        """Test that invalid parameter types are caught"""
        config_data = {
            "methods": [
                {
                    "name": "process_data",
                    "description": "Process some data",
                    "module_path": "tools.processor",
                    "function_name": "process",
                    "parameters": [
                        {
                            "name": "data",
                            "type": "CustomType",  # Invalid type
                            "description": "Data to process",
                            "required": True
                        }
                    ],
                    "return_type": "dict"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name
        
        try:
            # Load methods from config
            methods = self.parser.load_methods_config(config_path)
            
            # Validate all methods
            results = self.validator.validate_methods(methods)
            
            # Should fail validation
            assert len(results) == 1
            assert results[0].valid is False
            assert any("has invalid type" in error.lower() for error in results[0].errors)
        finally:
            Path(config_path).unlink()
