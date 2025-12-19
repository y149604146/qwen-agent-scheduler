"""
Simplified Agent Client using Ollama directly

This bypasses qwen-agent and uses Ollama's API directly to avoid
DashScope API key issues.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import logging
import requests
import json
import re
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field

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
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class SimpleAgentClient:
    """Simplified agent client using Ollama directly
    
    This implementation bypasses qwen-agent and directly uses Ollama's API,
    avoiding DashScope API key requirements.
    
    Attributes:
        model_config: Configuration for the LLM model
        tools: List of tool definitions
        tool_executor: Callable for executing tool/method calls
    """
    
    def __init__(self, model_config: ModelConfig, tools: List[Dict[str, Any]]):
        """Initialize SimpleAgentClient
        
        Args:
            model_config: Configuration for the Ollama model
            tools: List of tool definitions in standard format
            
        Raises:
            AgentClientError: If initialization fails
        """
        self.model_config = model_config
        self.tools = tools
        self.tool_executor: Optional[Callable] = None
        
        logger.info(f"SimpleAgentClient initialized with {len(tools)} tools")
        logger.info(f"Using Ollama at {model_config.api_base} with model {model_config.model_name}")
    
    def register_tool_executor(self, executor: Callable[[str, Dict[str, Any]], Any]) -> None:
        """Register a method executor for tool calls
        
        Args:
            executor: Callable that takes (method_name, parameters) and returns result
        """
        self.tool_executor = executor
        logger.info("Tool executor registered successfully")
    
    def process_task(self, task_description: str) -> AgentResponse:
        """Process a task using Ollama directly
        
        Args:
            task_description: User's task description
            
        Returns:
            AgentResponse with success status and response text
        """
        try:
            logger.info(f"Processing task: {task_description}")
            
            # Step 1: Build system prompt with available tools
            system_prompt = self._build_system_prompt()
            
            # Step 2: Call Ollama to understand the task
            response_text = self._call_ollama(system_prompt, task_description)
            logger.debug(f"Initial response: {response_text[:200]}...")
            
            # Step 3: Parse response for tool calls
            tool_calls = self._parse_tool_calls(response_text)
            
            # Step 4: Execute tools if needed
            if tool_calls and self.tool_executor:
                logger.info(f"Executing {len(tool_calls)} tool call(s)")
                
                tool_results = []
                for tool_call in tool_calls:
                    logger.info(f"Calling tool: {tool_call['name']} with params: {tool_call['parameters']}")
                    
                    try:
                        result = self.tool_executor(
                            tool_call['name'],
                            tool_call['parameters']
                        )
                        tool_results.append({
                            'tool': tool_call['name'],
                            'success': getattr(result, 'success', True),
                            'result': getattr(result, 'result', str(result))
                        })
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        tool_results.append({
                            'tool': tool_call['name'],
                            'success': False,
                            'result': f"Error: {e}"
                        })
                
                # Step 5: Generate final response with tool results
                final_response = self._generate_final_response(
                    task_description,
                    tool_results
                )
                response_text = final_response
            
            logger.info("Task processed successfully")
            return AgentResponse(
                success=True,
                response=response_text,
                tool_calls=tool_calls
            )
            
        except Exception as e:
            error_msg = f"Failed to process task: {e}"
            logger.error(error_msg)
            logger.exception("Task processing error details:")
            return AgentResponse(
                success=False,
                error=error_msg
            )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions
        
        Returns:
            System prompt string with tool information
        """
        prompt = "你是一个智能助手，可以使用以下工具来帮助用户：\n\n"
        
        for tool in self.tools:
            prompt += f"【工具】{tool['name']}\n"
            prompt += f"描述：{tool['description']}\n"
            
            if 'parameters' in tool and 'properties' in tool['parameters']:
                prompt += "参数：\n"
                for param_name, param_info in tool['parameters']['properties'].items():
                    required = param_name in tool['parameters'].get('required', [])
                    prompt += f"  - {param_name} ({param_info['type']})"
                    if required:
                        prompt += " [必需]"
                    prompt += f": {param_info['description']}\n"
            prompt += "\n"
        
        prompt += "【使用工具的格式】\n"
        prompt += "当需要使用工具时，请严格按照以下 JSON 格式回复：\n"
        prompt += '```json\n'
        prompt += '{"tool": "工具名称", "parameters": {"参数名": "参数值"}}\n'
        prompt += '```\n\n'
        prompt += "【重要】\n"
        prompt += "- 如果用户的问题需要使用工具，必须使用上述 JSON 格式\n"
        prompt += "- 如果不需要使用工具，直接用自然语言回答\n"
        prompt += "- 一次只能调用一个工具\n"
        
        return prompt
    
    def _call_ollama(self, system_prompt: str, user_message: str) -> str:
        """Call Ollama API
        
        Args:
            system_prompt: System prompt with instructions
            user_message: User's message
            
        Returns:
            Response text from Ollama
            
        Raises:
            Exception: If Ollama API call fails
        """
        url = f"{self.model_config.api_base}/api/generate"
        
        # Combine system prompt and user message
        full_prompt = f"{system_prompt}\n\n【用户问题】\n{user_message}\n\n【助手回复】\n"
        
        payload = {
            "model": self.model_config.model_name,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.model_config.temperature,
                "num_predict": self.model_config.max_tokens
            }
        }
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.model_config.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            raise Exception(f"Ollama request timed out after {self.model_config.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to Ollama at {self.model_config.api_base}")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {e}")
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from response
        
        Looks for JSON objects in the response that match the tool call format.
        
        Args:
            response: Response text from Ollama
            
        Returns:
            List of tool call dictionaries
        """
        tool_calls = []
        
        try:
            # Method 1: Look for JSON code blocks
            json_blocks = re.findall(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
            for json_str in json_blocks:
                try:
                    data = json.loads(json_str)
                    if 'tool' in data:
                        tool_calls.append({
                            'name': data['tool'],
                            'parameters': data.get('parameters', {})
                        })
                except json.JSONDecodeError:
                    continue
            
            # Method 2: Look for plain JSON objects if no code blocks found
            if not tool_calls:
                # Find all JSON-like structures
                json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
                matches = re.findall(json_pattern, response)
                
                for match in matches:
                    try:
                        data = json.loads(match)
                        if 'tool' in data:
                            tool_calls.append({
                                'name': data['tool'],
                                'parameters': data.get('parameters', {})
                            })
                    except json.JSONDecodeError:
                        continue
            
            if tool_calls:
                logger.debug(f"Parsed {len(tool_calls)} tool call(s) from response")
            else:
                logger.debug("No tool calls found in response")
                
        except Exception as e:
            logger.warning(f"Error parsing tool calls: {e}")
        
        return tool_calls
    
    def _generate_final_response(
        self,
        task: str,
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate final response with tool results
        
        Args:
            task: Original user task
            tool_results: Results from tool executions
            
        Returns:
            Final response text
        """
        # Build context with tool results
        context = f"用户的问题是：{task}\n\n"
        context += "我已经使用工具获取了以下信息：\n\n"
        
        for result in tool_results:
            context += f"【{result['tool']}】\n"
            if result['success']:
                context += f"结果：{result['result']}\n"
            else:
                context += f"执行失败：{result['result']}\n"
            context += "\n"
        
        context += "请根据以上工具返回的信息，用自然语言回答用户的问题。"
        context += "不要提及工具的名称，直接给出答案。"
        
        # Call Ollama again for final response
        try:
            final_response = self._call_ollama("", context)
            return final_response
        except Exception as e:
            logger.error(f"Failed to generate final response: {e}")
            # Fallback: return tool results directly
            return "\n".join([f"{r['tool']}: {r['result']}" for r in tool_results])
