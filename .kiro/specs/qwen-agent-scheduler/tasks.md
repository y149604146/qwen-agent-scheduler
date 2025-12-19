# Implementation Plan

- [x] 1. 设置项目结构和共享模块







  - 创建method-registration、agent-scheduler和shared三个目录
  - 设置Python包结构（__init__.py文件）
  - 创建requirements.txt文件并安装依赖
  - 配置pytest和Hypothesis测试框架
  - _Requirements: 所有需求的基础_

- [x] 2. 实现共享数据模型和数据库Schema





  - 在shared/models.py中实现ModelConfig、MethodParameter、MethodConfig、MethodMetadata、DatabaseConfig、ExecutionResult等数据类
  - 在shared/db_schema.py中定义PostgreSQL表结构和索引
  - 实现数据库连接和Schema初始化逻辑
  - _Requirements: 1.1, 4.1, 4.2, 5.1, 5.2, 5.3, 5.4_

- [ ]* 2.1 编写数据模型的属性测试
  - **Property 13: Database persistence round-trip**
  - **Validates: Requirements 4.3**

- [ ]* 2.2 编写updated_at自动更新的属性测试
  - **Property 15: Updated timestamp automation**
  - **Validates: Requirements 5.5**

- [x] 3. 实现配置加载器










  - 在shared/config_loader.py中实现YAML配置文件加载
  - 支持加载model_config.yaml和methods.yaml
  - 实现配置验证逻辑
  - _Requirements: 1.1, 1.2, 1.4_

- [ ]* 3.1 编写配置加载的属性测试
  - **Property 1: Configuration loading consistency**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 3.2 编写无效配置拒绝的属性测试
  - **Property 3: Invalid configuration rejection**
  - **Validates: Requirements 1.4**

- [ ]* 3.3 编写配置格式等价性的属性测试
  - **Property 4: Configuration format equivalence**
  - **Validates: Requirements 2.1**

- [x] 4. 实现Method Registration System - 配置解析器





  - 在method-registration/src/config_parser.py中实现ConfigParser类
  - 实现load_model_config()方法
  - 实现load_methods_config()方法
  - 支持JSON和YAML格式
  - _Requirements: 2.1, 2.2, 2.3_

- [ ]* 4.1 编写方法元数据完整性的属性测试
  - **Property 5: Method metadata completeness**
  - **Validates: Requirements 2.2**

- [ ]* 4.2 编写批量处理完整性的属性测试
  - **Property 6: Batch processing completeness**
  - **Validates: Requirements 2.3**


- [x] 5. 实现Method Registration System - 元数据验证器




  - 在method-registration/src/validator.py中实现MetadataValidator类
  - 实现validate_method()方法，验证方法名称、参数、返回值类型
  - 实现validate_methods()批量验证方法
  - 实现重复方法名检测
  - _Requirements: 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ]* 5.1 编写缺失字段检测的属性测试
  - **Property 7: Missing field detection**
  - **Validates: Requirements 2.4**

- [ ]* 5.2 编写重复方法名检测的属性测试
  - **Property 8: Duplicate method name detection**
  - **Validates: Requirements 2.5**

- [ ]* 5.3 编写方法名验证的属性测试
  - **Property 9: Method name validation**
  - **Validates: Requirements 3.1**

- [ ]* 5.4 编写参数完整性验证的属性测试
  - **Property 10: Parameter completeness validation**
  - **Validates: Requirements 3.2**

- [ ]* 5.5 编写返回值类型验证的属性测试
  - **Property 11: Return type validation**
  - **Validates: Requirements 3.3**

- [ ]* 5.6 编写验证错误详情的属性测试
  - **Property 12: Validation error detail**
  - **Validates: Requirements 3.4**

- [x] 6. 实现Method Registration System - 数据库写入器







  - 在method-registration/src/db_client.py中实现DatabaseWriter类
  - 实现ensure_schema()方法创建表结构
  - 实现upsert_method()和upsert_methods()方法
  - 实现事务管理和错误处理
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6.1 编写upsert幂等性的属性测试






  - **Property 14: Upsert idempotence**
  - **Validates: Requirements 4.4**


- [x] 7. 实现Method Registration System - 主入口


  - 在method-registration/src/main.py中实现主程序逻辑
  - 集成ConfigParser、MetadataValidator和DatabaseWriter
  - 实现命令行参数解析
  - 添加日志记录
  - _Requirements: 10.1, 10.2_

- [x] 7.1 编写配置错误日志详情的属性测试









  - **Property 26: Configuration error logging detail**
  - **Validates: Requirements 10.2**


- [x] 8. Checkpoint - 确保Method Registration System所有测试通过












  - 确保所有测试通过，如有问题请询问用户

- [x] 9. 实现Agent Scheduler Brain - 方法加载器





  - 在agent-scheduler/src/method_loader.py中实现MethodLoader类
  - 实现load_all_methods()从数据库加载方法
  - 实现load_method_by_name()查询特定方法
  - 实现convert_to_qwen_tools()转换为qwen-agent工具格式
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 9.1 编写方法加载完整性的属性测试
  - **Property 16: Method loading completeness**
  - **Validates: Requirements 6.1**

- [ ]* 9.2 编写JSON反序列化正确性的属性测试
  - **Property 17: JSON deserialization correctness**
  - **Validates: Requirements 6.2**

- [ ]* 9.3 编写qwen-agent工具格式转换的属性测试
  - **Property 18: qwen-agent tool format conversion**
  - **Validates: Requirements 6.3**

