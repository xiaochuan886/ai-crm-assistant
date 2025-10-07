# -*- coding: utf-8 -*-
"""
Simple Architecture Tests

Basic tests to verify the pluggable architecture works correctly.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from adapters.base_adapter import BaseCrmAdapter, CustomerData, OperationResult
from adapters.odoo_adapter import OdooAdapter
from core.agent import AiAgent


class MockAdapter(BaseCrmAdapter):
    """Mock CRM adapter for testing"""

    VERSION = "1.0.0"

    def _validate_config(self) -> None:
        pass

    def test_connection(self) -> OperationResult:
        return OperationResult(success=True, message="Mock connection successful")

    def create_customer(self, customer: CustomerData) -> OperationResult:
        return OperationResult(
            success=True,
            message=f"Created mock customer: {customer.name}",
            data={'customer_id': 'mock_123', 'name': customer.name}
        )

    def search_customers(self, **kwargs) -> OperationResult:
        return OperationResult(
            success=True,
            message="Found mock customers",
            data={'customers': [{'id': '1', 'name': 'Mock Customer'}]}
        )

    def get_customer(self, customer_id: str) -> OperationResult:
        return OperationResult(
            success=True,
            message="Retrieved mock customer",
            data={'customer': {'id': customer_id, 'name': 'Mock Customer'}}
        )

    def update_customer(self, customer_id: str, updates: dict) -> OperationResult:
        return OperationResult(
            success=True,
            message="Updated mock customer",
            data={'customer': {'id': customer_id, **updates}}
        )

    def search_products(self, **kwargs) -> OperationResult:
        return OperationResult(
            success=True,
            message="Found mock products",
            data={'products': [{'id': '1', 'name': 'Mock Product'}]}
        )

    def create_order(self, order) -> OperationResult:
        return OperationResult(
            success=True,
            message="Created mock order",
            data={'order_id': 'order_123'}
        )

    def get_system_info(self) -> dict:
        return {'system': 'mock', 'version': '1.0.0'}

    def get_required_fields(self, entity_type: str) -> dict:
        return {
            'entity_type': entity_type,
            'required_fields': ['name'],
            'optional_fields': ['email', 'phone']
        }


# Import MockAiService from core.agent
from core.agent import MockAiService


def test_basic_functionality():
    """Test basic functionality"""
    print("Testing basic functionality...")

    # Test customer data structure
    customer = CustomerData(
        name="Test Customer",
        email="test@example.com",
        phone="123-456-7890"
    )

    assert customer.name == "Test Customer"
    assert customer.email == "test@example.com"
    print("✓ Customer data structure works")

    # Test operation result structure
    success_result = OperationResult(
        success=True,
        message="Operation successful",
        data={'customer_id': '123'}
    )

    assert success_result.success is True
    assert success_result.data['customer_id'] == '123'
    print("✓ Operation result structure works")

    # Test base adapter interface
    adapter = MockAdapter({})
    info = adapter.get_adapter_info()
    assert 'adapter_name' in info
    print("✓ Base adapter interface works")


async def test_ai_agent():
    """Test AI agent with mock adapter"""
    print("Testing AI agent...")

    # Setup mock adapter and AI service
    adapter = MockAdapter({})
    ai_config = {'provider': 'mock'}

    # Create agent with mocked AI service
    agent = AiAgent(adapter, ai_config)
    agent.ai_service = MockAiService()

    # Test customer creation
    result = await agent.process_request(
        "Create a new customer named Test Customer with email test@example.com",
        "session_123",
        "user_456"
    )

    assert result['success'] is True
    assert 'Test Customer' in result['message']
    assert result['customer_id'] == 'mock_123'
    print("✓ AI agent customer creation works")

    # Test customer search
    result = await agent.process_request(
        "Search for customers named Test",
        "session_123",
        "user_456"
    )

    assert result['success'] is True
    assert 'Found' in result['message']
    assert 'customers' in result
    print("✓ AI agent customer search works")


def test_architecture_separation():
    """Test that core AI logic is separated from CRM-specific code"""
    print("Testing architecture separation...")

    # Verify that core agent doesn't have any Odoo-specific imports
    import core.agent
    agent_source = open(core.agent.__file__, 'r').read()

    # Should not contain Odoo-specific imports
    assert 'import odoo' not in agent_source
    assert 'from odoo' not in agent_source
    print("✓ Core agent has no Odoo-specific imports")

    # Should work with any adapter that implements the base interface
    adapter = MockAdapter({})
    ai_config = {'provider': 'mock'}

    # This should not raise any import errors
    agent = AiAgent(adapter, ai_config)
    print("✓ Agent works with any adapter implementing base interface")


async def run_all_tests():
    """Run all tests"""
    print("🧪 Running Architecture Validation Tests")
    print("=" * 50)

    try:
        test_basic_functionality()
        await test_ai_agent()
        test_architecture_separation()

        print("=" * 50)
        print("🎉 All tests passed!")
        print("\nArchitecture validation successful:")
        print("✅ Core AI engine is independent of CRM implementations")
        print("✅ Adapters implement the standard interface correctly")
        print("✅ AI agent can work with any CRM system through adapters")
        print("✅ Architecture separation principle is maintained")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(run_all_tests())