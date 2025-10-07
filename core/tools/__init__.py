"""
CRM智能体工具模块

基于LangChain框架的业务工具集合，支持：
- 客户管理工具
- 订单处理工具  
- 商品查询工具
- 工具注册与管理
"""

from .customer_tools import *
from .order_tools import *
from .product_tools import *
from .tool_registry import ToolRegistry

__all__ = [
    'ToolRegistry',
    # 客户管理工具将在customer_tools.py中定义
    # 订单管理工具将在order_tools.py中定义
    # 商品管理工具将在product_tools.py中定义
]