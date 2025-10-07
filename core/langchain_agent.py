"""
LangChain智能体引擎

基于LangChain框架的CRM智能助手核心引擎
"""

from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables import RunnableConfig

from .agent import ConversationContext
from .tools.tool_registry import tool_registry
from .tools.result_processor import ToolResultProcessor
from adapters.base_adapter import BaseAdapter


logger = logging.getLogger(__name__)


class LangChainAgent:
    """LangChain智能体引擎"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化智能体引擎
        
        Args:
            config: 配置字典，包含模型配置等
        """
        self.config = config
        self.llm = None
        self.agent = None
        self.agent_executor = None
        self.result_processor = ToolResultProcessor()
        self._initialized = False
        
        # 系统提示词
        self.system_prompt = """你是一个专业的CRM（客户关系管理）智能助手，名字叫小助手。你的主要职责是帮助用户管理客户信息、商品信息和订单处理。

## 你的能力范围：

### 客户管理
- 创建新客户档案
- 搜索和查找客户信息
- 获取客户详细信息
- 更新客户资料
- 管理当前活跃客户

### 商品管理
- 搜索商品信息
- 获取商品详细信息
- 查询商品价格和库存
- 检查商品可用性

### 订单管理
- 创建新订单
- 计算订单总价
- 验证订单数据
- 提供订单创建指导

## 工作原则：

1. **智能理解**：准确理解用户的意图，即使表达不够精确也要推断出真实需求
2. **主动协助**：当用户需求不明确时，主动询问必要信息
3. **上下文感知**：记住对话历史，维护会话状态（如当前活跃客户）
4. **工具优先**：优先使用可用的工具来获取准确信息，而不是猜测
5. **友好交互**：保持专业而友好的语调，提供清晰的反馈

## 特殊处理规则：

- 当用户提到"客户"但没有指定具体客户时，如果当前有活跃客户，优先使用活跃客户
- 创建订单前，确保客户和商品信息都已确认
- 遇到错误时，提供具体的解决建议
- 对于复杂操作，分步骤引导用户完成

## 响应格式：
- 使用清晰的中文回复
- 重要信息使用适当的格式化（如列表、表格等）
- 操作结果要明确说明成功或失败
- 提供后续操作建议

请始终记住，你的目标是让CRM操作变得简单高效，为用户提供最佳的客户关系管理体验。"""
    
    def initialize(self, adapter: BaseAdapter, context: ConversationContext):
        """
        初始化智能体
        
        Args:
            adapter: CRM适配器
            context: 会话上下文
        """
        try:
            # 初始化工具注册器
            tool_registry.initialize(adapter, context)
            
            # 初始化LLM
            self._initialize_llm()
            
            # 创建智能体
            self._create_agent()
            
            self._initialized = True
            logger.info("LangChain智能体初始化成功")
            
        except Exception as e:
            logger.error(f"初始化LangChain智能体失败: {e}")
            raise
    
    def _initialize_llm(self):
        """初始化语言模型"""
        ai_config = self.config.get('ai', {})
        
        # 获取API配置
        api_key = ai_config.get('api_key', 'sk-placeholder')
        base_url = ai_config.get('base_url', 'https://api.deepseek.com')
        model = ai_config.get('model', 'deepseek-chat')
        temperature = ai_config.get('temperature', 0.7)
        max_tokens = ai_config.get('max_tokens', 2000)
        
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=False
        )
        
        logger.info(f"LLM初始化完成: {model}")
    
    def _create_agent(self):
        """创建智能体"""
        # 获取所有工具
        tools = tool_registry.get_all_tools()
        
        # 创建提示词模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad")
        ])
        
        # 创建工具调用智能体
        self.agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # 创建智能体执行器
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            early_stopping_method="generate"
        )
        
        logger.info(f"智能体创建完成，加载了 {len(tools)} 个工具")
    
    def process_message(
        self, 
        message: str, 
        context: ConversationContext
    ) -> Dict[str, Any]:
        """
        处理用户消息
        
        Args:
            message: 用户消息
            context: 会话上下文
            
        Returns:
            处理结果字典
        """
        if not self._initialized:
            return {
                "success": False,
                "message": "智能体未初始化",
                "response": "系统错误：智能体未正确初始化，请联系管理员。"
            }
        
        try:
            # 刷新工具注册器的上下文
            tool_registry.refresh_context(context)
            
            # 准备输入数据
            agent_input = {
                "input": message,
                "chat_history": self._format_chat_history(context.chat_history)
            }
            
            # 执行智能体
            start_time = datetime.now()
            result = self.agent_executor.invoke(agent_input)
            end_time = datetime.now()
            
            # 处理结果
            response = result.get("output", "抱歉，我无法处理您的请求。")
            
            # 更新会话历史
            self._update_chat_history(context, message, response)
            
            # 记录执行时间
            execution_time = (end_time - start_time).total_seconds()
            logger.info(f"智能体执行完成，耗时: {execution_time:.2f}秒")
            
            return {
                "success": True,
                "message": "处理成功",
                "response": response,
                "execution_time": execution_time,
                "tool_calls": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}")
            return {
                "success": False,
                "message": f"处理失败: {str(e)}",
                "response": "抱歉，处理您的请求时遇到了问题，请稍后重试。"
            }
    
    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> List[Union[HumanMessage, AIMessage]]:
        """
        格式化聊天历史
        
        Args:
            chat_history: 聊天历史列表
            
        Returns:
            格式化的消息列表
        """
        formatted_history = []
        
        for entry in chat_history:
            if entry.get("role") == "user":
                formatted_history.append(HumanMessage(content=entry.get("content", "")))
            elif entry.get("role") == "assistant":
                formatted_history.append(AIMessage(content=entry.get("content", "")))
        
        return formatted_history
    
    def _update_chat_history(
        self, 
        context: ConversationContext, 
        user_message: str, 
        assistant_response: str
    ):
        """
        更新聊天历史
        
        Args:
            context: 会话上下文
            user_message: 用户消息
            assistant_response: 助手回复
        """
        # 添加用户消息
        context.chat_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 添加助手回复
        context.chat_history.append({
            "role": "assistant",
            "content": assistant_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持历史记录在合理范围内（最多保留最近20轮对话）
        max_history = 40  # 20轮对话 = 40条消息
        if len(context.chat_history) > max_history:
            context.chat_history = context.chat_history[-max_history:]
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取智能体信息
        
        Returns:
            智能体状态信息
        """
        if not self._initialized:
            return {"initialized": False, "error": "智能体未初始化"}
        
        tool_info = tool_registry.get_tool_info()
        
        return {
            "initialized": True,
            "model": self.config.get('ai', {}).get('model', 'unknown'),
            "tools": tool_info,
            "system_prompt_length": len(self.system_prompt),
            "agent_type": "tool_calling_agent"
        }
    
    def validate_agent(self) -> Dict[str, Any]:
        """
        验证智能体状态
        
        Returns:
            验证结果
        """
        validation_result = {
            "agent_initialized": self._initialized,
            "llm_available": self.llm is not None,
            "agent_executor_available": self.agent_executor is not None,
            "tools_validation": None,
            "overall_status": "unknown"
        }
        
        if self._initialized:
            # 验证工具
            validation_result["tools_validation"] = tool_registry.validate_tools()
            
            # 综合评估
            if (validation_result["agent_initialized"] and 
                validation_result["llm_available"] and 
                validation_result["agent_executor_available"] and
                validation_result["tools_validation"]["valid_tools"] > 0):
                validation_result["overall_status"] = "healthy"
            else:
                validation_result["overall_status"] = "degraded"
        else:
            validation_result["overall_status"] = "not_initialized"
        
        return validation_result