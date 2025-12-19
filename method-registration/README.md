# Method Registration System

Method Registration System 是一个命令行工具，用于读取配置文件、验证方法元数据并将其持久化到PostgreSQL数据库。该系统是Qwen Agent Scheduler项目的一部分，负责注册智能体可以调用的方法。

## 功能特性

- **配置文件解析**: 支持YAML和JSON格式的配置文件
- **元数据验证**: 验证方法名称、参数、返回值类型等元数据的完整性和正确性
- **数据库持久化**: 将验证通过的方法信息存储到PostgreSQL数据库
- **Upsert操作**: 支持插入新方法或更新已存在的方法
- **详细日志**: 提供详细的错误处理和日志记录

## 前置要求

1. **Python 3.9+**
2. **PostgreSQL数据库**: 运行中的PostgreSQL实例
3. **依赖包**: 从requirements.txt安装

## 安装

```bash
cd method-registration
pip install -r requirements.txt
```

## 配置

### 1. 模型配置文件 (model_config.yaml)

创建配置文件 `config/model_config.yaml`:

```yaml
model:
  name: "qwen3:4b"
  api_base: "http://localhost:11434"
  timeout: 30
  temperature: 0.7
  max_tokens: 2000

database:
  host: "localhost"
  port: 5432
  database: "test_db"
  user: "yuanyuan"
  password: "666666"
  pool_size: 5

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
```

**配置说明**:
- `model`: Ollama模型配置（用于未来扩展）
- `database`: PostgreSQL数据库连接参数
  - `host`: 数据库主机地址
  - `port`: 数据库端口（默认5432）
  - `database`: 数据库名称
  - `user`: 数据库用户名
  - `password`: 数据库密码
  - `pool_size`: 连接池大小
- `logging`: 日志配置
  - `level`: 日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
  - `format`: 日志格式
  - `file`: 日志文件路径

### 2. 方法注册配置文件 (methods.yaml)

创建方法注册配置文件 `config/methods.yaml`:

```yaml
methods:
  - name: "get_weather"
    description: "获取指定城市的天气信息"
    module_path: "tools.weather"
    function_name: "get_weather"
    parameters:
      - name: "city"
        type: "string"
        description: "城市名称"
        required: true
      - name: "unit"
        type: "string"
        description: "温度单位，celsius或fahrenheit"
        required: false
        default: "celsius"
    return_type: "dict"
  
  - name: "calculate"
    description: "执行数学计算"
    module_path: "tools.calculator"
    function_name: "calculate"
    parameters:
      - name: "expression"
        type: "string"
        description: "数学表达式"
        required: true
    return_type: "float"
```

**配置说明**:
- `name`: 方法名称（必须符合Python标识符规范，2-100字符）
- `description`: 方法描述（不能为空，最多1000字符）
- `module_path`: 方法所在模块的Python路径
- `function_name`: 函数名称
- `parameters`: 参数列表
  - `name`: 参数名称
  - `type`: 参数类型（string, int, float, bool, dict, list等）
  - `description`: 参数描述
  - `required`: 是否必需（true/false）
  - `default`: 默认值（可选）
- `return_type`: 返回值类型

### 3. JSON格式配置（可选）

系统也支持JSON格式的配置文件。参考 `config/model_config.json` 和 `config/methods.json`。

## 使用方法

### 基本用法

```bash
python src/main.py
```

这将使用默认配置文件路径：
- 模型配置: `config/model_config.yaml`
- 方法配置: `config/methods.yaml`

### 指定配置文件

```bash
python src/main.py --model-config config/model_config.yaml --methods-config config/methods.yaml
```

### 使用JSON格式配置

```bash
python src/main.py --model-config config/model_config.json --methods-config config/methods.json
```

### 命令行选项

- `--model-config`: 模型配置文件路径（默认: `config/model_config.yaml`）
- `--methods-config`: 方法注册配置文件路径（默认: `config/methods.yaml`）
- `--log-level`: 日志级别 - DEBUG, INFO, WARNING, ERROR, CRITICAL（默认: `INFO`）
- `--log-file`: 日志文件路径（默认: 仅输出到控制台）

### 示例

**使用调试日志级别:**
```bash
python src/main.py --log-level DEBUG
```

**指定日志文件:**
```bash
python src/main.py --log-file logs/registration.log
```

**完整示例:**
```bash
python src/main.py \
  --model-config config/model_config.yaml \
  --methods-config config/methods.yaml \
  --log-level INFO \
  --log-file logs/registration.log
```

## 架构

Method Registration System 由三个主要组件组成：

1. **ConfigParser (配置解析器)**: 读取和解析YAML/JSON配置文件
2. **MetadataValidator (元数据验证器)**: 验证方法元数据的完整性和正确性
3. **DatabaseWriter (数据库写入器)**: 将验证通过的方法写入PostgreSQL数据库

### 组件流程

```
配置文件 → ConfigParser → MetadataValidator → DatabaseWriter → PostgreSQL数据库
```

## 验证规则

系统会对方法元数据进行以下验证：

### 方法名称验证
- 必须符合Python标识符规范
- 长度在2-100字符之间
- 不能包含空格或特殊字符
- 不能以数字开头

