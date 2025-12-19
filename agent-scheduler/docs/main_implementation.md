# Main Entry Point Implementation

## Overview

The main entry point (`src/main.py`) for the Agent Scheduler Brain has been implemented. It integrates all components of the system to provide a complete task scheduling and execution service.

## Implementation Details

### Components Integrated

1. **MethodLoader** - Loads registered methods from PostgreSQL database
2. **MethodExecutor** - Executes methods dynamically with validation
3. **AgentClient** - Integrates with qwen-agent framework for task processing
4. **REST API** - Provides HTTP endpoints for task submission and queries

### Key Features

#### 1. Configuration Management
- Loads model and database configuration from YAML file
- Validates configuration before initialization
- Provides clear error messages for configuration issues

#### 2. Component Initialization
- Initializes all components in correct order
- Handles initialization failures gracefully
- Logs detailed information about initialization process

#### 3. Method Execution Integration
- Registers executor callback with AgentClient
- Provides seamless integration between qwen-agent and method execution
- Handles execution results and errors properly

#### 4. Logging System
- Configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Support for both console and file logging
- Structured log format with timestamps
- Detailed error logging with stack traces

#### 5. Server Management
- Uses uvicorn for ASGI server
- Configurable host and port
- Graceful shutdown handling
- Resource cleanup on exit

### Requirements Compliance

The implementation satisfies the following requirements:

#### Requirement 10.1: Error Logging Completeness
✅ All errors logged with timestamp, error type, message, and stack trace
- Implemented via structured logging format
- Exception handlers use `exc_info=True` for stack traces

#### Requirement 10.3: Database Error Logging Detail
✅ Database errors logged with SQL statement and error code
- MethodLoader errors caught and logged with details
- Database connection failures logged with configuration info

#### Requirement 10.4: Method Execution Error Logging Detail
✅ Method execution errors logged with method name, parameters, and exception info
- `_execute_method()` callback logs all execution details
- Errors include full context for debugging

## Usage

### Basic Usage

```bash
python src/main.py
```

### With Custom Configuration

```bash
python src/main.py --config /path/to/config.yaml
```

### With Custom Host and Port

```bash
python src/main.py --host 127.0.0.1 --port 8080
```

### With Debug Logging

```bash
python src/main.py --log-level DEBUG --log-file logs/debug.log
```

## Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--config` | Path to configuration YAML file | `config/model_config.yaml` |
| `--host` | Host address to bind to | `0.0.0.0` |
| `--port` | Port to listen on | `8000` |
| `--log-level` | Logging level | `INFO` |
| `--log-file` | Log file path | None (console only) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentSchedulerBrain                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ MethodLoader │  │ AgentClient  │  │MethodExecutor│     │
│  │              │  │              │  │              │     │
│  │ - Load       │  │ - Process    │  │ - Execute    │     │
│  │   methods    │  │   tasks      │  │   methods    │     │
│  │ - Convert    │  │ - Call tools │  │ - Validate   │     │
│  │   to tools   │  │              │  │   params     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┼─────────────────┘              │
│                           │                                │
│                    ┌──────▼───────┐                        │
│                    │   REST API   │                        │
│                    │              │                        │
│                    │ - /api/tasks │                        │
│                    │ - /api/methods│                       │
│                    └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling

The main entry point provides comprehensive error handling:

### Configuration Errors
- Invalid YAML syntax
- Missing required fields
- Invalid data types
- File not found

**Example Log:**
```
2025-12-18 10:00:00 - main - ERROR - Configuration error: Configuration file not found: config/model_config.yaml
```

### Database Errors
- Connection failures
- Query execution failures
- Schema issues

**Example Log:**
```
2025-12-18 10:00:00 - main - ERROR - Failed to initialize MethodLoader: Failed to initialize database connection: connection refused
```

### Method Execution Errors
- Method not found
- Parameter validation failures
- Execution exceptions

**Example Log:**
```
2025-12-18 10:00:00 - main - ERROR - Method 'test_method' execution failed: Parameter validation failed: Required parameter 'city' is missing
```

## Testing

The implementation includes comprehensive tests in `tests/test_main.py`:

- ✅ Logging configuration tests
- ✅ Application initialization tests
- ✅ Configuration loading tests
- ✅ Component integration tests
- ✅ Method execution callback tests
- ✅ Error handling tests
- ✅ Shutdown tests

Run tests:
```bash
pytest tests/test_main.py -v
```

## Examples

See `examples/main_demo.py` for a complete usage example.

## Next Steps

After implementing the main entry point, you can:

1. Register methods using the method-registration system
2. Start the Agent Scheduler Brain service
3. Submit tasks via the REST API
4. Monitor logs for debugging and performance analysis

## Troubleshooting

### Issue: "Configuration file not found"
**Solution:** Create `config/model_config.yaml` with proper configuration

### Issue: "Failed to initialize database connection"
**Solution:** Verify PostgreSQL is running and credentials are correct

### Issue: "No methods registered in database"
**Solution:** Run the method-registration system first to register methods

### Issue: "Failed to initialize qwen-agent"
**Solution:** Verify Ollama service is running with qwen3:4b model

## Related Documentation

- [API Implementation](api_implementation.md)
- [Method Loader Implementation](method_loader_implementation.md)
- [Agent Client Implementation](agent_client_implementation.md)
- [Executor Implementation](executor_implementation.md)
