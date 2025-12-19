"""Tests for ConfigParser class

Tests the configuration parsing functionality for both JSON and YAML formats.
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.config_parser import ConfigParser
from shared import ConfigurationError, ModelConfig, MethodConfig


class TestConfigParser:
    """Test suite for ConfigParser"""
    
    def test_load_model_config_yaml(self):
        """Test loading model config from YAML file"""
        parser = ConfigParser()
        config = parser.load_model_config('config/model_config.yaml')
        
        assert isinstance(config, ModelConfig)
        assert config.model_name == "qwen3:4b"
        assert config.api_base == "http://localhost:11434"
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
    
    def test_load_model_config_json(self):
        """Test loading model config from JSON file"""
        parser = ConfigParser()
        config = parser.load_model_config('config/model_config.json')
        
        assert isinstance(config, ModelConfig)
        assert config.model_name == "qwen3:4b"
        assert config.api_base == "http://localhost:11434"
        assert config.timeout == 30
        assert config.temperature == 0.7
        assert config.max_tokens == 2000
    
    def test_load_methods_config_yaml(self):
        """Test loading methods config from YAML file"""
        parser = ConfigParser()
        methods = parser.load_methods_config('config/methods.yaml')
        
        assert isinstance(methods, list)
        assert len(methods) == 2
        
        # Check first method
        weather_method = methods[0]
        assert isinstance(weather_method, MethodConfig)
        assert weather_method.name == "get_weather"
        assert weather_method.description == "获取指定城市的天气信息"
        assert weather_method.module_path == "tools.weather"
        assert weather_method.function_name == "get_weather"
        assert weather_method.return_type == "dict"
        assert len(weather_method.parameters) == 2
        
        # Check parameters
        city_param = weather_method.parameters[0]
        assert city_param.name == "city"
        assert city_param.type == "string"
        assert city_param.required is True
        
        unit_param = weather_method.parameters[1]
        assert unit_param.name == "unit"
        assert unit_param.type == "string"
        assert unit_param.required is False
        assert unit_param.default == "celsius"
        
        # Check second method
        calc_method = methods[1]
        assert calc_method.name == "calculate"
        assert calc_method.description == "执行数学计算"
        assert len(calc_method.parameters) == 1
    
    def test_load_methods_config_json(self):
        """Test loading methods config from JSON file"""
        parser = ConfigParser()
        methods = parser.load_methods_config('config/methods.json')
        
        assert isinstance(methods, list)
        assert len(methods) == 2
        
        # Check first method
        weather_method = methods[0]
        assert isinstance(weather_method, MethodConfig)
        assert weather_method.name == "get_weather"
        assert weather_method.description == "获取指定城市的天气信息"
        assert len(weather_method.parameters) == 2
        
        # Check second method
        calc_method = methods[1]
        assert calc_method.name == "calculate"
        assert len(calc_method.parameters) == 1
    
    def test_unsupported_file_format(self):
        """Test that unsupported file formats raise error"""
        parser = ConfigParser()
        
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b'test')
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_model_config(temp_path)
            
            assert "Unsupported file format" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_file(self):
        """Test that missing files raise error"""
        parser = ConfigParser()
        
        with pytest.raises(ConfigurationError) as exc_info:
            parser.load_model_config('nonexistent.yaml')
        
        assert "not found" in str(exc_info.value)
    
    def test_invalid_json(self):
        """Test that invalid JSON raises error"""
        parser = ConfigParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{ invalid json }')
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_model_config(temp_path)
            
            assert "Failed to parse JSON" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_model_section(self):
        """Test that missing model section raises error"""
        parser = ConfigParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"other": "data"}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_model_config(temp_path)
            
            assert "missing required 'model' section" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_missing_methods_section(self):
        """Test that missing methods section raises error"""
        parser = ConfigParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"other": "data"}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_methods_config(temp_path)
            
            assert "missing required 'methods' section" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_duplicate_method_names(self):
        """Test that duplicate method names raise error"""
        parser = ConfigParser()
        
        config_data = {
            "methods": [
                {
                    "name": "test_method",
                    "description": "Test",
                    "module_path": "test",
                    "function_name": "test",
                    "return_type": "str"
                },
                {
                    "name": "test_method",
                    "description": "Duplicate",
                    "module_path": "test",
                    "function_name": "test",
                    "return_type": "str"
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_methods_config(temp_path)
            
            assert "Duplicate method name" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_empty_methods_list(self):
        """Test that empty methods list raises error"""
        parser = ConfigParser()
        
        config_data = {"methods": []}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_methods_config(temp_path)
            
            assert "cannot be empty" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_model_config_values(self):
        """Test that invalid model config values raise errors"""
        parser = ConfigParser()
        
        # Test negative timeout
        config_data = {
            "model": {
                "name": "qwen3:4b",
                "api_base": "http://localhost:11434",
                "timeout": -5
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                parser.load_model_config(temp_path)
            
            assert "Timeout must be positive" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()
    
    def test_format_equivalence(self):
        """Test that JSON and YAML formats produce equivalent results"""
        parser = ConfigParser()
        
        yaml_config = parser.load_model_config('config/model_config.yaml')
        json_config = parser.load_model_config('config/model_config.json')
        
        assert yaml_config.model_name == json_config.model_name
        assert yaml_config.api_base == json_config.api_base
        assert yaml_config.timeout == json_config.timeout
        assert yaml_config.temperature == json_config.temperature
        assert yaml_config.max_tokens == json_config.max_tokens
        
        yaml_methods = parser.load_methods_config('config/methods.yaml')
        json_methods = parser.load_methods_config('config/methods.json')
        
        assert len(yaml_methods) == len(json_methods)
        
        for yaml_method, json_method in zip(yaml_methods, json_methods):
            assert yaml_method.name == json_method.name
            assert yaml_method.description == json_method.description
            assert yaml_method.module_path == json_method.module_path
            assert yaml_method.function_name == json_method.function_name
            assert yaml_method.return_type == json_method.return_type
            assert len(yaml_method.parameters) == len(json_method.parameters)
