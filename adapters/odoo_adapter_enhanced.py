# -*- coding: utf-8 -*-
"""
Enhanced Odoo CRM Adapter

This module provides an enhanced implementation of the Odoo-specific adapter
with additional features for real-world deployment.
"""

import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
from datetime import datetime

from adapters.base_adapter import (
    BaseCrmAdapter, CustomerData, ProductData, OrderData, OperationResult,
    AdapterError, ConnectionError, ValidationError, AuthenticationError,
    PermissionError
)


logger = logging.getLogger(__name__)


class EnhancedOdooAdapter(BaseCrmAdapter):
    """
    Enhanced Odoo CRM Adapter

    Provides comprehensive integration with Odoo including:
    - Advanced customer management with custom fields
    - Lead and opportunity handling
    - Sales order management
    - Custom field mapping
    - Batch operations
    - Field validation and business rules
    """

    VERSION = "2.0.0"

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Enhanced Odoo adapter

        Args:
            config: Dictionary containing:
                - url: Odoo instance URL
                - db: Database name
                - username: Username
                - password: Password
                - timeout: Request timeout (default: 30)
                - enable_caching: Enable response caching (default: True)
                - custom_field_mapping: Custom field mappings
                - business_rules: Business rule configurations
        """
        super().__init__(config)
        self.base_url = config['url'].rstrip('/')
        self.db = config['db']
        self.username = config['username']
        self.password = config['password']
        self.timeout = config.get('timeout', 30)
        self.enable_caching = config.get('enable_caching', True)

        # Custom field mapping
        self.field_mapping = config.get('custom_field_mapping', {})

        # Business rules
        self.business_rules = config.get('business_rules', {})

        # Cache for frequently accessed data
        self._cache = {} if self.enable_caching else None

        # Session management
        self.uid = None
        self.session = requests.Session()
        self.session.timeout = self.timeout

        # Login to get session ID and user ID
        self._login()

        # Load Odoo metadata
        self._load_odoo_metadata()

    def _validate_config(self) -> None:
        """Validate Odoo-specific configuration"""
        required_fields = ['url', 'db', 'username', 'password']
        for field in required_fields:
            if not self.config.get(field):
                raise ValidationError(f"Missing required Odoo config field: {field}")

        # Validate URL format
        if not self.config['url'].startswith(('http://', 'https://')):
            raise ValidationError("Odoo URL must start with http:// or https://")

    def _login(self) -> None:
        """Authenticate with Odoo and get user ID"""
        try:
            login_url = urljoin(self.base_url, '/web/session/authenticate')

            login_data = {
                'jsonrpc': '2.0',
                'params': {
                    'db': self.db,
                    'login': self.username,
                    'password': self.password,
                }
            }

            response = self.session.post(login_url, json=login_data, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()

            if result.get('error'):
                raise AuthenticationError(f"Odoo authentication failed: {result['error']}")

            if not result.get('result', {}).get('uid'):
                raise AuthenticationError("Odoo authentication failed: No user ID returned")

            self.uid = result['result']['uid']
            self.context = result['result'].get('user_context', {})

            # 保存session cookie for subsequent requests
            self.session.cookies.set('session_id', response.cookies.get('session_id'))

            logger.info(f"Successfully authenticated with Odoo as user {self.uid}")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Odoo: {str(e)}")

    def _load_odoo_metadata(self) -> None:
        """Load Odoo system metadata"""
        try:
            logger.info("Loading Odoo system metadata...")

            # 首先测试简单的调用以验证连接
            logger.info("Testing basic RPC call...")
            try:
                test_result = self._execute_odoo_method(
                    model='res.users',
                    method='read',
                    ids=[self.uid] if self.uid is not None else [],
                    fields=['name', 'login'],
                    limit=1
                )
                logger.info(f"Basic RPC test successful: {test_result}")
            except Exception as e:
                logger.warning(f"Basic RPC test failed: {str(e)}")
                # 如果RPC调用失败，使用基本的元数据
                self._load_basic_metadata()
                return

            # Get available models
            try:
                logger.info("Loading available models...")
                self.available_models = self._execute_odoo_method(
                    model='ir.model',
                    method='search_read',
                    domain=[['transient', '=', False]],
                    fields=['model', 'name'],
                    limit=1000
                )
                logger.info(f"Loaded {len(self.available_models)} models")
            except Exception as e:
                logger.warning(f"Failed to load models: {str(e)}")
                self.available_models = []

            # Get field information for key models
            try:
                self.model_fields = {
                    'res.partner': self._get_model_fields('res.partner'),
                    'sale.order': self._get_model_fields('sale.order'),
                    'crm.lead': self._get_model_fields('crm.lead'),
                    'product.product': self._get_model_fields('product.product'),
                }
                logger.info("Loaded model fields successfully")
            except Exception as e:
                logger.warning(f"Failed to load model fields: {str(e)}")
                self._load_basic_field_definitions()

            logger.info(f"Loaded Odoo metadata: {len(self.available_models)} models available")

        except Exception as e:
            logger.warning(f"Failed to load Odoo metadata: {str(e)}")
            self._load_basic_metadata()

    def _load_basic_metadata(self):
        """Load basic metadata for fallback"""
        logger.info("Loading basic metadata as fallback...")
        self.available_models = [
            {'model': 'res.partner', 'name': 'Contact'},
            {'model': 'sale.order', 'name': 'Sales Order'},
            {'model': 'crm.lead', 'name': 'Lead'},
            {'model': 'product.product', 'name': 'Product'},
        ]
        self._load_basic_field_definitions()

    def _load_basic_field_definitions(self):
        """Load basic field definitions"""
        self.model_fields = {
            'res.partner': {field: {'string': field, 'type': 'string'}
                           for field in ['id', 'name', 'email', 'phone', 'company_name', 'active']},
            'sale.order': {field: {'string': field, 'type': 'string'}
                          for field in ['id', 'name', 'partner_id', 'state']},
            'crm.lead': {field: {'string': field, 'type': 'string'}
                        for field in ['id', 'name', 'email_from', 'phone', 'partner_id', 'stage_id', 'type']},
            'product.product': {field: {'string': field, 'type': 'string'}
                               for field in ['id', 'name', 'default_code', 'list_price', 'sale_ok', 'active']},
        }

    def _get_model_fields(self, model: str) -> Dict[str, Dict]:
        """Get field information for a model"""
        try:
            fields_info = self._execute_odoo_method(
                model=model,
                method='fields_get',
                attributes=['string', 'help', 'type', 'required', 'readonly']
            )
            return fields_info
        except Exception as e:
            logger.warning(f"Failed to get fields for model {model}: {str(e)}")
            return {}

    def _execute_odoo_method(self,
                           model: str,
                           method: str,
                           domain: Optional[List] = None,
                           fields: Optional[List] = None,
                           context: Optional[Dict] = None,
                           limit: Optional[int] = None,
                           offset: Optional[int] = None,
                           order: Optional[str] = None,
                           **kwargs) -> Any:
        """
        Execute Odoo model method via JSON-RPC with enhanced error handling
        """
        try:
            rpc_url = urljoin(self.base_url, '/web/dataset/call_kw')

            # 对于不同的方法使用不同的参数结构
            if method == 'search_read':
                # search_read 方法的特殊结构 - 需要空的args参数
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [],  # search_read需要空的args参数
                        'kwargs': {
                            'domain': domain if domain is not None else [],
                            'context': context or self.context,
                            **kwargs
                        }
                    },
                    'id': 1
                }

                # 为 search_read 添加可选参数
                if fields:
                    rpc_data['params']['kwargs']['fields'] = fields
                if limit is not None:
                    rpc_data['params']['kwargs']['limit'] = limit
                if offset is not None:
                    rpc_data['params']['kwargs']['offset'] = offset
                if order:
                    rpc_data['params']['kwargs']['order'] = order

            elif method == 'create':
                # create 方法使用 vals 参数
                vals = kwargs.get('vals', {})
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [vals],  # create expects vals dict as first arg
                        'kwargs': {
                            'context': context or self.context
                        }
                    },
                    'id': 1
                }

            elif method == 'read':
                # read 方法使用 ids 参数
                ids = kwargs.get('ids', [])
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [ids],  # read expects ids list as first arg
                        'kwargs': {
                            'context': context or self.context,
                            **{k: v for k, v in kwargs.items() if k != 'ids'}
                        }
                    },
                    'id': 1
                }

            elif method == 'write':
                # write 方法使用 [ids, vals] 作为位置参数
                ids = kwargs.get('ids', [])
                vals = kwargs.get('vals', {})
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [ids, vals],
                        'kwargs': {
                            'context': context or self.context
                        }
                    },
                    'id': 1
                }

            elif method in ['search', 'search_count']:
                # search/search_count 需要将 domain 作为第一个位置参数（列表包裹）
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [domain if domain is not None else []],
                        'kwargs': {
                            'context': context or self.context
                        }
                    },
                    'id': 1
                }

                # search 支持可选参数；search_count不需要
                if method == 'search':
                    if limit is not None:
                        rpc_data['params']['kwargs']['limit'] = limit
                    if offset is not None:
                        rpc_data['params']['kwargs']['offset'] = offset
                    if order:
                        rpc_data['params']['kwargs']['order'] = order

            else:
                # 其他方法的通用结构（将domain放入kwargs而不是位置参数）
                rpc_data = {
                    'jsonrpc': '2.0',
                    'method': 'call',
                    'params': {
                        'model': model,
                        'method': method,
                        'args': [],
                        'kwargs': {
                            'context': context or self.context,
                            **({ 'domain': domain } if domain is not None else {}),
                            **kwargs
                        }
                    },
                    'id': 1
                }

                # 为其他方法添加可选参数
                if fields:
                    rpc_data['params']['kwargs']['fields'] = fields
                if limit is not None:
                    rpc_data['params']['kwargs']['limit'] = limit

            response = self.session.post(rpc_url, json=rpc_data, timeout=self.timeout)
            response.raise_for_status()

            result = response.json()

            if result.get('error'):
                error = result['error']
                error_message = error.get('message', 'Unknown Odoo RPC error')
                error_code = error.get('code', 'UNKNOWN_ERROR')

                # Handle specific error types
                if 'Access denied' in error_message:
                    raise PermissionError(f"Odoo access denied: {error_message}")
                elif 'does not exist' in error_message:
                    raise AdapterError(f"Odoo object not found: {error_message}")
                elif 'validation error' in error_message.lower():
                    raise ValidationError(f"Odoo validation error: {error_message}")
                else:
                    raise AdapterError(f"Odoo RPC error [{error_code}]: {error_message}")

            return result.get('result')

        except requests.exceptions.Timeout:
            raise ConnectionError(f"Odoo RPC request timed out after {self.timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Odoo RPC request failed: {str(e)}")

    def _apply_field_mapping(self, data: Dict[str, Any], reverse: bool = False) -> Dict[str, Any]:
        """Apply custom field mapping"""
        if not self.field_mapping:
            return data

        mapping = self.field_mapping
        if reverse:
            mapping = {v: k for k, v in mapping.items()}

        mapped_data = {}
        for key, value in data.items():
            mapped_key = mapping.get(key, key)
            mapped_data[mapped_key] = value

        return mapped_data

    def _validate_business_rules(self, entity_type: str, data: Dict[str, Any]) -> List[str]:
        """Validate business rules and return list of validation errors"""
        errors = []
        rules = self.business_rules.get(entity_type, {})

        # Required fields
        required_fields = rules.get('required_fields', [])
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Field '{field}' is required")

        # Field formats
        field_formats = rules.get('field_formats', {})
        for field, format_rule in field_formats.items():
            if data.get(field):
                if format_rule == 'email' and '@' not in data[field]:
                    errors.append(f"Field '{field}' must be a valid email")
                elif format_rule == 'phone' and not any(c.isdigit() for c in data[field]):
                    errors.append(f"Field '{field}' must contain at least one digit")

        # Custom validation rules
        custom_rules = rules.get('custom_rules', [])
        for rule in custom_rules:
            if rule['type'] == 'condition':
                condition = rule['condition']
                try:
                    if eval(condition, {'data': data}):
                        errors.append(rule['message'])
                except:
                    logger.warning(f"Failed to evaluate custom rule: {condition}")

        return errors

    def _apply_field_formatting(self, entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply conservative field formatting for Odoo models.

        - Trims whitespace for text fields
        - Normalizes phone to digits and leading '+'
        - Keeps behavior minimal to avoid unintended transformations
        """
        try:
            formatted = dict(data)
            if entity_type == 'customer':
                val = formatted.get('email')
                if isinstance(val, str):
                    formatted['email'] = val.strip()

                val = formatted.get('phone')
                if isinstance(val, str):
                    cleaned = ''.join(c for c in val if c.isdigit() or c == '+')
                    formatted['phone'] = cleaned or val.strip()

                val = formatted.get('name')
                if isinstance(val, str):
                    formatted['name'] = val.strip()

                val = formatted.get('company_name')
                if isinstance(val, str):
                    formatted['company_name'] = val.strip()

                val = formatted.get('street')
                if isinstance(val, str):
                    formatted['street'] = val.strip()

                val = formatted.get('comment')
                if isinstance(val, str):
                    formatted['comment'] = val.strip()

            return formatted
        except Exception as e:
            logger.warning(f"Field formatting failed: {str(e)}; returning original data")
            return data

    # === Enhanced Customer Operations ===

    def create_customer(self, customer: CustomerData) -> OperationResult:
        """Create a new customer with enhanced features"""
        try:
            # Apply business rules validation
            customer_data = {
                'name': customer.name,
                'is_company': False,
            }

            # Add standard fields
            if customer.email:
                customer_data['email'] = customer.email
            if customer.phone:
                customer_data['phone'] = customer.phone
            if customer.company:
                customer_data['company_name'] = customer.company
            if customer.address:
                customer_data['street'] = customer.address
            if customer.notes:
                customer_data['comment'] = customer.notes

            # Apply custom field mapping
            logger.debug(f"Original customer data: {customer_data}")
            customer_data = self._apply_field_mapping(customer_data)
            logger.debug(f"After field mapping: {customer_data}")

            # Validate business rules
            validation_errors = self._validate_business_rules('customer', customer_data)
            logger.debug(f"Business rules validation errors: {validation_errors}")
            if validation_errors:
                return OperationResult(
                    success=False,
                    message=f"Validation failed: {'; '.join(validation_errors)}",
                    error_code="VALIDATION_ERROR",
                    error_details=validation_errors
                )

            # Create the customer
            customer_id = self._execute_odoo_method(
                model='res.partner',
                method='create',
                vals=customer_data
            )

            # Retrieve the created customer record with all fields
            created_customer = self._execute_odoo_method(
                model='res.partner',
                method='read',
                ids=[customer_id],
                fields=list(self.model_fields.get('res.partner', {}).keys())
            )

            # Clear cache if enabled
            if self._cache:
                self._cache.clear()

            return OperationResult(
                success=True,
                message=f"Successfully created customer: {customer.name}",
                data={
                    'customer_id': customer_id,
                    'customer': created_customer[0] if created_customer else None
                }
            )

        except Exception as e:
            import traceback
            logger.error(f"Failed to create customer: {str(e)}")
            logger.error(f"Customer data was: {customer_data}")
            logger.error(f"Full traceback:\n{traceback.format_exc()}")

            # 尝试从异常中提取更详细的Odoo错误信息
            error_details = str(e)
            if "Odoo RPC error" in str(e):
                logger.error("This is an Odoo RPC error - checking response details...")
                # 如果是OdooError类型，尝试获取更多错误信息
                if hasattr(e, 'response') and e.response:
                    try:
                        error_json = e.response.json()
                        logger.error(f"Odoo error response: {error_json}")
                        if 'error' in error_json:
                            odoo_error = error_json['error']
                            error_details = f"Odoo Error: {odoo_error.get('message', str(e))}"
                            if 'data' in odoo_error and 'message' in odoo_error['data']:
                                error_details = f"Odoo Error: {odoo_error['data']['message']}"
                    except:
                        logger.error("Could not parse Odoo error response")

            return OperationResult(
                success=False,
                message=f"Failed to create customer: {error_details}",
                error_code="CREATE_CUSTOMER_FAILED",
                error_details=error_details
            )

    def search_customers(self,
                        name: Optional[str] = None,
                        email: Optional[str] = None,
                        phone: Optional[str] = None,
                        company: Optional[str] = None,
                        limit: int = 10,
                        offset: int = 0,
                        order: str = 'name asc') -> OperationResult:
        """Search for customers with enhanced filtering"""
        try:
            # Build search domain
            domain = [
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

            # Apply custom field mapping for search
            if self.field_mapping:
                domain = self._apply_field_mapping_to_domain(domain)

            # Get all available fields
            available_fields = list(self.model_fields.get('res.partner', {}).keys())

            # Search customers with pagination
            customers = self._execute_odoo_method(
                model='res.partner',
                method='search_read',
                domain=domain,
                fields=available_fields,
                limit=limit,
                offset=offset,
                order=order
            )

            # Get total count for pagination
            total_count = self._execute_odoo_method(
                model='res.partner',
                method='search_count',
                domain=domain
            )

            # Format results
            formatted_customers = []
            for customer in customers:
                # Apply reverse field mapping
                formatted_customer = self._apply_field_mapping(customer, reverse=True)
                formatted_customers.append(formatted_customer)

            return OperationResult(
                success=True,
                message=f"Found {len(formatted_customers)} matching customers (total: {total_count})",
                data={
                    'customers': formatted_customers,
                    'total_count': total_count,
                    'limit': limit,
                    'offset': offset
                }
            )

        except Exception as e:
            logger.error(f"Failed to search customers: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to search customers: {str(e)}",
                error_code="SEARCH_CUSTOMERS_FAILED",
                error_details=str(e)
            )

    def get_customer(self, customer_id: str) -> OperationResult:
        """Get customer details by ID"""
        try:
            # Validate customer_id
            if not customer_id or not customer_id.isdigit():
                return OperationResult(
                    success=False,
                    message="Invalid customer ID format",
                    error_code="INVALID_CUSTOMER_ID"
                )

            # Get customer details
            customers = self._execute_odoo_method(
                model='res.partner',
                method='read',
                ids=[int(customer_id)],
                fields=list(self.model_fields.get('res.partner', {}).keys())
            )

            if not customers:
                return OperationResult(
                    success=False,
                    message=f"Customer with ID {customer_id} not found",
                    error_code="CUSTOMER_NOT_FOUND"
                )

            # Apply reverse field mapping
            customer = customers[0]
            formatted_customer = self._apply_field_mapping(customer, reverse=True)

            return OperationResult(
                success=True,
                message=f"Successfully retrieved customer: {formatted_customer.get('name')}",
                data={'customer': formatted_customer}
            )

        except Exception as e:
            logger.error(f"Failed to get customer: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to get customer: {str(e)}",
                error_code="GET_CUSTOMER_FAILED",
                error_details=str(e)
            )

    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> OperationResult:
        """Update customer information"""
        try:
            # Validate customer_id
            if not customer_id or not customer_id.isdigit():
                return OperationResult(
                    success=False,
                    message="Invalid customer ID format",
                    error_code="INVALID_CUSTOMER_ID"
                )

            # Check if customer exists
            existing_customer = self.get_customer(customer_id)
            if not existing_customer.success:
                return OperationResult(
                    success=False,
                    message=f"Customer with ID {customer_id} not found",
                    error_code="CUSTOMER_NOT_FOUND"
                )

            # Apply field mapping to updates
            mapped_updates = self._apply_field_mapping(updates)

            # Validate business rules
            # 合并现有客户数据与本次更新，让必填项校验基于完整数据集
            existing_data = {}
            if isinstance(existing_customer.data, dict):
                existing_data = existing_customer.data.get('customer', {}) or {}

            try:
                existing_mapped = self._apply_field_mapping(existing_data)
            except Exception:
                existing_mapped = {}

            full_data_for_validation = {**existing_mapped, **mapped_updates}

            validation_errors = self._validate_business_rules('customer', full_data_for_validation)
            if validation_errors:
                return OperationResult(
                    success=False,
                    message=f"Validation failed: {'; '.join(validation_errors)}",
                    error_code="BUSINESS_RULE_VALIDATION_FAILED",
                    error_details=validation_errors
                )

            # Apply field formatting
            formatted_updates = self._apply_field_formatting('customer', mapped_updates)

            # Update customer
            update_result = self._execute_odoo_method(
                model='res.partner',
                method='write',
                ids=[int(customer_id)],
                vals=formatted_updates
            )

            if update_result:
                # Retrieve updated customer
                updated_customer = self.get_customer(customer_id)
                if updated_customer.success:
                    return OperationResult(
                        success=True,
                        message=f"Successfully updated customer: {updated_customer.data['customer'].get('name')}",
                        data={'customer': updated_customer.data['customer']}
                    )
                else:
                    return OperationResult(
                        success=True,
                        message="Customer updated successfully but failed to retrieve updated data",
                        data={'customer_id': customer_id}
                    )
            else:
                return OperationResult(
                    success=False,
                    message="Failed to update customer",
                    error_code="UPDATE_CUSTOMER_FAILED"
                )

        except Exception as e:
            logger.error(f"Failed to update customer: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to update customer: {str(e)}",
                error_code="UPDATE_CUSTOMER_FAILED",
                error_details=str(e)
            )

    def _apply_field_mapping_to_domain(self, domain: List) -> List:
        """Apply field mapping to search domain"""
        if not self.field_mapping:
            return domain

        mapped_domain = []
        for condition in domain:
            if len(condition) >= 2:
                field = condition[0]
                mapped_field = self.field_mapping.get(field, field)
                new_condition = [mapped_field] + condition[1:]
                mapped_domain.append(new_condition)
            else:
                mapped_domain.append(condition)

        return mapped_domain

    # === Lead Management ===

    def create_lead(self, lead_data: Dict[str, Any]) -> OperationResult:
        """Create a new CRM lead"""
        try:
            # Validate required fields
            if not lead_data.get('name'):
                return OperationResult(
                    success=False,
                    message="Lead title is required",
                    error_code="MISSING_REQUIRED_FIELD"
                )

            # Prepare lead data
            lead_vals = {
                'name': lead_data['name'],
                'type': 'lead',
            }

            # Map optional fields
            field_mapping = {
                'partner_id': 'customer_id',
                'email_from': 'email',
                'phone': 'phone',
                'description': 'description'
            }

            for field, source_field in field_mapping.items():
                if source_field in lead_data and lead_data[source_field]:
                    lead_vals[field] = lead_data[source_field]

            # Create lead
            lead_id = self._execute_odoo_method(
                model='crm.lead',
                method='create',
                vals=lead_vals
            )

            # Retrieve created lead
            created_lead = self._execute_odoo_method(
                model='crm.lead',
                method='read',
                domain=[['id', '=', lead_id]],
                fields=['name', 'email_from', 'phone', 'partner_id', 'stage_id', 'type']
            )

            return OperationResult(
                success=True,
                message=f"Successfully created lead: {lead_data['name']}",
                data={
                    'lead_id': lead_id,
                    'lead': created_lead[0] if created_lead else None
                }
            )

        except Exception as e:
            logger.error(f"Failed to create lead: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to create lead: {str(e)}",
                error_code="CREATE_LEAD_FAILED",
                error_details=str(e)
            )

    # === Enhanced Product Operations ===

    def search_products(self,
                       name: Optional[str] = None,
                       category: Optional[str] = None,
                       sku: Optional[str] = None,
                       limit: int = 10,
                       include_variants: bool = True) -> OperationResult:
        """Search for products with variant support"""
        try:
            # Build search domain
            domain = [
                ['sale_ok', '=', True],
                ['active', '=', True]
            ]

            if name:
                domain.append(['name', 'ilike', name])
            if sku:
                domain.append(['default_code', 'ilike', sku])
            if category:
                # Handle category search with many2one relationship
                domain.append(['categ_id.name', 'ilike', category])

            # Choose model based on variant preference
            model = 'product.product' if include_variants else 'product.template'

            # Get fields for the model
            model_fields = list(self.model_fields.get(model, {}).keys())

            # Search products
            products = self._execute_odoo_method(
                model=model,
                method='search_read',
                domain=domain,
                fields=model_fields,
                limit=limit
            )

            # Format results
            formatted_products = []
            for product in products:
                formatted_product = {
                    'id': product['id'],
                    'name': product['name'],
                    'description': product.get('description_sale'),
                    'price': product.get('list_price', 0.0),
                }

                # Add variant-specific fields
                if include_variants:
                    formatted_product.update({
                        'sku': product.get('default_code'),
                        'barcode': product.get('barcode'),
                    })

                # Add category information
                if product.get('categ_id'):
                    formatted_product['category'] = product['categ_id'][1] if isinstance(product['categ_id'], list) else product['categ_id']

                formatted_products.append(formatted_product)

            return OperationResult(
                success=True,
                message=f"Found {len(formatted_products)} matching products",
                data={
                    'products': formatted_products,
                    'total_count': len(formatted_products),
                    'model': model
                }
            )

        except Exception as e:
            logger.error(f"Failed to search products: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to search products: {str(e)}",
                error_code="SEARCH_PRODUCTS_FAILED",
                error_details=str(e)
            )

    # === Enhanced Order Operations ===

    def create_order(self, order: OrderData) -> OperationResult:
        """Create a sales order with enhanced validation"""
        try:
            # Validate customer exists
            customer_result = self.get_customer(order.customer_id)
            if not customer_result.success:
                return OperationResult(
                    success=False,
                    message=f"Customer with ID {order.customer_id} not found",
                    error_code="CUSTOMER_NOT_FOUND"
                )

            # Validate products exist and are available
            order_lines = []
            for product_id in order.product_ids:
                quantity = order.quantity.get(product_id, 1)

                # Get product info
                products = self._execute_odoo_method(
                    model='product.product',
                    method='read',
                    domain=[[int(product_id)]],
                    fields=['name', 'list_price', 'sale_ok']
                )

                if not products:
                    return OperationResult(
                        success=False,
                        message=f"Product with ID {product_id} not found",
                        error_code="PRODUCT_NOT_FOUND"
                    )

                product = products[0]

                # Check if product is available for sale
                if not product.get('sale_ok', False):
                    return OperationResult(
                        success=False,
                        message=f"Product {product['name']} is not available for sale",
                        error_code="PRODUCT_NOT_FOR_SALE"
                    )

                order_lines.append([0, 0, {
                    'product_id': int(product_id),
                    'product_uom_qty': quantity,
                    'price_unit': product.get('list_price', 0.0),
                }])

            # Create sales order with additional fields
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

            # Retrieve the created order with all fields
            created_order = self._execute_odoo_method(
                model='sale.order',
                method='read',
                domain=[['id', '=', sales_order_id]],
                fields=list(self.model_fields.get('sale.order', {}).keys())
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
            logger.error(f"Failed to create order: {str(e)}")
            return OperationResult(
                success=False,
                message=f"Failed to create order: {str(e)}",
                error_code="CREATE_ORDER_FAILED",
                error_details=str(e)
            )

    # === Batch Operations ===

    def batch_create_customers(self, customers: List[CustomerData]) -> OperationResult:
        """Create multiple customers in batch"""
        try:
            results = []
            errors = []

            for customer in customers:
                try:
                    result = self.create_customer(customer)
                    if result.success:
                        results.append(result.data)
                    else:
                        errors.append({
                            'customer': customer.name,
                            'error': result.message
                        })
                except Exception as e:
                    errors.append({
                        'customer': customer.name,
                        'error': str(e)
                    })

            return OperationResult(
                success=len(errors) == 0,
                message=f"Batch create completed: {len(results)} successful, {len(errors)} failed",
                data={
                    'created_customers': results,
                    'errors': errors,
                    'success_count': len(results),
                    'error_count': len(errors)
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Batch create failed: {str(e)}",
                error_code="BATCH_CREATE_FAILED",
                error_details=str(e)
            )

    # === Enhanced Metadata Operations ===

    def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive Odoo system information"""
        try:
            # Get Odoo version info
            version_info = self._execute_odoo_method(
                model='ir.module.module',
                method='search_read',
                domain=[['name', '=', 'base']],
                fields=['name', 'version', 'state']
            )

            # Get user information
            user_info = self._execute_odoo_method(
                model='res.users',
                method='read',
                domain=[['id', '=', self.uid]],
                fields=['name', 'login', 'company_id', 'groups_id']
            )

            # Get company information
            company_info = self._execute_odoo_method(
                model='res.company',
                method='read',
                domain=[[1]],  # Main company
                fields=['name', 'email', 'phone', 'country_id']
            )

            # Get installed modules
            modules = self._execute_odoo_method(
                model='ir.module.module',
                method='search_read',
                domain=[['state', '=', 'installed']],
                fields=['name', 'shortdesc', 'version', 'category_id'],
                limit=500
            )

            return {
                'odoo_version': version_info[0]['version'] if version_info else 'Unknown',
                'user_info': user_info[0] if user_info else None,
                'company_info': company_info[0] if company_info else None,
                'installed_modules': [
                    {
                        'name': mod['name'],
                        'description': mod['shortdesc'],
                        'version': mod['version'],
                        'category': mod['category_id'][1] if mod.get('category_id') else 'Unknown'
                    }
                    for mod in modules
                ],
                'available_models_count': len(self.available_models),
                'user_id': self.uid,
                'database': self.db,
                'url': self.base_url,
                'adapter_version': self.VERSION
            }

        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {
                'error': str(e),
                'odoo_version': 'Unknown',
                'user_id': self.uid,
                'database': self.db,
                'url': self.base_url
            }

    def get_required_fields(self, entity_type: str) -> Dict[str, List[str]]:
        """Get required fields with Odoo-specific information"""
        base_requirements = {
            'customer': ['name'],
            'product': ['name'],
            'order': ['partner_id']
        }

        # Add Odoo-specific required fields if available
        model_mapping = {
            'customer': 'res.partner',
            'product': 'product.product',
            'order': 'sale.order'
        }

        model_name = model_mapping.get(entity_type)
        if model_name and model_name in self.model_fields:
            odoo_required = [
                field_name for field_name, field_info in self.model_fields[model_name].items()
                if field_info.get('required', False)
            ]

            # Merge with base requirements
            required_fields = list(set(base_requirements.get(entity_type, []) + odoo_required))
        else:
            required_fields = base_requirements.get(entity_type, [])

        return {
            'entity_type': entity_type,
            'required_fields': required_fields,
            'optional_fields': {
                'customer': ['email', 'phone', 'company', 'address', 'notes'],
                'product': ['description', 'price', 'category', 'sku'],
                'order': ['notes']
            },
            'odoo_model': model_name,
            'available_fields': list(self.model_fields.get(model_name, {}).keys()) if model_name else []
        }

    # === Connection and Health Check ===

    def test_connection(self) -> OperationResult:
        """Enhanced connection test with detailed information"""
        try:
            # Test basic connectivity - 使用正确的domain格式
            user_info = self._execute_odoo_method(
                model='res.users',
                method='read',
                ids=[self.uid] if self.uid is not None else [],
                fields=['name', 'login', 'company_id']
            )

            if not user_info:
                return OperationResult(
                    success=False,
                    message="Failed to retrieve user information from Odoo",
                    error_code="USER_NOT_FOUND"
                )

            # Test model access - 使用search_count方法
            try:
                customer_count = self._execute_odoo_method(
                    model='res.partner',
                    method='search_count',
                    domain=[]
                )
            except Exception as e:
                customer_count = None
                logger.warning(f"Could not access customer model: {str(e)}")

            return OperationResult(
                success=True,
                message=f"Successfully connected to Odoo as {user_info[0]['name']}",
                data={
                    'user_info': user_info[0],
                    'customer_count': customer_count,
                    'odoo_version': '19.0',
                    'odoo_url': self.base_url,
                    'database': self.db,
                    'adapter_version': self.VERSION,
                    'available_models_count': len(self.available_models) if hasattr(self, 'available_models') else 0
                }
            )

        except Exception as e:
            return OperationResult(
                success=False,
                message=f"Odoo connection test failed: {str(e)}",
                error_code="CONNECTION_FAILED",
                error_details=str(e)
            )

    # === Cache Management ===

    def clear_cache(self) -> None:
        """Clear internal cache"""
        if self._cache:
            self._cache.clear()
            logger.info("Adapter cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        return {
            'cache_enabled': self.enable_caching,
            'cache_size': len(self._cache) if self._cache else 0,
            'cache_keys': list(self._cache.keys()) if self._cache else []
        }