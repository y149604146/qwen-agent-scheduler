"""Method Loader for Agent Scheduler Brain

This module provides the MethodLoader class for loading registered methods
from PostgreSQL database and converting them to qwen-agent tool format.
"""

import logging
from typing import List, Optional, Dict, Any
import psycopg2
from psycopg2.extras import RealDictCursor
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import DatabaseConfig, MethodMetadata
from shared.db_schema import DatabaseConnection


logger = logging.getLogger(__name__)


class MethodLoaderError(Exception):
    """Raised when method loading operations fail"""
    pass


class MethodLoader:
    """Loads registered methods from database and converts to qwen-agent format
    
    This class provides methods for loading method metadata from PostgreSQL
    and converting them to the tool definition format expected by qwen-agent.
    
    Attributes:
        db_connection: DatabaseConnection instance for connection pooling
    """
    
    def __init__(self, db_config: DatabaseConfig):
        """Initialize MethodLoader with database configuration
        
        Args:
            db_config: Database configuration object
            
        Raises:
            MethodLoaderError: If connection initialization fails
        """
        try:
            self.db_connection = DatabaseConnection(db_config)
            self.db_connection.initialize_pool()
            logger.info("MethodLoader initialized successfully")
        except psycopg2.Error as e:
            error_msg = f"Failed to initialize database connection: {e}"
            logger.error(error_msg)
            raise MethodLoaderError(error_msg) from e
    
    def load_all_methods(self) -> List[MethodMetadata]:
        """Load all registered methods from the database
        
        Returns:
            List of MethodMetadata objects for all registered methods.
            Returns empty list if no methods are registered.
            
        Raises:
            MethodLoaderError: If database query fails
        """
        conn = None
        cursor = None
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            select_sql = """
                SELECT id, name, description, parameters_json, return_type,
                       module_path, function_name, created_at, updated_at
                FROM registered_methods
                ORDER BY name;
            """
            
            cursor.execute(select_sql)
            rows = cursor.fetchall()
            
            if not rows:
                logger.warning("No methods found in database")
                return []
            
            methods = []
            for row in rows:
                try:
                    # Convert parameters_json to string if it's a dict
                    params_json = row['parameters_json']
                    if isinstance(params_json, dict):
                        params_json = json.dumps(params_json)
                    
                    method = MethodMetadata(
                        id=row['id'],
                        name=row['name'],
                        description=row['description'],
                        parameters_json=params_json,
                        return_type=row['return_type'],
                        module_path=row['module_path'],
                        function_name=row['function_name'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    methods.append(method)
                except (KeyError, json.JSONDecodeError) as e:
                    logger.error(f"Failed to deserialize method '{row.get('name', 'unknown')}': {e}")
                    # Skip this method and continue with others
                    continue
            
            logger.info(f"Successfully loaded {len(methods)} methods from database")
            return methods
            
        except psycopg2.Error as e:
            error_msg = f"Failed to load methods from database: {e}"
            logger.error(error_msg)
            raise MethodLoaderError(error_msg) from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_connection.return_connection(conn)
    
    def load_method_by_name(self, method_name: str) -> Optional[MethodMetadata]:
        """Load a specific method by its name
        
        Args:
            method_name: Name of the method to load
            
        Returns:
            MethodMetadata object if found, None otherwise
            
        Raises:
            MethodLoaderError: If database query fails
        """
        conn = None
        cursor = None
        
        try:
            conn = self.db_connection.get_connection()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            select_sql = """
                SELECT id, name, description, parameters_json, return_type,
                       module_path, function_name, created_at, updated_at
                FROM registered_methods
                WHERE name = %s;
            """
            
            cursor.execute(select_sql, (method_name,))
            row = cursor.fetchone()
            
            if not row:
                logger.info(f"Method '{method_name}' not found in database")
                return None
            
            # Convert parameters_json to string if it's a dict
            params_json = row['parameters_json']
            if isinstance(params_json, dict):
                params_json = json.dumps(params_json)
            
            method = MethodMetadata(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                parameters_json=params_json,
                return_type=row['return_type'],
                module_path=row['module_path'],
                function_name=row['function_name'],
                created_at=row['created_at'],
                updated_at=row['updated_at']
            )
            
            logger.info(f"Successfully loaded method '{method_name}' from database")
            return method
            
        except psycopg2.Error as e:
            error_msg = f"Failed to load method '{method_name}': {e}"
            logger.error(error_msg)
            raise MethodLoaderError(error_msg) from e
        except (json.JSONDecodeError, KeyError) as e:
            error_msg = f"Failed to deserialize method '{method_name}': {e}"
            logger.error(error_msg)
            raise MethodLoaderError(error_msg) from e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.db_connection.return_connection(conn)
    
    def convert_to_qwen_tools(self, methods: List[MethodMetadata]) -> List[Dict[str, Any]]:
        """Convert method metadata to qwen-agent tool definition format
        
        Converts a list of MethodMetadata objects to the tool definition format
        expected by qwen-agent framework.
        
        Args:
            methods: List of MethodMetadata objects to convert
            
        Returns:
            List of dictionaries in qwen-agent tool format. Each dictionary contains:
            - name: Tool name
            - description: Tool description
            - parameters: Parameter definitions in qwen-agent format
            
        Raises:
            MethodLoaderError: If conversion fails for any method
        """
        qwen_tools = []
        
        for method in methods:
            try:
                # Parse parameters from JSON
                parameters = method.parameters
                
                # Convert parameters to qwen-agent format
                # qwen-agent expects parameters in a specific schema format
                qwen_params = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for param in parameters:
                    # Map our type names to JSON schema types
                    type_mapping = {
                        "string": "string",
                        "str": "string",
                        "int": "integer",
                        "integer": "integer",
                        "float": "number",
                        "number": "number",
                        "bool": "boolean",
                        "boolean": "boolean",
                        "dict": "object",
                        "object": "object",
                        "list": "array",
                        "array": "array"
                    }
                    
                    param_type = type_mapping.get(param.type.lower(), "string")
                    
                    qwen_params["properties"][param.name] = {
                        "type": param_type,
                        "description": param.description
                    }
                    
                    # Add default value if present
                    if param.default is not None:
                        qwen_params["properties"][param.name]["default"] = param.default
                    
                    # Add to required list if parameter is required
                    if param.required:
                        qwen_params["required"].append(param.name)
                
                # Create qwen-agent tool definition
                qwen_tool = {
                    "name": method.name,
                    "description": method.description,
                    "parameters": qwen_params
                }
                
                qwen_tools.append(qwen_tool)
                logger.debug(f"Converted method '{method.name}' to qwen-agent tool format")
                
            except Exception as e:
                error_msg = f"Failed to convert method '{method.name}' to qwen-agent format: {e}"
                logger.error(error_msg)
                raise MethodLoaderError(error_msg) from e
        
        logger.info(f"Successfully converted {len(qwen_tools)} methods to qwen-agent tool format")
        return qwen_tools
    
    def close(self) -> None:
        """Close database connection pool
        
        Should be called when MethodLoader is no longer needed.
        """
        self.db_connection.close_pool()
        logger.info("MethodLoader closed")
