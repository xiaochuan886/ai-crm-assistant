# -*- coding: utf-8 -*-
"""
Base CRM Adapter Interface

This module defines the standard interface that all CRM adapters must implement.
The core AI engine interacts with CRM systems only through this interface,
ensuring complete separation between AI logic and CRM-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class CustomerData:
    """Standardized customer data structure"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ProductData:
    """Standardized product data structure"""
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    sku: Optional[str] = None


@dataclass
class OrderData:
    """Standardized order data structure"""
    customer_id: str
    product_ids: List[str]
    quantity: Dict[str, int]  # product_id -> quantity
    notes: Optional[str] = None


@dataclass
class OperationResult:
    """Standardized operation result"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_details: Optional[str] = None


class BaseCrmAdapter(ABC):
    """
    Base class for all CRM adapters.

    Each CRM system (Odoo, Salesforce, HubSpot, etc.) must implement this interface.
    The core AI engine will only interact with CRM systems through these methods.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize adapter with configuration

        Args:
            config: Dictionary containing CRM-specific configuration
                   (e.g., API endpoints, credentials, etc.)
        """
        self.config = config
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate adapter-specific configuration"""
        pass

    @abstractmethod
    def test_connection(self) -> OperationResult:
        """Test connection to CRM system"""
        pass

    # === Customer Operations ===

    @abstractmethod
    def create_customer(self, customer: CustomerData) -> OperationResult:
        """
        Create a new customer in the CRM system

        Args:
            customer: Standardized customer data

        Returns:
            OperationResult with customer ID and details
        """
        pass

    @abstractmethod
    def search_customers(self,
                        name: Optional[str] = None,
                        email: Optional[str] = None,
                        phone: Optional[str] = None,
                        company: Optional[str] = None,
                        limit: int = 10) -> OperationResult:
        """
        Search for customers in the CRM system

        Args:
            name: Customer name (partial match)
            email: Customer email
            phone: Customer phone
            company: Company name
            limit: Maximum number of results

        Returns:
            OperationResult with list of matching customers
        """
        pass

    @abstractmethod
    def get_customer(self, customer_id: str) -> OperationResult:
        """
        Get customer details by ID

        Args:
            customer_id: Unique customer identifier

        Returns:
            OperationResult with customer details
        """
        pass

    @abstractmethod
    def update_customer(self, customer_id: str, updates: Dict[str, Any]) -> OperationResult:
        """
        Update customer information

        Args:
            customer_id: Unique customer identifier
            updates: Dictionary of fields to update

        Returns:
            OperationResult with updated customer details
        """
        pass

    # === Product Operations ===

    @abstractmethod
    def search_products(self,
                       name: Optional[str] = None,
                       category: Optional[str] = None,
                       sku: Optional[str] = None,
                       limit: int = 10) -> OperationResult:
        """
        Search for products in the CRM system

        Args:
            name: Product name (partial match)
            category: Product category
            sku: Product SKU
            limit: Maximum number of results

        Returns:
            OperationResult with list of matching products
        """
        pass

    # === Order Operations ===

    @abstractmethod
    def create_order(self, order: OrderData) -> OperationResult:
        """
        Create a new order in the CRM system

        Args:
            order: Standardized order data

        Returns:
            OperationResult with order ID and details
        """
        pass

    # === Metadata Operations ===

    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get CRM system information

        Returns:
            Dictionary with system details (version, available modules, etc.)
        """
        pass

    @abstractmethod
    def get_required_fields(self, entity_type: str) -> Dict[str, List[str]]:
        """
        Get required fields for different entity types

        Args:
            entity_type: Type of entity (customer, product, order, etc.)

        Returns:
            Dictionary with required fields list
        """
        pass

    # === Utility Methods ===

    def get_adapter_info(self) -> Dict[str, Any]:
        """
        Get adapter information

        Returns:
            Dictionary with adapter details
        """
        return {
            'adapter_name': self.__class__.__name__,
            'crm_type': self.config.get('crm_type', 'Unknown'),
            'version': getattr(self, 'VERSION', '1.0.0'),
            'supported_operations': [
                'create_customer', 'search_customers', 'get_customer', 'update_customer',
                'search_products', 'create_order', 'get_system_info', 'get_required_fields'
            ]
        }


class AdapterError(Exception):
    """Base exception for CRM adapter errors"""
    pass


class ConnectionError(AdapterError):
    """Raised when connection to CRM fails"""
    pass


class ValidationError(AdapterError):
    """Raised when data validation fails"""
    pass


class AuthenticationError(AdapterError):
    """Raised when authentication fails"""
    pass


class PermissionError(AdapterError):
    """Raised when user lacks permissions for an operation"""
    pass