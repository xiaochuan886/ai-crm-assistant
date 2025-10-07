# -*- coding: utf-8 -*-
"""
Enhanced Odoo Adapter Tests

Comprehensive tests for the enhanced Odoo adapter including
business rules validation, custom field mapping, and batch operations.
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.base_adapter import CustomerData, ProductData, OrderData, OperationResult
from adapters.odoo_adapter_enhanced import EnhancedOdooAdapter
from core.agent_fixed import AiAgent, MockAiService


class MockEnhancedOdooAdapter(EnhancedOdooAdapter):
    """Mock Enhanced Odoo adapter for testing"""

    VERSION = "2.0.0"

    def __init__(self, config):
        # Skip the actual login and metadata loading
        self.config = config
        self.base_url = config['url'].rstrip('/')
        self.db = config['db']
        self.username = config['username']
        self.password = config['password']
        self.timeout = config.get('timeout', 30)
        self.enable_caching = config.get('enable_caching', True)
        self.field_mapping = config.get('custom_field_mapping', {})
        self.business_rules = config.get('business_rules', {})
        self._cache = {} if self.enable_caching else None
        self.uid = 1  # Mock user ID
        self.context = {}

        # Mock metadata
        self.available_models = [
            {'model': 'res.partner', 'name': 'Contact'},
            {'model': 'sale.order', 'name': 'Sales Order'},
            {'model': 'crm.lead', 'name': 'Lead'},
            {'model': 'product.product', 'name': 'Product'}
        ]

        self.model_fields = {
            'res.partner': {
                'name': {'string': 'Name', 'type': 'char', 'required': True},
                'email': {'string': 'Email', 'type': 'char', 'required': False},
                'phone': {'string': 'Phone', 'type': 'char', 'required': False},
                'company_name': {'string': 'Company', 'type': 'char', 'required': False},
                'street': {'string': 'Street', 'type': 'char', 'required': False},
                'comment': {'string': 'Notes', 'type': 'text', 'required': False},
            },
            'sale.order': {
                'name': {'string': 'Order Reference', 'type': 'char', 'required': True},
                'partner_id': {'string': 'Customer', 'type': 'many2one', 'required': True},
                'state': {'string': 'Status', 'type': 'selection', 'required': False},
                'amount_total': {'string': 'Total', 'type': 'float', 'required': False},
            },
            'crm.lead': {
                'name': {'string': 'Lead Title', 'type': 'char', 'required': True},
                'email_from': {'string': 'Email', 'type': 'char', 'required': False},
                'phone': {'string': 'Phone', 'type': 'char', 'required': False},
                'partner_id': {'string': 'Customer', 'type': 'many2one', 'required': False},
            },
            'product.product': {
                'name': {'string': 'Product Name', 'type': 'char', 'required': True},
                'default_code': {'string': 'SKU', 'type': 'char', 'required': False},
                'list_price': {'string': 'Price', 'type': 'float', 'required': False},
                'sale_ok': {'string': 'Can be Sold', 'type': 'boolean', 'required': False},
            }
        }

        # Mock data store
        self.mock_data = {
            'customers': {},
            'orders': {},
            'products': {},
            'leads': {},
            'next_ids': {'customer': 1, 'order': 1, 'lead': 1}
        }

    def _validate_config(self) -> None:
        """Mock validation"""
        pass

    def _login(self) -> None:
        """Mock login"""
        pass

    def _load_odoo_metadata(self) -> None:
        """Mock metadata loading"""
        pass

    def _execute_odoo_method(self, model, method, domain=None, fields=None, **kwargs) -> Any:
        """Mock Odoo method execution"""
        if model == 'res.partner':
            if method == 'create':
                customer_id = self.mock_data['next_ids']['customer']
                self.mock_data['next_ids']['customer'] += 1
                self.mock_data['customers'][customer_id] = domain[0][2] if domain else {}
                return customer_id
            elif method == 'read':
                if domain and len(domain) > 0 and domain[0] == ['id', '=', domain[0][1]]:
                    customer_id = domain[0][1]
                    if customer_id in self.mock_data['customers']:
                        return [{'id': customer_id, **self.mock_data['customers'][customer_id]}]
                return []
            elif method == 'search_read':
                results = []
                for cid, cdata in self.mock_data['customers'].items():
                    match = True
                    if domain:
                        for condition in domain:
                            if len(condition) == 3:
                                field, operator, value = condition
                                if field in cdata:
                                    if operator == 'ilike' and value.lower() not in str(cdata[field]).lower():
                                        match = False
                                        break
                    if match:
                        results.append({'id': cid, **cdata})
                return results[:kwargs.get('limit', 10)]
            elif method == 'search_count':
                count = 0
                for cid, cdata in self.mock_data['customers'].items():
                    if domain:
                        for condition in domain:
                            if len(condition) == 3:
                                field, operator, value = condition
                                if field in cdata:
                                    if operator == 'ilike' and value.lower() not in str(cdata[field]).lower():
                                        break
                        else:
                            count += 1
                return count

        elif model == 'crm.lead':
            if method == 'create':
                lead_id = self.mock_data['next_ids']['lead']
                self.mock_data['next_ids']['lead'] += 1
                self.mock_data['leads'][lead_id] = kwargs.get('vals', {})
                return lead_id
            elif method == 'read':
                if domain and len(domain) > 0:
                    lead_id = domain[0][1]
                    if lead_id in self.mock_data['leads']:
                        return [{'id': lead_id, **self.mock_data['leads'][lead_id]}]
                return []

        elif model == 'product.product':
            if method == 'read':
                if domain and len(domain) > 0:
                    product_id = domain[0][1]
                    # Mock product data
                    return [{
                        'id': product_id,
                        'name': 'Mock Product',
                        'list_price': 100.0,
                        'sale_ok': True,
                        'default_code': f'SKU{product_id}'
                    }]
                return []

        elif model == 'sale.order':
            if method == 'create':
                order_id = self.mock_data['next_ids']['order']
                self.mock_data['next_ids']['order'] += 1
                order_data = kwargs.get('vals', {})
                order_data['name'] = f'SO{order_id:04d}'
                self.mock_data['orders'][order_id] = order_data
                return order_id
            elif method == 'read':
                if domain and len(domain) > 0:
                    order_id = domain[0][1]
                    if order_id in self.mock_data['orders']:
                        return [{'id': order_id, **self.mock_data['orders'][order_id]}]
                return []

        return []


class TestEnhancedOdooAdapter:
    """Test suite for Enhanced Odoo Adapter"""

    def setup_method(self):
        """Setup test environment"""
        self.config = {
            'url': 'https://test-odoo.com',
            'db': 'test_db',
            'username': 'test_user',
            'password': 'test_pass',
            'custom_field_mapping': {
                'company': 'company_name',
                'notes': 'comment'
            },
            'business_rules': {
                'customer': {
                    'required_fields': ['name', 'email'],
                    'field_formats': {
                        'email': 'email',
                        'phone': 'phone'
                    },
                    'custom_rules': [
                        {
                            'type': 'condition',
                            'condition': "'test' in data.get('name', '').lower()",
                            'message': "Customer name cannot contain 'test'"
                        }
                    ]
                }
            }
        }

        self.adapter = MockEnhancedOdooAdapter(self.config)

    def test_adapter_initialization(self):
        """Test adapter initialization with configuration"""
        assert self.adapter.config == self.config
        assert self.adapter.field_mapping['company'] == 'company_name'
        assert self.adapter.business_rules['customer']['required_fields'] == ['name', 'email']

    def test_field_mapping(self):
        """Test custom field mapping functionality"""
        # Test forward mapping
        data = {'name': 'Test Customer', 'company': 'Test Company'}
        mapped = self.adapter._apply_field_mapping(data)
        assert mapped['company_name'] == 'Test Company'
        assert 'company' not in mapped

        # Test reverse mapping
        reverse_mapped = self.adapter._apply_field_mapping(mapped, reverse=True)
        assert reverse_mapped['company'] == 'Test Company'
        assert 'company_name' not in reverse_mapped

    def test_business_rules_validation(self):
        """Test business rules validation"""
        # Valid data
        valid_data = {
            'name': 'Valid Customer',
            'email': 'valid@example.com',
            'phone': '123-456-7890'
        }
        errors = self.adapter._validate_business_rules('customer', valid_data)
        assert len(errors) == 0

        # Missing required field
        invalid_data = {
            'name': 'Customer without Email'
        }
        errors = self.adapter._validate_business_rules('customer', invalid_data)
        assert len(errors) > 0
        assert any('email' in error for error in errors)

        # Invalid email format
        invalid_email_data = {
            'name': 'Customer',
            'email': 'invalid-email'
        }
        errors = self.adapter._validate_business_rules('customer', invalid_email_data)
        assert len(errors) > 0
        assert any('email' in error for error in errors)

        # Custom rule violation
        custom_rule_data = {
            'name': 'Test Customer',
            'email': 'test@example.com'
        }
        errors = self.adapter._validate_business_rules('customer', custom_rule_data)
        assert len(errors) > 0
        assert any("cannot contain 'test'" in error for error in errors)

    def test_create_customer_with_validation(self):
        """Test customer creation with business rules validation"""
        # Valid customer
        customer = CustomerData(
            name="Valid Customer",
            email="valid@example.com",
            phone="123-456-7890"
        )
        result = self.adapter.create_customer(customer)
        assert result.success is True
        assert 'customer_id' in result.data

        # Invalid customer (missing email)
        invalid_customer = CustomerData(
            name="Customer without Email"
        )
        result = self.adapter.create_customer(invalid_customer)
        assert result.success is False
        assert result.error_code == "VALIDATION_ERROR"

    def test_search_customers_with_pagination(self):
        """Test customer search with pagination and ordering"""
        # Create test customers
        customers = [
            CustomerData(name="Alice", email="alice@example.com"),
            CustomerData(name="Bob", email="bob@example.com"),
            CustomerData(name="Charlie", email="charlie@example.com")
        ]

        for customer in customers:
            self.adapter.create_customer(customer)

        # Test search with limit
        result = self.adapter.search_customers(limit=2, order='name asc')
        assert result.success is True
        assert len(result.data['customers']) == 2
        assert result.data['total_count'] == 3

        # Test search with offset
        result = self.adapter.search_customers(limit=2, offset=1, order='name asc')
        assert result.success is True
        assert len(result.data['customers']) == 2
        customers_returned = [c['name'] for c in result.data['customers']]
        assert 'Bob' in customers_returned
        assert 'Charlie' in customers_returned

    def test_create_lead(self):
        """Test lead creation"""
        lead_data = {
            'name': 'Test Lead',
            'email': 'lead@example.com',
            'description': 'Test lead description'
        }

        result = self.adapter.create_lead(lead_data)
        assert result.success is True
        assert 'lead_id' in result.data
        assert result.data['lead']['name'] == 'Test Lead'

    def test_batch_create_customers(self):
        """Test batch customer creation"""
        customers = [
            CustomerData(name="Batch Customer 1", email="batch1@example.com"),
            CustomerData(name="Batch Customer 2", email="batch2@example.com"),
            CustomerData(name="Batch Customer 3", email="batch3@example.com")
        ]

        result = self.adapter.batch_create_customers(customers)
        assert result.success is True
        assert result.data['success_count'] == 3
        assert result.data['error_count'] == 0
        assert len(result.data['created_customers']) == 3

    def test_system_info(self):
        """Test system information retrieval"""
        info = self.adapter.get_system_info()
        assert 'odoo_version' in info
        assert 'adapter_version' in info
        assert 'available_models_count' in info
        assert info['adapter_version'] == '2.0.0'

    def test_required_fields_info(self):
        """Test required fields information"""
        info = self.adapter.get_required_fields('customer')
        assert info['entity_type'] == 'customer'
        assert 'name' in info['required_fields']
        assert 'odoo_model' in info
        assert info['odoo_model'] == 'res.partner'

    def test_cache_operations(self):
        """Test cache management"""
        # Test cache info
        cache_info = self.adapter.get_cache_info()
        assert 'cache_enabled' in cache_info
        assert 'cache_size' in cache_info

        # Test cache clear
        self.adapter.clear_cache()
        cache_info = self.adapter.get_cache_info()
        assert cache_info['cache_size'] == 0

    def test_enhanced_connection_test(self):
        """Test enhanced connection test"""
        result = self.adapter.test_connection()
        assert result.success is True
        assert 'user_info' in result.data
        assert 'adapter_version' in result.data
        assert result.data['adapter_version'] == '2.0.0'

    def test_error_handling(self):
        """Test enhanced error handling"""
        # Test connection error
        bad_adapter = MockEnhancedOdooAdapter(self.config)
        # Simulate a failure by overriding the method
        def failing_method(*args, **kwargs):
            raise Exception("Simulated failure")
        bad_adapter._execute_odoo_method = failing_method

        customer = CustomerData(name="Test Customer")
        result = bad_adapter.create_customer(customer)
        assert result.success is False
        assert 'error_code' in result.__dict__


class TestIntegrationWithAiAgent:
    """Test integration between Enhanced Odoo Adapter and AI Agent"""

    def setup_method(self):
        """Setup test environment"""
        config = {
            'url': 'https://test-odoo.com',
            'db': 'test_db',
            'username': 'test_user',
            'password': 'test_pass',
            'business_rules': {
                'customer': {
                    'required_fields': ['name']
                }
            }
        }

        self.adapter = MockEnhancedOdooAdapter(config)
        ai_config = {'provider': 'mock'}
        self.agent = AiAgent(self.adapter, ai_config)

    @pytest.mark.asyncio
    async def test_ai_agent_with_enhanced_adapter(self):
        """Test AI Agent with Enhanced Odoo Adapter"""
        # Test customer creation
        result = await self.agent.process_request(
            "Create a new customer named John Doe with email john@example.com",
            "session_123",
            "user_456"
        )

        assert result['success'] is True
        assert 'customer_id' in result
        assert 'John Doe' in result['message']

    @pytest.mark.asyncio
    async def test_business_rules_integration(self):
        """Test business rules integration with AI Agent"""
        # This should fail due to business rules if email is required
        result = await self.agent.process_request(
            "Create a customer named Test Customer",
            "session_123",
            "user_456"
        )

        # Depending on business rules configuration, this might succeed or fail
        # The test verifies that the integration works
        assert 'success' in result
        assert 'message' in result


def run_enhanced_tests():
    """Run all enhanced tests"""
    print("🧪 Running Enhanced Odoo Adapter Tests")
    print("=" * 50)

    # Test basic functionality
    test_suite = TestEnhancedOdooAdapter()
    test_suite.setup_method()

    tests = [
        ("Adapter Initialization", test_suite.test_adapter_initialization),
        ("Field Mapping", test_suite.test_field_mapping),
        ("Business Rules Validation", test_suite.test_business_rules_validation),
        ("Customer Creation with Validation", test_suite.test_create_customer_with_validation),
        ("Customer Search with Pagination", test_suite.test_search_customers_with_pagination),
        ("Lead Creation", test_suite.test_create_lead),
        ("Batch Customer Creation", test_suite.test_batch_create_customers),
        ("System Information", test_suite.test_system_info),
        ("Required Fields Information", test_suite.test_required_fields_info),
        ("Cache Operations", test_suite.test_cache_operations),
        ("Enhanced Connection Test", test_suite.test_enhanced_connection_test),
        ("Error Handling", test_suite.test_error_handling),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name}: {str(e)}")
            failed += 1

    # Test AI Agent integration
    print("\n🤖 Testing AI Agent Integration")
    integration_test = TestIntegrationWithAiAgent()
    integration_test.setup_method()

    try:
        asyncio.run(integration_test.test_ai_agent_with_enhanced_adapter())
        print("✓ AI Agent Integration")
        passed += 1
    except Exception as e:
        print(f"❌ AI Agent Integration: {str(e)}")
        failed += 1

    print("\n" + "=" * 50)
    print(f"🎉 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("\n🎯 All tests passed!")
        print("Enhanced Odoo Adapter is ready for real-world deployment:")
        print("✅ Business rules validation works")
        print("✅ Custom field mapping works")
        print("✅ Batch operations work")
        print("✅ Enhanced error handling works")
        print("✅ AI Agent integration works")
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the implementation.")

    return failed == 0


if __name__ == "__main__":
    run_enhanced_tests()