### 参数验证
- 每个参数必须包含 `name`、`type`、`description` 字段
- 参数名称必须符合Python标识符规范
- 参数类型必须是有效的Python类型字符串
- 描述不能为空

### 返回值类型验证
- 必须是有效的Python类型字符串
- 支持的类型: string, int, float, bool, dict, list, None等

### 重复检测
- 检测配置文件中是否存在重复的方法名称
- 如果存在重复，报告错误并拒绝注册

## 数据库Schema

系统会自动创建以下数据库表结构：

```sql
CREATE TABLE IF NOT EXISTS registered_methods (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    parameters_json JSONB NOT NULL,
    return_type VARCHAR(50) NOT NULL,
    module_path VARCHAR(255) NOT NULL,
    function_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**字段说明**:
- `id`: 主键，自动递增
- `name`: 方法名称，唯一索引
- `description`: 方法描述
- `parameters_json`: JSON格式的参数列表
- `return_type`: 返回值类型
- `module_path`: 模块路径
- `function_name`: 函数名称
- `created_at`: 创建时间
- `updated_at`: 更新时间（自动更新）

## 错误处理

系统提供详细的错误处理和日志记录：

### 配置错误
- **YAML/JSON语法错误**: 记录文件路径和具体的解析错误
- **缺少必需字段**: 指出缺少的字段名称
- **无效数据类型**: 说明期望的类型和实际的类型

### 验证错误
- **无效方法名**: 说明不符合规范的原因
- **缺少参数字段**: 列出所有缺少的字段
- **重复方法名**: 指出重复的方法名称

### 数据库错误
- **连接失败**: 记录数据库连接参数和错误信息
- **Schema创建失败**: 记录SQL语句和数据库错误代码
- **插入/更新失败**: 记录方法名称和数据库错误

### 错误日志要求

根据设计规范，满足以下日志记录要求：

- **Requirement 10.1**: 所有错误包含时间戳、错误类型、消息和堆栈跟踪
- **Requirement 10.2**: 配置加载失败记录文件路径和具体解析错误
- **Requirement 10.3**: 数据库操作失败记录SQL语句和数据库错误代码

## 示例

### 运行演示

```bash
python examples/validator_demo.py
```

### 注册单个方法

创建一个简单的配置文件 `my_method.yaml`:

```yaml
methods:
  - name: "hello_world"
    description: "返回Hello World消息"
    module_path: "tools.greetings"
    function_name: "hello_world"
    parameters: []
    return_type: "string"
```

然后运行：

```bash
python src/main.py --methods-config my_method.yaml
```

### 批量注册方法

在 `methods.yaml` 中定义多个方法，然后运行：

```bash
python src/main.py
```

系统会按顺序处理所有方法，并报告每个方法的注册结果。

### 注册的时候，除了在config中添加方法信息，还需要在tools下添加对应方法的具体实现的python文件。

## 测试

运行测试套件：

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_validator.py -v

# 运行带覆盖率的测试
pytest tests/ --cov=src --cov-report=html
```

### 测试类型

- **单元测试**: 测试各个组件的功能
- **属性测试**: 使用Hypothesis进行基于属性的测试
- **集成测试**: 测试完整的注册流程

## 故障排除

### 数据库连接问题

如果遇到数据库连接错误：
1. 验证PostgreSQL正在运行
2. 检查配置文件中的数据库凭据
3. 确保数据库存在
4. 检查网络连接到数据库主机
5. 验证数据库用户权限

### 配置文件解析错误

如果遇到配置文件解析错误：
1. 验证YAML/JSON语法是否正确
2. 检查文件编码（应为UTF-8）
3. 确保所有必需字段都存在
4. 验证数据类型是否正确

### 验证失败

如果方法验证失败：
1. 检查方法名称是否符合Python标识符规范
2. 确保所有参数都有name、type、description字段
3. 验证返回值类型是否有效
4. 检查是否存在重复的方法名称

## 开发

### 项目结构

```
method-registration/
├── src/
│   ├── config_parser.py   # 配置文件解析器
│   ├── validator.py       # 元数据验证器
│   ├── db_client.py       # 数据库客户端
│   └── main.py            # 主入口
├── tests/
│   ├── test_config_parser.py
│   ├── test_validator.py
│   ├── test_db_client.py
│   └── test_integration_validator.py
├── config/
│   ├── model_config.yaml
│   ├── methods.yaml
│   ├── model_config.json
│   └── methods.json
├── examples/
│   └── validator_demo.py
└── requirements.txt
```

### 添加新功能

1. 在相应模块中实现功能
2. 在对应的测试文件中添加测试
3. 更新此README文档
4. 更新示例代码（如果适用）

## 与Agent Scheduler Brain集成

Method Registration System 注册的方法会被 Agent Scheduler Brain 加载和使用：

1. **注册方法**: 使用 Method Registration System 注册方法到数据库
2. **启动调度器**: Agent Scheduler Brain 从数据库加载已注册的方法
3. **处理任务**: 用户通过API提交任务，智能体调用相应的方法

完整的工作流程：

```
配置文件 → Method Registration System → PostgreSQL数据库
                                              ↓
                                    Agent Scheduler Brain → 智能体任务处理
```

## 许可证

[Your License Here]

## 贡献

[Your Contributing Guidelines Here]
