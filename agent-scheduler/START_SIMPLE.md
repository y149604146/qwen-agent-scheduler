# 使用简化 Agent 客户端启动

## 简介

简化的 Agent 客户端直接使用 Ollama API，完全绕过 qwen-agent 的 DashScope API key 验证问题。

## 优点

- ✅ 不需要 DashScope API key
- ✅ 直接使用 Ollama API
- ✅ 更简单、更可靠
- ✅ 完全本地化
- ✅ 更容易调试

## 启动方式

### 方式 1: 使用环境变量（默认）

简化客户端现在是默认选项：

```bash
cd agent-scheduler
python src/main.py
```

### 方式 2: 明确指定使用简化客户端

```bash
# PowerShell
$env:USE_SIMPLE_AGENT="1"
python src/main.py

# Bash/Linux
export USE_SIMPLE_AGENT=1
python src/main.py

# Windows CMD
set USE_SIMPLE_AGENT=1
python src/main.py
```

### 方式 3: 切换回标准客户端（如果需要）

```bash
# PowerShell
$env:USE_SIMPLE_AGENT="0"
python src/main.py

# Bash/Linux
export USE_SIMPLE_AGENT=0
python src/main.py
```

## 验证

启动后，你应该看到：

```
Using SimpleAgentClient (direct Ollama API)
Agent Scheduler Brain initialized successfully
```

而不是 DashScope API key 错误。

## 测试

### 1. 启动服务

```bash
cd agent-scheduler
python src/main.py
```

### 2. 访问 API 文档

浏览器打开：
```
http://localhost:8000/docs
```

### 3. 提交测试任务

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description":"你好，介绍一下你自己"}'
```

### 4. 查询任务状态

```bash
# 使用返回的 task_id
curl http://localhost:8000/api/tasks/{task_id}
```

## 工作原理

### 简化客户端流程

1. **接收任务** - 用户提交任务描述
2. **构建提示** - 包含可用工具的描述
3. **调用 Ollama** - 直接使用 Ollama API
4. **解析响应** - 查找工具调用（JSON 格式）
5. **执行工具** - 如果需要，调用注册的方法
6. **生成最终响应** - 基于工具结果生成回答

### 与标准客户端的区别

| 特性 | 标准客户端 | 简化客户端 |
|------|-----------|-----------|
| 依赖 | qwen-agent | 仅 requests |
| API Key | 需要（问题所在） | 不需要 ✅ |
| 复杂度 | 高 | 低 ✅ |
| 调试 | 困难 | 容易 ✅ |
| 功能 | 完整 | 核心功能 |

## 配置

简化客户端使用相同的配置文件 `config/model_config.yaml`：

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"  # Ollama API 地址
  timeout: 30
  temperature: 0.7
  max_tokens: 2000
```

## 日志

### 成功的日志示例

```
2025-12-18 17:30:00 - main - INFO - Using SimpleAgentClient (direct Ollama API)
2025-12-18 17:30:00 - simple_agent_client - INFO - SimpleAgentClient initialized with 2 tools
2025-12-18 17:30:00 - simple_agent_client - INFO - Using Ollama at http://localhost:11434 with model qwen3:4b
2025-12-18 17:30:05 - simple_agent_client - INFO - Processing task: 查询北京天气
2025-12-18 17:30:06 - simple_agent_client - INFO - Executing 1 tool call(s)
2025-12-18 17:30:06 - simple_agent_client - INFO - Calling tool: get_weather with params: {'city': '北京'}
2025-12-18 17:30:07 - simple_agent_client - INFO - Task processed successfully
```

## 故障排除

### 问题 1: Ollama 连接失败

```
Cannot connect to Ollama at http://localhost:11434
```

**解决方案**:
```bash
# 启动 Ollama
ollama serve
```

### 问题 2: 模型未找到

```
Model 'qwen3:4b' not found
```

**解决方案**:
```bash
# 下载模型
ollama pull qwen3:4b
```

### 问题 3: 工具未执行

检查日志中是否有 "Parsed X tool call(s)"。如果没有，说明模型没有正确理解工具调用格式。

**解决方案**:
- 检查工具描述是否清晰
- 尝试更明确的任务描述
- 查看 Ollama 的原始响应（DEBUG 日志）

### 问题 4: 超时

```
Ollama request timed out after 30 seconds
```

**解决方案**:
```yaml
# 在 config/model_config.yaml 中增加超时
model:
  timeout: 60  # 增加到 60 秒
```

## 性能

### 首次请求
- 可能需要 5-10 秒（模型加载）
- 后续请求会更快（1-3 秒）

### 优化建议
1. 保持 Ollama 服务持续运行
2. 使用较小的模型（qwen3:4b 已经很好）
3. 调整 temperature 和 max_tokens

## 限制

简化客户端的限制：

1. **单次工具调用** - 一次只能调用一个工具
2. **简单解析** - 使用正则表达式解析工具调用
3. **无对话历史** - 每次请求独立处理

这些限制对大多数用例来说是可以接受的。

## 切换回标准客户端

如果将来 qwen-agent 的问题解决了，可以切换回标准客户端：

```bash
$env:USE_SIMPLE_AGENT="0"
python src/main.py
```

## 总结

✅ **简化客户端已实现并设为默认**
✅ **完全绕过 DashScope API key 问题**
✅ **直接使用 Ollama API**
✅ **更简单、更可靠**

现在你可以直接启动服务，不会再遇到 API key 错误！

```bash
cd agent-scheduler
python src/main.py
```

然后访问 `http://localhost:8000/docs` 开始使用！
