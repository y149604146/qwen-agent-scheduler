# Requirements Document

## Introduction

本文档定义了基于qwen-agent框架的智能体调度系统的需求。该系统包含两个核心项目：
1. **方法注册系统（Method Registration System）** - 允许用户通过配置文件声明式地注册智能体方法，并将注册信息持久化到PostgreSQL数据库
2. **智能体调度大脑（Agent Scheduler Brain）** - 从数据库读取已注册的方法，使用qwen-agent框架实现智能体的方法调用和任务调度

该系统旨在实现智能体方法的解耦注册和灵活调度，支持使用Ollama私有化部署的大模型（如qwen3:4b）。

## Glossary

- **Method Registration System (方法注册系统)**: 负责读取配置文件、验证方法信息并将其存储到PostgreSQL数据库的系统组件
- **Agent Scheduler Brain (智能体调度大脑)**: 负责从数据库读取方法信息、使用qwen-agent框架调度和执行智能体任务的系统组件
- **qwen-agent**: 阿里云开源的智能体框架，用于构建和管理AI智能体
- **Ollama**: 用于本地部署大语言模型的工具
- **Method Metadata (方法元数据)**: 描述智能体方法的信息，包括方法名称、描述、参数、返回值等
- **PostgreSQL Database (数据库)**: 用于持久化存储方法注册信息的关系型数据库
- **Model Configuration (模型配置)**: 定义大模型连接参数的配置信息，包括模型名称、API端点等
- **Registration Config (注册配置)**: 用户编写的配置文件，声明需要注册的智能体方法

## Requirements

### Requirement 1: 模型配置管理

**User Story:** 作为系统管理员，我希望通过配置文件管理大模型连接参数，以便灵活切换不同的模型和部署环境

#### Acceptance Criteria

1. WHEN 系统启动时 THEN Method Registration System SHALL 从配置文件读取Ollama模型连接参数
2. WHEN 系统启动时 THEN Agent Scheduler Brain SHALL 从配置文件读取Ollama模型连接参数
3. WHEN 配置文件包含模型名称、API端点、超时时间等参数时 THEN 系统 SHALL 使用这些参数初始化qwen-agent客户端
4. WHEN 配置文件格式错误或缺少必需参数时 THEN 系统 SHALL 抛出清晰的错误信息并拒绝启动
5. WHERE 用户需要切换模型时 THEN 系统 SHALL 允许通过修改配置文件实现模型切换而无需修改代码

### Requirement 2: 方法注册配置

**User Story:** 作为开发者，我希望通过声明式配置文件注册智能体方法，以便实现方法注册与业务代码的解耦

#### Acceptance Criteria

1. WHEN 用户创建注册配置文件时 THEN Method Registration System SHALL 支持JSON或YAML格式的配置文件
2. WHEN 配置文件包含方法元数据时 THEN Method Registration System SHALL 解析方法名称、描述、参数列表、返回值类型等信息
3. WHEN 配置文件包含多个方法定义时 THEN Method Registration System SHALL 按顺序处理所有方法注册
4. WHEN 配置文件中的方法定义缺少必需字段时 THEN Method Registration System SHALL 报告具体的验证错误
5. WHEN 配置文件中存在重复的方法名称时 THEN Method Registration System SHALL 检测冲突并报告错误

### Requirement 3: 方法元数据验证

**User Story:** 作为系统维护者，我希望系统验证方法元数据的完整性和正确性，以便确保注册的方法可以被正确调用

#### Acceptance Criteria

1. WHEN Method Registration System 读取方法元数据时 THEN 系统 SHALL 验证方法名称符合命名规范
2. WHEN 方法元数据包含参数定义时 THEN 系统 SHALL 验证每个参数具有名称、类型和描述
3. WHEN 方法元数据包含返回值定义时 THEN 系统 SHALL 验证返回值类型的有效性
4. WHEN 验证失败时 THEN 系统 SHALL 生成包含字段名称和错误原因的详细错误报告
5. WHEN 所有验证通过时 THEN 系统 SHALL 标记该方法元数据为有效状态

### Requirement 4: PostgreSQL数据库持久化

**User Story:** 作为系统架构师，我希望将方法注册信息存储到PostgreSQL数据库，以便Agent Scheduler Brain可以查询和使用这些方法

#### Acceptance Criteria

1. WHEN Method Registration System 启动时 THEN 系统 SHALL 连接到配置文件中指定的PostgreSQL数据库
2. WHEN 数据库连接建立时 THEN 系统 SHALL 创建或验证方法注册表的schema
3. WHEN 方法元数据验证通过时 THEN 系统 SHALL 将方法信息插入到数据库表中
4. WHEN 数据库中已存在相同方法名称时 THEN 系统 SHALL 更新现有记录而不是创建重复记录
5. WHEN 数据库操作失败时 THEN 系统 SHALL 回滚事务并记录详细的错误日志

### Requirement 5: 方法注册表Schema设计

**User Story:** 作为数据库管理员，我希望方法注册表具有清晰的结构，以便高效存储和查询方法元数据

#### Acceptance Criteria

1. WHEN 创建方法注册表时 THEN 系统 SHALL 包含方法ID、方法名称、描述、创建时间、更新时间等基础字段
2. WHEN 存储方法参数时 THEN 系统 SHALL 使用JSON或JSONB类型存储参数列表
3. WHEN 存储方法返回值定义时 THEN 系统 SHALL 使用适当的数据类型存储返回值信息
4. WHEN 查询方法时 THEN 系统 SHALL 在方法名称字段上创建索引以提高查询性能
5. WHEN 记录被更新时 THEN 系统 SHALL 自动更新updated_at时间戳字段

### Requirement 6: Agent Scheduler Brain方法加载

