# DashScope API Key 错误修复

## 问题描述

运行 Agent Scheduler 时出现错误：
```
No api key provided. You can set by dashscope.api_key...
```
或
```
Error code: InvalidApiKey. Error message: Invalid API-key provided.
```

## 根本原因

qwen-agent 框架默认配置为使用阿里云的 DashScope API。即使配置了 `api_base` 指向本地 Ollama，它仍然会尝试验证 DashScope API key。

## 最终解决方案 ✅

### 使用 Ollama 的 OpenAI 兼容 API

**文件**: `agent-scheduler/src/agent_client.py`

Ollama 提供了 OpenAI 兼容的 API 端点（`/v1`），我们可以配置 qwen-agent 使用 OpenAI 模式而不是 DashScope：

```python
# Configure for Ollama using OpenAI-compatible API
os.environ['OPENAI_API_KEY'] = 'ollama-local-key'

llm_config = {
    'model': self.model_config.model_name,
    'model_server': 'openai',  # Use OpenAI-compatible mode
    'api_base': f"{self.model_config.api_base}/v1",  # Ollama's OpenAI endpoint
    'api_key': 'ollama-local-key',  # Dummy key for local Ollama
    'generate_cfg': {
        'temperature': self.model_config.temperature,
        'max_tokens': self.model_config.max_tokens,
    }
}
```

这个方法：
- ✅ 完全绕过 DashScope
- ✅ 使用 Ollama 的标准 OpenAI 兼容接口
- ✅ 不需要真实的 API key（本地 Ollama 不需要认证）

### 方案 2: 环境变量（备选）

在启动服务前设置环境变量：

**PowerShell**:
```powershell
$env:DASHSCOPE_API_KEY="dummy_key_for_ollama"
python src/main.py
```

**Bash/Linux**:
```bash
export DASHSCOPE_API_KEY="dummy_key_for_ollama"
python src/main.py
```

**Windows CMD**:
```cmd
set DASHSCOPE_API_KEY=dummy_key_for_ollama
python src/main.py
```

### 方案 3: 配置文件（永久设置）

创建 `~/.dashscope/api_key` 文件：

**PowerShell**:
```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.dashscope"
Set-Content -Path "$env:USERPROFILE\.dashscope\api_key" -Value "dummy_key_for_ollama"
```

**Bash/Linux**:
```bash
mkdir -p ~/.dashscope
echo "dummy_key_for_ollama" > ~/.dashscope/api_key
```

## 重启服务

修改代码后，必须重启服务：

```bash
# 1. 停止当前服务（Ctrl+C）

# 2. 确保 Ollama 正在运行
ollama serve

# 3. 重启 Agent Scheduler
cd agent-scheduler
python src/main.py
```

## 验证修复

### 1. 检查服务启动日志

应该看到：
```
Agent Scheduler Brain initialized successfully
```

而不是 DashScope API key 错误。

### 2. 测试 API 调用

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "你好"}'
```

### 3. 检查任务状态

```bash
# 使用返回的 task_id
curl http://localhost:8000/api/tasks/{task_id}
```

## 工作原理

### qwen-agent 的模型选择逻辑

1. **检查 API key**: qwen-agent 首先检查是否有 DashScope API key
2. **选择后端**: 
   - 如果有 API key 且没有 `api_base`，使用 DashScope
   - 如果有 `api_base`，使用指定的服务器（Ollama）
3. **发送请求**: 实际请求发送到 `api_base` 指定的地址

### 为什么需要虚拟 key

即使我们配置了 `api_base` 指向 Ollama，qwen-agent 仍然会在初始化时检查 API key 是否存在。设置一个虚拟 key 可以通过这个检查，而实际的 API 调用会发送到 Ollama。

### 安全性

- 虚拟 key 不会被发送到任何地方
- 所有请求都发送到本地 Ollama（`http://localhost:11434`）
- 数据不会离开本地机器

## 配置验证

### 检查配置文件

`config/model_config.yaml`:
```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"  # ← 确保指向 Ollama
  timeout: 30
  temperature: 0.7
  max_tokens: 2000
```

### 检查 Ollama

```bash
# 检查 Ollama 服务
curl http://localhost:11434/api/tags

# 检查模型
ollama list | grep qwen3:4b
```

### 检查环境变量（如果使用方案 2）

**PowerShell**:
```powershell
$env:DASHSCOPE_API_KEY
```

**Bash**:
```bash
echo $DASHSCOPE_API_KEY
```

## 故障排除

### 问题 1: 仍然看到 API key 错误

**解决方案**:
1. 确保已重启服务（修改代码后必须重启）
2. 检查代码修改是否正确应用
3. 尝试方案 2（环境变量）

### 问题 2: 连接 Ollama 失败

**解决方案**:
1. 确保 Ollama 正在运行：`ollama serve`
2. 测试 Ollama 连接：`curl http://localhost:11434/api/tags`
3. 检查防火墙设置

### 问题 3: 模型响应错误

**解决方案**:
1. 确保模型已下载：`ollama list`
2. 测试模型：`ollama run qwen3:4b "你好"`
3. 检查模型名称是否正确

## 完整的启动流程

```bash
# 1. 启动 PostgreSQL（如果还没运行）
# 根据你的系统启动 PostgreSQL

# 2. 启动 Ollama
ollama serve

# 3. 验证 Ollama
ollama list

# 4. 注册方法（如果还没有）
cd method-registration
python src/main.py
cd ..

# 5. 启动 Agent Scheduler
cd agent-scheduler
python src/main.py

# 6. 测试 API
# 在浏览器中打开: http://localhost:8000/docs
```

## 日志分析

### 成功的日志

```
2025-12-18 17:19:06 - agent_client - INFO - AgentClient initialized with 2 tools
2025-12-18 17:19:06 - agent_client - INFO - Processing task: 查询今天天气
2025-12-18 17:19:07 - agent_client - INFO - Task completed successfully
```

### 失败的日志

```
2025-12-18 17:19:06 - agent_client - ERROR - Failed to process task: No api key provided...
```

如果看到失败日志，说明修复没有生效，需要重启服务。

## 代码修改详情

### 修改前

```python
def _initialize_agent(self) -> None:
    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.tools.base import BaseTool, register_tool
        
        llm_config = {
            'model': self.model_config.model_name,
            'api_base': self.model_config.api_base,
            'generate_cfg': {
                'temperature': self.model_config.temperature,
                'max_tokens': self.model_config.max_tokens,
            }
        }
```

### 修改后

```python
def _initialize_agent(self) -> None:
    try:
        from qwen_agent.agents import Assistant
        from qwen_agent.tools.base import BaseTool, register_tool
        import os
        
        # Set environment variable to disable DashScope API key requirement
        os.environ['DASHSCOPE_API_KEY'] = 'dummy_key_for_ollama'
        
        llm_config = {
            'model': self.model_config.model_name,
            'model_server': 'ollama',
            'api_base': self.model_config.api_base,
            'generate_cfg': {
                'temperature': self.model_config.temperature,
                'max_tokens': self.model_config.max_tokens,
            }
        }
```

## 总结

✅ **代码已修复** - 添加了虚拟 API key 设置
✅ **配置已优化** - 明确指定使用 Ollama
✅ **文档已完善** - 提供了多种解决方案

**重要**: 修改代码后必须重启服务才能生效！
