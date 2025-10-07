# AI CRM助手智能体架构分析

## 系统概览

本系统是一个基于FastAPI的AI CRM助手，采用模块化设计，支持多种AI服务提供商和CRM系统适配器。

## 核心组件架构

```mermaid
graph TB
    %% 用户交互层
    subgraph "用户交互层"
        WEB[Web前端]
        WS[WebSocket连接]
        API[REST API]
    end

    %% 服务层
    subgraph "服务层 (main.py)"
        FASTAPI[FastAPI服务器]
        CM[ConnectionManager]
        ROUTES[API路由]
    end

    %% 核心智能体层
    subgraph "核心智能体层 (core/agent.py)"
        AGENT[AiAgent]
        INTENT[Intent解析器]
        CONTEXT[ConversationContext]
        EXECUTOR[Intent执行器]
    end

    %% AI服务层
    subgraph "AI服务层 (core/ai_services/)"
        BASE_AI[BaseAiService]
        DEEPSEEK[DeepSeekService]
        OPENAI[OpenAIService]
        MOCK_AI[MockAiService]
    end

    %% 适配器层
    subgraph "适配器层 (adapters/)"
        BASE_ADAPTER[BaseCrmAdapter]
        ODOO[OdooAdapter]
        MOCK_ADAPTER[MockCrmAdapter]
    end

    %% 数据模型层
    subgraph "数据模型层"
        CUSTOMER[CustomerData]
        PRODUCT[ProductData]
        ORDER[OrderData]
        RESULT[OperationResult]
    end

    %% 外部系统
    subgraph "外部系统"
        ODOO_SYS[Odoo CRM系统]
        DEEPSEEK_API[DeepSeek API]
        OPENAI_API[OpenAI API]
    end

    %% 连接关系
    WEB --> WS
    WEB --> API
    WS --> FASTAPI
    API --> FASTAPI
    FASTAPI --> CM
    FASTAPI --> ROUTES
    ROUTES --> AGENT

    AGENT --> INTENT
    AGENT --> CONTEXT
    AGENT --> EXECUTOR
    AGENT --> BASE_AI

    BASE_AI --> DEEPSEEK
    BASE_AI --> OPENAI
    BASE_AI --> MOCK_AI

    AGENT --> BASE_ADAPTER
    BASE_ADAPTER --> ODOO
    BASE_ADAPTER --> MOCK_ADAPTER

    ODOO --> CUSTOMER
    ODOO --> PRODUCT
    ODOO --> ORDER
    ODOO --> RESULT

    DEEPSEEK --> DEEPSEEK_API
    OPENAI --> OPENAI_API
    ODOO --> ODOO_SYS
```

## 智能体处理流程

```mermaid
sequenceDiagram
    participant User as 用户
    participant WS as WebSocket
    participant Agent as AiAgent
    participant AI as AI服务
    participant Adapter as CRM适配器
    participant CRM as CRM系统

    User->>WS: 发送自然语言请求
    WS->>Agent: process_request()
    
    Agent->>Agent: _get_context() 获取会话上下文
    Agent->>AI: _parse_intent() 解析用户意图
    AI-->>Agent: 返回Intent对象
    
    Agent->>Agent: _execute_intent() 执行意图
    
    alt 创建客户
        Agent->>Adapter: create_customer()
        Adapter->>CRM: JSON-RPC调用
        CRM-->>Adapter: 返回结果
        Adapter-->>Agent: OperationResult
    else 搜索客户
        Agent->>Adapter: search_customers()
        Adapter->>CRM: 查询请求
        CRM-->>Adapter: 客户列表
        Adapter-->>Agent: OperationResult
    else 创建订单
        Agent->>Adapter: create_order()
        Adapter->>CRM: 订单创建
        CRM-->>Adapter: 订单ID
        Adapter-->>Agent: OperationResult
    end
    
    Agent->>Agent: _update_context() 更新上下文
    Agent-->>WS: 返回处理结果
    WS-->>User: 显示响应
```

## Intent解析流程

```mermaid
flowchart TD
    START[用户输入] --> PARSE[解析意图]
    PARSE --> EXTRACT[提取实体]
    EXTRACT --> VALIDATE[验证参数]
    
    VALIDATE --> CREATE{创建操作?}
    VALIDATE --> SEARCH{搜索操作?}
    VALIDATE --> UPDATE{更新操作?}
    
    CREATE --> CREATE_CUSTOMER[创建客户]
    CREATE --> CREATE_ORDER[创建订单]
    
    SEARCH --> SEARCH_CUSTOMER[搜索客户]
    SEARCH --> SEARCH_PRODUCT[搜索产品]
    
    UPDATE --> UPDATE_CUSTOMER[更新客户]
    
    CREATE_CUSTOMER --> EXECUTE[执行CRM操作]
    CREATE_ORDER --> EXECUTE
    SEARCH_CUSTOMER --> EXECUTE
    SEARCH_PRODUCT --> EXECUTE
    UPDATE_CUSTOMER --> EXECUTE
    
    EXECUTE --> RESULT[返回结果]
```

