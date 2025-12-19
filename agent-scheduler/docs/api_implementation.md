# REST API Implementation

## Overview

The REST API provides HTTP endpoints for interacting with the Agent Scheduler Brain. It allows clients to submit tasks, query task status, and list registered methods.

## Architecture

The API is built using FastAPI and provides three main endpoint groups:

1. **Health Endpoints** - Service health checks
2. **Task Endpoints** - Task submission and status queries
3. **Method Endpoints** - Listing registered methods

## API Endpoints

### Health Endpoints

#### GET /
Root endpoint for basic health check.

**Response:**
```json
{
  "status": "ok",
  "service": "Agent Scheduler Brain"
}
```

#### GET /health
Detailed health check including component status.

**Response:**
```json
{
  "status": "healthy",
  "agent_client": true,
  "method_loader": true
}
```

### Task Endpoints

#### POST /api/tasks
Submit a new task for processing.

**Request Body:**
```json
{
  "task_description": "Get weather for Seattle"
}
```

**Response (201 Created):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

**Error Responses:**
- `400 Bad Request` - Empty or invalid task description
- `422 Unprocessable Entity` - Invalid request format
- `500 Internal Server Error` - Server-side error

#### GET /api/tasks/{task_id}
Query the status and result of a task.

**Response (200 OK):**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": "The weather in Seattle is...",
  "error": null,
  "created_at": "2025-12-18T10:00:00Z",
  "completed_at": "2025-12-18T10:00:05Z"
}
```

**Task Status Values:**
- `pending` - Task created but not yet processed
- `processing` - Task is currently being processed
- `completed` - Task completed successfully
- `failed` - Task processing failed

**Error Responses:**
- `404 Not Found` - Task ID not found
- `500 Internal Server Error` - Server-side error

### Method Endpoints

#### GET /api/methods
List all registered methods available for the agent.

**Response (200 OK):**
```json
{
  "methods": [
    {
      "name": "get_weather",
      "description": "Get weather information for a city",
      "parameters": [
        {
          "name": "city",
          "type": "string",
          "description": "City name",
          "required": true,
          "default": null
        }
      ],
      "return_type": "dict"
    }
  ],
  "count": 1
}
```

**Error Responses:**
- `500 Internal Server Error` - Server-side error or method loader not configured

## Implementation Details

### Components

#### AgentSchedulerAPI
Main API class that:
- Creates FastAPI application
- Registers all routes
- Manages task storage
- Integrates with AgentClient and MethodLoader

#### TaskStore
In-memory storage for task information. In production, this should be replaced with:
- Redis for distributed caching
- PostgreSQL for persistent storage
- Message queue for async processing

#### Request/Response Models
Pydantic models for request validation and response serialization:
- `TaskSubmissionRequest`
- `TaskSubmissionResponse`
- `TaskStatusResponse`
- `MethodInfo`
- `MethodsListResponse`
- `ErrorResponse`

### Error Handling

The API implements comprehensive error handling:

1. **Validation Errors (422)** - Pydantic validates request format
2. **Client Errors (400)** - Business logic validation (e.g., empty description)
3. **Not Found (404)** - Resource not found
4. **Server Errors (500)** - Internal errors with logging

All errors return a consistent format:
```json
{
  "error": "Error message",
  "detail": "Detailed error information"
}
```

### Logging

The API logs:
- Task creation and completion
- Error conditions with stack traces
- Component registration
- Request processing

## Usage Example

### Starting the Server

```python
from src.api import AgentSchedulerAPI
import uvicorn

# Create and configure API
api = AgentSchedulerAPI()
api.set_method_loader(method_loader)
api.set_agent_client(agent_client)

# Run server
uvicorn.run(api.app, host="0.0.0.0", port=8000)
```

### Using the API

```python
import requests

# Submit a task
response = requests.post(
    "http://localhost:8000/api/tasks",
    json={"task_description": "Get weather for Seattle"}
)
task_id = response.json()["task_id"]

# Query task status
response = requests.get(f"http://localhost:8000/api/tasks/{task_id}")
print(response.json())

# List methods
response = requests.get("http://localhost:8000/api/methods")
print(response.json())
```

### Using curl

```bash
# Submit task
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Get weather for Seattle"}'

# Query task status
curl http://localhost:8000/api/tasks/{task_id}

# List methods
curl http://localhost:8000/api/methods
```

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide:
- Interactive API testing
- Request/response schemas
- Example requests
- Authentication testing (if configured)

## Testing

The API includes comprehensive tests in `tests/test_api.py`:

```bash
# Run API tests
pytest tests/test_api.py -v

# Run with coverage
pytest tests/test_api.py --cov=src.api
```

Test coverage includes:
- Health endpoints
- Task submission with various inputs
- Task status queries
- Methods listing
- Error handling
- Edge cases

## Production Considerations

### Async Processing
Current implementation processes tasks synchronously. For production:

```python
from fastapi import BackgroundTasks

@app.post("/api/tasks")
async def submit_task(request: TaskSubmissionRequest, background_tasks: BackgroundTasks):
    task_id = task_store.create_task(request.task_description)
    background_tasks.add_task(process_task_async, task_id, request.task_description)
    return TaskSubmissionResponse(task_id=task_id, status=TaskStatus.PENDING)
```

### Persistent Storage
Replace TaskStore with database:

```python
# Use PostgreSQL for task storage
class DatabaseTaskStore:
    def __init__(self, db_config: DatabaseConfig):
        self.db = DatabaseConnection(db_config)
    
    def create_task(self, description: str) -> str:
        # Insert into tasks table
        pass
```

### Authentication
Add API key or JWT authentication:

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
```

### Rate Limiting
Implement rate limiting:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/tasks")
@limiter.limit("10/minute")
async def submit_task(request: Request, ...):
    pass
```

### CORS
Enable CORS for web clients:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 12.1**: HTTP server starts and listens on specified port ✓
- **Requirement 12.2**: POST endpoint accepts task description and returns task ID ✓
- **Requirement 12.3**: GET endpoint returns task status and result ✓
- **Requirement 12.4**: Returns HTTP 400 for invalid requests ✓
- **Requirement 12.5**: Returns HTTP 500 for server errors with logging ✓

All requirements are validated by the test suite in `tests/test_api.py`.
