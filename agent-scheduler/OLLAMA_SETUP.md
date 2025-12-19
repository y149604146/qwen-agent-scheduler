# Ollama 配置指南

## 问题说明

如果你看到以下错误：

```
No api key provided. You can set by dashscope.api_key = your_api_key...
```

这表示 qwen-agent 正在尝试使用 DashScope API（阿里云服务），而不是本地 Ollama。

## 解决方案

### 1. 确保 Ollama 服务正在运行

```bash
# 启动 Ollama 服务
ollama serve
```

在另一个终端窗口中验证：

```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/tags

# 或者
ollama list
```

### 2. 确保 qwen3:4b 模型已下载

```bash
# 下载模型（如果还没有）
ollama pull qwen3:4b

# 验证模型存在
ollama list | grep qwen3:4b
```

### 3. 验证配置文件

检查 `config/model_config.yaml`：

```yaml
model:
  name: "qwen3:4b"                          # 模型名称
  api_base: "http://localhost:11434"        # Ollama API 地址
  timeout: 30
  temperature: 0.7
  max_tokens: 2000
```

### 4. 代码已修复

`agent_client.py` 已更新，现在会明确指定使用 Ollama：

```python
llm_config = {
    'model': self.model_config.model_name,
    'model_server': 'ollama',  # 明确使用 Ollama
    'api_base': self.model_config.api_base,
    'generate_cfg': {
        'temperature': self.model_config.temperature,
        'max_tokens': self.model_config.max_tokens,
    }
}
```

## 测试配置

### 测试 Ollama 连接

```bash
# 测试 Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "qwen3:4b",
  "prompt": "你好",
  "stream": false
}'
```

应该返回 JSON 响应。

### 测试 Agent Scheduler

```bash
cd agent-scheduler

# 重启服务
python src/main.py
```

或者运行 demo：

```bash
python examples/main_demo.py
```

然后访问 API：

```bash
# 提交任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "查询北京今天天气"}'
```

## 常见问题

### Q: 仍然看到 DashScope API 错误

**A:** 确保：
1. Ollama 服务正在运行：`ollama serve`
2. 模型已下载：`ollama list`
3. 重启 Agent Scheduler 服务
4. 检查 `model_config.yaml` 中的 `api_base` 是否正确

### Q: Ollama 服务无法启动

**A:** 检查：
1. Ollama 是否已安装：`ollama --version`
2. 端口 11434 是否被占用：`netstat -ano | findstr :11434`
3. 查看 Ollama 日志

### Q: 模型下载失败

**A:** 尝试：
```bash
# 使用代理（如果需要）
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port

# 重新下载
ollama pull qwen3:4b
```

### Q: API 调用超时

**A:** 调整配置：
```yaml
model:
  timeout: 60  # 增加超时时间
```

## Ollama vs DashScope

| 特性 | Ollama (本地) | DashScope (云端) |
|------|--------------|------------------|
| 部署 | 本地部署 | 云端服务 |
| API Key | 不需要 | 需要 |
| 网络 | 本地网络 | 需要互联网 |
| 成本 | 免费 | 按使用付费 |
| 隐私 | 数据不离开本地 | 数据发送到云端 |
| 性能 | 取决于本地硬件 | 云端高性能 |

本项目配置为使用 **Ollama 本地部署**。

## 验证清单

在运行 Agent Scheduler 之前，确保：

- [ ] Ollama 服务正在运行
- [ ] qwen3:4b 模型已下载
- [ ] PostgreSQL 数据库正在运行
- [ ] 方法已注册到数据库
- [ ] 配置文件正确

### 快速验证脚本

```bash
# 检查 Ollama
echo "Checking Ollama..."
curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama is running" || echo "✗ Ollama is not running"

# 检查模型
echo "Checking qwen3:4b model..."
ollama list | grep -q qwen3:4b && echo "✓ qwen3:4b model exists" || echo "✗ qwen3:4b model not found"

# 检查 PostgreSQL
echo "Checking PostgreSQL..."
psql -h localhost -U postgres -c "SELECT 1" > /dev/null 2>&1 && echo "✓ PostgreSQL is running" || echo "✗ PostgreSQL is not running"

echo "Verification complete!"
```

## 启动顺序

正确的启动顺序：

1. **启动 PostgreSQL**
   ```bash
   # 确保 PostgreSQL 正在运行
   ```

2. **启动 Ollama**
   ```bash
   ollama serve
   ```

3. **注册方法**（如果还没有）
   ```bash
   cd method-registration
   python src/main.py
   ```

4. **启动 Agent Scheduler**
   ```bash
   cd agent-scheduler
   python src/main.py
   ```

5. **访问 API**
   ```
   http://localhost:8000/docs
   ```

## 故障排除

### 日志位置

- **Ollama 日志**: 查看 Ollama 服务输出
- **Agent Scheduler 日志**: 控制台输出或 `logs/agent_scheduler.log`
- **PostgreSQL 日志**: 取决于 PostgreSQL 配置

### 调试模式

启用详细日志：

```bash
# 在 model_config.yaml 中
logging:
  level: "DEBUG"  # 改为 DEBUG

# 或者在命令行
python src/main.py --log-level DEBUG
```

### 测试 Ollama 连接

```python
# test_ollama.py
import requests

response = requests.post(
    'http://localhost:11434/api/generate',
    json={
        'model': 'qwen3:4b',
        'prompt': '你好',
        'stream': False
    }
)

print(response.json())
```

## 性能优化

### Ollama 性能

- **GPU 加速**: 确保 Ollama 使用 GPU（如果可用）
- **模型大小**: qwen3:4b 是较小的模型，适合快速响应
- **并发请求**: Ollama 可以处理多个并发请求

### Agent Scheduler 性能

- **连接池**: 数据库连接池大小在 `model_config.yaml` 中配置
- **超时设置**: 根据需要调整超时时间
- **缓存**: 考虑缓存常用方法定义

## 参考资源

- [Ollama 官方文档](https://github.com/ollama/ollama)
- [qwen-agent 文档](https://github.com/QwenLM/Qwen-Agent)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

## 支持

如果遇到问题：

1. 检查所有服务是否正在运行
2. 查看日志文件
3. 验证配置文件
4. 测试各个组件独立工作
5. 查看本文档的故障排除部分
