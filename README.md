# Qwen Agent Scheduler

基于qwen-agent框架的智能体调度系统，包含方法注册系统和智能体调度大脑两个核心组件。

## 概述

Qwen Agent Scheduler 是一个完整的智能体方法注册和调度系统，允许您：

1. **声明式注册方法**: 通过配置文件定义智能体可以调用的方法
2. **自动验证**: 验证方法元数据的完整性和正确性
3. **持久化存储**: 将方法信息存储到PostgreSQL数据库
4. **智能调度**: 使用qwen-agent框架理解自然语言任务并调用相应方法
5. **RESTful API**: 提供HTTP接口供客户端使用

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    Qwen Agent Scheduler                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │ Method Registration  │         │  Agent Scheduler     │     │
│  │      System          │         │       Brain          │     │
│  │                      │         │                      │     │
│  │  • Config Parser     │         │  • Method Loader     │     │
│  │  • Validator         │────────▶│  • Agent Client      │     │
│  │  • DB Writer         │  Store  │  • Executor          │     │
│  │                      │ Methods │  • REST API          │     │
│  └──────────────────────┘         └──────────────────────┘     │
│           │                                 │                    │
│           │                                 │                    │
│           ▼                                 ▼                    │
│  ┌─────────────────────────────────────────────────────┐       │
│  │           PostgreSQL Database                        │       │
│  │           (registered_methods table)                 │       │
│  └─────────────────────────────────────────────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Ollama Service  │
                    │   (qwen3:4b)     │
                    └──────────────────┘
```

## 项目结构

```
qwen-agent-scheduler/
├── method-registration/          # 方法注册系统
│   ├── config/                   # 配置文件
│   │   ├── model_config.yaml    # 模型和数据库配置
│   │   ├── methods.yaml         # 方法注册配置（YAML格式）
│   │   ├── model_config.json    # 模型配置（JSON格式）
│   │   └── methods.json         # 方法注册配置（JSON格式）
│   ├── src/                      # 源代码
│   │   ├── config_parser.py     # 配置文件解析器
│   │   ├── validator.py         # 元数据验证器
│   │   ├── db_client.py         # 数据库客户端
│   │   └── main.py              # 主入口
│   ├── tests/                    # 测试
│   ├── examples/                 # 示例代码
│   ├── requirements.txt          # 依赖
│   ├── pytest.ini                # pytest配置
│   └── README.md                 # 详细文档
│
├── agent-scheduler/              # 智能体调度大脑
│   ├── config/                   # 配置文件
│   │   └── model_config.yaml    # 模型和数据库配置
│   ├── src/                      # 源代码
│   │   ├── method_loader.py     # 方法加载器
│   │   ├── agent_client.py      # qwen-agent客户端
│   │   ├── executor.py          # 方法执行引擎
│   │   ├── api.py               # REST API
│   │   └── main.py              # 主入口
│   ├── tests/                    # 测试
│   ├── examples/                 # 示例代码
│   ├── workspace/                # 工作空间（存放工具实现）
│   ├── requirements.txt          # 依赖
│   ├── pytest.ini                # pytest配置
│   └── README.md                 # 详细文档
│
├── shared/                       # 共享模块
│   ├── models.py                 # 数据模型
│   ├── db_schema.py              # 数据库Schema
│   ├── config_loader.py          # 配置加载器
│   ├── requirements.txt          # 依赖
│   └── __init__.py
│
├── .kiro/                        # Kiro规范文档
│   └── specs/
│       └── qwen-agent-scheduler/
│           ├── requirements.md   # 需求文档
│           ├── design.md         # 设计文档
│           └── tasks.md          # 任务列表
│
├── requirements.txt              # 根依赖文件
├── pytest.ini                    # 根pytest配置
└── README.md                     # 本文件
```

## 前置要求

在开始之前，请确保您的系统满足以下要求：

1. **Python 3.9+**: 系统使用Python开发
2. **PostgreSQL 13+**: 用于存储方法注册信息
3. **Ollama**: 用于运行大语言模型（如qwen3:4b）
4. **pip**: Python包管理器

### 安装Ollama和模型

```bash
# 安装Ollama（参考 https://ollama.ai）
# Linux/Mac:
curl -fsSL https://ollama.ai/install.sh | sh

# 拉取qwen3:4b模型
ollama pull qwen3:4b

# 验证Ollama服务运行
ollama list
```

### 设置PostgreSQL数据库

```bash
# 创建数据库
createdb test_db