**User Story:** 作为智能体开发者，我希望Agent Scheduler Brain能够从数据库加载已注册的方法，以便智能体可以调用这些方法

#### Acceptance Criteria

1. WHEN Agent Scheduler Brain 启动时 THEN 系统 SHALL 连接到PostgreSQL数据库并查询所有已注册的方法
2. WHEN 从数据库读取方法元数据时 THEN 系统 SHALL 反序列化JSON格式的参数和返回值定义
3. WHEN 方法加载完成时 THEN 系统 SHALL 将方法元数据转换为qwen-agent框架可识别的工具定义格式
4. WHEN 数据库中没有注册方法时 THEN 系统 SHALL 记录警告日志并继续运行
5. WHEN 方法元数据格式不兼容时 THEN 系统 SHALL 跳过该方法并记录错误日志

### Requirement 7: qwen-agent框架集成

**User Story:** 作为智能体用户，我希望Agent Scheduler Brain使用qwen-agent框架调度任务，以便智能体能够理解用户意图并调用相应的方法

#### Acceptance Criteria

1. WHEN Agent Scheduler Brain 初始化时 THEN 系统 SHALL 使用模型配置创建qwen-agent客户端实例
2. WHEN 用户提交任务请求时 THEN 系统 SHALL 将请求传递给qwen-agent进行意图理解
3. WHEN qwen-agent决定调用某个方法时 THEN 系统 SHALL 根据方法名称查找对应的方法元数据
4. WHEN 方法调用完成时 THEN 系统 SHALL 将执行结果返回给qwen-agent继续处理
5. WHEN qwen-agent生成最终响应时 THEN 系统 SHALL 将响应返回给用户

### Requirement 8: 方法执行引擎

**User Story:** 作为系统开发者，我希望Agent Scheduler Brain能够动态执行已注册的方法，以便实现灵活的方法调用

#### Acceptance Criteria

1. WHEN qwen-agent请求调用方法时 THEN 系统 SHALL 根据方法名称和参数构造方法调用
2. WHEN 方法参数类型不匹配时 THEN 系统 SHALL 尝试进行类型转换或返回参数错误
3. WHEN 方法执行成功时 THEN 系统 SHALL 返回方法的返回值
4. WHEN 方法执行抛出异常时 THEN 系统 SHALL 捕获异常并返回格式化的错误信息
5. WHEN 方法执行超时时 THEN 系统 SHALL 终止执行并返回超时错误

### Requirement 9: 测试环境配置

**User Story:** 作为测试工程师，我希望使用qwen3:4b模型和Ollama部署进行测试，以便验证系统功能的正确性

#### Acceptance Criteria

1. WHEN 运行测试用例时 THEN 系统 SHALL 使用配置文件中指定的qwen3:4b模型
2. WHEN 测试环境启动时 THEN 系统 SHALL 验证Ollama服务的可用性
3. WHEN Ollama服务不可用时 THEN 测试 SHALL 跳过或失败并提供清晰的错误信息
4. WHEN 测试数据库连接时 THEN 系统 SHALL 使用测试专用的PostgreSQL数据库实例
5. WHEN 测试完成时 THEN 系统 SHALL 清理测试数据以避免污染数据库

### Requirement 10: 错误处理和日志记录

**User Story:** 作为运维人员，我希望系统提供详细的错误处理和日志记录，以便快速定位和解决问题

#### Acceptance Criteria

1. WHEN 系统遇到错误时 THEN 系统 SHALL 记录包含时间戳、错误类型、错误消息和堆栈跟踪的日志
2. WHEN 配置文件加载失败时 THEN 系统 SHALL 记录配置文件路径和具体的解析错误
3. WHEN 数据库操作失败时 THEN 系统 SHALL 记录SQL语句和数据库错误代码
4. WHEN 方法执行失败时 THEN 系统 SHALL 记录方法名称、输入参数和异常信息
5. WHEN 日志级别设置为DEBUG时 THEN 系统 SHALL 记录详细的执行流程和中间状态

### Requirement 11: 配置文件热加载

**User Story:** 作为系统管理员，我希望能够在不重启系统的情况下重新加载方法注册配置，以便快速更新方法定义

#### Acceptance Criteria

1. WHERE 系统支持热加载功能时 WHEN 用户触发配置重载命令时 THEN Method Registration System SHALL 重新读取注册配置文件
2. WHERE 系统支持热加载功能时 WHEN 配置文件被修改时 THEN 系统 SHALL 检测文件变化并自动重新加载
3. WHERE 系统支持热加载功能时 WHEN 重新加载配置时 THEN 系统 SHALL 验证新配置的有效性
4. WHERE 系统支持热加载功能时 WHEN 新配置验证失败时 THEN 系统 SHALL 保持当前配置不变并记录错误
5. WHERE 系统支持热加载功能时 WHEN 新配置加载成功时 THEN 系统 SHALL 更新数据库中的方法注册信息

### Requirement 12: API接口设计

**User Story:** 作为前端开发者，我希望Agent Scheduler Brain提供RESTful API接口，以便客户端可以提交任务和获取结果

#### Acceptance Criteria

1. WHEN Agent Scheduler Brain 启动时 THEN 系统 SHALL 启动HTTP服务器监听指定端口
2. WHEN 客户端发送POST请求到任务提交端点时 THEN 系统 SHALL 接收任务描述并返回任务ID
3. WHEN 客户端查询任务状态时 THEN 系统 SHALL 返回任务的执行状态和结果
4. WHEN 请求参数格式错误时 THEN 系统 SHALL 返回HTTP 400状态码和错误详情
5. WHEN 服务器内部错误时 THEN 系统 SHALL 返回HTTP 500状态码并记录错误日志
