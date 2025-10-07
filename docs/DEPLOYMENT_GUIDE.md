# Enhanced Odoo Adapter - 部署指南

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- Odoo 12+ (推荐 Odoo 15+)
- 网络连接（用于AI API调用）

### 2. 安装依赖

```bash
pip install requests dataclasses
```

### 3. 基础配置

创建配置文件 `config.yaml`：

```yaml
# Odoo连接配置
odoo:
  url: "https://your-odoo-instance.com"
  db: "your_database"
  username: "your_username"
  password: "your_password"
  timeout: 30
  enable_caching: true

# AI服务配置
ai_service:
  provider: "openai"
  api_key: "your-openai-api-key"
  model: "gpt-4"
  temperature: 0.1
  max_tokens: 500
```

### 4. 基础使用示例

```python
from adapters.odoo_adapter_enhanced import EnhancedOdooAdapter
from core.agent_fixed import AiAgent
from adapters.base_adapter import CustomerData

# 1. 创建适配器
config = {
    'url': 'https://your-odoo-instance.com',
    'db': 'your_database',
    'username': 'your_username',
    'password': 'your_password'
}

adapter = EnhancedOdooAdapter(config)

# 2. 测试连接
result = adapter.test_connection()
if result.success:
    print(f"✅ 连接成功: {result.message}")
else:
    print(f"❌ 连接失败: {result.message}")

# 3. 直接使用适配器
customer = CustomerData(
    name="张三",
    email="zhangsan@example.com",
    phone="13800138000",
    company="示例公司"
)

result = adapter.create_customer(customer)
if result.success:
    print(f"✅ 客户创建成功: {result.message}")
else:
    print(f"❌ 客户创建失败: {result.message}")

# 4. 通过AI代理使用
ai_config = {
    'provider': 'openai',
    'api_key': 'your-openai-api-key'
}

agent = AiAgent(adapter, ai_config)

# 处理自然语言请求
result = await agent.process_request(
    "创建一个新客户，名叫李四，邮箱是lisi@example.com，电话是13900139000",
    "session_123",
    "user_456"
)

print(f"AI处理结果: {result}")
```

## 📋 高级配置

### 自定义字段映射

```yaml
custom_field_mapping:
  # 将标准字段映射到您的Odoo自定义字段
  company: "x_company_id"        # company字段映射到x_company_id
  notes: "x_internal_notes"      # notes字段映射到x_internal_notes
  industry: "x_industry_type"    # 添加新的industry字段映射
  source: "x_lead_source"        # 添加source字段映射
```

### 业务规则配置

```yaml
business_rules:
  customer:
    required_fields:
      - "name"
      - "email"
      - "phone"    # 必须提供电话号码

    field_formats:
      email: "email"     # 验证邮箱格式
      phone: "phone"     # 基本电话验证

    custom_rules:
      # 公司名称不能包含禁用词
      - type: "condition"
        condition: "'spam' in data.get('company', '').lower()"
        message: "公司名称不能包含敏感词汇"

      # 客户名称长度限制
      - type: "condition"
        condition: "len(data.get('name', '')) < 2"
        message: "客户名称至少需要2个字符"

  order:
    required_fields:
      - "partner_id"

    custom_rules:
      # 最小订单金额
      - type: "condition"
        condition: "data.get('amount_total', 0) < 50"
        message: "订单金额不能少于50元"
```

### 高级搜索配置

```yaml
advanced:
  default_search_limit: 20
  max_search_limit: 100

  # 同步字段配置
  sync_fields:
    customer_create:
      - "name"
      - "email"
      - "phone"
      - "company_name"
      - "street"
      - "x_custom_field_1"  # 自定义字段

    customer_update:
      - "email"
      - "phone"
      - "street"
      - "x_custom_field_1"
```

## 🔧 实际部署步骤

### 步骤1: 准备Odoo环境

1. 确保Odoo实例可访问
2. 创建专用API用户账号
3. 配置适当的权限：
   - 销售模块访问权限
   - 客户管理权限
   - 产品查看权限
   - 订单管理权限

### 步骤2: 配置网络

```yaml
# 如果使用反向代理
odoo:
  url: "https://odoo.yourcompany.com"
  # 或使用内部IP
  # url: "http://192.168.1.100:8069"

# 配置超时设置
advanced:
  timeout: 60  # 网络较慢时增加超时时间
```

### 步骤3: 安全配置

```yaml
security:
  rate_limit:
    enabled: true
    requests_per_minute: 100
    burst_size: 20

  # 数据脱敏（用于日志）
  mask_sensitive_data:
    enabled: true
    fields_to_mask:
      - "password"
      - "api_key"
```

### 步骤4: 监控配置

```yaml
monitoring:
  enable_metrics: true
  metrics_interval: 300  # 每5分钟收集一次指标

  enable_error_tracking: true
  error_webhook: "https://your-monitoring-system.com/webhook"

  # 日志配置
  logging:
    level: "INFO"
    log_requests: true
    log_responses: false  # 避免记录敏感数据
```