# 或使用psql
psql -U postgres
CREATE DATABASE test_db;
\q
```

## 快速开始

### 1. 安装依赖

```bash
# 克隆或下载项目后，安装所有依赖
pip install -r requirements.txt

# 或分别安装各模块依赖
pip install -r shared/requirements.txt
pip install -r method-registration/requirements.txt
pip install -r agent-scheduler/requirements.txt
```

### 2. 配置数据库连接

编辑配置文件，设置数据库连接参数：

**method-registration/config/model_config.yaml**:
```yaml
database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "yuanyuan"
  password: "666666"  # 修改为您的密码
  pool_size: 5
```

**agent-scheduler/config/model_config.yaml**:
```yaml
database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "yuanyuan"
  password: "666666"  # 修改为您的密码
  pool_size: 5
```

### 3. 注册方法

首先，使用Method Registration System注册方法：

```bash
cd method-registration
python src/main.py
```

这将读取 `config/methods.yaml` 中定义的方法并注册到数据库。

### 4. 启动Agent Scheduler Brain

然后，启动Agent Scheduler Brain服务：

```bash
cd agent-scheduler
python src/main.py
```

服务将在 `http://localhost:8000` 启动。

### 5. 测试API

使用curl或其他HTTP客户端测试API：

```bash
# 检查健康状态
curl http://localhost:8000/health

# 查看已注册的方法
curl http://localhost:8000/api/methods

# 提交任务
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "帮我计算 2 + 2"}'

# 查询任务状态（使用返回的task_id）
curl http://localhost:8000/api/tasks/{task_id}
```

### 6. 访问API文档

打开浏览器访问交互式API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 使用指南

### Method Registration System（方法注册系统）

详细使用说明请参考 [method-registration/README.md](method-registration/README.md)

**主要功能**:
- 解析YAML/JSON配置文件
- 验证方法元数据
- 将方法注册到PostgreSQL数据库
- 支持Upsert操作（插入或更新）

**基本用法**:
```bash
cd method-registration

# 使用默认配置
python src/main.py

# 指定配置文件
python src/main.py --model-config config/model_config.yaml --methods-config config/methods.yaml

# 使用JSON格式
python src/main.py --methods-config config/methods.json

# 启用调试日志
python src/main.py --log-level DEBUG
```

### Agent Scheduler Brain（智能体调度大脑）

详细使用说明请参考 [agent-scheduler/README.md](agent-scheduler/README.md)

**主要功能**:
- 从数据库加载已注册的方法
- 使用qwen-agent理解自然语言任务
- 动态执行方法
- 提供RESTful API接口

**基本用法**:
```bash
cd agent-scheduler

# 使用默认配置
python src/main.py

# 指定配置文件
python src/main.py --config config/model_config.yaml

# 自定义主机和端口
python src/main.py --host 0.0.0.0 --port 8080

# 启用调试日志
python src/main.py --log-level DEBUG --log-file logs/debug.log
```

## 配置文件说明

### 模型配置 (model_config.yaml)

```yaml
model:
  name: "qwen3:4b"              # Ollama模型名称
  api_base: "http://localhost:11434"  # Ollama API端点
  timeout: 30                    # 请求超时时间（秒）
  temperature: 0.7               # 生成温度
  max_tokens: 2000               # 最大生成token数

database:
  host: "localhost"              # 数据库主机
  port: 5432                     # 数据库端口
  database: "test_db"      # 数据库名称， 这里代码用的是test_db
  user: "yuanyuan"               # 数据库用户，这里代码用的是yuanyuan
  password: "666666"      # 数据库密码，这里代码用的是666666
  pool_size: 5                   # 连接池大小

logging:
  level: "INFO"                  # 日志级别
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"           # 日志文件路径
```

### 方法注册配置 (methods.yaml)

```yaml
methods:
  - name: "method_name"          # 方法名称（必须符合Python标识符规范）
    description: "方法描述"       # 方法描述
    module_path: "tools.module"  # 方法所在模块路径
    function_name: "function"    # 函数名称
    parameters:                  # 参数列表
      - name: "param1"           # 参数名称
        type: "string"           # 参数类型
        description: "参数描述"   # 参数描述
        required: true           # 是否必需
      - name: "param2"
        type: "int"
        description: "可选参数"
        required: false
        default: 10              # 默认值
    return_type: "dict"          # 返回值类型
```

## 测试

### 运行所有测试

