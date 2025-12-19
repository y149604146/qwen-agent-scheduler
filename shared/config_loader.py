"""Configuration loader for qwen-agent-scheduler system

This module provides functionality to load and validate YAML configuration files
for both model configuration and method registration.
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from .models import (
    ModelConfig,
    DatabaseConfig,
    MethodConfig,
    MethodParameter
)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded"""
    pass


class ConfigLoader:
    """Loads and validates YAML configuration files"""
    
    @staticmethod
    def load_yaml(file_path: str) -> Dict[str, Any]:
        """Load YAML file and return parsed content
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            Parsed YAML content as dictionary
            
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
                content = yaml.safe_load(f)
                
            if content is None:
                raise ConfigurationError(f"Configuration file is empty: {file_path}")
                
            if not isinstance(content, dict):
                raise ConfigurationError(
                    f"Configuration file must contain a YAML dictionary: {file_path}"
                )
                
            return content
            
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse YAML file {file_path}: {str(e)}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read configuration file {file_path}: {str(e)}"
            )
    
    @staticmethod
    def load_model_config(file_path: str) -> ModelConfig:
        """Load model configuration from YAML file
        
        Expected YAML structure:
        ```yaml
        model:
          name: "qwen3:4b"
          api_base: "http://localhost:11434"
          timeout: 30
          temperature: 0.7
          max_tokens: 2000
        ```
        
        Args:
            file_path: Path to model configuration YAML file
            
        Returns:
            ModelConfig object
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        config_data = ConfigLoader.load_yaml(file_path)
        
        # Validate model section exists
        if 'model' not in config_data:
            raise ConfigurationError(
                f"Configuration file {file_path} missing required 'model' section"
            )
        
        model_data = config_data['model']
        
        if not isinstance(model_data, dict):
            raise ConfigurationError(
                f"'model' section must be a dictionary in {file_path}"
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
    
    @staticmethod
    def load_database_config(file_path: str) -> DatabaseConfig:
        """Load database configuration from YAML file
        
        Expected YAML structure:
        ```yaml
        database:
          host: "localhost"
          port: 5432
          database: "test_db"
          user: "yuanyuan"
          password: "666666"
          pool_size: 5
        ```
        
        Args:
            file_path: Path to configuration YAML file
            
        Returns:
            DatabaseConfig object
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        config_data = ConfigLoader.load_yaml(file_path)
        
        # Validate database section exists
        if 'database' not in config_data:
            raise ConfigurationError(
                f"Configuration file {file_path} missing required 'database' section"
            )
        
        db_data = config_data['database']
        
        if not isinstance(db_data, dict):
            raise ConfigurationError(
                f"'database' section must be a dictionary in {file_path}"
            )
        
        # Validate required fields
        required_fields = ['host', 'port', 'database', 'user', 'password']
        missing_fields = [field for field in required_fields if field not in db_data]
        
        if missing_fields:
            raise ConfigurationError(
                f"Database configuration missing required fields: {', '.join(missing_fields)}"
            )
        
        # Extract values with defaults
        try:
            db_config = DatabaseConfig(
                host=str(db_data['host']),
                port=int(db_data['port']),
                database=str(db_data['database']),
                user=str(db_data['user']),
                password=str(db_data['password']),
                pool_size=int(db_data.get('pool_size', 5))
            )
        except (ValueError, TypeError) as e:
            raise ConfigurationError(
                f"Invalid data type in database configuration: {str(e)}"
            )
        
        # Validate values
        if not db_config.host:
            raise ConfigurationError("Database host cannot be empty")
        
        if not 1 <= db_config.port <= 65535:
            raise ConfigurationError(
                f"Database port must be between 1 and 65535, got {db_config.port}"
            )
        
        if not db_config.database:
            raise ConfigurationError("Database name cannot be empty")
        
        if not db_config.user:
            raise ConfigurationError("Database user cannot be empty")
        
        if db_config.pool_size <= 0:
            raise ConfigurationError(
                f"Pool size must be positive, got {db_config.pool_size}"
            )
        
        return db_config
    
    @staticmethod
    def load_methods_config(file_path: str) -> List[MethodConfig]:
        """Load method registration configuration from YAML file
        
        Expected YAML structure:
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
        
        Args:
            file_path: Path to methods configuration YAML file
            
        Returns:
            List of MethodConfig objects
            
        Raises:
            ConfigurationError: If configuration is invalid or missing required fields
        """
        config_data = ConfigLoader.load_yaml(file_path)
        
        # Validate methods section exists
        if 'methods' not in config_data:
            raise ConfigurationError(
                f"Configuration file {file_path} missing required 'methods' section"
            )
        
        methods_data = config_data['methods']
        
        if not isinstance(methods_data, list):
            raise ConfigurationError(
                f"'methods' section must be a list in {file_path}"
            )
        
        if len(methods_data) == 0:
            raise ConfigurationError(
                f"'methods' section cannot be empty in {file_path}"
            )
        
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


# Convenience functions
def load_model_config(file_path: str) -> ModelConfig:
    """Load model configuration from YAML file
    
    Args:
        file_path: Path to model configuration YAML file
        
    Returns:
        ModelConfig object
    """
    return ConfigLoader.load_model_config(file_path)


def load_database_config(file_path: str) -> DatabaseConfig:
    """Load database configuration from YAML file
    
    Args:
        file_path: Path to configuration YAML file
        
    Returns:
        DatabaseConfig object
    """
    return ConfigLoader.load_database_config(file_path)


def load_methods_config(file_path: str) -> List[MethodConfig]:
    """Load method registration configuration from YAML file
    
    Args:
        file_path: Path to methods configuration YAML file
        
    Returns:
        List of MethodConfig objects
    """
    return ConfigLoader.load_methods_config(file_path)
