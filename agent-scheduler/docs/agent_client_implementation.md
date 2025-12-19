# Agent Client Implementation

## Overview

The `AgentClient` class provides integration with the qwen-agent framework for processing user tasks and managing tool execution.

## Architecture

The AgentClient wraps the qwen-agent Assistant and provides:
1. Initialization with model configuration and tool definitions
2. Tool executor registration for dynamic method execution
3. Task processing that leverages qwen-agent's natural language understanding

## Key Components

### AgentClient Class

**Responsibilities:**
- Initialize qwen-agent Assistant with model configuration
- Convert tool definitions to qwen-agent format
- Register and manage tool executors
- Process user tasks and return responses

### AgentResponse Dataclass

**Attributes:**
- `success`: Boolean indicating if task processing succeeded
- `response`: The agent's final response text
- `tool_calls`: List of tool calls made during processing
- `error`: Error message if processing failed

## Usage Example

```python
from shared.models import ModelConfig, ExecutionResult
from src.agent_client import AgentClient

# Configure the model
model_config = ModelConfig(
    model_name="qwen3:4b",
    api_base="http://localhost:11434",
    timeout=30,
    temperature=0.7,
    max_tokens=2000
)

# Define tools in qwen-agent format
tools = [
    {
        "name": "get_weather",
        "description": "Get weather information for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["city"]
        }
    }
]

# Create the agent client
client = AgentClient(model_config, tools)

# Define an executor function
def execute_method(method_name: str, params: dict) -> ExecutionResult:
    if method_name == "get_weather":
        city = params.get("city", "Unknown")
        return ExecutionResult(
            success=True,
            result=f"Weather in {city}: Sunny, 25°C"
        )
    return ExecutionResult(
        success=False,
        error=f"Unknown method: {method_name}"
    )

# Register the executor
client.register_tool_executor(execute_method)

# Process a user task
response = client.process_task("What's the weather in Beijing?")

if response.success:
    print(f"Agent response: {response.response}")
    print(f"Tool calls made: {len(response.tool_calls)}")
else:
    print(f"Error: {response.error}")
```

## Integration with Method Loader

The AgentClient is designed to work seamlessly with the MethodLoader:

```python
from src.method_loader import MethodLoader
from src.agent_client import AgentClient
from shared.models import DatabaseConfig, ModelConfig

# Load methods from database
db_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="test_db",
    user="postgres",
    password="password"
)

loader = MethodLoader(db_config)
methods = loader.load_all_methods()
tools = loader.convert_to_qwen_tools(methods)

# Create agent client with loaded tools
model_config = ModelConfig(
    model_name="qwen3:4b",
    api_base="http://localhost:11434"
)

client = AgentClient(model_config, tools)

# Register executor (to be implemented in next task)
# client.register_tool_executor(executor.execute)
```

## Error Handling

The AgentClient handles errors gracefully:

1. **Initialization Errors**: If qwen-agent cannot be initialized, raises `AgentClientError`
2. **Task Processing Errors**: Returns `AgentResponse` with `success=False` and error message
3. **Tool Execution Errors**: Caught and returned as error strings to the agent

## Requirements Validation

This implementation satisfies the following requirements:

- **Requirement 7.1**: ✅ Uses model configuration to create qwen-agent client instance
- **Requirement 7.2**: ✅ Passes user task requests to qwen-agent for intent understanding
- **Requirement 7.3**: ✅ Looks up method metadata via registered executor when tools are called
- **Requirement 7.4**: ✅ Returns execution results back to qwen-agent for continued processing
- **Requirement 7.5**: ✅ Returns final agent response to the user

## Testing

The implementation includes comprehensive unit tests:

- Agent client initialization with valid configuration
- Configuration storage and retrieval
- Tool executor registration
- Executor invocation after registration
- AgentResponse dataclass functionality

Run tests with:
```bash
cd agent-scheduler
python -m pytest tests/test_agent_client.py -v
```

## Next Steps

The next task (Task 11) will implement the MethodExecutor class, which will provide the actual method execution logic that can be registered with the AgentClient via `register_tool_executor()`.
