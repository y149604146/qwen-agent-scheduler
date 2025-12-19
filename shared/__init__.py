"""Shared modules - 共享模块

包含两个项目共用的数据模型、数据库Schema和配置加载器
"""

__version__ = "0.1.0"

from .models import (
    ModelConfig,
    MethodParameter,
    MethodConfig,
    MethodMetadata,
    DatabaseConfig,
    ExecutionResult,
    ValidationResult
)

from .db_schema import (
    DatabaseConnection,
    create_database_connection
)

from .config_loader import (
    ConfigLoader,
    ConfigurationError,
    load_model_config,
    load_database_config,
    load_methods_config
)

__all__ = [
    'ModelConfig',
    'MethodParameter',
    'MethodConfig',
    'MethodMetadata',
    'DatabaseConfig',
    'ExecutionResult',
    'ValidationResult',
    'DatabaseConnection',
    'create_database_connection',
    'ConfigLoader',
    'ConfigurationError',
    'load_model_config',
    'load_database_config',
    'load_methods_config'
]
