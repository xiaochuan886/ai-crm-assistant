"""
订单管理工具集

基于LangChain的订单处理业务工具，支持创建订单、计算总价、验证订单数据
"""

from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..agent import ConversationContext
from adapters.base_adapter import BaseAdapter


class OrderItem(BaseModel):
    """订单项"""
    product_id: int
    quantity: int
    unit_price: Optional[float] = None


class OrderCalculation(BaseModel):
    """订单计算结果"""
    subtotal: float
    tax: float
    total: float
    items: List[Dict[str, Any]]


# 全局变量，将在工具注册时设置
_adapter: Optional[BaseAdapter] = None
_context: Optional[ConversationContext] = None


def set_adapter_and_context(adapter: BaseAdapter, context: ConversationContext):
    """设置适配器和上下文"""
    global _adapter, _context
    _adapter = adapter
    _context = context


@tool
def create_order(
    customer_id: Optional[int] = None,
    products: str = Field(description="商品列表，格式：'商品ID:数量,商品ID:数量' 例如：'1:2,3:1'"),
    notes: Optional[str] = None
) -> str:
    """
    创建订单
    
    Args:
        customer_id: 客户ID（可选，未指定时使用当前活跃客户）
        products: 商品列表，格式：'商品ID:数量,商品ID:数量'，例如：'1:2,3:1'
        notes: 订单备注
        
    Returns:
        订单创建结果的描述信息
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    # 确定客户ID
    target_customer_id = customer_id
    if not target_customer_id and _context:
        target_customer_id = _context.active_customer_id
        
    if not target_customer_id:
        return "错误：未指定客户ID，且当前会话中没有活跃客户。请先搜索或创建客户。"
    
    try:
        # 解析商品列表
        product_list = []
        if products:
            for item in products.split(','):
                if ':' in item:
                    product_id_str, quantity_str = item.strip().split(':', 1)
                    try:
                        product_id = int(product_id_str.strip())
                        quantity = int(quantity_str.strip())
                        if quantity > 0:
                            product_list.append({
                                "product_id": product_id,
                                "quantity": quantity
                            })
                    except ValueError:
                        return f"错误：商品格式不正确 '{item}'，应为 '商品ID:数量'"
        
        if not product_list:
            return "错误：未提供有效的商品列表"
        
        # 构建订单数据
        order_data = {
            "customer_id": target_customer_id,
            "products": product_list
        }
        if notes:
            order_data["notes"] = notes
            
        # 创建订单
        result = _adapter.create_order(order_data)
        
        if result.success:
            order_info = f"成功创建订单！\n"
            order_info += f"订单ID：{result.data.get('id', '未知')}\n"
            order_info += f"客户ID：{target_customer_id}\n"
            order_info += f"商品数量：{len(product_list)} 种\n"
            if result.data.get('total'):
                order_info += f"订单总额：¥{result.data['total']}"
            return order_info
        else:
            return f"创建订单失败：{result.message}"
            
    except Exception as e:
        return f"创建订单时发生错误：{str(e)}"


@tool
def calculate_order_total(
    products: str = Field(description="商品列表，格式：'商品ID:数量,商品ID:数量' 例如：'1:2,3:1'")
) -> str:
    """
    计算订单总价
    
    在创建订单前预估价格
    
    Args:
        products: 商品列表，格式：'商品ID:数量,商品ID:数量'，例如：'1:2,3:1'
        
    Returns:
        订单价格计算结果
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        # 解析商品列表
        product_list = []
        if products:
            for item in products.split(','):
                if ':' in item:
                    product_id_str, quantity_str = item.strip().split(':', 1)
                    try:
                        product_id = int(product_id_str.strip())
                        quantity = int(quantity_str.strip())
                        if quantity > 0:
                            product_list.append({
                                "product_id": product_id,
                                "quantity": quantity
                            })
                    except ValueError:
                        return f"错误：商品格式不正确 '{item}'，应为 '商品ID:数量'"
        
        if not product_list:
            return "错误：未提供有效的商品列表"
        
        # 获取商品价格并计算总价
        total_amount = 0.0
        calculation_details = ["订单价格计算："]
        
        for item in product_list:
            product_id = item["product_id"]
            quantity = item["quantity"]
            
            # 搜索商品获取价格
            product_result = _adapter.search_products(query="", limit=1, product_id=product_id)
            
            if product_result.success and product_result.data and len(product_result.data) > 0:
                product = product_result.data[0]
                unit_price = product.get('list_price', 0.0)
                line_total = unit_price * quantity
                total_amount += line_total
                
                calculation_details.append(
                    f"- {product.get('name', f'商品{product_id}')}：¥{unit_price} × {quantity} = ¥{line_total}"
                )
            else:
                calculation_details.append(f"- 商品ID {product_id}：价格信息不可用")
        
        calculation_details.append(f"\n订单总计：¥{total_amount}")
        
        return "\n".join(calculation_details)
        
    except Exception as e:
        return f"计算订单总价时发生错误：{str(e)}"