```bash
# 从项目根目录运行
pytest

# 或指定详细输出
pytest -v

# 运行带覆盖率的测试
pytest --cov=. --cov-report=html
```

### 运行特定模块的测试

```bash
# 方法注册系统测试
pytest method-registration/tests/

# 智能体调度大脑测试
pytest agent-scheduler/tests/

# 共享模块测试
pytest shared/tests/
```

### 运行特定类型的测试

```bash
# 单元测试
pytest -m unit

# 属性测试（Property-Based Testing）
pytest -m property

# 集成测试
pytest -m integration
```

### 运行特定测试文件

```bash
# 测试配置解析器
pytest method-registration/tests/test_config_parser.py -v

# 测试方法执行器
pytest agent-scheduler/tests/test_executor.py -v
```

## 开发

### 测试框架

项目使用以下测试框架：
- **pytest**: 单元测试和集成测试框架
- **Hypothesis**: 属性测试（Property-Based Testing）框架

每个属性测试运行至少100次迭代以确保代码正确性。

### 代码质量

- 遵循PEP 8代码风格
- 使用类型注解（Type Hints）
- 编写文档字符串（Docstrings）
- 保持测试覆盖率 > 80%

### 添加新方法

1. 在 `agent-scheduler/workspace/tools/` 中实现方法
2. 在 `method-registration/config/methods.yaml` 中添加方法定义
3. 运行 Method Registration System 注册方法
4. 重启 Agent Scheduler Brain 加载新方法
5. 编写测试验证方法功能

### 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 故障排除

### 数据库连接失败

**问题**: 无法连接到PostgreSQL数据库

**解决方案**:
1. 确认PostgreSQL服务正在运行: `pg_isready`
2. 检查配置文件中的数据库凭据
3. 验证数据库存在: `psql -l`
4. 检查防火墙设置
5. 验证用户权限

### Ollama服务不可用

**问题**: 无法连接到Ollama服务

**解决方案**:
1. 确认Ollama服务正在运行: `ollama list`
2. 检查API端点配置: `http://localhost:11434`
3. 验证模型已下载: `ollama pull qwen3:4b`
4. 检查网络连接

### 方法注册失败

**问题**: 方法验证失败或无法注册

**解决方案**:
1. 检查方法名称是否符合Python标识符规范
2. 确保所有必需字段都存在
3. 验证参数类型是否有效
4. 检查是否存在重复的方法名称
5. 查看详细错误日志

### 方法执行失败

**问题**: Agent调用方法时失败

**解决方案**:
1. 确认方法实现存在于指定的模块路径
2. 检查参数类型是否匹配
3. 验证方法返回值类型
4. 查看执行日志了解详细错误
5. 测试方法是否可以独立运行

## 示例

### 示例1: 注册天气查询方法

1. 实现方法 (`agent-scheduler/workspace/tools/weather.py`):
```python
def get_weather(city: str, unit: str = "celsius") -> dict:
    """获取指定城市的天气信息"""
    # 实现天气查询逻辑
    return {
        "city": city,
        "temperature": 25,
        "unit": unit,
        "condition": "sunny"
    }
```

2. 在 `methods.yaml` 中注册:
```yaml
methods:
  - name: "get_weather"
    description: "获取指定城市的天气信息"
    module_path: "workspace.tools.weather"
    function_name: "get_weather"
    parameters:
      - name: "city"
        type: "string"
        description: "城市名称"
        required: true
      - name: "unit"
        type: "string"
        description: "温度单位"
        required: false
        default: "celsius"
    return_type: "dict"
```

3. 注册方法:
```bash
cd method-registration
python src/main.py
```

4. 使用方法:
```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"task_description": "查询北京的天气"}'
```

### 示例2: 运行完整演示

```bash
# 运行方法注册演示
cd method-registration
python examples/validator_demo.py

# 运行Agent调度演示
cd agent-scheduler
python examples/main_demo.py

# 运行完整集成演示
python examples/full_integration_demo.py
```

## 文档

- [需求文档](.kiro/specs/qwen-agent-scheduler/requirements.md)
- [设计文档](.kiro/specs/qwen-agent-scheduler/design.md)
- [任务列表](.kiro/specs/qwen-agent-scheduler/tasks.md)
- [Method Registration System详细文档](method-registration/README.md)
- [Agent Scheduler Brain详细文档](agent-scheduler/README.md)

## 许可证

MIT

## 联系方式

如有问题或建议，请提交Issue或Pull Request。
