# MethodLoader Implementation Documentation

## Overview

The `MethodLoader` class is responsible for loading registered methods from the PostgreSQL database and converting them to the format expected by the qwen-agent framework.

## Implementation Details

### Class: MethodLoader

Located in: `agent-scheduler/src/method_loader.py`

#### Initialization

```python
loader = MethodLoader(db_config)
```

Creates a database connection pool and initializes the loader.

#### Methods

##### 1. load_all_methods()

Loads all registered methods from the database.

**Returns:** `List[MethodMetadata]`

**Behavior:**
- Queries all methods from `registered_methods` table
- Orders results by method name
- Handles JSON deserialization of parameters
- Skips methods with invalid metadata and logs errors
- Returns empty list if no methods found (with warning log)

**Error Handling:**
- Raises `MethodLoaderError` if database query fails
- Logs and skips individual methods with deserialization errors

##### 2. load_method_by_name(method_name: str)

Loads a specific method by its name.

**Parameters:**
- `method_name`: Name of the method to load

**Returns:** `Optional[MethodMetadata]`

**Behavior:**
- Queries database for method with exact name match
- Returns `None` if method not found
- Handles JSON deserialization

**Error Handling:**
- Raises `MethodLoaderError` if database query fails
- Raises `MethodLoaderError` if deserialization fails

##### 3. convert_to_qwen_tools(methods: List[MethodMetadata])

Converts method metadata to qwen-agent tool definition format.

**Parameters:**
- `methods`: List of MethodMetadata objects to convert

**Returns:** `List[Dict[str, Any]]`

**Output Format:**
```json
{
  "name": "method_name",
  "description": "Method description",
  "parameters": {
    "type": "object",
    "properties": {
      "param_name": {
        "type": "string",
        "description": "Parameter description",
        "default": "optional_default_value"
      }
    },
    "required": ["required_param_names"]
  }
}
```

**Type Mapping:**
- `string`, `str` → `"string"`
- `int`, `integer` → `"integer"`
- `float`, `number` → `"number"`
- `bool`, `boolean` → `"boolean"`
- `dict`, `object` → `"object"`
- `list`, `array` → `"array"`
- Unknown types → `"string"` (default)

**Error Handling:**
- Raises `MethodLoaderError` if conversion fails for any method

##### 4. close()

Closes the database connection pool. Should be called when the loader is no longer needed.

## Requirements Validation

### Requirement 6.1: Method Loading Completeness
✅ `load_all_methods()` loads all methods from database and returns complete list

### Requirement 6.2: JSON Deserialization Correctness
✅ Properly deserializes `parameters_json` field from database
✅ Handles both string and dict formats from PostgreSQL JSONB
✅ Converts to `MethodParameter` objects

### Requirement 6.3: qwen-agent Tool Format Conversion
✅ Converts to correct schema with `name`, `description`, and `parameters`
✅ Maps parameter types to JSON schema types
✅ Handles required vs optional parameters
✅ Includes default values when present

### Requirement 6.4: Empty Database Handling
✅ Returns empty list when no methods registered
✅ Logs warning message

### Requirement 6.5: Incompatible Metadata Handling
✅ Skips methods with deserialization errors
✅ Logs error messages for problematic methods
✅ Continues processing remaining methods

## Usage Example

```python
from shared.models import DatabaseConfig
from agent_scheduler.src.method_loader import MethodLoader

# Initialize loader
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="test_db",
    user="postgres",
    password="password"
)

loader = MethodLoader(db_config)

try:
    # Load all methods
    methods = loader.load_all_methods()
    print(f"Loaded {len(methods)} methods")
    
    # Load specific method
    weather_method = loader.load_method_by_name("get_weather")
    if weather_method:
        print(f"Found method: {weather_method.name}")
    
    # Convert to qwen-agent format
    qwen_tools = loader.convert_to_qwen_tools(methods)
    
    # Use with qwen-agent
    # agent = Agent(tools=qwen_tools)
    
finally:
    loader.close()
```

## Testing

Tests are located in `agent-scheduler/tests/test_method_loader.py`

Run tests with:
```bash
pytest agent-scheduler/tests/test_method_loader.py -v
```

## Error Handling

All database errors are wrapped in `MethodLoaderError` with descriptive messages.

Common errors:
- Database connection failures
- Invalid JSON in parameters_json field
- Missing required fields in database records
- Type conversion errors

All errors are logged with appropriate log levels:
- `ERROR`: Critical failures that prevent operation
- `WARNING`: Non-critical issues (e.g., empty database)
- `INFO`: Normal operations
- `DEBUG`: Detailed operation information

## Performance Considerations

- Uses connection pooling for efficient database access
- Loads all methods in a single query
- Minimal memory overhead for conversion operations
- Suitable for hundreds of registered methods

## Future Enhancements

Potential improvements:
- Caching of loaded methods to reduce database queries
- Lazy loading of methods on demand
- Support for method versioning
- Batch conversion optimizations
