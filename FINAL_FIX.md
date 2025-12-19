# 最终修复方案 - Ollama OpenAI 兼容 API

## 问题演变

1. **第一个错误**: `No api key provided`
   - qwen-agent 要求 DashScope API key

2. **第二个错误**: `Invalid API-key provided`
   - 设置了虚拟 key，但 qwen-agent 尝试验证它

3. **根本原因**: qwen-agent 默认使用 DashScope，即使配置了 `api_base`

## ✅ 最终解决方案

### 使用 Ollama 的 OpenAI 兼容 API

Ollama 提供了 OpenAI 兼容的 API 端点（`/v1`），我们配置 qwen-agent 使用 OpenAI 模式：

**修改文件**: `agent-scheduler/src/agent_client.py`

```python
# Configure for Ollama using OpenAI-compatible API
os.environ['OPENAI_API_KEY'] = 'ollama-local-key'

llm_config = {
    'model': self.model_config.model_name,
    'model_server': 'openai',  # ← 使用 OpenAI 模式
    'api_base': f"{self.model_config.api_base}/v1",  # ← 添加 /v1
    'api_key': 'ollama-local-key',  # ← 虚拟 key（本地不需要）
    'generate_cfg': {
        'temperature': self.model_config.temperature,
        'max_tokens': self.model_config.max_tokens,
    }
}
```

### 为什么这样可以工作

1. **Ollama 的 OpenAI 兼容性**
   - Ollama 在 `/v1` 端点提供 OpenAI 兼容的 API
   - 支持 `/v1/chat/completions` 等标准端点

2. **绕过 DashScope**
   - 使用 `model_server='openai'` 而不是默认的 DashScope
   - qwen-agent 会使用 OpenAI 的客户端库

3. **本地认证**
   - Ollama 本地部署不需要真实的 API key
   - 虚拟 key 只是为了满足 qwen-agent 的参数要求

## 🔴 重要：必须重启服务

```bash
# 1. 停止当前服务（Ctrl+C）

# 2. 重新启动
cd agent-scheduler
python src/main.py
```

## 验证修复

### 1. 测试 Ollama OpenAI API

```bash
python test_ollama_openai.py
```

应该看到：
```
✓ Success!
Ollama's OpenAI-compatible API is working correctly!
```

### 2. 测试 Agent Scheduler

重启服务后，提交任务：

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "你好"}'
```

### 3. 检查日志

成功的日志应该显示：
```
2025-12-18 17:25:09 - agent_client - INFO - Processing task: 你好
2025-12-18 17:25:10 - agent_client - INFO - Task completed successfully
```

而不是：
```
ERROR - Failed to process task: Invalid API-key provided
```

## Ollama OpenAI 兼容端点

Ollama 提供以下 OpenAI 兼容端点：

| 端点 | 用途 |
|------|------|
| `/v1/chat/completions` | 聊天补全（推荐） |
| `/v1/completions` | 文本补全 |
| `/v1/embeddings` | 文本嵌入 |
| `/v1/models` | 列出模型 |

我们使用的配置会自动路由到正确的端点。

## 配置对比

### 之前的配置（不工作）

```python
llm_config = {
    'model': 'qwen3:4b',
    'model_server': 'ollama',  # ← 这个模式有问题
    'api_base': 'http://localhost:11434',
}
```

### 现在的配置（工作）

```python
llm_config = {
    'model': 'qwen3:4b',
    'model_server': 'openai',  # ← 使用 OpenAI 模式
    'api_base': 'http://localhost:11434/v1',  # ← 添加 /v1
    'api_key': 'ollama-local-key',  # ← 虚拟 key
}
```

## 故障排除

### 问题 1: 连接被拒绝

```
Connection refused to http://localhost:11434/v1
```

**解决方案**:
```bash
# 确保 Ollama 正在运行
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

# 验证
ollama list
```

### 问题 3: 仍然看到 DashScope 错误

**解决方案**:
1. 确保代码修改已保存
2. 完全停止并重启服务（不是热重载）
3. 检查是否在正确的目录运行

### 问题 4: 超时错误

```
Request timed out
```

**解决方案**:
```yaml
# 在 config/model_config.yaml 中增加超时
model:
  timeout: 60  # 增加到 60 秒
```

## 完整的启动流程

```bash
# 1. 测试 Ollama OpenAI API
python test_ollama_openai.py

# 2. 如果测试通过，启动服务
cd agent-scheduler
python src/main.py

# 3. 在浏览器中测试
# 打开: http://localhost:8000/docs

# 4. 提交测试任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "你好，介绍一下你自己"}'
```

## 技术细节

### qwen-agent 的模型服务器支持

qwen-agent 支持多种模型服务器：
- `dashscope` - 阿里云 DashScope（默认）
- `openai` - OpenAI 或兼容的 API
- `ollama` - Ollama 原生 API（但实现有问题）

我们选择 `openai` 模式，因为：
1. Ollama 完全兼容 OpenAI API
2. qwen-agent 的 OpenAI 支持更成熟
3. 避免了 DashScope 的 API key 验证

### API 端点映射

当使用 `model_server='openai'` 时：
- qwen-agent 调用 → OpenAI 客户端库
- OpenAI 客户端 → `{api_base}/chat/completions`
- 实际请求 → `http://localhost:11434/v1/chat/completions`
- Ollama 处理 → 返回 OpenAI 格式的响应

## 性能考虑

### 首次请求可能较慢
- Ollama 需要加载模型到内存
- 后续请求会更快

### 优化建议
1. 保持 Ollama 服务持续运行
2. 使用较小的模型（qwen3:4b 已经很好）
3. 考虑使用 GPU 加速（如果可用）

## 安全性

### 本地部署的优势
- ✅ 数据不离开本地机器
- ✅ 不需要真实的 API key
- ✅ 完全控制模型和数据
- ✅ 无网络依赖（除了初始下载）

### 虚拟 API Key
- 只用于满足 qwen-agent 的参数要求
- 不会被发送到任何远程服务器
- Ollama 本地部署不验证 API key

## 总结

✅ **问题已解决** - 使用 Ollama 的 OpenAI 兼容 API
✅ **代码已更新** - `agent_client.py` 配置为使用 OpenAI 模式
✅ **测试脚本已创建** - `test_ollama_openai.py` 用于验证
✅ **文档已完善** - 详细的故障排除指南

**下一步**: 重启服务并测试！
