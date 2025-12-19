"""Metadata validator for Method Registration System

This module provides the MetadataValidator class that validates method
metadata for completeness and correctness before database registration.
"""

import re
from typing import List, Set

from shared import (
    MethodConfig,
    ValidationResult
)


class MetadataValidator:
    """Validator for method metadata
    
    This class validates method configurations to ensure they meet
    all requirements before being registered in the database.
    
    Validation rules:
    - Method names must be valid Python identifiers (2-100 characters)
    - All required fields must be present and non-empty
    - Parameters must have name, type, and description
    - Return types must be valid Python type strings
    - No duplicate method names in batch validation
    """
    
    # Valid Python type strings for return types and parameters
    VALID_TYPES = {
        'string', 'str',
        'int', 'integer',
        'float',
        'bool', 'boolean',
        'dict', 'dictionary',
        'list', 'array',
        'tuple',
        'set',
        'None', 'NoneType',
        'Any',
        'bytes',
        'bytearray'
    }
    
    def __init__(self):
        """Initialize the validator"""
        pass
    
    def validate_method(self, method: MethodConfig) -> ValidationResult:
        """Validate a single method configuration
        
        Performs comprehensive validation including:
        - Method name validation (Python identifier rules, length 2-100)
        - Description validation (non-empty, max 1000 characters)
        - Parameter validation (name, type, description required)
        - Return type validation (valid Python type)
        - Module path and function name validation
        
        Args:
            method: MethodConfig object to validate
            
        Returns:
            ValidationResult with validation status and any error messages
        """
        result = ValidationResult(valid=True, method_name=method.name)
        
        # Validate method name
        if not method.name:
            result.add_error("Method name is required and cannot be empty")
        else:
            # Check length
            if len(method.name) < 2:
                result.add_error(
                    f"Method name '{method.name}' is too short (minimum 2 characters)"
                )
            elif len(method.name) > 100:
                result.add_error(
                    f"Method name '{method.name}' is too long (maximum 100 characters)"
                )
            
            # Check if it's a valid Python identifier
            if not self._is_valid_identifier(method.name):
                result.add_error(
                    f"Method name '{method.name}' is not a valid Python identifier. "
                    f"Must start with letter or underscore, contain only letters, "
                    f"digits, and underscores, and not be a Python keyword"
                )
        
        # Validate description
        if not method.description:
            result.add_error("Method description is required and cannot be empty")
        elif len(method.description) > 1000:
            result.add_error(
                f"Method description is too long (maximum 1000 characters, got {len(method.description)})"
            )
        
        # Validate module path
        if not method.module_path:
            result.add_error("Module path is required and cannot be empty")
        elif not self._is_valid_module_path(method.module_path):
            result.add_error(
                f"Module path '{method.module_path}' is not valid. "
                f"Must be a valid Python module path (e.g., 'package.module')"
            )
        
        # Validate function name
        if not method.function_name:
            result.add_error("Function name is required and cannot be empty")
        elif not self._is_valid_identifier(method.function_name):
            result.add_error(
                f"Function name '{method.function_name}' is not a valid Python identifier"
            )
        
        # Validate return type
        if not method.return_type:
            result.add_error("Return type is required and cannot be empty")
        elif not self._is_valid_type(method.return_type):
            result.add_error(
                f"Return type '{method.return_type}' is not a recognized Python type. "
                f"Valid types: {', '.join(sorted(self.VALID_TYPES))}"
            )
        
        # Validate parameters
        if method.parameters is not None:
            param_names_seen: Set[str] = set()
            
            for idx, param in enumerate(method.parameters):
                # Check parameter name
                if not param.name:
                    result.add_error(
                        f"Parameter at index {idx} is missing required field 'name'"
                    )
                else:
                    # Check for duplicate parameter names
                    if param.name in param_names_seen:
                        result.add_error(
                            f"Duplicate parameter name '{param.name}' found"
                        )
                    param_names_seen.add(param.name)
                    
                    # Validate parameter name is a valid identifier
                    if not self._is_valid_identifier(param.name):
                        result.add_error(
                            f"Parameter name '{param.name}' is not a valid Python identifier"
                        )
                
                # Check parameter type
                if not param.type:
                    result.add_error(
                        f"Parameter '{param.name if param.name else f'at index {idx}'}' "
                        f"is missing required field 'type'"
                    )
                elif not self._is_valid_type(param.type):
                    result.add_error(
                        f"Parameter '{param.name}' has invalid type '{param.type}'. "
                        f"Valid types: {', '.join(sorted(self.VALID_TYPES))}"
                    )
                
                # Check parameter description
                if not param.description:
                    result.add_error(
                        f"Parameter '{param.name if param.name else f'at index {idx}'}' "
                        f"is missing required field 'description'"
                    )
                elif len(param.description) > 500:
                    result.add_error(
                        f"Parameter '{param.name}' description is too long "
                        f"(maximum 500 characters, got {len(param.description)})"
                    )
        
        return result
    
    def validate_methods(self, methods: List[MethodConfig]) -> List[ValidationResult]:
        """Validate multiple method configurations
        
        Performs individual validation on each method and also checks
        for duplicate method names across the entire list.
        
        Args:
            methods: List of MethodConfig objects to validate
            
        Returns:
            List of ValidationResult objects, one per method
        """
        results = []
        method_names_seen: Set[str] = set()
        duplicate_names: Set[str] = set()
        
        # First pass: identify duplicate names
        for method in methods:
            if method.name:
                if method.name in method_names_seen:
                    duplicate_names.add(method.name)
                method_names_seen.add(method.name)
        
        # Second pass: validate each method
        for method in methods:
            result = self.validate_method(method)
            
            # Add duplicate name error if applicable
            if method.name and method.name in duplicate_names:
                result.add_error(
                    f"Duplicate method name '{method.name}' found in configuration"
                )
            
            results.append(result)
        
        return results
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if a string is a valid Python identifier
        
        A valid identifier:
        - Starts with a letter (a-z, A-Z) or underscore (_)
        - Contains only letters, digits, and underscores
        - Is not a Python keyword
        
        Args:
            name: String to check
            
        Returns:
            True if valid identifier, False otherwise
        """
        if not name:
            return False
        
        # Check if it's a valid identifier using Python's built-in check
        if not name.isidentifier():
            return False
        
        # Check if it's a Python keyword
        import keyword
        if keyword.iskeyword(name):
            return False
        
        return True
    
    def _is_valid_module_path(self, path: str) -> bool:
        """Check if a string is a valid Python module path
        
        A valid module path consists of valid identifiers separated by dots.
        Examples: 'module', 'package.module', 'package.subpackage.module'
        
        Args:
            path: String to check
            
        Returns:
            True if valid module path, False otherwise
        """
        if not path:
            return False
        
        # Split by dots and check each part
        parts = path.split('.')
        
        if len(parts) == 0:
            return False
        
        # Each part must be a valid identifier
        for part in parts:
            if not self._is_valid_identifier(part):
                return False
        
        return True
    
    def _is_valid_type(self, type_str: str) -> bool:
        """Check if a string represents a valid Python type
        
        Args:
            type_str: Type string to check
            
        Returns:
            True if valid type, False otherwise
        """
        if not type_str:
            return False
        
        # Check against known valid types
        return type_str in self.VALID_TYPES
