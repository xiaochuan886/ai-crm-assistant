# -*- coding: utf-8 -*-
"""
Architecture Tests

Tests to verify that the pluggable architecture works correctly.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

# Import core components
from adapters.base_adapter import BaseCrmAdapter, CustomerData, OperationResult
from adapters.odoo_adapter import OdooAdapter
from core.agent import AiAgent
from core.ai_services.openai_service import OpenAIService


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


class MockAiService:
    """Mock AI service for testing"""

    async def parse_intent(self, prompt: str) -> str:
        # Simple mock: return create customer intent for any input containing "create" and "customer"
        if "create" in prompt.lower() and "customer" in prompt.lower():
            return '''{
                "action": "create",
                "entity_type": "customer",
                "parameters": {
                    "name": "Test Customer",
                    "email": "test@example.com"
                },
                "confidence": 0.95
            }'''
        elif "search" in prompt.lower() and "customer" in prompt.lower():
            return '''{
                "action": "search",
                "entity_type": "customer",
                "parameters": {
                    "name": "Test"
                },
                "confidence": 0.90
            }'''
        else:
            return '''{
                "action": "unknown",
                "entity_type": "unknown",
                "parameters": {},
                "confidence": 0.0
            }'''


def test_base_adapter_interface():
    """Test that base adapter interface is properly defined"""
    # Mock adapter should implement all required methods
    adapter = MockAdapter({})

    # Test that all required methods exist and are callable
    assert hasattr(adapter, 'test_connection')
    assert hasattr(adapter, 'create_customer')
    assert hasattr(adapter, 'search_customers')
    assert hasattr(adapter, 'get_customer')
    assert hasattr(adapter, 'update_customer')
    assert hasattr(adapter, 'search_products')
    assert hasattr(adapter, 'create_order')
    assert hasattr(adapter, 'get_system_info')
    assert hasattr(adapter, 'get_required_fields')

    # Test adapter info
    info = adapter.get_adapter_info()
    assert 'adapter_name' in info
    assert 'supported_operations' in info


@pytest.mark.asyncio
async def test_ai_agent_with_mock_adapter():
    """Test AI agent with mock adapter"""
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

    # Test customer search
    result = await agent.process_request(
        "Search for customers named Test",
        "session_123",
        "user_456"
    )

    assert result['success'] is True
    assert 'Found' in result['message']
    assert 'customers' in result


def test_customer_data_structure():
    """Test standardized customer data structure"""
    customer = CustomerData(
        name="Test Customer",
        email="test@example.com",
        phone="123-456-7890"
    )

    assert customer.name == "Test Customer"
    assert customer.email == "test@example.com"
    assert customer.phone == "123-456-7890"
    assert customer.company is None  # Optional field


def test_operation_result_structure():
    """Test standardized operation result structure"""
    success_result = OperationResult(
        success=True,
        message="Operation successful",
        data={'customer_id': '123'}
    )

    assert success_result.success is True
    assert success_result.message == "Operation successful"
    assert success_result.data['customer_id'] == '123'

    error_result = OperationResult(
        success=False,
        message="Operation failed",
        error_code="VALIDATION_ERROR",
        error_details="Missing required field"
    )

    assert error_result.success is False
    assert error_result.error_code == "VALIDATION_ERROR"
    assert error_result.error_details == "Missing required field"


def test_architecture_separation():
    """Test that core AI logic is separated from CRM-specific code"""
    # This test verifies that the core agent doesn't import any Odoo-specific code

    # Import core agent - should work without Odoo installed
    from core.agent import AiAgent

    # Verify that core agent doesn't have any Odoo-specific imports
    import core.agent
    agent_source = open(core.agent.__file__, 'r').read()

    # Should not contain Odoo-specific imports
    assert 'import odoo' not in agent_source
    assert 'from odoo' not in agent_source

    # Should work with any adapter that implements the base interface
    adapter = MockAdapter({})
    ai_config = {'provider': 'mock'}

    # This should not raise any import errors
    agent = AiAgent(adapter, ai_config)


if __name__ == "__main__":
    # Run basic tests
    print("Running architecture tests...")

    test_base_adapter_interface()
    print("✓ Base adapter interface test passed")

    test_customer_data_structure()
    print("✓ Customer data structure test passed")

    test_operation_result_structure()
    print("✓ Operation result structure test passed")

    test_architecture_separation()
    print("✓ Architecture separation test passed")

    # Run async test
    asyncio.run(test_ai_agent_with_mock_adapter())
    print("✓ AI agent with mock adapter test passed")

    print("\nAll architecture tests passed! 🎉")
    print("\nThe pluggable architecture is working correctly:")
    print("- Core AI engine is independent of CRM implementations")
    print("- Adapters implement the standard interface")
    print("- AI agent can work with any CRM system through adapters")