"""Data models for qwen-agent-scheduler system

This module defines all shared data models used by both
Method Registration System and Agent Scheduler Brain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json


@dataclass
class ModelConfig:
    """Configuration for the LLM model (Ollama/qwen)
    
    Attributes:
        model_name: Name of the model (e.g., "qwen3:4b")
        api_base: Ollama API endpoint (e.g., "http://localhost:11434")
        timeout: Request timeout in seconds
        temperature: Generation temperature (0.0-1.0)
        max_tokens: Maximum number of tokens to generate
    """
    model_name: str
    api_base: str
    timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class MethodParameter:
    """Definition of a method parameter
    
    Attributes:
        name: Parameter name
        type: Parameter type (e.g., "string", "int", "float")
        description: Human-readable description of the parameter
        required: Whether this parameter is required
        default: Default value if parameter is optional
    """
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'type': self.type,
            'description': self.description,
            'required': self.required,
            'default': self.default
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MethodParameter':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            type=data['type'],
            description=data['description'],
            required=data.get('required', True),
            default=data.get('default')
        )


@dataclass
class MethodConfig:
    """Configuration for a method to be registered
    
    Attributes:
        name: Method name
        description: Human-readable description
        parameters: List of parameter definitions
        return_type: Return value type
        module_path: Python module path where method is defined
        function_name: Function name within the module
    """
    name: str
    description: str
    parameters: List[MethodParameter]
    return_type: str
    module_path: str
    function_name: str


@dataclass
class MethodMetadata:
    """Method metadata as stored in the database
    
    Attributes:
        id: Database primary key (None for new records)
        name: Method name
        description: Human-readable description
        parameters_json: JSON-serialized parameter list
        return_type: Return value type
        module_path: Python module path
        function_name: Function name
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    name: str
    description: str
    parameters_json: str
    return_type: str
    module_path: str
    function_name: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @property
    def parameters(self) -> List[MethodParameter]:
        """Deserialize parameters from JSON"""
        # Handle both string and already-parsed data
        if isinstance(self.parameters_json, str):
            params_data = json.loads(self.parameters_json)
        elif isinstance(self.parameters_json, list):
            params_data = self.parameters_json
        else:
            # If it's already a dict or other type, try to use it directly
            params_data = self.parameters_json
        
        return [MethodParameter.from_dict(p) for p in params_data]
    
    @classmethod
    def from_method_config(cls, config: MethodConfig) -> 'MethodMetadata':
        """Create MethodMetadata from MethodConfig"""
        params_json = json.dumps([p.to_dict() for p in config.parameters])
        return cls(
            name=config.name,
            description=config.description,
            parameters_json=params_json,
            return_type=config.return_type,
            module_path=config.module_path,
            function_name=config.function_name
        )
    
    def to_method_config(self) -> MethodConfig:
        """Convert to MethodConfig"""
        return MethodConfig(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            return_type=self.return_type,
            module_path=self.module_path,
            function_name=self.function_name
        )


@dataclass
class DatabaseConfig:
    """PostgreSQL database configuration
    
    Attributes:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        pool_size: Connection pool size
    """
    host: str
    port: int
    database: str
    user: str
    password: str
    pool_size: int = 5
    
    def get_connection_string(self) -> str:
        """Generate PostgreSQL connection string"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class ExecutionResult:
    """Result of method execution
    
    Attributes:
        success: Whether execution succeeded
        result: Return value from the method
        error: Error message if execution failed
        execution_time: Time taken to execute in seconds
    """
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0


@dataclass
class ValidationResult:
    """Result of method metadata validation
    
    Attributes:
        valid: Whether validation passed
        errors: List of validation error messages
        method_name: Name of the method being validated
    """
    valid: bool
    errors: List[str] = field(default_factory=list)
    method_name: Optional[str] = None
    
    def add_error(self, error: str) -> None:
        """Add a validation error"""
        self.valid = False
        self.errors.append(error)
