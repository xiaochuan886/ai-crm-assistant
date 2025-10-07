"""
模拟CRM适配器 - 用于测试和开发
"""

from typing import Dict, Any, List, Optional

class MockCrmAdapter:
    """模拟CRM适配器，返回测试数据"""

    def __init__(self):
        self.customers = []
        self.products = []
        self.orders = []
        self._init_mock_data()

    def _init_mock_data(self):
        """初始化模拟数据"""
        # 模拟客户数据
        self.customers = [
            {
                "id": "mock_customer_1",
                "name": "张三",
                "email": "zhangsan@example.com",
                "phone": "13800138000",
                "company": "测试公司A"
            },
            {
                "id": "mock_customer_2",
                "name": "李四",
                "email": "lisi@example.com",
                "phone": "13800138001",
                "company": "测试公司B"
            }
        ]

        # 模拟产品数据
        self.products = [
            {
                "id": "mock_product_1",
                "name": "企业版软件",
                "price": 9999.00,
                "description": "企业级软件解决方案"
            },
            {
                "id": "mock_product_2",
                "name": "专业服务",
                "price": 2999.00,
                "description": "专业技术咨询服务"
            }
        ]

    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建客户"""
        customer = {
            "id": f"mock_customer_{len(self.customers) + 1}",
            **customer_data,
            "created_at": "2024-01-01T00:00:00Z"
        }
        self.customers.append(customer)

        return {
            "success": True,
            "customer_id": customer["id"],
            "message": f"客户 {customer.get('name', '')} 创建成功",
            "customer": customer
        }

    async def search_customers(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索客户"""
        if not query:
            return self.customers  # Return all customers if no query

        query_lower = query.lower()
        results = []

        for customer in self.customers:
            if (query_lower in (customer.get('name') or '').lower() or
                query_lower in (customer.get('email') or '').lower() or
                query_lower in (customer.get('company') or '').lower()):
                results.append(customer)

        return results

    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """获取客户详情"""
        for customer in self.customers:
            if customer["id"] == customer_id:
                return {
                    "success": True,
                    "customer": customer
                }

        return {
            "success": False,
            "error": "客户未找到"
        }

    async def update_customer(self, customer_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新客户信息"""
        for i, customer in enumerate(self.customers):
            if customer["id"] == customer_id:
                self.customers[i].update(update_data)
                return {
                    "success": True,
                    "message": "客户信息更新成功",
                    "customer": self.customers[i]
                }

        return {
            "success": False,
            "error": "客户未找到"
        }

    async def delete_customer(self, customer_id: str) -> Dict[str, Any]:
        """删除客户"""
        for i, customer in enumerate(self.customers):
            if customer["id"] == customer_id:
                deleted_customer = self.customers.pop(i)
                return {
                    "success": True,
                    "message": f"客户 {deleted_customer.get('name', '')} 删除成功"
                }

        return {
            "success": False,
            "error": "客户未找到"
        }

    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建产品"""
        product = {
            "id": f"mock_product_{len(self.products) + 1}",
            **product_data,
            "created_at": "2024-01-01T00:00:00Z"
        }
        self.products.append(product)

        return {
            "success": True,
            "product_id": product["id"],
            "message": f"产品 {product.get('name', '')} 创建成功",
            "product": product
        }

    async def search_products(self, query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """搜索产品"""
        query_lower = query.lower()
        results = []

        for product in self.products:
            if (query_lower in product.get('name', '').lower() or
                query_lower in product.get('description', '').lower()):
                results.append(product)

        return results

    async def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建订单"""
        order = {
            "id": f"mock_order_{len(self.orders) + 1}",
            **order_data,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        self.orders.append(order)

        return {
            "success": True,
            "order_id": order["id"],
            "message": f"订单 {order['id']} 创建成功",
            "order": order
        }

    async def get_orders(self, customer_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """获取订单列表"""
        results = self.orders

        if customer_id:
            results = [order for order in results if order.get('customer_id') == customer_id]

        if status:
            results = [order for order in results if order.get('status') == status]

        return results

    async def get_adapter_info(self) -> Dict[str, Any]:
        """获取适配器信息"""
        return {
            "name": "Mock CRM Adapter",
            "version": "1.0.0",
            "description": "模拟CRM适配器，用于测试和开发",
            "capabilities": [
                "create_customer",
                "search_customers",
                "get_customer",
                "update_customer",
                "delete_customer",
                "create_product",
                "search_products",
                "create_order",
                "get_orders"
            ]
        }

    async def test_connection(self) -> Dict[str, Any]:
        """测试连接"""
        return {
            "success": True,
            "message": "Mock适配器连接成功",
            "timestamp": "2024-01-01T00:00:00Z"
        }