## 🧪 测试部署

### 1. 连接测试

```python
# 测试基本连接
result = adapter.test_connection()
print(f"连接状态: {result.success}")
print(f"详细信息: {result.data}")

# 测试系统信息
info = adapter.get_system_info()
print(f"Odoo版本: {info['odoo_version']}")
print(f"可用模型数: {info['available_models_count']}")
```

### 2. 功能测试

```python
# 测试客户创建
customer = CustomerData(
    name="测试客户",
    email="test@example.com",
    phone="1234567890"
)

result = adapter.create_customer(customer)
print(f"客户创建: {result.success}")

# 测试客户搜索
result = adapter.search_customers(name="测试")
print(f"搜索结果: {len(result.data.get('customers', []))}个客户")
```

### 3. AI集成测试

```python
# 测试自然语言处理
result = await agent.process_request(
    "帮我创建一个客户，名字叫测试用户，邮箱是test@user.com",
    "test_session",
    "test_user"
)

print(f"AI处理: {result['success']}")
print(f"响应: {result['message']}")
```

## 📊 性能优化

### 1. 缓存策略

```yaml
odoo:
  enable_caching: true  # 启用缓存提高性能

# 定期清理缓存
adapter.clear_cache()
```

### 2. 批量操作

```python
# 批量创建客户
customers = [
    CustomerData(name="客户1", email="c1@example.com"),
    CustomerData(name="客户2", email="c2@example.com"),
    # ... 更多客户
]

result = adapter.batch_create_customers(customers)
print(f"批量创建结果: {result.data['success_count']}成功, {result.data['error_count']}失败")
```

### 3. 异步处理

```python
import asyncio

# 并发处理多个请求
async def process_multiple_requests():
    tasks = []
    for i in range(5):
        task = agent.process_request(
            f"创建客户{i}",
            f"session_{i}",
            f"user_{i}"
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(process_multiple_requests())
```

## 🚨 故障排除

### 常见问题

#### 1. 连接失败
```python
# 检查网络连接
import requests
try:
    response = requests.get(f"{config['url']}/web", timeout=10)
    print(f"Odoo实例响应: {response.status_code}")
except Exception as e:
    print(f"网络连接问题: {e}")
```

#### 2. 权限不足
```python
# 检查用户权限
info = adapter.get_system_info()
if not info.get('user_info'):
    print("用户权限不足，请检查用户配置")
```

#### 3. 字段不存在
```python
# 检查模型字段
fields = adapter.model_fields.get('res.partner', {})
if not fields:
    print("无法获取模型字段信息")
else:
    print(f"可用字段: {list(fields.keys())}")
```

### 日志分析

```python
import logging

# 启用详细日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('adapters.odoo_adapter_enhanced')

# 查看详细日志
adapter = EnhancedOdooAdapter(config)
# 现在所有操作都会记录详细日志
```

## 📈 扩展功能

### 1. 自定义AI服务

```python
from core.agent_fixed import BaseAiService

class CustomAiService(BaseAiService):
    async def parse_intent(self, prompt: str) -> str:
        # 实现您的自定义AI逻辑
        return '{"action": "create", "entity_type": "customer", "confidence": 0.9}'

# 使用自定义AI服务
ai_config = {'provider': 'custom'}
agent = AiAgent(adapter, ai_config)
agent.ai_service = CustomAiService()
```

### 2. 自定义业务规则

```python
class CustomOdooAdapter(EnhancedOdooAdapter):
    def _validate_business_rules(self, entity_type: str, data: Dict[str, Any]) -> List[str]:
        errors = super()._validate_business_rules(entity_type, data)

        # 添加自定义验证逻辑
        if entity_type == 'customer':
            if data.get('name') and 'VIP' in data['name']:
                errors.append("VIP客户需要特殊处理流程")

        return errors
```

### 3. 集成外部系统

```python
class IntegratedOdooAdapter(EnhancedOdooAdapter):
    def create_customer(self, customer: CustomerData) -> OperationResult:
        # 调用Odoo创建客户
        result = super().create_customer(customer)

        if result.success:
            # 同时创建到外部CRM系统
            self.sync_to_external_crm(customer, result.data['customer_id'])

        return result

    def sync_to_external_crm(self, customer: CustomerData, odoo_id: int):
        # 实现外部CRM同步逻辑
        pass
```

## 📞 技术支持

如果遇到问题，请：

1. 检查日志文件中的错误信息
2. 确认Odoo实例和用户权限配置
3. 验证网络连接和防火墙设置
4. 查看测试用例了解正确的使用方法

---

**文档版本**: v2.0
**最后更新**: 2025-10-06
**适配器版本**: Enhanced Odoo Adapter v2.0.0