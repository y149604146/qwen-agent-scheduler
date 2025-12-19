"""Agent Client for qwen-agent framework integration

This module provides the AgentClient class that wraps qwen-agent framework
functionality for processing user tasks and managing tool execution.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.models import ModelConfig


logger = logging.getLogger(__name__)


class AgentClientError(Exception):
    """Raised when agent client operations fail"""
    pass


@dataclass
class AgentResponse:
    """Response from agent task processing
    
    Attributes:
        success: Whether the task was processed successfully
        response: The agent's response text
        tool_calls: List of tool calls made during processing
        error: Error message if processing failed
    """
    success: bool
    response: str = ""
    tool_calls: List[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class AgentClient:
    """Client for qwen-agent framework integration
    
    This class wraps the qwen-agent framework to provide task processing
    capabilities with registered tools/methods.
    
    Attributes:
        model_config: Configuration for the LLM model
        tools: List of tool definitions in qwen-agent format
        tool_executor: Callable for executing tool/method calls
    """
    
    def __init__(self, model_config: ModelConfig, tools: List[Dict[str, Any]]):
        """Initialize AgentClient with model configuration and tools
        
        Args:
            model_config: Configuration for the Ollama/qwen model
            tools: List of tool definitions in qwen-agent format
            
        Raises:
            AgentClientError: If initialization fails
        """
        self.model_config = model_config
        self.tools = tools
        self.tool_executor: Optional[Callable] = None
        self._agent = None
        
        try:
            self._initialize_agent()
            logger.info(f"AgentClient initialized with {len(tools)} tools")
        except Exception as e:
            error_msg = f"Failed to initialize AgentClient: {e}"
            logger.error(error_msg)
            raise AgentClientError(error_msg) from e
    
    def _initialize_agent(self) -> None:
        """Initialize the qwen-agent client
        
        Creates and configures the qwen-agent instance with the provided
        model configuration and tool definitions.
        
        Raises:
            AgentClientError: If agent initialization fails
        """
        try:
            # Import qwen-agent framework
            from qwen_agent.agents import Assistant
            from qwen_agent.tools.base import BaseTool, register_tool
            import os
            
            # Configure for Ollama - use native Ollama API without authentication
            # Set DASHSCOPE_API_KEY to empty string to disable validation
            os.environ['DASHSCOPE_API_KEY'] = ''
            
            # Use Ollama's native API endpoint
            # qwen-agent will use the api_base directly without key validation
            llm_config = {
                'model': self.model_config.model_name,
                'api_base': self.model_config.api_base,
                'generate_cfg': {
                    'temperature': self.model_config.temperature,
                    'max_tokens': self.model_config.max_tokens,
                }
            }
            
            # Note: We intentionally don't set 'model_server' to let qwen-agent
            # auto-detect based on api_base
            
            # Create tool wrappers for qwen-agent
            self._tool_wrappers = []
            for tool_def in self.tools:
                tool_wrapper = self._create_tool_wrapper(tool_def)
                self._tool_wrappers.append(tool_wrapper)
            
            # Initialize the Assistant agent with tools
            self._agent = Assistant(
                llm=llm_config,
                function_list=self._tool_wrappers
            )
            
            logger.debug(f"qwen-agent Assistant initialized with model {self.model_config.model_name}")
            
        except ImportError as e:
            error_msg = f"Failed to import qwen-agent: {e}. Ensure qwen-agent is installed."
            logger.error(error_msg)
            raise AgentClientError(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to initialize qwen-agent: {e}"
            logger.error(error_msg)
            raise AgentClientError(error_msg) from e
    
    def _create_tool_wrapper(self, tool_def: Dict[str, Any]) -> 'BaseTool':
        """Create a qwen-agent tool wrapper for a tool definition
        
        Args:
            tool_def: Tool definition in qwen-agent format
            
        Returns:
            BaseTool instance that wraps the tool execution
        """
        from qwen_agent.tools.base import BaseTool
        
        tool_name = tool_def['name']
        tool_description = tool_def['description']
        tool_parameters = tool_def['parameters']
        
        # Create a custom tool class that uses our executor
        class CustomTool(BaseTool):
            name = tool_name
            description = tool_description
            parameters = [tool_parameters]
            
            def __init__(self, executor_func: Optional[Callable] = None):
                super().__init__()
                self.executor_func = executor_func
            
            def call(self, params: Dict[str, Any], **kwargs) -> str:
                """Execute the tool with given parameters"""
                if self.executor_func is None:
                    return f"Error: No executor registered for tool '{self.name}'"
                
                try:
                    # Call the registered executor
                    result = self.executor_func(self.name, params)
                    
                    # Format the result as a string for the agent
                    if hasattr(result, 'success'):
                        if result.success:
                            return str(result.result)
                        else:
                            return f"Error: {result.error}"
                    else:
                        return str(result)
                        
                except Exception as e:
                    logger.error(f"Tool '{self.name}' execution failed: {e}")
                    return f"Error executing tool: {e}"
        
        # Create instance with reference to executor (will be set later)
        tool_instance = CustomTool(executor_func=self.tool_executor)
        
        # Store reference so we can update executor later
        if not hasattr(self, '_tool_instances'):
            self._tool_instances = []
        self._tool_instances.append(tool_instance)
        
        return tool_instance
    
    def register_tool_executor(self, executor: Callable[[str, Dict[str, Any]], Any]) -> None:
        """Register a method executor for tool calls
        
        The executor should be a callable that takes a method name and parameters
        and returns an ExecutionResult or similar object.
        
        Args:
            executor: Callable that executes methods. Should accept:
                     - method_name (str): Name of the method to execute
                     - params (Dict[str, Any]): Parameters for the method
                     Returns: ExecutionResult or similar object with success/result/error
        """
        self.tool_executor = executor
        
        # Update all tool instances with the new executor
        if hasattr(self, '_tool_instances'):
            for tool_instance in self._tool_instances:
                tool_instance.executor_func = executor
        
        logger.info("Tool executor registered successfully")
    
    def process_task(self, task_description: str) -> AgentResponse:
        """Process a user task request using qwen-agent
        
        Sends the task description to the qwen-agent, which will understand
        the user's intent and call appropriate tools/methods to complete the task.
        
        Args:
            task_description: Natural language description of the task
            
        Returns:
            AgentResponse containing the agent's response and execution details
            
        Raises:
            AgentClientError: If task processing fails
        """
        if self._agent is None:
            error_msg = "Agent not initialized"
            logger.error(error_msg)
            return AgentResponse(success=False, error=error_msg)
        
        try:
            logger.info(f"Processing task: {task_description}")
            
            # Create message for the agent
            messages = [{'role': 'user', 'content': task_description}]
            
            # Run the agent
            responses = []
            tool_calls = []
            
            for response in self._agent.run(messages=messages):
                responses.append(response)
                
                # Track tool calls if present
                if isinstance(response, list):
                    for item in response:
                        if isinstance(item, dict) and 'function_call' in item:
                            tool_calls.append(item['function_call'])
                elif isinstance(response, dict):
                    if 'function_call' in response:
                        tool_calls.append(response['function_call'])
            
            # Extract final response text
            final_response = ""
            if responses:
                last_response = responses[-1]
                if isinstance(last_response, list) and last_response:
                    last_item = last_response[-1]
                    if isinstance(last_item, dict):
                        final_response = last_item.get('content', str(last_item))
                    else:
                        final_response = str(last_item)
                elif isinstance(last_response, dict):
                    final_response = last_response.get('content', str(last_response))
                else:
                    final_response = str(last_response)
            
            logger.info(f"Task processed successfully with {len(tool_calls)} tool calls")
            
            return AgentResponse(
                success=True,
                response=final_response,
                tool_calls=tool_calls
            )
            
        except Exception as e:
            error_msg = f"Failed to process task: {e}"
            logger.error(error_msg)
            return AgentResponse(
                success=False,
                error=error_msg
            )
