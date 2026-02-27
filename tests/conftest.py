"""Shared fixtures for all tests."""
import pytest
from datetime import date, datetime
from jsonshift import Mapper


@pytest.fixture
def mapper():
    """Instance of Mapper."""
    return Mapper()


@pytest.fixture
def basic_payload():
    """Basic test payload."""
    return {
        "name": "John",
        "email": "john@example.com",
        "cpf": "12345678901",
        "amount": 1000.50,
        "phone": None,
    }


@pytest.fixture
def list_payload():
    """Payload with lists."""
    return {
        "users": [
            {"id": 1, "name": "Alice", "email": "alice@example.com"},
            {"id": 2, "name": "Bob", "email": "bob@example.com"},
        ]
    }


@pytest.fixture
def nested_payload():
    """Deeply nested payload."""
    return {
        "company": {
            "departments": [
                {
                    "name": "Engineering",
                    "teams": [
                        {
                            "name": "Backend",
                            "members": [
                                {"id": 1, "name": "Alice", "salary": 5000},
                                {"id": 2, "name": "Bob", "salary": 4500},
                            ]
                        },
                        {
                            "name": "Frontend",
                            "members": [
                                {"id": 3, "name": "Charlie", "salary": 4800},
                            ]
                        },
                    ]
                },
                {
                    "name": "Sales",
                    "teams": [
                        {
                            "name": "US",
                            "members": [
                                {"id": 4, "name": "Diana", "salary": 3500},
                            ]
                        },
                    ]
                },
            ]
        }
    }


@pytest.fixture
def invoice_payload():
    """Real-world invoice payload."""
    return {
        "invoice_id": "INV-001",
        "customer": {
            "name": "ACME Corp",
            "cnpj": "12345678000199",
            "address": "123 Main St"
        },
        "items": [
            {
                "sku": "PROD-001",
                "description": "Product A",
                "quantity": 10,
                "unit_price": 100.50,
                "tax_rate": 0.15
            },
            {
                "sku": "PROD-002",
                "description": "Product B",
                "quantity": 5,
                "unit_price": 250.00,
                "tax_rate": 0.15
            },
        ],
        "issue_date": "2025-02-27",
        "due_date": "2025-03-27"
    }
