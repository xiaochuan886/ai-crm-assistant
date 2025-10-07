"""
商品管理工具集

基于LangChain的商品查询业务工具，支持搜索商品、查看商品详情
"""

from typing import Optional, List, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from adapters.base_adapter import BaseAdapter


class ProductSearchResult(BaseModel):
    """商品搜索结果"""
    products: List[Dict[str, Any]]
    total_count: int
    message: str


# 全局变量，将在工具注册时设置
_adapter: Optional[BaseAdapter] = None


def set_adapter(adapter: BaseAdapter):
    """设置适配器"""
    global _adapter
    _adapter = adapter


@tool
def search_products(
    query: str,
    category: Optional[str] = None,
    limit: int = Field(default=10, description="搜索结果数量限制，默认10条")
) -> str:
    """
    搜索商品
    
    支持按商品名称、描述进行模糊搜索，可选择按分类筛选
    
    Args:
        query: 搜索关键词（商品名称或描述）
        category: 商品分类（可选）
        limit: 返回结果数量限制
        
    Returns:
        搜索结果的格式化描述
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        # 构建搜索参数
        search_params = {"query": query, "limit": limit}
        if category:
            search_params["category"] = category
            
        result = _adapter.search_products(**search_params)
        
        if result.success and result.data:
            products = result.data
            if not products:
                category_text = f"分类'{category}'中" if category else ""
                return f"未找到{category_text}包含'{query}'的商品"
            
            # 格式化搜索结果
            result_lines = [f"找到 {len(products)} 个商品："]
            for i, product in enumerate(products, 1):
                product_info = f"{i}. {product.get('name', '未知商品')}"
                if product.get('list_price'):
                    product_info += f" - ¥{product['list_price']}"
                if product.get('categ_id'):
                    # 如果有分类信息，显示分类
                    categ_name = product['categ_id']
                    if isinstance(categ_name, list) and len(categ_name) > 1:
                        categ_name = categ_name[1]  # Odoo返回格式 [id, name]
                    product_info += f" ({categ_name})"
                product_info += f" [ID: {product.get('id', '未知')}]"
                result_lines.append(product_info)
                
            return "\n".join(result_lines)
        else:
            return f"搜索商品失败：{result.message}"
            
    except Exception as e:
        return f"搜索商品时发生错误：{str(e)}"


@tool
def get_product_details(product_id: int) -> str:
    """
    获取商品详细信息
    
    Args:
        product_id: 商品ID
        
    Returns:
        商品详细信息的格式化描述
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        # 注意：base_adapter中没有get_product方法，我们通过search_products实现
        # 这里假设适配器支持按ID精确搜索
        result = _adapter.search_products(query="", limit=1, product_id=product_id)
        
        if result.success and result.data and len(result.data) > 0:
            product = result.data[0]
            
            # 格式化商品信息
            info_lines = [f"商品详细信息："]
            info_lines.append(f"名称：{product.get('name', '未知')}")
            info_lines.append(f"ID：{product.get('id', product_id)}")
            
            if product.get('list_price'):
                info_lines.append(f"价格：¥{product['list_price']}")
            if product.get('standard_price'):
                info_lines.append(f"成本价：¥{product['standard_price']}")
            if product.get('categ_id'):
                categ_name = product['categ_id']
                if isinstance(categ_name, list) and len(categ_name) > 1:
                    categ_name = categ_name[1]
                info_lines.append(f"分类：{categ_name}")
            if product.get('description'):
                info_lines.append(f"描述：{product['description']}")
            if product.get('qty_available') is not None:
                info_lines.append(f"库存数量：{product['qty_available']}")
            if product.get('uom_id'):
                uom_name = product['uom_id']
                if isinstance(uom_name, list) and len(uom_name) > 1:
                    uom_name = uom_name[1]
                info_lines.append(f"计量单位：{uom_name}")
                
            return "\n".join(info_lines)
        else:
            return f"未找到ID为 {product_id} 的商品"
            
    except Exception as e:
        return f"获取商品信息时发生错误：{str(e)}"


@tool
def get_product_price(product_id: int) -> str:
    """
    获取商品价格信息
    
    Args:
        product_id: 商品ID
        
    Returns:
        商品价格信息
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        result = _adapter.search_products(query="", limit=1, product_id=product_id)
        
        if result.success and result.data and len(result.data) > 0:
            product = result.data[0]
            
            price_info = f"商品 {product.get('name', '未知商品')} 的价格信息：\n"
            if product.get('list_price'):
                price_info += f"销售价：¥{product['list_price']}\n"
            if product.get('standard_price'):
                price_info += f"成本价：¥{product['standard_price']}\n"
            
            return price_info.strip()
        else:
            return f"未找到ID为 {product_id} 的商品价格信息"
            
    except Exception as e:
        return f"获取商品价格时发生错误：{str(e)}"


@tool
def check_product_stock(product_id: int) -> str:
    """
    检查商品库存
    
    Args:
        product_id: 商品ID
        
    Returns:
        商品库存信息
    """
    if not _adapter:
        return "错误：系统未正确初始化"
    
    try:
        result = _adapter.search_products(query="", limit=1, product_id=product_id)
        
        if result.success and result.data and len(result.data) > 0:
            product = result.data[0]
            
            stock_info = f"商品 {product.get('name', '未知商品')} 的库存信息：\n"
            if product.get('qty_available') is not None:
                qty = product['qty_available']
                stock_info += f"可用库存：{qty}"
                if qty <= 0:
                    stock_info += " (缺货)"
                elif qty < 10:
                    stock_info += " (库存较低)"
            else:
                stock_info += "库存信息不可用"
            
            return stock_info
        else:
            return f"未找到ID为 {product_id} 的商品库存信息"
            
    except Exception as e:
        return f"检查商品库存时发生错误：{str(e)}"


# 导出所有工具
PRODUCT_TOOLS = [
    search_products,
    get_product_details,
    get_product_price,
    check_product_stock
]