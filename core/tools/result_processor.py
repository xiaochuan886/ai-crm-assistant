"""
工具结果处理器

格式化和美化工具执行结果，提供更好的用户体验
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json


class ToolResultProcessor:
    """工具结果处理器"""
    
    @staticmethod
    def format_customer_info(customer_data: Dict[str, Any]) -> str:
        """
        格式化客户信息
        
        Args:
            customer_data: 客户数据字典
            
        Returns:
            格式化的客户信息字符串
        """
        if not customer_data:
            return "客户信息为空"
        
        info_lines = ["📋 客户信息："]
        
        # 基本信息
        if customer_data.get('name'):
            info_lines.append(f"姓名：{customer_data['name']}")
        
        if customer_data.get('email'):
            info_lines.append(f"邮箱：{customer_data['email']}")
        
        if customer_data.get('phone'):
            info_lines.append(f"电话：{customer_data['phone']}")
        
        if customer_data.get('id'):
            info_lines.append(f"客户ID：{customer_data['id']}")
        
        # 地址信息
        if customer_data.get('street') or customer_data.get('city'):
            address_parts = []
            if customer_data.get('street'):
                address_parts.append(customer_data['street'])
            if customer_data.get('city'):
                address_parts.append(customer_data['city'])
            if customer_data.get('country'):
                address_parts.append(customer_data['country'])
            
            if address_parts:
                info_lines.append(f"地址：{', '.join(address_parts)}")
        
        # 其他信息
        if customer_data.get('company'):
            info_lines.append(f"公司：{customer_data['company']}")
        
        if customer_data.get('create_date'):
            info_lines.append(f"创建时间：{customer_data['create_date']}")
        
        return "\n".join(info_lines)
    
    @staticmethod
    def format_customer_list(customers: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
        """
        格式化客户列表
        
        Args:
            customers: 客户列表
            limit: 显示限制数量
            
        Returns:
            格式化的客户列表字符串
        """
        if not customers:
            return "未找到匹配的客户"
        
        display_customers = customers[:limit] if limit else customers
        
        result_lines = [f"🔍 找到 {len(customers)} 个客户："]
        
        for i, customer in enumerate(display_customers, 1):
            customer_line = f"{i}. "
            
            if customer.get('name'):
                customer_line += f"{customer['name']}"
            else:
                customer_line += "未知客户"
            
            details = []
            if customer.get('email'):
                details.append(f"邮箱: {customer['email']}")
            if customer.get('phone'):
                details.append(f"电话: {customer['phone']}")
            if customer.get('id'):
                details.append(f"ID: {customer['id']}")
            
            if details:
                customer_line += f" ({', '.join(details)})"
            
            result_lines.append(customer_line)
        
        if limit and len(customers) > limit:
            result_lines.append(f"... 还有 {len(customers) - limit} 个客户未显示")
        
        return "\n".join(result_lines)
    
    @staticmethod
    def format_product_info(product_data: Dict[str, Any]) -> str:
        """
        格式化商品信息
        
        Args:
            product_data: 商品数据字典
            
        Returns:
            格式化的商品信息字符串
        """
        if not product_data:
            return "商品信息为空"
        
        info_lines = ["📦 商品信息："]
        
        # 基本信息
        if product_data.get('name'):
            info_lines.append(f"商品名称：{product_data['name']}")
        
        if product_data.get('id'):
            info_lines.append(f"商品ID：{product_data['id']}")
        
        if product_data.get('default_code'):
            info_lines.append(f"商品编码：{product_data['default_code']}")
        
        # 价格信息
        if product_data.get('list_price') is not None:
            info_lines.append(f"销售价格：¥{product_data['list_price']}")
        
        if product_data.get('standard_price') is not None:
            info_lines.append(f"成本价格：¥{product_data['standard_price']}")
        
        # 库存信息
        if product_data.get('qty_available') is not None:
            info_lines.append(f"可用库存：{product_data['qty_available']}")
        
        if product_data.get('virtual_available') is not None:
            info_lines.append(f"预测库存：{product_data['virtual_available']}")
        
        # 分类信息
        if product_data.get('categ_id'):
            if isinstance(product_data['categ_id'], list) and len(product_data['categ_id']) > 1:
                info_lines.append(f"商品分类：{product_data['categ_id'][1]}")
            else:
                info_lines.append(f"分类ID：{product_data['categ_id']}")
        
        # 其他信息
        if product_data.get('sale_ok'):
            info_lines.append(f"可销售：{'是' if product_data['sale_ok'] else '否'}")
        
        if product_data.get('purchase_ok'):
            info_lines.append(f"可采购：{'是' if product_data['purchase_ok'] else '否'}")
        
        return "\n".join(info_lines)
    
    @staticmethod
    def format_product_list(products: List[Dict[str, Any]], limit: Optional[int] = None) -> str:
        """
        格式化商品列表
        
        Args:
            products: 商品列表
            limit: 显示限制数量
            
        Returns:
            格式化的商品列表字符串
        """
        if not products:
            return "未找到匹配的商品"
        
        display_products = products[:limit] if limit else products
        
        result_lines = [f"🛍️ 找到 {len(products)} 个商品："]
        
        for i, product in enumerate(display_products, 1):
            product_line = f"{i}. "
            
            if product.get('name'):
                product_line += f"{product['name']}"
            else:
                product_line += "未知商品"
            
            details = []
            if product.get('list_price') is not None:
                details.append(f"价格: ¥{product['list_price']}")
            if product.get('qty_available') is not None:
                details.append(f"库存: {product['qty_available']}")
            if product.get('id'):
                details.append(f"ID: {product['id']}")
            
            if details:
                product_line += f" ({', '.join(details)})"
            
            result_lines.append(product_line)
        
        if limit and len(products) > limit:
            result_lines.append(f"... 还有 {len(products) - limit} 个商品未显示")
        
        return "\n".join(result_lines)
    
    @staticmethod
    def format_order_summary(order_data: Dict[str, Any]) -> str:
        """
        格式化订单摘要
        
        Args:
            order_data: 订单数据字典
            
        Returns:
            格式化的订单摘要字符串
        """
        if not order_data:
            return "订单信息为空"
        
        info_lines = ["📋 订单摘要："]
        
        # 基本信息
        if order_data.get('id'):
            info_lines.append(f"订单ID：{order_data['id']}")
        
        if order_data.get('name'):
            info_lines.append(f"订单编号：{order_data['name']}")
        
        if order_data.get('partner_id'):
            if isinstance(order_data['partner_id'], list) and len(order_data['partner_id']) > 1:
                info_lines.append(f"客户：{order_data['partner_id'][1]}")
            else:
                info_lines.append(f"客户ID：{order_data['partner_id']}")
        
        # 金额信息
        if order_data.get('amount_total') is not None:
            info_lines.append(f"订单总额：¥{order_data['amount_total']}")
        
        if order_data.get('amount_untaxed') is not None:
            info_lines.append(f"未税金额：¥{order_data['amount_untaxed']}")
        
        if order_data.get('amount_tax') is not None:
            info_lines.append(f"税额：¥{order_data['amount_tax']}")
        
        # 状态信息
        if order_data.get('state'):
            state_map = {
                'draft': '草稿',
                'sent': '已发送',
                'sale': '销售订单',
                'done': '已完成',
                'cancel': '已取消'
            }
            state_text = state_map.get(order_data['state'], order_data['state'])
            info_lines.append(f"订单状态：{state_text}")
        
        # 时间信息
        if order_data.get('date_order'):
            info_lines.append(f"订单日期：{order_data['date_order']}")
        
        if order_data.get('create_date'):
            info_lines.append(f"创建时间：{order_data['create_date']}")
        
        # 备注信息
        if order_data.get('note'):
            info_lines.append(f"备注：{order_data['note']}")
        
        return "\n".join(info_lines)
    
    @staticmethod
    def format_operation_result(result: Any, operation_type: str = "操作") -> str:
        """
        格式化操作结果
        
        Args:
            result: 操作结果
            operation_type: 操作类型描述
            
        Returns:
            格式化的结果字符串
        """
        if hasattr(result, 'success'):
            # OperationResult 类型
            if result.success:
                status_icon = "✅"
                status_text = f"{operation_type}成功"
                
                if result.data:
                    if isinstance(result.data, dict):
                        if 'id' in result.data:
                            status_text += f"（ID: {result.data['id']}）"
                    elif isinstance(result.data, list):
                        status_text += f"（返回 {len(result.data)} 条记录）"
                
                if result.message:
                    status_text += f"\n详情：{result.message}"
                
                return f"{status_icon} {status_text}"
            else:
                status_icon = "❌"
                status_text = f"{operation_type}失败"
                
                if result.message:
                    status_text += f"\n错误：{result.message}"
                
                return f"{status_icon} {status_text}"
        else:
            # 其他类型的结果
            return f"📋 {operation_type}结果：{str(result)}"
    
    @staticmethod
    def format_error(error: Exception, context: str = "") -> str:
        """
        格式化错误信息
        
        Args:
            error: 异常对象
            context: 错误上下文
            
        Returns:
            格式化的错误信息
        """
        error_lines = ["❌ 操作失败"]
        
        if context:
            error_lines.append(f"上下文：{context}")
        
        error_lines.append(f"错误类型：{type(error).__name__}")
        error_lines.append(f"错误详情：{str(error)}")
        
        return "\n".join(error_lines)
    
    @staticmethod
    def format_json_data(data: Any, title: str = "数据") -> str:
        """
        格式化JSON数据
        
        Args:
            data: 要格式化的数据
            title: 数据标题
            
        Returns:
            格式化的JSON字符串
        """
        try:
            formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
            return f"📄 {title}：\n```json\n{formatted_json}\n```"
        except (TypeError, ValueError) as e:
            return f"❌ 无法格式化{title}：{str(e)}"