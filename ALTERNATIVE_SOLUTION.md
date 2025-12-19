# 替代解决方案 - 绕过 qwen-agent 的 LLM 限制

## 当前问题

qwen-agent 框架与本地 Ollama 的集成存在问题：
1. 默认使用 DashScope API
2. 即使配置 OpenAI 模式，仍然验证 API key
3. Ollama 的 `/v1` 端点可能在某些版本中不可用

## 建议的解决方案

### 方案 A: 升级 Ollama（推荐）

确保使用最新版本的 Ollama，它完全支持 OpenAI 兼容 API。

```bash
# 检查 Ollama 版本
ollama --version

# 如果版本较旧，升级 Ollama
# Windows: 重新下载并安装最新版本
# https://ollama.com/download

# 验证 OpenAI 端点
curl http://localhost:11434/v1/models
```

### 方案 B: 使用真实的 DashScope API Key

如果你有阿里云 DashScope 账号，可以使用真实的 API key：

```bash
# 设置环境变量
$env:DASHSCOPE_API_KEY="your_real_api_key"

# 或者在代码中设置
# 在 agent_client.py 中：
os.environ['DASHSCOPE_API_KEY'] = 'your_real_api_key'
```

**注意**: 这会使用云端服务而不是本地 Ollama。

### 方案 C: 简化 Agent 实现（推荐用于开发）

创建一个简化的 Agent 客户端，直接使用 Ollama API 而不通过 qwen-agent：

#### 1. 创建简化的 Agent 客户端

创建文件 `agent-scheduler/src/simple_agent_client.py`:

```python
"""
Simplified Agent Client using Ollama directly

This bypasses qwen-agent and uses Ollama's API directly.
"""

import logging
import requests
import json
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass

from shared.models import ModelConfig

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Response from agent task processing"""
    success: bool
    response: str = ""
    tool_calls: List[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.tool_calls is None:
            self.tool_calls = []


class SimpleAgentClient:
    """Simplified agent client using Ollama directly"""
    
    def __init__(self, model_config: ModelConfig, tools: List[Dict[str, Any]]):
        self.model_config = model_config
        self.tools = tools
        self.tool_executor: Optional[Callable] = None
        logger.info(f"SimpleAgentClient initialized with {len(tools)} tools")
    
    def register_tool_executor(self, executor: Callable) -> None:
        """Register tool executor"""
        self.tool_executor = executor
        logger.info("Tool executor registered")
    
    def process_task(self, task_description: str) -> AgentResponse:
        """Process a task using Ollama directly"""
        try:
            logger.info(f"Processing task: {task_description}")
            
            # Build system prompt with available tools
            system_prompt = self._build_system_prompt()
            
            # Call Ollama
            response_text = self._call_ollama(system_prompt, task_description)
            
            # Parse response for tool calls
            tool_calls = self._parse_tool_calls(response_text)
            
            # Execute tools if needed
            if tool_calls and self.tool_executor:
                results = []
                for tool_call in tool_calls:
                    result = self.tool_executor(
                        tool_call['name'],
                        tool_call['parameters']
                    )
                    results.append(result)
                
                # Generate final response with tool results
                final_response = self._generate_final_response(
                    task_description,
                    tool_calls,
                    results
                )
                response_text = final_response
            
            return AgentResponse(
                success=True,
                response=response_text,
                tool_calls=tool_calls
            )
            
        except Exception as e:
            error_msg = f"Failed to process task: {e}"
            logger.error(error_msg)
            return AgentResponse(
                success=False,
                error=error_msg
            )
    
    def _build_system_prompt(self) -> str:
        """Build system prompt with tool descriptions"""
        prompt = "你是一个智能助手，可以使用以下工具来帮助用户：\n\n"
        
        for tool in self.tools:
            prompt += f"工具名称: {tool['name']}\n"
            prompt += f"描述: {tool['description']}\n"
            
            if 'parameters' in tool and 'properties' in tool['parameters']:
                prompt += "参数:\n"
                for param_name, param_info in tool['parameters']['properties'].items():
                    required = param_name in tool['parameters'].get('required', [])
                    prompt += f"  - {param_name} ({param_info['type']})"
                    if required:
                        prompt += " [必需]"
                    prompt += f": {param_info['description']}\n"
            prompt += "\n"
        
        prompt += "当需要使用工具时，请以 JSON 格式回复：\n"
        prompt += '{"tool": "工具名称", "parameters": {"参数名": "参数值"}}\n\n'
        prompt += "如果不需要使用工具，直接回答用户的问题。"
        
        return prompt
    
    def _call_ollama(self, system_prompt: str, user_message: str) -> str:
        """Call Ollama API"""
        url = f"{self.model_config.api_base}/api/generate"
        
        prompt = f"{system_prompt}\n\n用户: {user_message}\n助手:"
        
        payload = {
            "model": self.model_config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.model_config.temperature,
                "num_predict": self.model_config.max_tokens
            }
        }
        
        response = requests.post(
            url,
            json=payload,
            timeout=self.model_config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '')
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    def _parse_tool_calls(self, response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from response"""
        tool_calls = []
        
        # Try to find JSON in response
        try:
            # Look for JSON object
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)
                
                if 'tool' in data:
                    tool_calls.append({
                        'name': data['tool'],
                        'parameters': data.get('parameters', {})
                    })
        except:
            pass
        
        return tool_calls
    
    def _generate_final_response(
        self,
        task: str,
        tool_calls: List[Dict],
        results: List[Any]
    ) -> str:
        """Generate final response with tool results"""
        
        # Build context with tool results
        context = f"用户任务: {task}\n\n"
        context += "工具执行结果:\n"
        
        for tool_call, result in zip(tool_calls, results):
            context += f"- {tool_call['name']}: "
            if hasattr(result, 'success') and result.success:
                context += str(result.result)
            else:
                context += "执行失败"
            context += "\n"
        
        context += "\n请根据以上信息回答用户的问题。"
        
        # Call Ollama again for final response
        return self._call_ollama("", context)
```

