# Demo Scripts - 修复说明

## 问题总结

运行 demo 脚本时可能遇到的问题和解决方案。

## 1. method-registration/examples/validator_demo.py

### 问题
```
ModuleNotFoundError: No module named 'shared'
```

### 解决方案
✅ **已修复** - 更新了导入路径

### 运行方法
```bash
cd method-registration
python examples/validator_demo.py
```

### 预期输出
```
======================================================================
MetadataValidator Demo
======================================================================

Example 1: Valid method configuration
----------------------------------------------------------------------
Method name: get_weather
Valid: True
No errors - method is valid!

Example 2: Invalid method name (contains hyphen)
----------------------------------------------------------------------
Method name: get-weather
Valid: False
Errors:
  - Method name 'get-weather' is not a valid Python identifier...

...
```

## 2. agent-scheduler/examples/*.py

### 问题
在 Windows 系统上可能遇到 Unicode 编码错误：
```
UnicodeEncodeError: 'gbk' codec can't encode character '\u2713'
```

### 原因
Windows 控制台默认使用 GBK 编码，无法显示某些 Unicode 字符（如 ✓ ✗）

### 解决方案

#### 方案 1: 设置控制台编码（推荐）
```powershell
# 在 PowerShell 中运行
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
python examples/executor_demo.py
```

#### 方案 2: 使用环境变量
```powershell
$env:PYTHONIOENCODING="utf-8"
python examples/executor_demo.py
```

#### 方案 3: 重定向到文件
```bash
python examples/executor_demo.py > output.txt 2>&1
type output.txt
```

#### 方案 4: 修改 demo 文件
如果需要永久修复，可以在每个 demo 文件开头添加：

```python
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
```

## 3. 所有 Demo 脚本的通用运行方法

### method-registration demos

```bash
cd method-registration

# Validator demo
python examples/validator_demo.py
```

### agent-scheduler demos

```bash
cd agent-scheduler

# Executor demo
python examples/executor_demo.py

# API demo (需要数据库)
python examples/api_demo.py

# Main demo (需要数据库和 Ollama)
python examples/main_demo.py

# Full integration demo (需要所有服务)
python examples/full_integration_demo.py
```

## 4. Demo 脚本依赖检查

### 基础依赖
所有 demo 都需要：
```bash
pip install -r requirements.txt
pip install -r ../shared/requirements.txt
```

### 服务依赖

| Demo | PostgreSQL | Ollama | qwen3:4b |
|------|-----------|--------|----------|
| validator_demo.py | ❌ | ❌ | ❌ |
| executor_demo.py | ❌ | ❌ | ❌ |
| api_demo.py | ✅ | ❌ | ❌ |
| main_demo.py | ✅ | ✅ | ✅ |
| full_integration_demo.py | ✅ | ✅ | ✅ |

### 检查服务状态

```bash
# 检查 PostgreSQL
psql -h localhost -U postgres -c "SELECT version();"

# 检查 Ollama
curl http://localhost:11434/api/tags

# 检查 qwen3:4b 模型
ollama list | grep qwen3:4b
```

## 5. 快速测试所有 Demo

### 测试脚本（PowerShell）

```powershell
# test_demos.ps1

Write-Host "Testing method-registration demos..." -ForegroundColor Cyan
cd method-registration
python examples/validator_demo.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ validator_demo.py passed" -ForegroundColor Green
} else {
    Write-Host "✗ validator_demo.py failed" -ForegroundColor Red
}

Write-Host "`nTesting agent-scheduler demos..." -ForegroundColor Cyan
cd ../agent-scheduler

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING="utf-8"

python examples/executor_demo.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ executor_demo.py passed" -ForegroundColor Green
} else {
    Write-Host "✗ executor_demo.py failed" -ForegroundColor Red
}

Write-Host "`nDemo testing complete!" -ForegroundColor Cyan
```

### 测试脚本（Bash）

```bash
#!/bin/bash
# test_demos.sh

echo "Testing method-registration demos..."
cd method-registration
python examples/validator_demo.py
if [ $? -eq 0 ]; then
    echo "✓ validator_demo.py passed"
else
    echo "✗ validator_demo.py failed"
fi

echo -e "\nTesting agent-scheduler demos..."
cd ../agent-scheduler

export PYTHONIOENCODING=utf-8

python examples/executor_demo.py
if [ $? -eq 0 ]; then
    echo "✓ executor_demo.py passed"
else
    echo "✗ executor_demo.py failed"
fi

echo -e "\nDemo testing complete!"
```

## 6. 常见问题

### Q: 为什么 validator_demo.py 现在可以运行了？
A: 修复了导入路径，正确添加了 workspace root 到 Python path。

### Q: 为什么 Windows 上会有编码问题？
A: Windows 控制台默认使用 GBK 编码，而 demo 脚本使用了 UTF-8 字符（如 ✓ ✗）。

### Q: 如何永久解决 Windows 编码问题？
A: 在 PowerShell 配置文件中添加：
```powershell
# $PROFILE
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING="utf-8"
```

### Q: Demo 需要真实的数据库吗？
A: 
- `validator_demo.py` 和 `executor_demo.py` 不需要
- 其他 demo 需要 PostgreSQL 和/或 Ollama

### Q: 如何跳过需要服务的 demo？
A: 只运行不需要服务的 demo：
```bash
# 这些不需要任何服务
python examples/validator_demo.py
python examples/executor_demo.py
```

## 7. 修复状态

| 文件 | 状态 | 说明 |
|------|------|------|
| method-registration/examples/validator_demo.py | ✅ 已修复 | 导入路径已更正 |
| agent-scheduler/examples/executor_demo.py | ⚠️ 编码问题 | 需要设置 UTF-8 编码 |
| agent-scheduler/examples/api_demo.py | ⚠️ 编码问题 | 需要设置 UTF-8 编码 |
| agent-scheduler/examples/main_demo.py | ⚠️ 编码问题 | 需要设置 UTF-8 编码 |
| agent-scheduler/examples/full_integration_demo.py | ⚠️ 编码问题 | 需要设置 UTF-8 编码 |

## 8. 推荐的运行顺序

1. **validator_demo.py** - 学习如何验证方法配置
2. **executor_demo.py** - 学习如何执行方法
3. **api_demo.py** - 学习 API 接口（需要数据库）
4. **main_demo.py** - 完整的方法注册流程（需要所有服务）
5. **full_integration_demo.py** - 端到端集成测试（需要所有服务）

## 总结

✅ **validator_demo.py 已修复并可以正常运行**

⚠️ **其他 demo 在 Windows 上需要设置 UTF-8 编码**

建议在运行 agent-scheduler demos 之前执行：
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING="utf-8"
```
