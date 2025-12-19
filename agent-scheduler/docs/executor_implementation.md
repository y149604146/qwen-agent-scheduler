# Method Executor Implementation

## Overview

The `MethodExecutor` class provides dynamic method execution capabilities for the Agent Scheduler Brain. It handles parameter validation, type conversion, error handling, and timeout control.

## Features

### 1. Parameter Validation
- Validates required parameters are present
- Detects unknown parameters
- Checks parameter types against method metadata

### 2. Type Conversion
- Automatic type conversion for parameters
- Supports: string, int, float, bool, dict, list
- Handles JSON string conversion for complex types

### 3. Error Handling
- Catches and formats exceptions from method execution
- Provides detailed error messages
- Returns structured ExecutionResult objects

### 4. Timeout Control
- Configurable timeout for method execution
- Default timeout: 30 seconds
- Platform-aware (Unix signal-based, Windows compatible)

### 5. Method Caching
- Caches loaded methods to avoid repeated imports
- Improves performance for repeated method calls

## Usage Example

```python
from shared.models import MethodMetadata, MethodParameter, DatabaseConfig
from agent_scheduler.src.method_loader import MethodLoader
from agent_scheduler.src.executor import MethodExecutor
import json

# Load methods from database
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="test_db",
    user="postgres",
    password="password"
)

loader = MethodLoader(db_config)
methods_list = loader.load_all_methods()

# Create methods dictionary
methods_dict = {m.name: m for m in methods_list}

# Initialize executor
executor = MethodExecutor(methods_dict, default_timeout=30)

# Execute a method
result = executor.execute(
    method_name="add_numbers",
    params={"a": 5, "b": 3}
)

if result.success:
    print(f"Result: {result.result}")
    print(f"Execution time: {result.execution_time:.3f}s")
else:
    print(f"Error: {result.error}")
```

## Integration with Agent Client

The executor is designed to work seamlessly with the AgentClient:

```python
from agent_scheduler.src.agent_client import AgentClient
from agent_scheduler.src.method_loader import MethodLoader
from agent_scheduler.src.executor import MethodExecutor

# Load methods and convert to qwen-agent format
loader = MethodLoader(db_config)
methods_list = loader.load_all_methods()
qwen_tools = loader.convert_to_qwen_tools(methods_list)

# Create methods dictionary for executor
methods_dict = {m.name: m for m in methods_list}
executor = MethodExecutor(methods_dict)

# Initialize agent client
agent_client = AgentClient(model_config, qwen_tools)

# Register executor with agent client
agent_client.register_tool_executor(
    lambda method_name, params: executor.execute(method_name, params)
)

# Process user task
response = agent_client.process_task("Add 5 and 3")
print(response.response)
```

## Method Execution Flow

1. **Validation**: Check if method exists and validate parameters
2. **Preparation**: Apply type conversion and fill in default values
3. **Loading**: Import the method module and function (cached)
4. **Execution**: Call the method with prepared parameters
5. **Result**: Return ExecutionResult with success/error information

## Error Handling

The executor handles various error scenarios:

- **Method not found**: Returns error if method doesn't exist
- **Parameter validation failure**: Returns error with specific validation issue
- **Type conversion failure**: Returns error if parameter cannot be converted
- **Module import failure**: Returns error if method module cannot be imported
- **Function not found**: Returns error if function doesn't exist in module
- **Execution exception**: Catches and returns formatted exception information
- **Timeout**: Returns error if execution exceeds timeout (Unix only)

## Type Conversion

The executor supports automatic type conversion:

| Input Type | Supported Conversions |
|------------|----------------------|
| string/str | Any value → string |
| int/integer | Numeric strings → int |
| float/number | Numeric strings → float |
| bool/boolean | "true"/"false"/"1"/"0" → bool |
| dict/object | JSON string → dict |
| list/array | JSON string → list |

## Performance Considerations

- **Method Caching**: Methods are cached after first load to avoid repeated imports
- **Connection Pooling**: Uses database connection pooling for efficient queries
- **Timeout Control**: Prevents long-running methods from blocking the system
- **Error Recovery**: Gracefully handles errors without crashing the system

## Testing

The executor includes comprehensive tests covering:

- Parameter validation (valid, missing, unknown)
- Type conversion (all supported types)
- Method execution (success, failure, exceptions)
- Error handling (various error scenarios)
- Method caching
- Custom timeout

Run tests with:
```bash
pytest agent-scheduler/tests/test_executor.py -v
```

## Platform Notes

### Windows
- Timeout control using `signal.alarm()` is not available on Windows
- Methods execute without timeout on Windows
- Consider using threading or multiprocessing for timeout on Windows

### Unix/Linux
- Full timeout support using signal handlers
- Methods are terminated if they exceed the timeout

## Future Enhancements

Potential improvements for the executor:

1. **Async Support**: Add async method execution support
2. **Resource Limits**: Add memory and CPU usage limits
3. **Retry Logic**: Add automatic retry for transient failures
4. **Metrics**: Add execution metrics and monitoring
5. **Sandboxing**: Add sandboxed execution for untrusted methods
6. **Windows Timeout**: Implement timeout using threading for Windows
