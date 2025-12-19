"""Full Integration Demo for Agent Scheduler Brain

This script demonstrates how all components work together:
- MethodLoader loads methods from database
- AgentClient processes tasks using qwen-agent
- MethodExecutor executes registered methods
- REST API provides HTTP interface

Note: This requires a running PostgreSQL database with registered methods
and an Ollama service with qwen3:4b model.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api import AgentSchedulerAPI
from src.method_loader import MethodLoader
from src.agent_client import AgentClient
from src.executor import MethodExecutor
from shared.models import DatabaseConfig, ModelConfig
from shared.config_loader import load_config
import uvicorn
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_components():
    """Set up all components for the Agent Scheduler Brain
    
    Returns:
        Tuple of (api, method_loader, agent_client, executor)
    """
    logger.info("Setting up Agent Scheduler Brain components...")
    
    # 1. Load configuration
    config_path = Path(__file__).parent.parent / "config" / "model_config.yaml"
    
    try:
        config = load_config(str(config_path))
        model_config = config['model']
        db_config = config['database']
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        logger.info("Using default configuration for demo...")
        
        # Default configuration
        model_config = ModelConfig(
            model_name="qwen3:4b",
            api_base="http://localhost:11434",
            timeout=30,
            temperature=0.7,
            max_tokens=2000
        )
        
        db_config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="postgres",
            password="postgres",
            pool_size=5
        )
    
    # 2. Initialize MethodLoader
    logger.info("Initializing MethodLoader...")
    try:
        method_loader = MethodLoader(db_config)
        methods = method_loader.load_all_methods()
        logger.info(f"Loaded {len(methods)} methods from database")
    except Exception as e:
        logger.error(f"Failed to initialize MethodLoader: {e}")
        logger.warning("API will run without method loading capability")
        method_loader = None
        methods = []
    
    # 3. Initialize AgentClient
    logger.info("Initializing AgentClient...")
    try:
        if methods:
            qwen_tools = method_loader.convert_to_qwen_tools(methods)
            agent_client = AgentClient(model_config, qwen_tools)
            logger.info(f"AgentClient initialized with {len(qwen_tools)} tools")
        else:
            agent_client = AgentClient(model_config, [])
            logger.warning("AgentClient initialized without tools")
    except Exception as e:
        logger.error(f"Failed to initialize AgentClient: {e}")
        logger.warning("API will run without agent processing capability")
        agent_client = None
    
    # 4. Initialize MethodExecutor
    logger.info("Initializing MethodExecutor...")
    try:
        if methods:
            methods_dict = {m.name: m for m in methods}
            executor = MethodExecutor(methods_dict)
            logger.info(f"MethodExecutor initialized with {len(methods_dict)} methods")
            
            # Register executor with agent client
            if agent_client:
                agent_client.register_tool_executor(executor.execute)
                logger.info("MethodExecutor registered with AgentClient")
        else:
            executor = None
            logger.warning("MethodExecutor not initialized (no methods)")
    except Exception as e:
        logger.error(f"Failed to initialize MethodExecutor: {e}")
        executor = None
    
    # 5. Initialize API
    logger.info("Initializing REST API...")
    api = AgentSchedulerAPI()
    
    if method_loader:
        api.set_method_loader(method_loader)
    if agent_client:
        api.set_agent_client(agent_client)
    
    logger.info("All components initialized successfully!")
    
    return api, method_loader, agent_client, executor


def main():
    """Main entry point"""
    print("=" * 70)
    print("Agent Scheduler Brain - Full Integration Demo")
    print("=" * 70)
    print()
    
    # Setup components
    api, method_loader, agent_client, executor = setup_components()
    
    print()
    print("Component Status:")
    print(f"  MethodLoader:   {'✓ Ready' if method_loader else '✗ Not available'}")
    print(f"  AgentClient:    {'✓ Ready' if agent_client else '✗ Not available'}")
    print(f"  MethodExecutor: {'✓ Ready' if executor else '✗ Not available'}")
    print()
    
    # Display API information
    print("API Server Information:")
    print("  Base URL:           http://localhost:8000")
    print("  Interactive Docs:   http://localhost:8000/docs")
    print("  ReDoc:              http://localhost:8000/redoc")
    print()
    
    print("Available Endpoints:")
    print("  GET    /health              - Health check")
    print("  POST   /api/tasks           - Submit a task")
    print("  GET    /api/tasks/{id}      - Query task status")
    print("  GET    /api/methods         - List registered methods")
    print()
    
    print("Example Usage:")
    print("  # Submit a task")
    print('  curl -X POST http://localhost:8000/api/tasks \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"task_description": "Your task here"}\'')
    print()
    print("  # List methods")
    print("  curl http://localhost:8000/api/methods")
    print()
    
    print("=" * 70)
    print("Starting server... Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Run the server
    try:
        uvicorn.run(
            api.app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        
        # Cleanup
        if method_loader:
            method_loader.close()
        
        print("Server stopped. Goodbye!")


if __name__ == "__main__":
    main()
