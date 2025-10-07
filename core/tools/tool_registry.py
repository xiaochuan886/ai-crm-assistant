"""
工具注册管理器

统一管理所有LangChain工具的注册、配置和访问
"""

from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool

from .customer_tools import CUSTOMER_TOOLS, set_adapter_and_context as set_customer_context
from .product_tools import PRODUCT_TOOLS, set_adapter_and_context as set_product_context
from .order_tools import ORDER_TOOLS, set_adapter_and_context as set_order_context
from ..agent import ConversationContext
from adapters.base_adapter import BaseAdapter


class ToolRegistry:
    """工具注册管理器"""
    
    def __init__(self):
        self._tools: List[BaseTool] = []
        self._tool_map: Dict[str, BaseTool] = {}
        self._adapter: Optional[BaseAdapter] = None
        self._context: Optional[ConversationContext] = None
        self._initialized = False
    
    def initialize(self, adapter: BaseAdapter, context: ConversationContext):
        """
        初始化工具注册器
        
        Args:
            adapter: CRM适配器实例
            context: 会话上下文实例
        """
        self._adapter = adapter
        self._context = context
        
        # 设置各工具模块的适配器和上下文
        set_customer_context(adapter, context)
        set_product_context(adapter, context)
        set_order_context(adapter, context)
        
        # 注册所有工具
        self._register_all_tools()
        self._initialized = True
    
    def _register_all_tools(self):
        """注册所有工具"""
        self._tools.clear()
        self._tool_map.clear()
        
        # 注册客户管理工具
        for tool in CUSTOMER_TOOLS:
            self._register_tool(tool, "customer")
        
        # 注册商品管理工具
        for tool in PRODUCT_TOOLS:
            self._register_tool(tool, "product")
        
        # 注册订单管理工具
        for tool in ORDER_TOOLS:
            self._register_tool(tool, "order")
    
    def _register_tool(self, tool: BaseTool, category: str):
        """
        注册单个工具
        
        Args:
            tool: 工具实例
            category: 工具分类
        """
        # 添加分类信息到工具元数据
        if hasattr(tool, 'metadata'):
            tool.metadata = tool.metadata or {}
            tool.metadata['category'] = category
        
        self._tools.append(tool)
        self._tool_map[tool.name] = tool
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        获取所有注册的工具
        
        Returns:
            所有工具的列表
        """
        if not self._initialized:
            raise RuntimeError("工具注册器未初始化，请先调用 initialize() 方法")
        
        return self._tools.copy()
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """
        根据名称获取工具
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例，如果不存在则返回None
        """
        return self._tool_map.get(name)
    
    def get_tools_by_category(self, category: str) -> List[BaseTool]:
        """
        根据分类获取工具
        
        Args:
            category: 工具分类（customer, product, order）
            
        Returns:
            指定分类的工具列表
        """
        return [
            tool for tool in self._tools
            if hasattr(tool, 'metadata') and 
            tool.metadata and 
            tool.metadata.get('category') == category
        ]
    
    def get_tool_info(self) -> Dict[str, Any]:
        """
        获取工具信息摘要
        
        Returns:
            包含工具统计和分类信息的字典
        """
        if not self._initialized:
            return {"error": "工具注册器未初始化"}
        
        categories = {}
        for tool in self._tools:
            category = "unknown"
            if hasattr(tool, 'metadata') and tool.metadata:
                category = tool.metadata.get('category', 'unknown')
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append({
                "name": tool.name,
                "description": tool.description
            })
        
        return {
            "total_tools": len(self._tools),
            "categories": categories,
            "initialized": self._initialized
        }
    
    def validate_tools(self) -> Dict[str, Any]:
        """
        验证所有工具的可用性
        
        Returns:
            验证结果
        """
        if not self._initialized:
            return {"error": "工具注册器未初始化"}
        
        validation_results = {
            "total_tools": len(self._tools),
            "valid_tools": 0,
            "invalid_tools": 0,
            "details": []
        }
        
        for tool in self._tools:
            try:
                # 基本验证：检查工具是否有必要的属性
                if hasattr(tool, 'name') and hasattr(tool, 'description'):
                    validation_results["valid_tools"] += 1
                    validation_results["details"].append({
                        "name": tool.name,
                        "status": "valid",
                        "description": tool.description[:100] + "..." if len(tool.description) > 100 else tool.description
                    })
                else:
                    validation_results["invalid_tools"] += 1
                    validation_results["details"].append({
                        "name": getattr(tool, 'name', 'unknown'),
                        "status": "invalid",
                        "error": "缺少必要属性"
                    })
            except Exception as e:
                validation_results["invalid_tools"] += 1
                validation_results["details"].append({
                    "name": getattr(tool, 'name', 'unknown'),
                    "status": "error",
                    "error": str(e)
                })
        
        return validation_results
    
    def refresh_context(self, context: ConversationContext):
        """
        刷新会话上下文
        
        Args:
            context: 新的会话上下文
        """
        if self._initialized:
            self._context = context
            # 重新设置各工具模块的上下文
            set_customer_context(self._adapter, context)
            set_product_context(self._adapter, context)
            set_order_context(self._adapter, context)


# 全局工具注册器实例
tool_registry = ToolRegistry()