@tool
def validate_order_data(
    customer_id: Optional[int] = None,
    products: str = Field(description="商品列表，格式：'商品ID:数量,商品ID:数量' 例如：'1:2,3:1'")
) -> str:
    """
    验证订单数据有效性
    
    检查客户是否存在、商品是否存在、库存是否充足等
    
    Args:
        customer_id: 客户ID（可选，未指定时使用当前活跃客户）
        products: 商品列表，格式：'商品ID:数量,商品ID:数量'
        
    Returns:
        验证结果的详细描述
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    # 确定客户ID
    target_customer_id = customer_id
    if not target_customer_id and _context:
        target_customer_id = _context.active_customer_id
        
    if not target_customer_id:
        return "错误：未指定客户ID，且当前会话中没有活跃客户"
    
    try:
        validation_results = ["订单数据验证结果："]
        is_valid = True
        
        # 验证客户
        customer_result = _adapter.get_customer(target_customer_id)
        if customer_result.success and customer_result.data:
            validation_results.append(f"✓ 客户验证通过：{customer_result.data.get('name', '未知客户')}")
        else:
            validation_results.append(f"✗ 客户验证失败：客户ID {target_customer_id} 不存在")
            is_valid = False
        
        # 解析并验证商品
        product_list = []
        if products:
            for item in products.split(','):
                if ':' in item:
                    product_id_str, quantity_str = item.strip().split(':', 1)
                    try:
                        product_id = int(product_id_str.strip())
                        quantity = int(quantity_str.strip())
                        if quantity > 0:
                            product_list.append({
                                "product_id": product_id,
                                "quantity": quantity
                            })
                    except ValueError:
                        validation_results.append(f"✗ 商品格式错误：'{item}' 应为 '商品ID:数量'")
                        is_valid = False
        
        if not product_list:
            validation_results.append("✗ 未提供有效的商品列表")
            is_valid = False
        else:
            validation_results.append(f"\n商品验证（共 {len(product_list)} 种商品）：")
            
            for item in product_list:
                product_id = item["product_id"]
                quantity = item["quantity"]
                
                # 验证商品存在性
                product_result = _adapter.search_products(query="", limit=1, product_id=product_id)
                
                if product_result.success and product_result.data and len(product_result.data) > 0:
                    product = product_result.data[0]
                    product_name = product.get('name', f'商品{product_id}')
                    
                    # 检查库存
                    available_qty = product.get('qty_available')
                    if available_qty is not None:
                        if available_qty >= quantity:
                            validation_results.append(f"✓ {product_name}：需要 {quantity}，库存 {available_qty}")
                        else:
                            validation_results.append(f"✗ {product_name}：需要 {quantity}，库存不足（仅 {available_qty}）")
                            is_valid = False
                    else:
                        validation_results.append(f"? {product_name}：库存信息不可用")
                else:
                    validation_results.append(f"✗ 商品ID {product_id}：商品不存在")
                    is_valid = False
        
        # 总结
        validation_results.append(f"\n验证结果：{'通过' if is_valid else '失败'}")
        if is_valid:
            validation_results.append("订单数据有效，可以创建订单")
        else:
            validation_results.append("订单数据存在问题，请修正后重试")
        
        return "\n".join(validation_results)
        
    except Exception as e:
        return f"验证订单数据时发生错误：{str(e)}"


@tool
def get_order_template() -> str:
    """
    获取订单创建模板和示例
    
    Returns:
        订单创建的格式说明和示例
    """
    template = """订单创建格式说明：

1. 商品列表格式：'商品ID:数量,商品ID:数量'
   示例：'1:2,3:1' 表示商品1购买2个，商品3购买1个

2. 创建订单步骤：
   - 步骤1：搜索或确认客户
   - 步骤2：搜索商品获取商品ID
   - 步骤3：验证订单数据
   - 步骤4：创建订单

3. 示例流程：
   - 搜索客户："张三"
   - 搜索商品："笔记本电脑"
   - 验证订单：客户ID=1，商品="1:1"
   - 创建订单：客户ID=1，商品="1:1"

4. 注意事项：
   - 确保商品ID正确
   - 检查库存是否充足
   - 数量必须为正整数"""
   
    return template


# 导出所有工具
ORDER_TOOLS = [
    create_order,
    calculate_order_total,
    validate_order_data,
    get_order_template
]