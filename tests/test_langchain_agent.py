"""
LangChain智能体系统测试用例
测试智能体工具调用、上下文管理和错误处理功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from core.langchain_agent import LangChainAgent
from core.agent import ConversationContext
from adapters.mock_adapter import MockCrmAdapter


class TestLangChainAgent:
    """LangChain智能体测试类"""
    
    @pytest.fixture
    def mock_adapter(self):
        """创建模拟CRM适配器"""
        adapter = MockCrmAdapter({})
        return adapter
    
    @pytest.fixture
    def conversation_context(self):
        """创建会话上下文"""
        return ConversationContext(
            session_id="test_session",
            user_id="test_user",
            history=[],
            chat_history=[],
            session_data={}
        )
    
    @pytest.fixture
    def langchain_agent(self):
        """创建LangChain智能体实例"""
        return LangChainAgent()
    
    def test_agent_initialization(self, langchain_agent, mock_adapter, conversation_context):
        """测试智能体初始化"""
        # 初始状态应该是未初始化
        assert not langchain_agent.is_initialized()
        
        # 初始化智能体
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        # 初始化后应该可用
        assert langchain_agent.is_initialized()
        assert langchain_agent.adapter == mock_adapter
        assert langchain_agent.context == conversation_context
    
    @pytest.mark.asyncio
    async def test_customer_creation_flow(self, langchain_agent, mock_adapter, conversation_context):
        """测试客户创建流程"""
        # 初始化智能体
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        # 模拟用户请求创建客户
        user_message = "帮我创建一个新客户，姓名是张三，邮箱是zhangsan@example.com，电话是13800138000"
        
        with patch.object(langchain_agent, 'agent_executor') as mock_executor:
            # 模拟智能体执行结果
            mock_executor.invoke.return_value = {
                "output": "已成功创建客户张三，客户ID为123"
            }
            
            response = await langchain_agent.process_message(user_message)
            
            # 验证响应
            assert "张三" in response
            assert "成功" in response
            
            # 验证调用参数
            call_args = mock_executor.invoke.call_args[0][0]
            assert call_args["input"] == user_message
            assert "chat_history" in call_args
    
    @pytest.mark.asyncio
    async def test_product_search_flow(self, langchain_agent, mock_adapter, conversation_context):
        """测试产品搜索流程"""
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        user_message = "搜索名称包含'笔记本'的产品"
        
        with patch.object(langchain_agent, 'agent_executor') as mock_executor:
            mock_executor.invoke.return_value = {
                "output": "找到3个相关产品：联想笔记本、华为笔记本、苹果笔记本"
            }
            
            response = await langchain_agent.process_message(user_message)
            
            assert "笔记本" in response
            assert "3个" in response
    
    @pytest.mark.asyncio
    async def test_order_creation_flow(self, langchain_agent, mock_adapter, conversation_context):
        """测试订单创建流程"""
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        # 先设置活跃客户
        conversation_context.active_customer_id = "123"
        conversation_context.active_customer_name = "张三"
        
        user_message = "为当前客户创建订单，产品ID是456，数量是2"
        
        with patch.object(langchain_agent, 'agent_executor') as mock_executor:
            mock_executor.invoke.return_value = {
                "output": "已为客户张三创建订单，订单号为ORD001，总金额为2000元"
            }
            
            response = await langchain_agent.process_message(user_message)
            
            assert "张三" in response
            assert "ORD001" in response
            assert "2000" in response
    
    @pytest.mark.asyncio
    async def test_context_management(self, langchain_agent, mock_adapter, conversation_context):
        """测试上下文管理"""
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        # 模拟多轮对话
        messages = [
            "你好，我是新用户",
            "帮我创建客户张三",
            "查看刚才创建的客户信息"
        ]
        
        with patch.object(langchain_agent, 'agent_executor') as mock_executor:
            mock_executor.invoke.return_value = {"output": "处理完成"}
            
            for message in messages:
                await langchain_agent.process_message(message)
            
            # 验证聊天历史被正确维护
            assert len(conversation_context.chat_history) == len(messages) * 2  # 用户消息 + AI响应
            
            # 验证最后一次调用包含完整的聊天历史
            last_call_args = mock_executor.invoke.call_args[0][0]
            assert len(last_call_args["chat_history"]) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, langchain_agent, mock_adapter, conversation_context):
        """测试错误处理"""
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        user_message = "执行一个会失败的操作"
        
        with patch.object(langchain_agent, 'agent_executor') as mock_executor:
            # 模拟执行异常
            mock_executor.invoke.side_effect = Exception("模拟错误")
            
            with pytest.raises(Exception):
                await langchain_agent.process_message(user_message)
    
    def test_agent_info(self, langchain_agent, mock_adapter, conversation_context):
        """测试智能体信息获取"""
        langchain_agent.initialize(mock_adapter, conversation_context)
        
        info = langchain_agent.get_agent_info()
        
        assert "name" in info
        assert "version" in info
        assert "tools" in info
        assert "status" in info
        assert info["status"] == "initialized"
    
    def test_agent_validation(self, langchain_agent, mock_adapter, conversation_context):
        """测试智能体验证"""
        # 未初始化时验证失败
        assert not langchain_agent.validate_agent()
        
        # 初始化后验证成功
        langchain_agent.initialize(mock_adapter, conversation_context)
        assert langchain_agent.validate_agent()


class TestToolIntegration:
    """工具集成测试"""
    
    @pytest.fixture
    def initialized_agent(self):
        """创建已初始化的智能体"""
        agent = LangChainAgent()
        adapter = MockCrmAdapter({})
        context = ConversationContext(
            session_id="test",
            user_id="test",
            history=[],
            chat_history=[],
            session_data={}
        )
        agent.initialize(adapter, context)
        return agent, adapter, context
    
    @pytest.mark.asyncio
    async def test_customer_tools_integration(self, initialized_agent):
        """测试客户工具集成"""
        agent, adapter, context = initialized_agent
        
        # 测试客户创建工具
        with patch('core.tools.customer_tools.create_customer') as mock_tool:
            mock_tool.return_value = "客户创建成功"
            
            # 这里应该测试工具是否正确注册和调用
            # 由于LangChain的复杂性，这里主要验证工具注册
            assert agent.tool_registry is not None
            customer_tools = agent.tool_registry.get_tools_by_category("customer")
            assert len(customer_tools) > 0
    
    @pytest.mark.asyncio
    async def test_product_tools_integration(self, initialized_agent):
        """测试产品工具集成"""
        agent, adapter, context = initialized_agent
        
        product_tools = agent.tool_registry.get_tools_by_category("product")
        assert len(product_tools) > 0
        
        # 验证产品搜索工具存在
        search_tool = agent.tool_registry.get_tool_by_name("search_products")
        assert search_tool is not None
    
    @pytest.mark.asyncio
    async def test_order_tools_integration(self, initialized_agent):
        """测试订单工具集成"""
        agent, adapter, context = initialized_agent
        
        order_tools = agent.tool_registry.get_tools_by_category("order")
        assert len(order_tools) > 0
        
        # 验证订单创建工具存在
        create_tool = agent.tool_registry.get_tool_by_name("create_order")
        assert create_tool is not None


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])