# -*- coding: utf-8 -*-
"""
Core AI Agent

This module contains the main AI agent that processes natural language requests
and orchestrates CRM operations through the adapter interface.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime

from adapters.base_adapter import BaseCrmAdapter, CustomerData, ProductData, OrderData, OperationResult


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Intent:
    """Parsed user intent"""
    action: str  # create, search, update, delete
    entity_type: str  # customer, product, order
    parameters: Dict[str, Any]
    confidence: float


@dataclass
class ConversationContext:
    """Conversation context for multi-turn dialogues"""
    session_id: str
    user_id: str
    history: List[Dict[str, Any]]  # 保留原有历史记录格式（兼容性）
    pending_intent: Optional[Intent] = None
    last_entity_mentioned: Optional[str] = None
    # Session memory: currently selected customer
    active_customer_id: Optional[str] = None
    active_customer_name: Optional[str] = None
    
    # 新增字段支持LangChain智能体
    chat_history: List[Dict[str, str]] = None  # LangChain格式的聊天历史
    session_data: Dict[str, Any] = None  # 会话级别的数据存储
    
    def __post_init__(self):
        """初始化默认值"""
        if self.chat_history is None:
            self.chat_history = []
        if self.session_data is None:
            self.session_data = {}


class AiAgent:
    """
    Core AI Agent for CRM operations

    This agent processes natural language input, parses user intent,
    and executes CRM operations through pluggable adapters.
    """

    def __init__(self, adapter: BaseCrmAdapter, ai_config: Dict[str, Any]):
        """
        Initialize AI Agent

        Args:
            adapter: CRM adapter instance
            ai_config: AI service configuration
        """
        self.adapter = adapter
        self.ai_config = ai_config
        self.contexts: Dict[str, ConversationContext] = {}

        # 对话记忆窗口长度（默认为5轮，可在YAML中通过 conversation.history_rounds 配置）
        try:
            self.conversation_max_rounds = int(
                (self.ai_config.get('conversation') or {}).get('history_rounds', 5)
            )
        except Exception:
            self.conversation_max_rounds = 5

        # Initialize AI service
        self.ai_service = self._init_ai_service()

    def _init_ai_service(self):
        """Initialize AI service based on configuration"""
        provider = self.ai_config.get('provider', 'openai')
        logger.info(f"初始化AI服务，提供者: {provider}")
        logger.info(f"AI配置: {self.ai_config}")

        if provider == 'openai':
            from .ai_services.openai_service import OpenAIService
            return OpenAIService(self.ai_config)
        elif provider == 'deepseek':
            from .ai_services.deepseek_official_service import DeepSeekOfficialService
            return DeepSeekOfficialService(self.ai_config)
        elif provider == 'deepseek_modelscope':
            from .ai_services.deepseek_service import DeepSeekService
            return DeepSeekService(self.ai_config)
        elif provider == 'claude':
            from .ai_services.claude_service import ClaudeService
            return ClaudeService(self.ai_config)
        elif provider == 'mock':
            # Allow mock service for testing
            from .ai_services.mock_ai_service import MockAIService
            logger.info("使用Mock AI服务")
            return MockAIService(self.ai_config)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    async def process_request(self,
                            text_input: str,
                            session_id: str,
                            user_id: str) -> Dict[str, Any]:
        """
        Process natural language request

        Args:
            text_input: User's natural language input
            session_id: Session identifier
            user_id: User identifier

        Returns:
            Dictionary with response and operation results
        """
        try:
            # Get or create conversation context
            context = self._get_context(session_id, user_id)

            # Parse user intent
            intent = await self._parse_intent(text_input, context)

            # 确保intent是Intent对象，如果是字典则转换
            if isinstance(intent, dict):
                intent = Intent(
                    action=intent.get('action', 'unknown'),
                    entity_type=intent.get('entity_type', 'unknown'),
                    parameters=intent.get('parameters', {}),
                    confidence=intent.get('confidence', 0.0)
                )

            # Log the parsed intent for debugging
            logger.info(f"Parsed intent: {intent.action} {intent.entity_type} (confidence: {intent.confidence})")

            # Execute intent if confidence is high enough
            if intent.confidence >= 0.7:
                result = await self._execute_intent(intent, context)
            else:
                # Ask for clarification
                result = {
                    'success': False,
                    'message': f"I'm not sure what you want to do. Did you mean to {intent.action} a {intent.entity_type}?",
                    'clarification_needed': True,
                    'suggested_intent': intent
                }

            # Update conversation context
            self._update_context(context, text_input, intent, result)

            return result

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                'success': False,
                'message': f"Sorry, I encountered an error: {str(e)}",
                'error_type': type(e).__name__
            }

    async def _parse_intent(self, text_input: str, context: ConversationContext) -> Intent:
        """
        Parse user intent from natural language input

        Args:
            text_input: User's input text
            context: Conversation context

        Returns:
            Parsed intent object
        """
        # Build conversation history for context
        history_text = self._build_history_text(context)

        # Build prompt for intent parsing
        prompt = self._build_intent_prompt(text_input, history_text)

        # Call AI service for intent parsing
        ai_response = await self.ai_service.parse_intent(prompt)

        # Parse AI response into Intent object
        return self._parse_intent_response(ai_response)

    async def _execute_intent(self, intent: Union[Intent, Dict[str, Any]], context: ConversationContext) -> Dict[str, Any]:
        """
        Execute parsed intent using the CRM adapter

        Args:
            intent: Parsed user intent (Intent object or dict)
            context: Conversation context

        Returns:
            Operation result
        """
        try:
            # 处理None值或字典类型的intent
            if intent is None:
                intent = Intent(
                    action='unknown',
                    entity_type='unknown',
                    parameters={},
                    confidence=0.0
                )
            elif isinstance(intent, dict):
                intent = Intent(
                    action=intent.get('action', 'unknown'),
                    entity_type=intent.get('entity_type', 'unknown'),
                    parameters=intent.get('parameters', {}),
                    confidence=intent.get('confidence', 0.0)
                )
            # 处理问候语 - 使用AI生成自然回应
            if intent.action == 'greeting':
                if hasattr(self.ai_service, 'generate_response'):
                    ai_response = await self.ai_service.generate_response(
                        "用户向我问好，请生成一个友好、自然的问候回应，并简单介绍我的功能"
                    )
                    return {
                        'success': True,
                        'message': ai_response,
                        'is_greeting': True
                    }
                else:
                    return {
                        'success': True,
                        'message': "你好！我是您的AI CRM助手 👋 很高兴为您服务！我可以帮您管理客户信息、处理订单、搜索产品等。有什么需要帮助的吗？",
                        'is_greeting': True
                    }

            # 处理自我介绍 - 使用AI生成自然回应
            elif intent.action == 'introduction':
                if hasattr(self.ai_service, 'generate_response'):
                    ai_response = await self.ai_service.generate_response(
                        "用户问我是谁，请生成一个专业但友好的自我介绍，说明我的CRM助手功能"
                    )
                    return {
                        'success': True,
                        'message': ai_response,
                        'is_introduction': True
                    }
                else:
                    return {
                        'success': True,
                        'message': "我是您的智能CRM助手 🤖 专门帮助您高效管理客户关系。我能创建客户档案、搜索信息、处理订单等。让我来简化您的工作吧！",
                        'is_introduction': True
                    }

            # 处理帮助请求 - 使用AI生成自然回应
            elif intent.action == 'help':
                if hasattr(self.ai_service, 'generate_response'):
                    ai_response = await self.ai_service.generate_response(
                        "用户请求帮助，请生成一个详细的功能菜单，说明我能做什么"
                    )
                    return {
                        'success': True,
                        'message': ai_response,
                        'is_help': True
                    }
                else:
                    return {
                        'success': True,
                        'message': "我很乐意帮助您！以下是我能为您做的事情：\n\n📝 **客户管理**\n• 创建新客户档案\n• 搜索客户信息\n• 更新客户资料\n\n📦 **订单处理**\n• 创建新订单\n• 查询订单状态\n• 订单管理\n\n🔍 **产品查询**\n• 搜索产品信息\n• 查看产品详情\n\n请告诉我您想做什么，我会立即为您处理！",
                        'is_help': True
                    }

            # CRM 操作意图
            elif intent.action == 'create' and intent.entity_type == 'customer':
                return await self._create_customer(intent.parameters, context)

            elif intent.action == 'update' and intent.entity_type == 'customer':
                return await self._update_customer(intent.parameters, context)

            elif intent.action == 'search' and intent.entity_type == 'customer':
                return await self._search_customers(intent.parameters, context)

            elif intent.action == 'create' and intent.entity_type == 'order':
                return await self._create_order(intent.parameters, context)

            elif intent.action == 'search' and intent.entity_type == 'product':
                return await self._search_products(intent.parameters, context)

            # 未知意图 - 使用AI生成自然的澄清回应
            else:
                if hasattr(self.ai_service, 'generate_response'):
                    ai_response = await self.ai_service.generate_response(
                        f"用户说了我不太理解的话，识别到的意图是{intent.action} {intent.entity_type}，请生成一个友好的澄清回应，询问用户具体需要什么帮助"
                    )
                    return {
                        'success': True,
                        'message': ai_response,
                        'clarification_needed': True,
                        'suggested_intent': intent
                    }
                else:
                    return {
                        'success': False,
                        'message': f"I'm not sure what you want to do. Did you mean to {intent.action} a {intent.entity_type}?",
                        'clarification_needed': True,
                        'suggested_intent': intent
                    }

        except Exception as e:
            import traceback
            logger.error(f"Error executing intent: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")

            # 尝试使用AI生成友好的错误消息
            try:
                if hasattr(self.ai_service, 'generate_response'):
                    ai_response = await self.ai_service.generate_response(
                        f"系统在执行{intent.action} {intent.entity_type}操作时遇到了技术问题：{str(e)}。请生成一个友好、专业的中文回复，向用户解释这个问题并提供解决方案建议。不要使用技术术语，要让用户感到被理解和帮助。"
                    )
                    return {
                        'success': False,
                        'message': ai_response,
                        'error_type': type(e).__name__,
                        'is_friendly_error': True
                    }
            except Exception as ai_error:
                logger.error(f"Failed to generate AI error response: {ai_error}")

            # 如果AI生成失败，返回友好的预设错误消息
            friendly_errors = {
                'Odoo RPC error': "抱歉，我现在无法连接到CRM系统来创建客户。这可能是系统暂时繁忙或网络连接问题。请您稍后再试，或者联系系统管理员检查CRM系统的状态。",
                'ValidationError': "抱歉，您提供的信息有些问题无法创建客户。请检查一下客户信息是否完整和正确。",
                'ConnectionError': "抱歉，现在无法连接到CRM系统。请稍后再试或联系技术支持。",
                'TimeoutError': "抱歉，系统响应超时了。请稍后再试，如果问题持续存在请联系技术支持。"
            }

            error_key = None
            for key in friendly_errors:
                if key in str(e):
                    error_key = key
                    break

            if error_key:
                return {
                    'success': False,
                    'message': friendly_errors[error_key],
                    'error_type': type(e).__name__,
                    'is_friendly_error': True
                }
            else:
                return {
                    'success': False,
                    'message': f"抱歉，在处理您的请求时遇到了问题：{str(e)}。请稍后再试或联系技术支持。",
                    'error_type': type(e).__name__,
                    'is_friendly_error': True
                }

    # === Intent Execution Methods ===

    async def _create_customer(self, parameters: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Create a new customer"""
        # Validate required parameters
        if not parameters.get('name'):
            return {
                'success': False,
                'message': "I need a customer name to create a new customer. Could you provide that?",
                'missing_fields': ['name']
            }

        # Create customer data object
        customer = CustomerData(
            name=parameters['name'],
            email=parameters.get('email'),
            phone=parameters.get('phone'),
            company=parameters.get('company'),
            address=parameters.get('address'),
            notes=parameters.get('notes')
        )

        # Execute through adapter - EnhancedOdooAdapter expects CustomerData object, not dict
        result = self.adapter.create_customer(customer)

        if result.success:
            return {
                'success': True,
                'message': f"Successfully created customer: {customer.name}",
                'customer_id': result.data.get('customer_id') if result.data else None,
                'customer_details': result.data if result.data else {}
            }
        else:
            return {
                'success': False,
                'message': f"Failed to create customer: {result.message}",
                'error_details': result.error_details
            }

    async def _search_customers(self, parameters: dict, context: ConversationContext) -> dict:
        """处理搜索客户的逻辑"""
        logger.info(f"开始搜索客户，参数: {parameters}")
        # 兼容参数为字符串（直接作为name）或None的情况
        if isinstance(parameters, str):
            parameters = { 'name': parameters }
        elif parameters is None:
            parameters = {}
        # 通过适配器执行搜索；支持 name/email/phone/company 四个可选参数
        result = self.adapter.search_customers(
            name=parameters.get('name'),
            email=parameters.get('email'),
            phone=parameters.get('phone'),
            company=parameters.get('company'),
            limit=parameters.get('limit', 10)
        )

        # 兼容不同适配器返回的数据结构：
        # - MockAdapter: 直接返回列表
        # - OdooAdapter/EnhancedOdooAdapter: OperationResult.data 为字典，包含 customers 列表
        customers: list = []
        if result.success:
            if isinstance(result.data, list):
                customers = result.data
            elif isinstance(result.data, dict):
                customers = result.data.get('customers', [])
            else:
                customers = []

            if customers:
                # 如果只有一个匹配项，则自动获取其详细信息
                if len(customers) == 1 and customers[0].get('id') is not None:
                    detail = self.adapter.get_customer(str(customers[0]['id']))
                    if detail.success and isinstance(detail.data, dict) and detail.data.get('customer'):
                        cust = detail.data['customer']
                        # write session memory
                        context.active_customer_id = str(cust.get('id')) if cust.get('id') is not None else None
                        context.active_customer_name = cust.get('name')
                        # 展示更完整的信息（仅显示常见字段，避免过长）
                        message = (
                            "为您找到该客户的详细信息：\n"
                            f"- 姓名: {cust.get('name', 'N/A')}\n"
                            f"- ID: {cust.get('id', 'N/A')}\n"
                            f"- 邮箱: {cust.get('email', 'N/A')}\n"
                            f"- 电话: {cust.get('phone', 'N/A')}\n"
                            f"- 公司: {cust.get('company') or cust.get('company_name', 'N/A')}\n"
                            f"- 地址: {cust.get('street', cust.get('address', 'N/A'))}"
                        )
                        message += "\n\n我已记住该客户，后续更新信息可直接说明无需再提供ID。"
                        customers = [cust]
                    else:
                        # 回退到简要列表展示
                        message = (
                            "为您找到以下客户：\n" +
                            "\n".join([
                                f"- {c.get('name', 'N/A')} (ID: {c.get('id', 'N/A')})"
                                for c in customers
                            ])
                        )
                else:
                    # 多个匹配时，列表中尽量展示常见字段以便快速区分
                    def fmt(c: dict) -> str:
                        extra = []
                        if c.get('email'): extra.append(f"邮箱: {c['email']}")
                        if c.get('phone'): extra.append(f"电话: {c['phone']}")
                        comp = c.get('company') or c.get('company_name')
                        if comp: extra.append(f"公司: {comp}")
                        extras = ("，".join(extra)) if extra else ""
                        return f"- {c.get('name', 'N/A')} (ID: {c.get('id', 'N/A')})" + (f"，{extras}" if extras else "")

                    message = (
                        "为您找到以下客户：\n" +
                        "\n".join([fmt(c) for c in customers])
                    )
            else:
                message = "未找到相关客户。"
        else:
            message = f"搜索客户失败: {result.message}"

        return {
            "success": result.success,
            "message": message,
            "customers": customers
        }

    async def _update_customer(self, parameters: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Update customer information"""
        customer_id = parameters.get('id')
        updates = {k: v for k, v in parameters.items() if k != 'id' and v is not None}

        if not customer_id:
            # Try to use session memory
            if context and getattr(context, 'active_customer_id', None):
                customer_id = context.active_customer_id
                logger.info(f"未提供ID，使用会话记忆中的客户ID: {customer_id}")
            else:
                return {"success": False, "message": "更新客户需要提供客户ID（或先搜索并选择客户）"}

        logger.info(f"开始更新客户 {customer_id}，更新内容: {updates}")
        result = self.adapter.update_customer(customer_id, updates)

        if result.success:
            message = f"成功更新客户 {customer_id} 的信息。"
        else:
            message = f"更新客户失败: {result.message}"

        return {
            "success": result.success,
            "message": message
        }

    async def _search_products(self, parameters: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Search for products"""
        # Build query string from parameters
        query_parts = []
        for field in ['name', 'category', 'sku']:
            if parameters.get(field):
                query_parts.append(parameters[field])

        query = ' '.join(query_parts) if query_parts else ''

        result = self.adapter.search_products(
            query=query,
            filters={'limit': parameters.get('limit', 10)}
        )

        # Handle MockCrmAdapter response format (returns list directly)
        if isinstance(result, list):
            products = result
            if products:
                return {
                    'success': True,
                    'message': f"Found {len(products)} matching products",
                    'products': products
                }
            else:
                return {
                    'success': True,
                    'message': "No matching products found",
                    'products': []
                }
        else:
            # Handle standard adapter response format
            if result.success:
                products = result.data.get('products', [])
                if products:
                    return {
                        'success': True,
                        'message': f"Found {len(products)} matching products",
                        'products': products
                    }
                else:
                    return {
                        'success': True,
                        'message': "No matching products found",
                        'products': []
                    }
            else:
                return {
                    'success': False,
                    'message': f"Failed to search products: {result.message}",
                    'error_details': result.error_details
                }

    async def _create_order(self, parameters: Dict[str, Any], context: ConversationContext) -> Dict[str, Any]:
        """Create a new order"""
        # Validate required parameters
        if not parameters.get('customer_id'):
            return {
                'success': False,
                'message': "I need a customer to create an order. Could you specify which customer?",
                'missing_fields': ['customer_id']
            }

        if not parameters.get('products'):
            return {
                'success': False,
                'message': "I need at least one product to create an order. Which products would you like to include?",
                'missing_fields': ['products']
            }

        # Create order data object
        order = OrderData(
            customer_id=parameters['customer_id'],
            product_ids=[p.get('product_id') for p in parameters['products']],
            quantity={p.get('product_id'): p.get('quantity', 1) for p in parameters['products']},
            notes=parameters.get('notes')
        )

        # Execute through adapter
        result = self.adapter.create_order(order)

        if result.success:
            return {
                'success': True,
                'message': f"Successfully created order for customer {parameters['customer_id']}",
                'order_id': result.data.get('order_id'),
                'order_details': result.data
            }
        else:
            return {
                'success': False,
                'message': f"Failed to create order: {result.message}",
                'error_details': result.error_details
            }

    # === Context Management ===

    def _get_context(self, session_id: str, user_id: str) -> ConversationContext:
        """Get or create conversation context"""
        if session_id not in self.contexts:
            self.contexts[session_id] = ConversationContext(
                session_id=session_id,
                user_id=user_id,
                history=[]
            )
        return self.contexts[session_id]

    def _update_context(self, context: ConversationContext, user_input: str, intent: Intent, result: Dict[str, Any]):
        """Update conversation context"""
        context.history.append({
            'timestamp': datetime.now().isoformat(),
            'user_input': user_input,
            'intent': {
                'action': intent.action,
                'entity_type': intent.entity_type,
                'confidence': intent.confidence
            },
            'result': result
        })

        # Update last entity mentioned
        if intent.confidence >= 0.7:
            context.last_entity_mentioned = intent.entity_type

    # === Helper Methods ===

    def _build_history_text(self, context: ConversationContext) -> str:
        """Build conversation history text for context"""
        if not context.history:
            return ""

        history_lines = []
        # 按配置取最近N轮完整对话
        recent = context.history[-self.conversation_max_rounds:]
        for item in recent:
            history_lines.append(f"User: {item['user_input']}")
            msg = item.get('result', {}).get('message')
            if msg:
                history_lines.append(f"Assistant: {msg}")

        return "\n".join(history_lines)

    def _build_intent_prompt(self, user_input: str, history: str) -> str:
        """Build prompt for intent parsing"""
        prompt = f"""You are a CRM assistant that needs to parse user intent from natural language.

Analyze the user's input and determine:
1. The action (create, search, update, delete, greeting)
2. The entity type (customer, product, order, or null for greeting)
3. The relevant parameters
4. Your confidence in this interpretation (0.0 to 1.0)

Recent conversation history:
{history}

User input: "{user_input}"

IMPORTANT: Handle greetings properly! If the user says "你好", "hello", "hi", etc., treat it as a greeting with high confidence.

Respond with a JSON object in this format:
{{
    "action": "create|search|update|delete|greeting",
    "entity_type": "customer|product|order|null",
    "parameters": {{
        "name": "extracted name if applicable",
        "email": "extracted email if applicable",
        "phone": "extracted phone if applicable",
        "company": "extracted company if applicable"
    }},
    "confidence": 0.95
}}

Only extract parameters that are explicitly mentioned in the user input. For greetings, set entity_type to "null" and parameters to {{}}. If confidence is less than 0.7, indicate clarification is needed."""

        return prompt

    def _parse_intent_response(self, ai_response: str) -> Intent:
        """Parse AI response into Intent object"""
        try:
            # Clean up AI response - remove markdown code blocks if present
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove ```
            cleaned_response = cleaned_response.strip()

            logger.info(f"Cleaned AI response: {cleaned_response}")
            response_data = json.loads(cleaned_response)
            return Intent(
                action=response_data.get('action', 'unknown'),
                entity_type=response_data.get('entity_type', 'unknown'),
                parameters=response_data.get('parameters', {}),
                confidence=response_data.get('confidence', 0.0)
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse AI response: {ai_response}")
            logger.error(f"Parse error: {str(e)}")
            return Intent(
                action='unknown',
                entity_type='unknown',
                parameters={},
                confidence=0.0
            )

    def _get_supported_operations(self) -> List[str]:
        """Get list of supported operations"""
        return [
            "create customer",
            "search customers",
            "search products",
            "create order"
        ]

    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            'agent_version': '1.0.0',
            'ai_provider': self.ai_config.get('provider'),
            'adapter_info': self.adapter.get_adapter_info(),
            'supported_operations': self._get_supported_operations(),
            'active_sessions': len(self.contexts)
        }


class MockAiService:
    """Mock AI service for testing"""

    async def parse_intent(self, prompt: str) -> str:
        # 提取用户输入
        user_input_start = prompt.find('User input: "') + 13
        user_input_end = prompt.find('"', user_input_start)
        user_input = prompt[user_input_start:user_input_end]

        user_input_lower = user_input.lower()

        # 处理问候语
        greetings = ["你好", "hello", "hi", "嗨", "您好"]
        if any(greeting in user_input_lower for greeting in greetings):
            return '''{
                "action": "greeting",
                "entity_type": null,
                "parameters": {},
                "confidence": 0.95
            }'''

        # 处理创建客户
        if "create" in user_input_lower and "customer" in user_input_lower:
            return '''{
                "action": "create",
                "entity_type": "customer",
                "parameters": {
                    "name": "Test Customer",
                    "email": "test@example.com"
                },
                "confidence": 0.95
            }'''

        # 处理搜索客户
        elif "search" in user_input_lower and "customer" in user_input_lower:
            return '''{
                "action": "search",
                "entity_type": "customer",
                "parameters": {
                    "name": "Test"
                },
                "confidence": 0.90
            }'''

        # 默认返回未知意图，要求澄清
        else:
            return '''{
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.3
            }'''