## 适配器模式架构

```mermaid
classDiagram
    class BaseCrmAdapter {
        <<abstract>>
        +config: Dict
        +test_connection() OperationResult
        +create_customer(CustomerData) OperationResult
        +search_customers() OperationResult
        +get_customer(str) OperationResult
        +update_customer(str, Dict) OperationResult
        +search_products() OperationResult
        +create_order(OrderData) OperationResult
        +get_system_info() Dict
        +get_required_fields(str) Dict
    }
    
    class OdooAdapter {
        +base_url: str
        +db: str
        +username: str
        +password: str
        +uid: int
        +_login() None
        +_execute_odoo_method() Any
    }
    
    class MockCrmAdapter {
        +customers: List
        +products: List
        +orders: List
        +_generate_id() str
    }
    
    class CustomerData {
        +name: str
        +email: str
        +phone: str
        +company: str
        +address: str
        +notes: str
    }
    
    class ProductData {
        +name: str
        +description: str
        +price: float
        +category: str
        +sku: str
    }
    
    class OrderData {
        +customer_id: str
        +product_ids: List[str]
        +quantity: Dict[str, int]
        +notes: str
    }
    
    class OperationResult {
        +success: bool
        +message: str
        +data: Dict
        +error_code: str
        +error_details: str
    }
    
    BaseCrmAdapter <|-- OdooAdapter
    BaseCrmAdapter <|-- MockCrmAdapter
    BaseCrmAdapter --> CustomerData
    BaseCrmAdapter --> ProductData
    BaseCrmAdapter --> OrderData
    BaseCrmAdapter --> OperationResult
```
## AI服务架构

```mermaid
classDiagram
    class BaseAiService {
        <<abstract>>
        +parse_intent(str) str
    }
    
    class DeepSeekService {
        +auth_token: str
        +base_url: str
        +model: str
        +temperature: float
        +max_tokens: int
        +_validate_connection() None
        +_get_headers() Dict
        +_call_api(list) Dict
        +extract_entities(str, str) Dict
        +generate_response(str, Dict) str
    }
    
    class OpenAIService {
        +api_key: str
        +model: str
        +temperature: float
        +max_tokens: int
        +base_url: str
    }
    
    class MockAiService {
        +parse_intent(str) str
    }
    
    BaseAiService <|-- DeepSeekService
    BaseAiService <|-- OpenAIService
    BaseAiService <|-- MockAiService
```

## 核心数据流

```mermaid
graph LR
    subgraph "输入处理"
        INPUT[自然语言输入]
        CONTEXT[会话上下文]
    end
    
    subgraph "意图理解"
        PARSE[意图解析]
        ENTITY[实体提取]
        INTENT_OBJ[Intent对象]
    end
    
    subgraph "业务执行"
        VALIDATE[参数验证]
        EXECUTE[CRM操作]
        RESULT_OBJ[OperationResult]
    end
    
    subgraph "响应生成"
        FORMAT[格式化响应]
        UPDATE_CTX[更新上下文]
        OUTPUT[结构化输出]
    end
    
    INPUT --> PARSE
    CONTEXT --> PARSE
    PARSE --> ENTITY
    ENTITY --> INTENT_OBJ
    INTENT_OBJ --> VALIDATE
    VALIDATE --> EXECUTE
    EXECUTE --> RESULT_OBJ
    RESULT_OBJ --> FORMAT
    FORMAT --> UPDATE_CTX
    UPDATE_CTX --> OUTPUT
```

## 关键特性

### 1. 模块化设计
- **适配器模式**: 支持多种CRM系统（Odoo、Mock等）
- **策略模式**: 支持多种AI服务提供商（DeepSeek、OpenAI等）
- **标准化接口**: 统一的数据模型和操作接口

### 2. 异步处理
- 基于FastAPI的异步Web服务
- WebSocket实时通信
- 异步AI服务调用

### 3. 会话管理
- 多轮对话上下文保持
- 会话状态管理
- 历史记录维护

### 4. 错误处理
- 分层异常处理
- 标准化错误响应
- 连接状态监控

### 5. 扩展性
- 插件化适配器架构
- 可配置AI服务
- 标准化数据接口

## 配置管理

系统支持多种配置方式：
- AI服务配置（API密钥、模型参数等）
- CRM适配器配置（连接信息、认证等）
- 服务器配置（端口、CORS等）

## 部署架构

系统支持多种部署方式：
- 单机部署
- Docker容器化
- Kubernetes集群部署