- [x] 10. 实现Agent Scheduler Brain - qwen-agent客户端





  - 在agent-scheduler/src/agent_client.py中实现AgentClient类
  - 使用qwen-agent框架初始化客户端
  - 实现process_task()处理用户任务
  - 实现register_tool_executor()注册方法执行器
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 10.1 编写Agent客户端初始化的属性测试
  - **Property 19: Agent client initialization**
  - **Validates: Requirements 7.1**

- [ ]* 10.2 编写配置参数传播的属性测试
  - **Property 2: Configuration parameter propagation**
  - **Validates: Requirements 1.3**

- [ ]* 10.3 编写方法名查找的属性测试
  - **Property 20: Method lookup by name**
  - **Validates: Requirements 7.3**

- [x] 11. 实现Agent Scheduler Brain - 方法执行引擎





  - 在agent-scheduler/src/executor.py中实现MethodExecutor类
  - 实现execute()动态执行方法
  - 实现validate_params()参数验证
  - 实现类型转换和异常处理
  - 实现超时控制
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ]* 11.1 编写有效参数方法执行的属性测试
  - **Property 21: Method execution with valid parameters**
  - **Validates: Requirements 8.1, 8.3**

- [ ]* 11.2 编写类型强制转换或错误的属性测试
  - **Property 22: Type coercion or error**
  - **Validates: Requirements 8.2**

- [ ]* 11.3 编写异常处理的属性测试
  - **Property 23: Exception handling**
  - **Validates: Requirements 8.4**

- [x] 12. 实现Agent Scheduler Brain - REST API




  - 在agent-scheduler/src/api.py中使用FastAPI实现REST接口
  - 实现POST /api/tasks端点提交任务
  - 实现GET /api/tasks/{task_id}端点查询任务状态
  - 实现GET /api/methods端点查询已注册方法
  - 实现错误处理和HTTP状态码
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ]* 12.1 编写任务提交响应的属性测试
  - **Property 33: Task submission response**
  - **Validates: Requirements 12.2**

- [ ]* 12.2 编写任务状态查询的属性测试
  - **Property 34: Task status query**
  - **Validates: Requirements 12.3**

- [ ]* 12.3 编写无效请求错误响应的属性测试
  - **Property 35: Invalid request error response**
  - **Validates: Requirements 12.4**

- [ ]* 12.4 编写服务器错误响应的属性测试
  - **Property 36: Server error response**
  - **Validates: Requirements 12.5**

- [x] 13. 实现Agent Scheduler Brain - 主入口





  - 在agent-scheduler/src/main.py中实现主程序逻辑
  - 集成MethodLoader、AgentClient、MethodExecutor和API
  - 实现服务器启动逻辑
  - 添加日志记录
  - _Requirements: 10.1, 10.3, 10.4_

- [ ]* 13.1 编写数据库错误日志详情的属性测试
  - **Property 27: Database error logging detail**
  - **Validates: Requirements 10.3**

- [ ]* 13.2 编写方法执行错误日志详情的属性测试
  - **Property 28: Method execution error logging detail**
  - **Validates: Requirements 10.4**

- [ ]* 13.3 编写错误日志完整性的属性测试
  - **Property 25: Error logging completeness**
  - **Validates: Requirements 10.1**

- [ ]* 13.4 编写Debug日志详细程度的属性测试
  - **Property 29: Debug logging verbosity**
  - **Validates: Requirements 10.5**

- [x] 14. 创建配置文件示例和文档





  - 创建method-registration/config/model_config.yaml示例
  - 创建method-registration/config/methods.yaml示例
  - 创建agent-scheduler/config/model_config.yaml示例
  - 编写README.md说明如何使用两个项目
  - _Requirements: 1.1, 1.2, 2.1_

- [x] 15. 实现测试环境配置





  - 配置测试使用qwen3:4b模型
  - 实现Ollama服务可用性检查
  - 配置测试专用PostgreSQL数据库
  - 实现测试数据清理逻辑
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ]* 15.1 编写测试数据清理的属性测试
  - **Property 24: Test data cleanup**
  - **Validates: Requirements 9.5**

- [x] 16. Checkpoint - 确保所有核心功能测试通过





  - 确保所有测试通过，如有问题请询问用户

- [ ]* 17. 实现配置热加载功能（可选）
  - 在method-registration中实现配置文件监听
  - 实现配置重载命令
  - 实现配置验证和回滚逻辑
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [ ]* 17.1 编写热加载配置刷新的属性测试
  - **Property 30: Hot reload configuration refresh**
  - **Validates: Requirements 11.1, 11.3**

- [ ]* 17.2 编写热加载失败安全的属性测试
  - **Property 31: Hot reload failure safety**
  - **Validates: Requirements 11.4**

- [ ]* 17.3 编写热加载数据库更新的属性测试
  - **Property 32: Hot reload database update**
  - **Validates: Requirements 11.5**

- [ ]* 18. 编写集成测试
  - 编写端到端方法注册流程测试
  - 编写端到端任务执行流程测试
  - 使用testcontainers启动PostgreSQL
  - 测试与真实Ollama服务的集成
  - _Requirements: 所有需求的集成验证_

- [ ]* 19. 创建Docker部署配置
  - 为method-registration创建Dockerfile
  - 为agent-scheduler创建Dockerfile
  - 创建docker-compose.yml包含PostgreSQL和Ollama
  - 编写部署文档
  - _Requirements: 部署相关_

- [x] 20. Final Checkpoint - 确保所有测试通过





  - 确保所有测试通过，如有问题请询问用户
