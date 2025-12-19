"""Main entry point for Agent Scheduler Brain

This module provides the main entry point for the Agent Scheduler Brain service.
It integrates MethodLoader, AgentClient, MethodExecutor, and the REST API to
provide a complete task scheduling and execution system.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional
import argparse

# Add parent directory to path for shared module imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config_loader import load_model_config, load_database_config, ConfigurationError
from shared.models import ModelConfig, DatabaseConfig

from method_loader import MethodLoader, MethodLoaderError
from executor import MethodExecutor, MethodExecutorError
from api import AgentSchedulerAPI

# Import agent client based on environment variable
# Set USE_SIMPLE_AGENT=1 to use simplified client (bypasses qwen-agent issues)
USE_SIMPLE_AGENT = os.getenv('USE_SIMPLE_AGENT', '1') == '1'

if USE_SIMPLE_AGENT:
    from simple_agent_client import SimpleAgentClient as AgentClient
    from simple_agent_client import AgentClientError
    logger = logging.getLogger(__name__)
    logger.info("Using SimpleAgentClient (direct Ollama API)")
else:
    from agent_client import AgentClient, AgentClientError
    logger = logging.getLogger(__name__)
    logger.info("Using standard AgentClient (qwen-agent)")


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure logging for the application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, logs to console only.
    """
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    logging.info(f"Logging configured: level={log_level}, file={log_file or 'console only'}")


logger = logging.getLogger(__name__)


