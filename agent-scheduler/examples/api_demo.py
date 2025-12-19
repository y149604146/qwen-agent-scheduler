"""Demo script for Agent Scheduler Brain REST API

This script demonstrates how to use the REST API endpoints.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api import AgentSchedulerAPI
from src.method_loader import MethodLoader
from src.agent_client import AgentClient
from src.executor import MethodExecutor
from shared.models import DatabaseConfig, ModelConfig
import uvicorn


def create_demo_api():
    """Create and configure API instance for demo
    
    In a real application, this would load configuration from files
    and connect to actual database and Ollama service.
    """
    # Create API instance
    api = AgentSchedulerAPI()
    
    # In production, you would:
    # 1. Load database config and create MethodLoader
    # db_config = DatabaseConfig(
    #     host="localhost",
    #     port=5432,
    #     database="test_db",
    #     user="postgres",
    #     password="password"
    # )
    # method_loader = MethodLoader(db_config)
    # api.set_method_loader(method_loader)
    
    # 2. Load model config and create AgentClient
    # model_config = ModelConfig(
    #     model_name="qwen3:4b",
    #     api_base="http://localhost:11434",
    #     timeout=30,
    #     temperature=0.7,
    #     max_tokens=2000
    # )
    # methods = method_loader.load_all_methods()
    # qwen_tools = method_loader.convert_to_qwen_tools(methods)
    # agent_client = AgentClient(model_config, qwen_tools)
    
    # 3. Create MethodExecutor and register with agent
    # methods_dict = {m.name: m for m in methods}
    # executor = MethodExecutor(methods_dict)
    # agent_client.register_tool_executor(executor.execute)
    # api.set_agent_client(agent_client)
    
    return api


def main():
    """Run the API server"""
    print("Starting Agent Scheduler Brain API Demo...")
    print("\nNote: This is a demo without database and Ollama connection.")
    print("In production, configure database and model settings.\n")
    
    # Create API
    api = create_demo_api()
    
    # Run server
    print("API Documentation available at: http://localhost:8000/docs")
    print("Health check: http://localhost:8000/health")
    print("\nAPI Endpoints:")
    print("  POST   /api/tasks          - Submit a new task")
    print("  GET    /api/tasks/{id}     - Query task status")
    print("  GET    /api/methods        - List registered methods")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        api.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
