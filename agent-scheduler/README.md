# Agent Scheduler Brain

Agent Scheduler Brain is a service that loads registered methods from a PostgreSQL database and uses the qwen-agent framework to process natural language tasks by calling appropriate methods.

## Features

- **Method Loading**: Automatically loads registered methods from PostgreSQL database
- **qwen-agent Integration**: Uses qwen-agent framework for natural language understanding
- **Dynamic Execution**: Executes methods dynamically with parameter validation and type conversion
- **REST API**: Provides RESTful endpoints for task submission and status queries
- **Comprehensive Logging**: Detailed logging for debugging and monitoring

## Prerequisites

1. **Python 3.9+**
2. **PostgreSQL Database**: Running instance with registered methods
3. **Ollama Service**: Running with qwen3:4b model (or other compatible model)
4. **Dependencies**: Install from requirements.txt

## Installation

```bash
cd agent-scheduler
pip install -r requirements.txt
```

## Configuration

Create a configuration file at `config/model_config.yaml`:

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"
  timeout: 30
  temperature: 0.7
  max_tokens: 2000

database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "yuanyuan"
  password: "666666"
  pool_size: 5

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/agent_scheduler.log"
```

## Usage

### Starting the Server

**Basic usage:**
```bash
python src/main.py
```

**With custom configuration:**
```bash
python src/main.py --config /path/to/config.yaml
```

**With custom host and port:**
```bash
python src/main.py --host 127.0.0.1 --port 8080
```

**With debug logging:**
```bash
python src/main.py --log-level DEBUG --log-file logs/debug.log
```

### Command Line Options

- `--config`: Path to configuration YAML file (default: `config/model_config.yaml`)
- `--host`: Host address to bind to (default: `0.0.0.0`)
- `--port`: Port to listen on (default: `8000`)
- `--log-level`: Logging level - DEBUG, INFO, WARNING, ERROR, CRITICAL (default: `INFO`)
- `--log-file`: Log file path (default: console only)

### API Endpoints

Once the server is running, the following endpoints are available:

#### Health Check
```bash
GET /health
```

Returns the health status of the service.

#### Submit Task
```bash
POST /api/tasks
Content-Type: application/json

{
  "task_description": "Get the weather for Beijing"
}
```

Returns:
```json
{
  "task_id": "uuid",
  "status": "completed"
}
```

#### Query Task Status
```bash
GET /api/tasks/{task_id}
```

Returns:
```json
{
  "task_id": "uuid",
  "status": "completed",
  "result": "...",
  "error": null,
  "created_at": "2025-12-18T10:00:00Z",
  "completed_at": "2025-12-18T10:00:05Z"
}
```

#### List Registered Methods
```bash
GET /api/methods
```

Returns:
```json
{
  "methods": [
    {
      "name": "get_weather",
      "description": "Get weather information",
      "parameters": [...],
      "return_type": "dict"
    }
  ],
  "count": 1
}
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Architecture

The Agent Scheduler Brain consists of four main components:

1. **MethodLoader**: Loads registered methods from PostgreSQL database
2. **MethodExecutor**: Executes methods dynamically with validation
3. **AgentClient**: Integrates with qwen-agent for task processing
4. **API**: Provides REST endpoints for external access

### Component Flow

```
User Request → REST API → AgentClient → qwen-agent
                                ↓
                          MethodExecutor → Registered Methods
                                ↑
                          MethodLoader ← PostgreSQL Database
```

## Error Handling

The application provides comprehensive error handling and logging:

- **Configuration Errors**: Logged with file path and specific parsing error
- **Database Errors**: Logged with SQL statement and database error code
- **Method Execution Errors**: Logged with method name, parameters, and exception info
- **API Errors**: Return appropriate HTTP status codes with error details

### Error Logging Requirements

According to the design specification, the following logging requirements are met:

- **Requirement 10.1**: All errors include timestamp, error type, message, and stack trace
- **Requirement 10.3**: Database errors include SQL statement and error code
- **Requirement 10.4**: Method execution errors include method name, parameters, and exception info

## Examples

### Running the Demo

```bash
python examples/main_demo.py
```

### Testing with curl

Submit a task:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Calculate 2 + 2"}'
```

Query task status:
```bash
curl http://localhost:8000/api/tasks/{task_id}
```

List methods:
```bash
curl http://localhost:8000/api/methods
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_main.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Troubleshooting

### Database Connection Issues

If you see database connection errors:
1. Verify PostgreSQL is running
2. Check database credentials in config file
3. Ensure database exists and schema is initialized
4. Check network connectivity to database host

### Ollama Service Issues

If you see model initialization errors:
1. Verify Ollama service is running: `ollama list`
2. Check if qwen3:4b model is available: `ollama pull qwen3:4b`
3. Verify API endpoint in config file
4. Check network connectivity to Ollama service

### No Methods Available

If the application starts but reports no methods:
1. Verify methods are registered in the database
2. Run the method-registration system first
3. Check database connection and query permissions

## Development

### Project Structure

```
agent-scheduler/
├── src/
│   ├── main.py           # Main entry point
│   ├── method_loader.py  # Method loading from database
│   ├── agent_client.py   # qwen-agent integration
│   ├── executor.py       # Method execution engine
│   └── api.py            # REST API endpoints
├── tests/
│   ├── test_main.py
│   ├── test_method_loader.py
│   ├── test_agent_client.py
│   ├── test_executor.py
│   └── test_api.py
├── config/
│   └── model_config.yaml
├── examples/
│   └── main_demo.py
└── requirements.txt
```

### Adding New Features

1. Implement the feature in the appropriate module
2. Add tests in the corresponding test file
3. Update this README with usage instructions
4. Update the API documentation if adding new endpoints

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
