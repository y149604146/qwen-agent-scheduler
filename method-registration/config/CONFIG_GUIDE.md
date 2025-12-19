# Configuration Guide

This directory contains configuration files for the Method Registration System. The system supports both YAML and JSON formats.

## Configuration Files

### 1. Model Configuration Files

- **model_config.yaml** - YAML format (recommended, supports comments)
- **model_config.json** - JSON format (alternative)

These files configure:
- Ollama model settings
- PostgreSQL database connection
- Logging configuration

### 2. Method Registration Files

- **methods.yaml** - YAML format (recommended, supports comments)
- **methods.json** - JSON format (alternative)

These files define the methods to be registered in the database.

## Model Configuration Structure

### YAML Format (model_config.yaml)

```yaml
model:
  name: "qwen3:4b"                          # Ollama model name
  api_base: "http://localhost:11434"        # Ollama API endpoint
  timeout: 30                                # Request timeout (seconds)
  temperature: 0.7                           # Generation temperature (0.0-1.0)
  max_tokens: 2000                           # Maximum tokens to generate

database:
  host: "localhost"                          # PostgreSQL host
  port: 5432                                 # PostgreSQL port
  database: "test_db"                  # Database name
  user: "yuanyuan"                           # Database user
  password: "666666"                  # Database password
  pool_size: 5                               # Connection pool size

logging:
  level: "INFO"                              # Log level
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"                       # Log file path
```

### JSON Format (model_config.json)

```json
{
  "model": {
    "name": "qwen3:4b",
    "api_base": "http://localhost:11434",
    "timeout": 30,
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "database": "test_db",
    "user": "postgres",
    "password": "your_password",
    "pool_size": 5
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/app.log"
  }
}
```

## Method Registration Structure

### YAML Format (methods.yaml)

```yaml
methods:
  - name: "method_name"                      # Method name (Python identifier)
    description: "Method description"        # Description (1-1000 chars)
    module_path: "tools.module"              # Python module path
    function_name: "function_name"           # Function name
    parameters:                              # Parameter list
      - name: "param1"                       # Parameter name
        type: "string"                       # Parameter type
        description: "Parameter description" # Description
        required: true                       # Required flag
      - name: "param2"
        type: "int"
        description: "Optional parameter"
        required: false
        default: 10                          # Default value (optional)
    return_type: "dict"                      # Return type
```

### JSON Format (methods.json)

```json
{
  "methods": [
    {
      "name": "method_name",
      "description": "Method description",
      "module_path": "tools.module",
      "function_name": "function_name",
      "parameters": [
        {
          "name": "param1",
          "type": "string",
          "description": "Parameter description",
          "required": true
        },
        {
          "name": "param2",
          "type": "int",
          "description": "Optional parameter",
          "required": false,
          "default": 10
        }
      ],
      "return_type": "dict"
    }
  ]
}
```

## Field Descriptions

### Model Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model.name` | string | Yes | Ollama model name (e.g., "qwen3:4b") |
| `model.api_base` | string | Yes | Ollama API endpoint URL |
| `model.timeout` | integer | Yes | Request timeout in seconds |
| `model.temperature` | float | Yes | Generation temperature (0.0-1.0) |
| `model.max_tokens` | integer | Yes | Maximum tokens to generate |
| `database.host` | string | Yes | PostgreSQL host address |
| `database.port` | integer | Yes | PostgreSQL port number |
| `database.database` | string | Yes | Database name |
| `database.user` | string | Yes | Database username |
| `database.password` | string | Yes | Database password |
| `database.pool_size` | integer | Yes | Connection pool size |
| `logging.level` | string | Yes | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `logging.format` | string | Yes | Python logging format string |
| `logging.file` | string | Yes | Log file path |

### Method Registration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Method name (2-100 chars, valid Python identifier) |
| `description` | string | Yes | Method description (1-1000 chars) |
| `module_path` | string | Yes | Python module path (e.g., "tools.weather") |
| `function_name` | string | Yes | Function name in the module |
| `parameters` | array | Yes | List of parameters (can be empty) |
| `parameters[].name` | string | Yes | Parameter name (valid Python identifier) |
| `parameters[].type` | string | Yes | Parameter type (string, int, float, bool, dict, list, etc.) |
| `parameters[].description` | string | Yes | Parameter description |
| `parameters[].required` | boolean | Yes | Whether parameter is required |
| `parameters[].default` | any | No | Default value for optional parameters |
| `return_type` | string | Yes | Return value type |

## Validation Rules

### Method Name
- Must be a valid Python identifier
- Length: 2-100 characters
- Cannot start with a digit
- Cannot contain spaces or special characters (except underscore)
- Examples: `get_weather`, `calculate`, `fetch_data`

### Parameter Types
Supported types:
- `string` - String values
- `int` - Integer numbers
- `float` - Floating-point numbers
- `bool` - Boolean values (true/false)
- `dict` - Dictionary/object
- `list` - Array/list
- `None` - No return value
- Custom types (must be valid Python type strings)

### Return Types
Same as parameter types, plus:
- `None` - For functions that don't return a value

## Usage Examples

### Using YAML Configuration

```bash
python src/main.py --model-config config/model_config.yaml --methods-config config/methods.yaml
```

### Using JSON Configuration

```bash
python src/main.py --model-config config/model_config.json --methods-config config/methods.json
```

### Using Default Configuration

```bash
# Uses config/model_config.yaml and config/methods.yaml by default
python src/main.py
```

## Environment Variables

You can also use environment variables for sensitive information:

```bash
export DB_PASSWORD="your_secure_password"
export DB_HOST="production-db.example.com"
```

Then reference them in your configuration (requires code modification to support this).

## Best Practices

1. **Use YAML for Development**: YAML supports comments and is more readable
2. **Use JSON for Production**: JSON is more widely supported by tools
3. **Secure Passwords**: Never commit passwords to version control
4. **Validate Before Running**: The system validates configuration on startup
5. **Keep Backups**: Keep backup copies of working configurations
6. **Document Custom Methods**: Add clear descriptions for all methods
7. **Use Descriptive Names**: Choose clear, descriptive method and parameter names
8. **Test Incrementally**: Register and test methods one at a time

## Troubleshooting

### Configuration Parse Errors

**Problem**: YAML/JSON syntax error

**Solution**:
- Validate YAML: Use online YAML validator or `yamllint`
- Validate JSON: Use online JSON validator or `jq`
- Check indentation (YAML is indentation-sensitive)
- Check for missing commas, quotes, or brackets

### Database Connection Errors

**Problem**: Cannot connect to database

**Solution**:
- Verify PostgreSQL is running
- Check host, port, database name
- Verify username and password
- Check network connectivity
- Ensure database exists

### Method Validation Errors

**Problem**: Method fails validation

**Solution**:
- Check method name follows Python identifier rules
- Ensure all required fields are present
- Verify parameter types are valid
- Check for duplicate method names
- Review error messages for specific issues

## Additional Resources

- [Method Registration System README](../README.md)
- [Main Project README](../../README.md)
- [Design Document](../../.kiro/specs/qwen-agent-scheduler/design.md)
- [Requirements Document](../../.kiro/specs/qwen-agent-scheduler/requirements.md)
