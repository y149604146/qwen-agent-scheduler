"""Method Executor for Agent Scheduler Brain

This module provides the MethodExecutor class for dynamically executing
registered methods with parameter validation, type conversion, and error handling.
"""

import logging
import importlib
import signal
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
import time

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import MethodMetadata, ExecutionResult


logger = logging.getLogger(__name__)


class MethodExecutorError(Exception):
    """Raised when method execution operations fail"""
    pass


class TimeoutError(MethodExecutorError):
    """Raised when method execution exceeds timeout"""
    pass


@contextmanager
def timeout_context(seconds: int):
    """Context manager for timeout control
    
    Args:
        seconds: Timeout duration in seconds
        
    Raises:
        TimeoutError: If execution exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Method execution exceeded timeout of {seconds} seconds")
    
    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        # Restore the old handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class MethodExecutor:
    """Executes registered methods dynamically with validation and error handling
    
    This class provides dynamic method execution capabilities with:
    - Parameter validation against method metadata
    - Type conversion for parameters
    - Exception handling and error formatting
    - Timeout control for method execution
    
    Attributes:
        methods: Dictionary mapping method names to MethodMetadata
        default_timeout: Default timeout in seconds for method execution
    """
    
    def __init__(self, methods: Dict[str, MethodMetadata], default_timeout: int = 30):
        """Initialize MethodExecutor with method metadata
        
        Args:
            methods: Dictionary mapping method names to MethodMetadata objects
            default_timeout: Default timeout in seconds (default: 30)
        """
        self.methods = methods
        self.default_timeout = default_timeout
        self._method_cache: Dict[str, Callable] = {}
        
        logger.info(f"MethodExecutor initialized with {len(methods)} methods")
    
    def validate_params(self, method_name: str, params: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate method parameters against method metadata
        
        Validates that:
        - All required parameters are present
        - No unknown parameters are provided
        - Parameter types are compatible (basic validation)
        
        Args:
            method_name: Name of the method to validate parameters for
            params: Dictionary of parameter names to values
            
        Returns:
            Tuple of (is_valid, error_message). If valid, error_message is None.
        """
        if method_name not in self.methods:
            return False, f"Method '{method_name}' not found"
        
        method = self.methods[method_name]
        method_params = method.parameters
        
        # Check for required parameters
        for param in method_params:
            if param.required and param.name not in params:
                # Check if parameter has a default value
                if param.default is None:
                    return False, f"Required parameter '{param.name}' is missing"
        
        # Check for unknown parameters
        param_names = {p.name for p in method_params}
        for param_name in params.keys():
            if param_name not in param_names:
                return False, f"Unknown parameter '{param_name}'"
        
        logger.debug(f"Parameters validated successfully for method '{method_name}'")
        return True, None
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert a value to the target type
        
        Attempts to convert the value to the specified type. Supports:
        - string/str
        - int/integer
        - float/number
        - bool/boolean
        - dict/object
        - list/array
        
        Args:
            value: Value to convert
            target_type: Target type name
            
        Returns:
            Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        # Normalize type name
        target_type = target_type.lower()
        
        # If value is already the correct type, return it
        type_checks = {
            'string': str,
            'str': str,
            'int': int,
            'integer': int,
            'float': float,
            'number': (int, float),
            'bool': bool,
            'boolean': bool,
            'dict': dict,
            'object': dict,
            'list': list,
            'array': list
        }
        
        expected_type = type_checks.get(target_type)
        if expected_type and isinstance(value, expected_type):
            return value
        
        # Attempt conversion
        try:
            if target_type in ('string', 'str'):
                return str(value)
            elif target_type in ('int', 'integer'):
                return int(value)
            elif target_type in ('float', 'number'):
                return float(value)
            elif target_type in ('bool', 'boolean'):
                # Handle string boolean values
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes'):
                        return True
                    elif value.lower() in ('false', '0', 'no'):
                        return False
                return bool(value)
            elif target_type in ('dict', 'object'):
                if isinstance(value, str):
                    import json
                    return json.loads(value)
                return dict(value)
            elif target_type in ('list', 'array'):
                if isinstance(value, str):
                    import json
                    return json.loads(value)
                return list(value)
            else:
                # Unknown type, return as-is
                logger.warning(f"Unknown type '{target_type}', returning value as-is")
                return value
        except (ValueError, TypeError, Exception) as e:
            raise ValueError(f"Cannot convert value '{value}' to type '{target_type}': {e}")
    
    def _prepare_params(self, method_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare parameters for method execution
        
        Fills in default values for missing optional parameters and
        attempts type conversion for all parameters.
        
        Args:
            method_name: Name of the method
            params: Dictionary of provided parameters
            
        Returns:
            Dictionary of prepared parameters with defaults and type conversion
            
        Raises:
            ValueError: If type conversion fails
        """
        method = self.methods[method_name]
        prepared_params = {}
        
        for param in method.parameters:
            if param.name in params:
                # Parameter provided, attempt type conversion
                try:
                    prepared_params[param.name] = self._convert_type(params[param.name], param.type)
                except ValueError as e:
                    raise ValueError(f"Parameter '{param.name}': {e}")
            elif not param.required and param.default is not None:
                # Use default value for optional parameter
                prepared_params[param.name] = param.default
            elif not param.required:
                # Optional parameter without default, skip it
                continue
            # If required parameter is missing, validation should have caught it
        
        return prepared_params
    
    def _load_method(self, method_name: str) -> Callable:
        """Load the actual method function from its module
        
        Uses importlib to dynamically import the module and retrieve the function.
        Results are cached to avoid repeated imports.
        
        Args:
            method_name: Name of the method to load
            
        Returns:
            The callable method function
            
        Raises:
            MethodExecutorError: If method cannot be loaded
        """
        # Check cache first
        if method_name in self._method_cache:
            return self._method_cache[method_name]
        
        method = self.methods[method_name]
        
        try:
            # Import the module
            module = importlib.import_module(method.module_path)
            
            # Get the function from the module
            if not hasattr(module, method.function_name):
                raise MethodExecutorError(
                    f"Function '{method.function_name}' not found in module '{method.module_path}'"
                )
            
            func = getattr(module, method.function_name)
            
            # Verify it's callable
            if not callable(func):
                raise MethodExecutorError(
                    f"'{method.function_name}' in module '{method.module_path}' is not callable"
                )
            
            # Cache the function
            self._method_cache[method_name] = func
            logger.debug(f"Loaded method '{method_name}' from {method.module_path}.{method.function_name}")
            
            return func
            
        except ImportError as e:
            error_msg = f"Failed to import module '{method.module_path}': {e}"
            logger.error(error_msg)
            raise MethodExecutorError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to load method '{method_name}': {e}"
            logger.error(error_msg)
            raise MethodExecutorError(error_msg) from e
    
    def execute(self, method_name: str, params: Dict[str, Any], timeout: Optional[int] = None) -> ExecutionResult:
        """Execute a registered method with given parameters
        
        This method:
        1. Validates parameters
        2. Prepares parameters (type conversion, defaults)
        3. Loads the method function
        4. Executes with timeout control
        5. Returns formatted result or error
        
        Args:
            method_name: Name of the method to execute
            params: Dictionary of parameter names to values
            timeout: Timeout in seconds (uses default_timeout if None)
            
        Returns:
            ExecutionResult with success status, result/error, and execution time
        """
        start_time = time.time()
        
        # Check if method exists
        if method_name not in self.methods:
            error_msg = f"Method '{method_name}' not found"
            logger.error(error_msg)
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=time.time() - start_time
            )
        
        # Validate parameters
        is_valid, error_msg = self.validate_params(method_name, params)
        if not is_valid:
            logger.error(f"Parameter validation failed for '{method_name}': {error_msg}")
            return ExecutionResult(
                success=False,
                error=f"Parameter validation failed: {error_msg}",
                execution_time=time.time() - start_time
            )
        
        # Prepare parameters (type conversion and defaults)
        try:
            prepared_params = self._prepare_params(method_name, params)
        except ValueError as e:
            logger.error(f"Parameter preparation failed for '{method_name}': {e}")
            return ExecutionResult(
                success=False,
                error=f"Parameter preparation failed: {e}",
                execution_time=time.time() - start_time
            )
        
        # Load the method function
        try:
            func = self._load_method(method_name)
        except MethodExecutorError as e:
            logger.error(f"Failed to load method '{method_name}': {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time
            )
        
        # Execute the method with timeout control
        timeout_seconds = timeout if timeout is not None else self.default_timeout
        
        try:
            logger.info(f"Executing method '{method_name}' with params: {prepared_params}")
            
            # Note: signal.alarm only works on Unix systems
            # For Windows compatibility, we'll skip timeout for now
            # In production, consider using threading or multiprocessing
            if sys.platform != 'win32':
                with timeout_context(timeout_seconds):
                    result = func(**prepared_params)
            else:
                # On Windows, execute without timeout
                result = func(**prepared_params)
            
            execution_time = time.time() - start_time
            logger.info(f"Method '{method_name}' executed successfully in {execution_time:.3f}s")
            
            return ExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except TimeoutError as e:
            execution_time = time.time() - start_time
            error_msg = f"Method execution timeout: {e}"
            logger.error(f"Method '{method_name}' timed out after {execution_time:.3f}s")
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Method execution failed: {type(e).__name__}: {e}"
            logger.error(f"Method '{method_name}' failed: {error_msg}")
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=execution_time
            )
