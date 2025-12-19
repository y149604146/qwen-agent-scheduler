# 快速修复：DashScope API 错误

## 问题
```
No api key provided. You can set by dashscope.api_key...
```

## 原因
qwen-agent 默认尝试使用 DashScope（阿里云服务），而不是本地 Ollama。

## 解决方案

### ✅ 代码已修复

`agent-scheduler/src/agent_client.py` 已更新，添加了 `model_server='ollama'` 配置。

### 重启服务

```bash
# 1. 停止当前运行的服务（Ctrl+C）

# 2. 确保 Ollama 正在运行
ollama serve

# 3. 在另一个终端，重启 Agent Scheduler
cd agent-scheduler
python src/main.py
```

### 测试

```bash
# 提交任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "查询北京今天天气"}'
```

或者在浏览器中访问：
```
http://localhost:8000/docs
```

## 验证 Ollama

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 检查模型是否存在
ollama list | grep qwen3:4b
```

## 如果还有问题

查看详细文档：
- `agent-scheduler/OLLAMA_SETUP.md` - 完整的 Ollama 配置指南
- `FIXES_SUMMARY.md` - 所有修复的总结

## 修改内容

**文件**: `agent-scheduler/src/agent_client.py`

**修改前**:
```python
llm_config = {
    'model': self.model_config.model_name,
    'api_base': self.model_config.api_base,
    'generate_cfg': {
        'temperature': self.model_config.temperature,
        'max_tokens': self.model_config.max_tokens,
    }
}
```

**修改后**:
```python
llm_config = {
    'model': self.model_config.model_name,
    'model_server': 'ollama',  # ← 添加这一行
    'api_base': self.model_config.api_base,
    'generate_cfg': {
        'temperature': self.model_config.temperature,
        'max_tokens': self.model_config.max_tokens,
    }
}
```

这个简单的修改告诉 qwen-agent 使用本地 Ollama 而不是云端 DashScope 服务。
