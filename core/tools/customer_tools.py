"""
客户管理工具集

基于LangChain的客户管理业务工具，支持创建、搜索、查看、更新客户信息
"""

from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..agent import ConversationContext
from adapters.base_adapter import BaseAdapter


class CustomerSearchResult(BaseModel):
    """客户搜索结果"""
    customers: List[Dict[str, Any]]
    total_count: int
    message: str


class CustomerOperationResult(BaseModel):
    """客户操作结果"""
    success: bool
    customer_id: Optional[int] = None
    customer_data: Optional[Dict[str, Any]] = None
    message: str


# 全局变量，将在工具注册时设置
_adapter: Optional[BaseAdapter] = None
_context: Optional[ConversationContext] = None


def set_adapter_and_context(adapter: BaseAdapter, context: ConversationContext):
    """设置适配器和上下文"""
    global _adapter, _context
    _adapter = adapter
    _context = context


@tool
def create_customer(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company_name: Optional[str] = None,
    street: Optional[str] = None
) -> str:
    """
    创建新客户
    
    Args:
        name: 客户姓名（必填）
        email: 邮箱地址
        phone: 电话号码
        company_name: 公司名称
        street: 地址
        
    Returns:
        创建结果的描述信息
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        # 构建客户数据
        customer_data = {"name": name}
        if email:
            customer_data["email"] = email
        if phone:
            customer_data["phone"] = phone
        if company_name:
            customer_data["company_name"] = company_name
        if street:
            customer_data["street"] = street
            
        # 创建客户
        result = _adapter.create_customer(customer_data)
        
        if result.success:
            # 更新当前活跃客户
            if _context and result.data and "id" in result.data:
                _context.update_active_customer(
                    result.data["id"], 
                    result.data.get("name", name)
                )
            return f"成功创建客户：{name}，客户ID：{result.data.get('id', '未知')}"
        else:
            return f"创建客户失败：{result.message}"
            
    except Exception as e:
        return f"创建客户时发生错误：{str(e)}"


@tool
def search_customers(
    query: str,
    limit: int = Field(default=10, description="搜索结果数量限制，默认10条")
) -> str:
    """
    搜索客户
    
    支持按姓名、邮箱、电话进行模糊搜索
    
    Args:
        query: 搜索关键词（姓名、邮箱或电话）
        limit: 返回结果数量限制
        
    Returns:
        搜索结果的格式化描述
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        result = _adapter.search_customers(query, limit)
        
        if result.success and result.data:
            customers = result.data
            if not customers:
                return f"未找到包含'{query}'的客户"
            
            # 格式化搜索结果
            result_lines = [f"找到 {len(customers)} 位客户："]
            for i, customer in enumerate(customers, 1):
                customer_info = f"{i}. {customer.get('name', '未知姓名')}"
                if customer.get('email'):
                    customer_info += f" ({customer['email']})"
                if customer.get('phone'):
                    customer_info += f" - {customer['phone']}"
                customer_info += f" [ID: {customer.get('id', '未知')}]"
                result_lines.append(customer_info)
                
            return "\n".join(result_lines)
        else:
            return f"搜索客户失败：{result.message}"
            
    except Exception as e:
        return f"搜索客户时发生错误：{str(e)}"


@tool
def get_customer_details(customer_id: int) -> str:
    """
    获取客户详细信息
    
    Args:
        customer_id: 客户ID
        
    Returns:
        客户详细信息的格式化描述
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        result = _adapter.get_customer(customer_id)
        
        if result.success and result.data:
            customer = result.data
            
            # 更新当前活跃客户
            if _context:
                _context.update_active_customer(
                    customer_id, 
                    customer.get("name", "未知客户")
                )
            
            # 格式化客户信息
            info_lines = [f"客户详细信息："]
            info_lines.append(f"姓名：{customer.get('name', '未知')}")
            info_lines.append(f"ID：{customer.get('id', customer_id)}")
            
            if customer.get('email'):
                info_lines.append(f"邮箱：{customer['email']}")
            if customer.get('phone'):
                info_lines.append(f"电话：{customer['phone']}")
            if customer.get('company_name'):
                info_lines.append(f"公司：{customer['company_name']}")
            if customer.get('street'):
                info_lines.append(f"地址：{customer['street']}")
                
            return "\n".join(info_lines)
        else:
            return f"获取客户信息失败：{result.message}"
            
    except Exception as e:
        return f"获取客户信息时发生错误：{str(e)}"


@tool
def update_customer(
    customer_id: Optional[int] = None,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company_name: Optional[str] = None,
    street: Optional[str] = None
) -> str:
    """
    更新客户信息
    
    如果未指定customer_id，将使用当前会话中的活跃客户
    
    Args:
        customer_id: 客户ID（可选，未指定时使用当前活跃客户）
        name: 新的姓名
        email: 新的邮箱
        phone: 新的电话
        company_name: 新的公司名称
        street: 新的地址
        
    Returns:
        更新结果的描述信息
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    # 确定要更新的客户ID
    target_customer_id = customer_id
    if not target_customer_id and _context:
        target_customer_id = _context.active_customer_id
        
    if not target_customer_id:
        return "错误：未指定客户ID，且当前会话中没有活跃客户"
    
    try:
        # 构建更新数据
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if email is not None:
            update_data["email"] = email
        if phone is not None:
            update_data["phone"] = phone
        if company_name is not None:
            update_data["company_name"] = company_name
        if street is not None:
            update_data["street"] = street
            
        if not update_data:
            return "错误：未提供任何要更新的字段"
        
        # 执行更新
        result = _adapter.update_customer(target_customer_id, update_data)
        
        if result.success:
            # 更新上下文中的客户名称
            if _context and name:
                _context.update_active_customer(target_customer_id, name)
                
            updated_fields = ", ".join(update_data.keys())
            return f"成功更新客户 {target_customer_id} 的信息：{updated_fields}"
        else:
            return f"更新客户信息失败：{result.message}"
            
    except Exception as e:
        return f"更新客户信息时发生错误：{str(e)}"


@tool
def get_current_customer() -> str:
    """
    获取当前会话中的活跃客户信息
    
    Returns:
        当前活跃客户的信息，如果没有则返回提示
    """
    if not _context:
        return "错误：系统未正确初始化"
        
    if not _context.active_customer_id:
        return "当前会话中没有活跃的客户"
        
    return f"当前活跃客户：{_context.active_customer_name} (ID: {_context.active_customer_id})"


# 导出所有工具
CUSTOMER_TOOLS = [
    create_customer,
    search_customers,
    get_customer_details,
    update_customer,
    get_current_customer
]