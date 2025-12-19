"""Demo script for Agent Scheduler Brain main entry point

This script demonstrates how to use the Agent Scheduler Brain application.

Prerequisites:
1. PostgreSQL database running with registered methods
2. Ollama service running with qwen3:4b model
3. Configuration file at config/model_config.yaml

Usage:
    python examples/main_demo.py
"""

import sys
import io
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except (AttributeError, io.UnsupportedOperation):
        pass  # Already wrapped or not supported

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import AgentSchedulerBrain, setup_logging


def main():
    """Run the Agent Scheduler Brain demo"""
    
    # Setup logging
    setup_logging(log_level="INFO")
    
    print("=" * 80)
    print("Agent Scheduler Brain - Demo")
    print("=" * 80)
    print()
    
    # Configuration file path
    config_path = Path(__file__).parent.parent / 'config' / 'model_config.yaml'
    
    if not config_path.exists():
        print(f"Error: Configuration file not found at {config_path}")
        print("Please create a configuration file with model and database settings.")
        return
    
    print(f"Using configuration: {config_path}")
    print()
    
    try:
        # Initialize the application
        print("Initializing Agent Scheduler Brain...")
        app = AgentSchedulerBrain(config_path=str(config_path))
        print("✓ Application initialized successfully")
        print()
        
        # Display loaded configuration
        print("Configuration:")
        print(f"  Model: {app.model_config.model_name}")
        print(f"  API Base: {app.model_config.api_base}")
        print(f"  Database: {app.db_config.database} at {app.db_config.host}:{app.db_config.port}")
        print()
        
        # Display loaded methods
        methods = app.method_loader.load_all_methods()
        print(f"Loaded Methods: {len(methods)}")
        for method in methods:
            print(f"  - {method.name}: {method.description}")
        print()
        
        # Start the server
        print("Starting API server...")
        print("API will be available at: http://0.0.0.0:8000")
        print("API documentation at: http://0.0.0.0:8000/docs")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 80)
        print()
        
        app.run(host="0.0.0.0", port=8000)
        
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        if 'app' in locals():
            app.shutdown()
        print("Demo completed.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nPlease ensure:")
        print("  1. PostgreSQL database is running and accessible")
        print("  2. Methods are registered in the database")
        print("  3. Ollama service is running with qwen3:4b model")
        print("  4. Configuration file is correct")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
