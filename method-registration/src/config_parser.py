"""Configuration parser for Method Registration System

This module provides the ConfigParser class that loads and parses
configuration files in both JSON and YAML formats for method registration.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

from shared import (
    ModelConfig,
    MethodConfig,
    ConfigLoader,
    ConfigurationError
)


class ConfigParser:
    """Parser for configuration files supporting JSON and YAML formats
    
    This class provides methods to load model configuration and method
    registration configuration from files in either JSON or YAML format.
    """
    
    @staticmethod
    def _detect_format(file_path: str) -> str:
        """Detect file format based on extension
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Format string: 'json' or 'yaml'
            
        Raises:
            ConfigurationError: If format cannot be determined
        """
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix in ['.json']:
            return 'json'
        elif suffix in ['.yaml', '.yml']:
            return 'yaml'
        else:
            raise ConfigurationError(
                f"Unsupported file format: {suffix}. "
                f"Supported formats: .json, .yaml, .yml"
            )
    
    @staticmethod
    def _load_json(file_path: str) -> Dict[str, Any]:
        """Load JSON file and return parsed content
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON content as dictionary
            
        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        path = Path(file_path)
        
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {file_path}")
        
        if not path.is_file():
            raise ConfigurationError(f"Configuration path is not a file: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                
            if content is None:
                raise ConfigurationError(f"Configuration file is empty: {file_path}")
                
            if not isinstance(content, dict):
                raise ConfigurationError(
                    f"Configuration file must contain a JSON object: {file_path}"
                )
                
            return content
            
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Failed to parse JSON file {file_path}: {str(e)}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read configuration file {file_path}: {str(e)}"
            )
    
    @staticmethod
    def _load_file(file_path: str) -> Dict[str, Any]:
        """Load configuration file in JSON or YAML format
        
        Args:
            file_path: Path to configuration file
            
        Returns:
            Parsed configuration as dictionary
            
        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        file_format = ConfigParser._detect_format(file_path)
        
        if file_format == 'json':
            return ConfigParser._load_json(file_path)
        else:  # yaml
            return ConfigLoader.load_yaml(file_path)
    
    def load_model_config(self, config_path: str) -> ModelConfig:
        """Load model configuration from JSON or YAML file
        
        Supports both JSON and YAML formats. Format is auto-detected
        based on file extension (.json, .yaml, .yml).
        
        Expected structure:
        ```yaml
        model:
          name: "qwen3:4b"
          api_base: "http://localhost:11434"
          timeout: 30
          temperature: 0.7
          max_tokens: 2000
        ```
        
        Or in JSON:
        ```json
        {
          "model": {
            "name": "qwen3:4b",
            "api_base": "http://localhost:11434",
            "timeout": 30,
            "temperature": 0.7,
            "max_tokens": 2000
          }
        }
        ```
        
        Args:
            config_path: Path to model configuration file
            
        Returns:
            ModelConfig object
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        config_data = self._load_file(config_path)
        
        # Validate model section exists
        if 'model' not in config_data:
            raise ConfigurationError(
                f"Configuration file {config_path} missing required 'model' section"
            )
        
        model_data = config_data['model']
        
        if not isinstance(model_data, dict):
            raise ConfigurationError(
                f"'model' section must be a dictionary in {config_path}"
            )
        
        # Validate required fields
        required_fields = ['name', 'api_base']
        missing_fields = [field for field in required_fields if field not in model_data]
        
        if missing_fields:
            raise ConfigurationError(
                f"Model configuration missing required fields: {', '.join(missing_fields)}"
            )
        
        # Extract values with defaults
        try:
            model_config = ModelConfig(
                model_name=str(model_data['name']),
                api_base=str(model_data['api_base']),
                timeout=int(model_data.get('timeout', 30)),
                temperature=float(model_data.get('temperature', 0.7)),
                max_tokens=int(model_data.get('max_tokens', 2000))
            )
        except (ValueError, TypeError) as e:
            raise ConfigurationError(
                f"Invalid data type in model configuration: {str(e)}"
            )
        
        # Validate values
        if not model_config.model_name:
            raise ConfigurationError("Model name cannot be empty")
        
        if not model_config.api_base:
            raise ConfigurationError("API base URL cannot be empty")
        
        if model_config.timeout <= 0:
            raise ConfigurationError(f"Timeout must be positive, got {model_config.timeout}")
        
        if not 0.0 <= model_config.temperature <= 2.0:
            raise ConfigurationError(
                f"Temperature must be between 0.0 and 2.0, got {model_config.temperature}"
            )
        
        if model_config.max_tokens <= 0:
            raise ConfigurationError(
                f"Max tokens must be positive, got {model_config.max_tokens}"
            )
        
        return model_config
    
    def load_methods_config(self, config_path: str) -> List[MethodConfig]:
        """Load method registration configuration from JSON or YAML file
        
        Supports both JSON and YAML formats. Format is auto-detected
        based on file extension (.json, .yaml, .yml).
        
        Expected structure:
        ```yaml
        methods:
          - name: "get_weather"
            description: "Get weather information"
            module_path: "tools.weather"
            function_name: "get_weather"
            parameters:
              - name: "city"
                type: "string"
                description: "City name"
                required: true
              - name: "unit"
                type: "string"
                description: "Temperature unit"
                required: false
                default: "celsius"
            return_type: "dict"
        ```
        
        Or in JSON:
        ```json
        {
          "methods": [
            {
              "name": "get_weather",
              "description": "Get weather information",
              "module_path": "tools.weather",
              "function_name": "get_weather",
              "parameters": [
                {
                  "name": "city",
                  "type": "string",
                  "description": "City name",
                  "required": true
                }
              ],
              "return_type": "dict"
            }
          ]
        }
        ```
        
        Args:
            config_path: Path to methods configuration file
            
        Returns:
            List of MethodConfig objects
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        # Use the shared ConfigLoader's method loading logic
        # but with our file loading that supports both JSON and YAML
        config_data = self._load_file(config_path)
        
        # Validate methods section exists
        if 'methods' not in config_data:
            raise ConfigurationError(
                f"Configuration file {config_path} missing required 'methods' section"
            )
        
        methods_data = config_data['methods']
        
        if not isinstance(methods_data, list):
            raise ConfigurationError(
                f"'methods' section must be a list in {config_path}"
            )
        
        if len(methods_data) == 0:
            raise ConfigurationError(
                f"'methods' section cannot be empty in {config_path}"
            )
        
        # Delegate to shared ConfigLoader for parsing the methods data
        # We'll use a temporary YAML approach by reusing the logic
        from shared.models import MethodParameter
        
        methods = []
        method_names_seen = set()
        
        for idx, method_data in enumerate(methods_data):
            if not isinstance(method_data, dict):
                raise ConfigurationError(
                    f"Method at index {idx} must be a dictionary"
                )
            
            # Validate required method fields
            required_fields = ['name', 'description', 'module_path', 'function_name', 'return_type']
            missing_fields = [field for field in required_fields if field not in method_data]
            
            if missing_fields:
                raise ConfigurationError(
                    f"Method at index {idx} missing required fields: {', '.join(missing_fields)}"
                )
            
            method_name = method_data['name']
            
            # Check for duplicate method names
            if method_name in method_names_seen:
                raise ConfigurationError(
                    f"Duplicate method name found: '{method_name}'"
                )
            method_names_seen.add(method_name)
            
            # Parse parameters
            parameters = []
            if 'parameters' in method_data:
                params_data = method_data['parameters']
                
                if not isinstance(params_data, list):
                    raise ConfigurationError(
                        f"Parameters for method '{method_name}' must be a list"
                    )
                
                for param_idx, param_data in enumerate(params_data):
                    if not isinstance(param_data, dict):
                        raise ConfigurationError(
                            f"Parameter at index {param_idx} for method '{method_name}' must be a dictionary"
                        )
                    
                    # Validate required parameter fields
                    param_required_fields = ['name', 'type', 'description']
                    param_missing_fields = [
                        field for field in param_required_fields 
                        if field not in param_data
                    ]
                    
                    if param_missing_fields:
                        raise ConfigurationError(
                            f"Parameter at index {param_idx} for method '{method_name}' "
                            f"missing required fields: {', '.join(param_missing_fields)}"
                        )
                    
                    try:
                        param = MethodParameter(
                            name=str(param_data['name']),
                            type=str(param_data['type']),
                            description=str(param_data['description']),
                            required=bool(param_data.get('required', True)),
                            default=param_data.get('default')
                        )
                        parameters.append(param)
                    except (ValueError, TypeError) as e:
                        raise ConfigurationError(
                            f"Invalid parameter data for method '{method_name}': {str(e)}"
                        )
            
            # Create MethodConfig
            try:
                method_config = MethodConfig(
                    name=str(method_data['name']),
                    description=str(method_data['description']),
                    parameters=parameters,
                    return_type=str(method_data['return_type']),
                    module_path=str(method_data['module_path']),
                    function_name=str(method_data['function_name'])
                )
                methods.append(method_config)
            except (ValueError, TypeError) as e:
                raise ConfigurationError(
                    f"Invalid method data at index {idx}: {str(e)}"
                )
        
        return methods