class AgentSchedulerBrain:
    """Main application class for Agent Scheduler Brain
    
    This class orchestrates all components of the Agent Scheduler Brain:
    - MethodLoader: Loads registered methods from database
    - MethodExecutor: Executes methods dynamically
    - AgentClient: Processes tasks using qwen-agent
    - API: Provides REST endpoints for task submission and queries
    
    Attributes:
        model_config: Configuration for the LLM model
        db_config: Configuration for PostgreSQL database
        method_loader: MethodLoader instance
        method_executor: MethodExecutor instance
        agent_client: AgentClient instance
        api: AgentSchedulerAPI instance
    """
    
    def __init__(self, config_path: str):
        """Initialize Agent Scheduler Brain
        
        Args:
            config_path: Path to configuration YAML file
            
        Raises:
            ConfigurationError: If configuration is invalid
            MethodLoaderError: If method loading fails
            AgentClientError: If agent initialization fails
        """
        self.config_path = config_path
        self.model_config: Optional[ModelConfig] = None
        self.db_config: Optional[DatabaseConfig] = None
        self.method_loader: Optional[MethodLoader] = None
        self.method_executor: Optional[MethodExecutor] = None
        self.agent_client: Optional[AgentClient] = None
        self.api: Optional[AgentSchedulerAPI] = None
        
        logger.info("Initializing Agent Scheduler Brain...")
        
        # Load configuration
        self._load_configuration()
        
        # Initialize components
        self._initialize_components()
        
        logger.info("Agent Scheduler Brain initialized successfully")
    
    def _load_configuration(self) -> None:
        """Load configuration from YAML file
        
        Raises:
            ConfigurationError: If configuration loading fails
        """
        try:
            logger.info(f"Loading configuration from {self.config_path}")
            
            # Load model configuration
            self.model_config = load_model_config(self.config_path)
            logger.info(f"Model configuration loaded: {self.model_config.model_name} at {self.model_config.api_base}")
            
            # Load database configuration
            self.db_config = load_database_config(self.config_path)
            logger.info(f"Database configuration loaded: {self.db_config.database} at {self.db_config.host}:{self.db_config.port}")
            
        except ConfigurationError as e:
            logger.error(f"Configuration error: {e}")
            raise
        except Exception as e:
            error_msg = f"Failed to load configuration from {self.config_path}: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg) from e
    
    def _initialize_components(self) -> None:
        """Initialize all system components
        
        Raises:
            MethodLoaderError: If method loader initialization fails
            AgentClientError: If agent client initialization fails
        """
        try:
            # Initialize MethodLoader
            logger.info("Initializing MethodLoader...")
            self.method_loader = MethodLoader(self.db_config)
            
            # Load all registered methods
            logger.info("Loading registered methods from database...")
            methods = self.method_loader.load_all_methods()
            logger.info(f"Loaded {len(methods)} registered methods")
            
            if len(methods) == 0:
                logger.warning("No methods registered in database. Agent will have no tools available.")
            
            # Convert methods to dictionary for executor
            methods_dict = {method.name: method for method in methods}
            
            # Initialize MethodExecutor
            logger.info("Initializing MethodExecutor...")
            self.method_executor = MethodExecutor(methods_dict)
            
            # Convert methods to qwen-agent tool format
            logger.info("Converting methods to qwen-agent tool format...")
            qwen_tools = self.method_loader.convert_to_qwen_tools(methods)
            logger.info(f"Converted {len(qwen_tools)} methods to qwen-agent tools")
            
            # Initialize AgentClient
            logger.info("Initializing AgentClient...")
            self.agent_client = AgentClient(self.model_config, qwen_tools)
            
            # Register executor with agent client
            logger.info("Registering method executor with agent client...")
            self.agent_client.register_tool_executor(self._execute_method)
            
            # Initialize API
            logger.info("Initializing REST API...")
            self.api = AgentSchedulerAPI()
            self.api.set_agent_client(self.agent_client)
            self.api.set_method_loader(self.method_loader)
            
            logger.info("All components initialized successfully")
            
        except MethodLoaderError as e:
            error_msg = f"Failed to initialize MethodLoader: {e}"
            logger.error(error_msg)
            raise
        except AgentClientError as e:
            error_msg = f"Failed to initialize AgentClient: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Failed to initialize components: {e}"
            logger.error(error_msg, exc_info=True)
            raise
    
    def _execute_method(self, method_name: str, params: dict) -> any:
        """Execute a method using the MethodExecutor
        
        This is the callback function registered with the AgentClient
        for executing tool calls.
        
        Args:
            method_name: Name of the method to execute
            params: Dictionary of parameters
            
        Returns:
            ExecutionResult from the method executor
        """
        logger.info(f"Executing method '{method_name}' with params: {params}")
        
        try:
            result = self.method_executor.execute(method_name, params)
            
            if result.success:
                logger.info(f"Method '{method_name}' executed successfully in {result.execution_time:.3f}s")
            else:
                logger.error(f"Method '{method_name}' execution failed: {result.error}")
            
            return result
            
        except Exception as e:
            error_msg = f"Unexpected error executing method '{method_name}': {e}"
            logger.error(error_msg, exc_info=True)
            from shared.models import ExecutionResult
            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time=0.0
            )
    
    def run(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Start the API server
        
        Args:
            host: Host address to bind to (default: 0.0.0.0)
            port: Port to listen on (default: 8000)
        """
        try:
            import uvicorn
            
            logger.info(f"Starting Agent Scheduler Brain API server on {host}:{port}")
            logger.info(f"API documentation available at http://{host}:{port}/docs")
            
            # Run the server
            uvicorn.run(
                self.api.app,
                host=host,
                port=port,
                log_level="info"
            )
            
        except ImportError:
            logger.error("uvicorn not installed. Install with: pip install uvicorn")
            raise
        except Exception as e:
            logger.error(f"Failed to start API server: {e}", exc_info=True)
            raise
    
    def shutdown(self) -> None:
        """Shutdown the application and cleanup resources"""
        logger.info("Shutting down Agent Scheduler Brain...")
        
        try:
            if self.method_loader:
                self.method_loader.close()
                logger.info("MethodLoader closed")
        except Exception as e:
            logger.error(f"Error closing MethodLoader: {e}")
        
        logger.info("Agent Scheduler Brain shutdown complete")


def parse_arguments():
    """Parse command line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Agent Scheduler Brain - qwen-agent task scheduling service"
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/model_config.yaml',
        help='Path to configuration YAML file (default: config/model_config.yaml)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host address to bind to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to listen on (default: 8000)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Log file path (default: console only)'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the application"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(log_level=args.log_level, log_file=args.log_file)
    
    logger.info("=" * 80)
    logger.info("Agent Scheduler Brain - Starting")
    logger.info("=" * 80)
    
    app = None
    
    try:
        # Initialize application
        app = AgentSchedulerBrain(config_path=args.config)
        
        # Run the server
        app.run(host=args.host, port=args.port)
        
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        logger.error("Please check your configuration file and try again")
        sys.exit(1)
    except MethodLoaderError as e:
        logger.error(f"Database error: {e}")
        logger.error("Please check your database connection and ensure methods are registered")
        sys.exit(1)
    except AgentClientError as e:
        logger.error(f"Agent initialization error: {e}")
        logger.error("Please check your model configuration and Ollama service")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal (Ctrl+C)")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if app:
            app.shutdown()
        logger.info("=" * 80)
        logger.info("Agent Scheduler Brain - Stopped")
        logger.info("=" * 80)


if __name__ == "__main__":
    main()
