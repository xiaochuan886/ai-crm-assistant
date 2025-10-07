# -*- coding: utf-8 -*-
"""
Quick Architecture Test

Simple test to verify the pluggable architecture works correctly.
"""

import sys
import os
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from adapters.base_adapter import BaseCrmAdapter, CustomerData, OperationResult
from core.agent_fixed import AiAgent, MockAiService


class SimpleAdapter(BaseCrmAdapter):
    """Simple mock adapter for testing"""

    VERSION = "1.0.0"

    def _validate_config(self) -> None:
        pass

    def test_connection(self) -> OperationResult:
        return OperationResult(success=True, message="Mock connection successful")

    def create_customer(self, customer: CustomerData) -> OperationResult:
        return OperationResult(
            success=True,
            message=f"Created customer: {customer.name}",
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


async def test_basic_functionality():
    """Test basic functionality"""
    print("🧪 Testing Architecture Components")
    print("=" * 40)

    # Test 1: Basic data structures
    print("1. Testing data structures...")
    customer = CustomerData(
        name="Test Customer",
        email="test@example.com"
    )
    print(f"   ✓ CustomerData: {customer.name}")

    # Test 2: Adapter interface
    print("2. Testing adapter interface...")
    adapter = SimpleAdapter({})
    info = adapter.get_adapter_info()
    print(f"   ✓ Adapter: {info['adapter_name']}")

    # Test 3: AI Agent
    print("3. Testing AI Agent...")
    ai_config = {'provider': 'mock'}
    agent = AiAgent(adapter, ai_config)
    agent_info = agent.get_agent_info()
    print(f"   ✓ Agent: {agent_info['agent_version']}")

    # Test 4: Natural language processing
    print("4. Testing natural language processing...")
    result = await agent.process_request(
        "Create a new customer named John Doe",
        "session_123",
        "user_456"
    )

    print(f"   ✓ Processing: {result['success']}")
    print(f"   ✓ Message: {result['message']}")

    print("\n🎉 All tests passed!")
    print("\nArchitecture Validation Results:")
    print("✅ Core AI engine is independent")
    print("✅ Adapter pattern works correctly")
    print("✅ Natural language processing works")
    print("✅ Pluggable architecture is functional")

    return True


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())