#### 2. 修改 main.py 使用简化客户端

在 `agent-scheduler/src/main.py` 中：

```python
# 替换导入
# from src.agent_client import AgentClient
from src.simple_agent_client import SimpleAgentClient as AgentClient
```

#### 3. 重启服务

```bash
cd agent-scheduler
python src/main.py
```

### 方案 D: 使用 LangChain（高级）

如果需要更强大的功能，考虑使用 LangChain 替代 qwen-agent：

```python
from langchain.llms import Ollama
from langchain.agents import initialize_agent, Tool

llm = Ollama(
    model="qwen3:4b",
    base_url="http://localhost:11434"
)

tools = [
    Tool(
        name="get_weather",
        func=weather_function,
        description="Get weather information"
    )
]

agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
```

## 推荐方案

### 对于生产环境
1. **升级 Ollama** 到最新版本
2. 使用 **OpenAI 兼容 API**（方案 A）
3. 或使用 **真实的 DashScope API key**（方案 B）

### 对于开发/测试
1. 使用 **简化的 Agent 客户端**（方案 C）
2. 直接调用 Ollama API
3. 避免 qwen-agent 的复杂性

## 验证步骤

### 1. 检查 Ollama 版本和功能

```bash
# 版本
ollama --version

# 测试标准 API
curl -X POST http://localhost:11434/api/generate \
  -d '{"model":"qwen3:4b","prompt":"你好","stream":false}'

# 测试 OpenAI 兼容 API（如果支持）
curl -X POST http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:4b","messages":[{"role":"user","content":"你好"}]}'
```

### 2. 选择合适的方案

- 如果 `/v1` 端点工作 → 使用方案 A（当前实现）
- 如果 `/v1` 不工作 → 使用方案 C（简化客户端）
- 如果有 DashScope key → 使用方案 B

### 3. 测试服务

```bash
# 启动服务
python src/main.py

# 测试 API
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description":"你好"}'
```

## 总结

qwen-agent 与本地 Ollama 的集成存在兼容性问题。推荐：

1. **短期**: 使用简化的 Agent 客户端（方案 C）
2. **长期**: 升级 Ollama 或考虑使用 LangChain

这样可以避免 DashScope API key 的问题，直接使用本地 Ollama。
