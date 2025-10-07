# -*- coding: utf-8 -*-
"""
Odoo CRM Adapter

This module implements the Odoo-specific adapter that translates standard CRM operations
into Odoo API calls using JSON-RPC interface.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from adapters.base_adapter import (
    BaseCrmAdapter, CustomerData, ProductData, OrderData, OperationResult,
    AdapterError, ConnectionError, ValidationError, AuthenticationError
)


logger = logging.getLogger(__name__)


class OdooAdapter(BaseCrmAdapter):
    """
    Odoo CRM Adapter

    Implements the standard CRM interface for Odoo using JSON-RPC API.
    """

    VERSION = "1.1.0"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Odoo adapter

        Args:
            config: Dictionary containing:
                - url: Odoo instance URL
                - db: Database name
                - username: Username
                - password: Password
                - uid: User ID (optional, will be obtained via login)
        """
        super().__init__(config)
        self.base_url = config['url'].rstrip('/')
        self.db = config['db']
        self.username = config.get('username')
        self.password = config.get('password')
        self.api_key = config.get('api_key')
        self.uid = None
        self.session = requests.Session()

        # For JSON-2 API (api_key), login is not required. Fallback to legacy login when no api_key.
        if not self.api_key:
            # Login to get session ID and user ID
            self._login()

    def _validate_config(self) -> None:
        """Validate Odoo-specific configuration"""
        # Require base URL and database name
        for field in ['url', 'db']:
            if not self.config.get(field):
                raise ValidationError(f"Missing required Odoo config field: {field}")

        # Either api_key (JSON-2) or username+password (legacy) must be provided
        has_api_key = bool(self.config.get('api_key'))
        has_userpass = bool(self.config.get('username')) and bool(self.config.get('password'))
        if not (has_api_key or has_userpass):
            raise ValidationError("Missing authentication: provide api_key or username+password")

    def _login(self) -> None:
        """Authenticate with Odoo and get user ID"""
        try:
            login_url = urljoin(self.base_url, '/web/session/authenticate')

            login_data = {
                'jsonrpc': '2.0',
                'method': 'call',
                'params': {
                    'db': self.db,
                    'login': self.username,
                    'password': self.password,
                },
                'id': 1
            }

            response = self.session.post(login_url, json=login_data, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get('error'):
                raise AuthenticationError(f"Odoo authentication failed: {result['error']}")

            if not result.get('result', {}).get('uid'):
                raise AuthenticationError("Odoo authentication failed: No user ID returned")

            self.uid = result['result']['uid']
            logger.info(f"Successfully authenticated with Odoo as user {self.uid}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Odoo: {str(e)}")

    def _execute_odoo_method(self,
                           model: str,
                           method: str,
                           domain: Optional[List] = None,
                           fields: Optional[List] = None,
                           context: Optional[Dict] = None,
                           **kwargs) -> Any:
        """
        Execute Odoo model method. Prefer JSON-2 API when api_key is provided;
        otherwise fall back to legacy JSON-RPC.
        """
        try:
            if self.api_key:
                # JSON-2 API
                url = urljoin(self.base_url + '/', f"json/2/{model}/{method}")
                headers = {
                    'Authorization': f"Bearer {self.api_key}",
                    'X-Odoo-Database': self.db,
                    'Content-Type': 'application/json'
                }

                payload: Dict[str, Any] = {}
                if context:
                    payload['context'] = context

                if method in ['search_read', 'search_count']:
                    payload['domain'] = domain or []
                    if method == 'search_read':
                        if fields is not None:
                            payload['fields'] = fields
                        for opt in ['limit', 'offset', 'order']:
                            if opt in kwargs and kwargs[opt] is not None:
                                payload[opt] = kwargs[opt]
                elif method == 'read':
                    ids = kwargs.get('ids') or ([kwargs.get('id')] if kwargs.get('id') is not None else [])
                    payload['ids'] = ids
                    if fields is not None:
                        payload['fields'] = fields
                elif method == 'write':
                    ids = kwargs.get('ids') or ([kwargs.get('id')] if kwargs.get('id') is not None else [])
                    payload['ids'] = ids
                    payload['vals'] = kwargs.get('vals', {})
                elif method == 'create':
                    payload['vals'] = kwargs.get('vals', {})
                else:
                    payload.update(kwargs)

                response = self.session.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                if isinstance(data, dict) and data.get('error'):
                    raise AdapterError(f"Odoo method {method} failed: {data['error']}")
                return data
            else:
                # Legacy JSON-RPC
                rpc_url = urljoin(self.base_url, '/web/dataset/call_kw')
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [domain] if domain is not None else [],
                        'kwargs': {
                            **kwargs,
                            'context': context or {}
                        }
                    },
                    'id': 1
                }
                if fields:
                    rpc_data['params']['kwargs']['fields'] = fields

                response = self.session.post(rpc_url, json=rpc_data, timeout=30)
                response.raise_for_status()
                result = response.json()
                if result.get('error'):
                    raise AdapterError(f"Odoo RPC error: {result['error']}")
                return result.get('result')
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Odoo request failed: {str(e)}")

    # === Base Adapter Implementation ===

    def test_connection(self) -> OperationResult:
        """Test connection to Odoo"""
        try:
            # Try to read current user info
            user_info = self._execute_odoo_method(
                model='res.users',
                method='read',
                ids=[self.uid] if self.uid is not None else [],
                fields=['name', 'login', 'company_id']
            )

            if user_info:
                return OperationResult(
                    success=True,
                    message=f"Successfully connected to Odoo as user {user_info[0]['name']}",
                    data={
                        'user_info': user_info[0],
                        'odoo_url': self.base_url,
                        'database': self.db
                    }
                )
            else:
                return OperationResult(
                    success=False,
                    message="Failed to retrieve user information from Odoo",
                    error_code="USER_NOT_FOUND"
                )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Odoo connection test failed: {str(e)}",
                error_code="CONNECTION_FAILED",
                error_details=str(e)
            )

    # === Customer Operations ===

    def create_customer(self, customer: CustomerData) -> OperationResult:
        """Create a new customer in Odoo"""
        try:
            # Prepare customer data for Odoo
            customer_data = {
                'name': customer.name,
                'is_company': False,
                'customer_rank': 1,
            }

            # Add optional fields if provided
            if customer.email:
                customer_data['email'] = customer.email
            if customer.phone:
                customer_data['phone'] = customer.phone
            if customer.company:
                # For company name, we set is_company=True for the company record
                # and link the contact to it
                customer_data['company_name'] = customer.company
            if customer.address:
                customer_data['street'] = customer.address
            if customer.notes:
                customer_data['comment'] = customer.notes

            # Create the customer
            customer_id = self._execute_odoo_method(
                model='res.partner',
                method='create',
                vals=customer_data
            )

            # Retrieve the created customer record
            created_customer = self._execute_odoo_method(
                model='res.partner',
                method='read',
                ids=[customer_id],
                fields=['name', 'email', 'phone', 'company_name', 'street', 'comment']
            )

            return OperationResult(
                success=True,
                message=f"Successfully created customer: {customer.name}",
                data={
                    'customer_id': customer_id,
                    'customer': created_customer[0] if created_customer else None
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to create customer: {str(e)}",
                error_code="CREATE_CUSTOMER_FAILED",
                error_details=str(e)
            )

    def search_customers(self,
                        name: Optional[str] = None,
                        email: Optional[str] = None,
                        phone: Optional[str] = None,
                        company: Optional[str] = None,
                        limit: int = 10) -> OperationResult:
        """Search for customers in Odoo"""
        try:
            # Build search domain
            domain = [
                ['customer_rank', '>', 0],  # Only customers
                ['active', '=', True]
            ]

            if name:
                domain.append(['name', 'ilike', name])
            if email:
                domain.append(['email', 'ilike', email])
            if phone:
                domain.append(['phone', 'ilike', phone])
            if company:
                domain.append(['company_name', 'ilike', company])

            # Search customers
            customers = self._execute_odoo_method(
                model='res.partner',
                method='search_read',
                domain=domain,
                fields=['name', 'email', 'phone', 'company_name', 'street', 'comment'],
                limit=limit
            )

            # Format results
            formatted_customers = []
            for customer in customers:
                formatted_customers.append({
                    'id': customer['id'],
                    'name': customer['name'],
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'company': customer.get('company_name'),
                    'address': customer.get('street'),
                    'notes': customer.get('comment')
                })

            return OperationResult(
                success=True,
                message=f"Found {len(formatted_customers)} matching customers",
                data={
                    'customers': formatted_customers,
                    'total_count': len(formatted_customers)
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to search customers: {str(e)}",
                error_code="SEARCH_CUSTOMERS_FAILED",
                error_details=str(e)
            )

    def get_customer(self, customer_id: str) -> OperationResult:
        """Get customer details by ID"""
        try:
            customers = self._execute_odoo_method(
                model='res.partner',
                method='read',
                ids=[int(customer_id)],
                fields=['name', 'email', 'phone', 'company_name', 'street', 'comment', 'customer_rank']
            )

            if not customers:
                return OperationResult(
                    success=False,
                    message=f"Customer with ID {customer_id} not found",
                    error_code="CUSTOMER_NOT_FOUND"
                )

            customer = customers[0]
            formatted_customer = {
                'id': customer['id'],
                'name': customer['name'],
                'email': customer.get('email'),
                'phone': customer.get('phone'),
                'company': customer.get('company_name'),
                'address': customer.get('street'),
                'notes': customer.get('comment'),
                'customer_rank': customer.get('customer_rank')
            }

            return OperationResult(
                success=True,
                message=f"Retrieved customer: {customer['name']}",
                data={'customer': formatted_customer}
            )

        except ValueError:
            return OperationResult(
                success=False,
                message=f"Invalid customer ID: {customer_id}",
                error_code="INVALID_CUSTOMER_ID"
            )
        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to get customer: {str(e)}",
                error_code="GET_CUSTOMER_FAILED",
                error_details=str(e)
            )

    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> OperationResult:
        """Update customer information"""
        try:
            # Check if customer exists
            existing = self.get_customer(customer_id)
            if not existing.success:
                return existing

            # Update the customer
            self._execute_odoo_method(
                model='res.partner',
                method='write',
                ids=[int(customer_id)],
                vals=updates
            )

            # Retrieve updated customer
            updated = self.get_customer(customer_id)

            return OperationResult(
                success=True,
                message=f"Successfully updated customer: {updated.data['customer']['name']}",
                data={'customer': updated.data['customer']}
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to update customer: {str(e)}",
                error_code="UPDATE_CUSTOMER_FAILED",
                error_details=str(e)
            )

    # === Product Operations ===

    def search_products(self,
                       name: Optional[str] = None,
                       category: Optional[str] = None,
                       sku: Optional[str] = None,
                       limit: int = 10) -> OperationResult:
        """Search for products in Odoo"""
        try:
            # Build search domain
            domain = [
                ['sale_ok', '=', True],  # Only products available for sale
                ['active', '=', True]
            ]

            if name:
                domain.append(['name', 'ilike', name])
            if sku:
                domain.append(['default_code', 'ilike', sku])
            if category:
                # Search by category name (requires joining with product.category)
                domain.append(['categ_id.name', 'ilike', category])

            # Search products
            products = self._execute_odoo_method(
                model='product.product',
                method='search_read',
                domain=domain,
                fields=['name', 'default_code', 'description_sale', 'list_price', 'categ_id'],
                limit=limit
            )

            # Format results
            formatted_products = []
            for product in products:
                formatted_products.append({
                    'id': product['id'],
                    'name': product['name'],
                    'sku': product.get('default_code'),
                    'description': product.get('description_sale'),
                    'price': product.get('list_price'),
                    'category': product.get('categ_id', [False, ''])[1] if product.get('categ_id') else None
                })

            return OperationResult(
                success=True,
                message=f"Found {len(formatted_products)} matching products",
                data={
                    'products': formatted_products,
                    'total_count': len(formatted_products)
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to search products: {str(e)}",
                error_code="SEARCH_PRODUCTS_FAILED",
                error_details=str(e)
            )

    # === Order Operations ===

    def create_order(self, order: OrderData) -> OperationResult:
        """Create a new sales order in Odoo"""
        try:
            # Validate customer exists
            customer_result = self.get_customer(order.customer_id)
            if not customer_result.success:
                return OperationResult(
                    success=False,
                    message=f"Customer with ID {order.customer_id} not found",
                    error_code="CUSTOMER_NOT_FOUND"
                )

            # Prepare order lines
            order_lines = []
            for product_id in order.product_ids:
                quantity = order.quantity.get(product_id, 1)

                # Get product info for price
                products = self._execute_odoo_method(
                    model='product.product',
                    method='read',
                    domain=[[int(product_id)]],
                    fields=['name', 'list_price']
                )

                if not products:
                    return OperationResult(
                        success=False,
                        message=f"Product with ID {product_id} not found",
                        error_code="PRODUCT_NOT_FOUND"
                    )

                product = products[0]
                order_lines.append([0, 0, {
                    'product_id': int(product_id),
                    'product_uom_qty': quantity,
                    'price_unit': product.get('list_price', 0.0),
                }])

            # Create sales order
            order_data = {
                'partner_id': int(order.customer_id),
                'state': 'draft',
                'order_line': order_lines,
            }

            if order.notes:
                order_data['note'] = order.notes

            sales_order_id = self._execute_odoo_method(
                model='sale.order',
                method='create',
                vals=order_data
            )

            # Retrieve the created order
            created_order = self._execute_odoo_method(
                model='sale.order',
                method='read',
                domain=[['id', '=', sales_order_id]],
                fields=['name', 'partner_id', 'state', 'amount_total']
            )

            return OperationResult(
                success=True,
                message=f"Successfully created sales order: {created_order[0]['name']}",
                data={
                    'order_id': sales_order_id,
                    'order': created_order[0] if created_order else None
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Failed to create order: {str(e)}",
                error_code="CREATE_ORDER_FAILED",
                error_details=str(e)
            )

    # === Metadata Operations ===

    def get_system_info(self) -> Dict[str, Any]:
        """Get Odoo system information"""
        try:
            # Get Odoo version info
            version_info = self._execute_odoo_method(
                model='ir.module.module',
                method='search_read',
                domain=[['name', '=', 'base']],
                fields=['name', 'version', 'state']
            )

            # Get installed modules
            modules = self._execute_odoo_method(
                model='ir.module.module',
                method='search_read',
                domain=[['state', '=', 'installed']],
                fields=['name', 'shortdesc', 'version'],
                limit=100
            )

            return {
                'odoo_version': version_info[0]['version'] if version_info else 'Unknown',
                'installed_modules': [
                    {
                        'name': mod['name'],
                        'description': mod['shortdesc'],
                        'version': mod['version']
                    }
                    for mod in modules
                ],
                'user_id': self.uid,
                'database': self.db,
                'url': self.base_url
            }

        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {
                'error': str(e),
                'odoo_version': 'Unknown',
                'installed_modules': []
            }

    def get_required_fields(self, entity_type: str) -> Dict[str, List[str]]:
        """Get required fields for different entity types"""
        required_fields = {
            'customer': ['name'],  # Name is the only truly required field for customers
            'product': ['name'],   # Name is required for products
            'order': ['partner_id']  # Customer is required for orders
        }

        return {
            'entity_type': entity_type,
            'required_fields': required_fields.get(entity_type, []),
            'optional_fields': {
                'customer': ['email', 'phone', 'company', 'address', 'notes'],
                'product': ['description', 'price', 'category', 'sku'],
                'order': ['notes']
            }
        }