"""Test complex real-world scenarios end-to-end (NEW)."""
import pytest
from datetime import date
from jsonshift import Mapper


class TestRealWorldScenarios:
    """Real-world transformation scenarios."""

    def test_customer_to_contract_transformation(self):
        """Transform customer data into contract structure."""
        payload = {
            "customer_name": "John Doe",
            "cpf": "12345678901",
            "email": "john@example.com",
            "amount": 1500.0,
            "products": [
                {"id": "PROD-001", "price": 500.0},
                {"id": "PROD-002", "price": 1000.0}
            ]
        }
        
        spec = {
            "map": {
                "customer.name": "customer_name",
                "customer.document.number": "cpf",
                "customer.email": "email",
                "contract.total_amount": "amount",
                "contract.items[*].product_id": "products[*].id",
                "contract.items[*].product_price": "products[*].price"
            },
            "defaults": {
                "contract.status": "active",
                "contract.type": "CCB",
                "contract.created_at": {"$now": "datetime"},
                "customer.type": "individual"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["customer"]["name"] == "John Doe"
        assert result["customer"]["document"]["number"] == "12345678901"
        assert result["contract"]["status"] == "active"
        assert len(result["contract"]["items"]) == 2
        assert result["contract"]["items"][0]["product_price"] == 500.0

    def test_invoice_with_items_and_calculations(self):
        """Transform invoice with item calculations."""
        payload = {
            "invoice_id": "INV-001",
            "customer": {
                "name": "ACME Corp",
                "cnpj": "12345678000199"
            },
            "items": [
                {
                    "sku": "PROD-001",
                    "quantity": 10,
                    "unit_price": 100.50,
                    "tax_rate": 0.15
                },
                {
                    "sku": "PROD-002",
                    "quantity": 5,
                    "unit_price": 250.00,
                    "tax_rate": 0.15
                }
            ]
        }
        
        spec = {
            "map": {
                "invoice.number": "invoice_id",
                "invoice.customer.name": "customer.name",
                "invoice.customer.cnpj": "customer.cnpj",
                "invoice.line_items[*].sku": "items[*].sku",
                "invoice.line_items[*].quantity": "items[*].quantity",
                "invoice.line_items[*].unit_price": "items[*].unit_price"
            },
            "defaults": {
                "invoice.line_items[*].subtotal": {
                    "$mul": {
                        "value": {"$path": "items[*].quantity"},
                        "by": {"$path": "items[*].unit_price"}
                    }
                },
                "invoice.line_items[*].tax": {
                    "$mul": {
                        "value": {
                            "$mul": {
                                "value": {"$path": "items[*].quantity"},
                                "by": {"$path": "items[*].unit_price"}
                            }
                        },
                        "by": {"$path": "items[*].tax_rate"}
                    }
                },
                "invoice.status": "issued"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["invoice"]["number"] == "INV-001"
        assert len(result["invoice"]["line_items"]) == 2
        assert result["invoice"]["line_items"][0]["subtotal"] == 1005.0
        assert abs(result["invoice"]["line_items"][0]["tax"] - 150.75) < 0.01

    def test_nested_organization_structure(self):
        """Complex nested organization with formatting."""
        payload = {
            "org": {
                "name": "TechCorp",
                "departments": [
                    {
                        "name": "engineering",
                        "budget": 1000000,
                        "teams": [
                            {
                                "name": "backend",
                                "members": [
                                    {"id": 1, "name": "alice", "salary": 5000},
                                    {"id": 2, "name": "bob", "salary": 4500}
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        
        spec = {
            "map": {
                "organization.name": "org.name",
                "organization.departments[*].name": "org.departments[*].name",
                "organization.departments[*].budget": "org.departments[*].budget"
            },
            "defaults": {
                "organization.departments[*].budget_formatted": {
                    "$format": {
                        "value": {"$path": "org.departments[*].budget"},
                        "number": {
                            "decimals": 0,
                            "thousand": ".",
                            "decimal": ","
                        }
                    }
                },
                "organization.departments[*].name_upper": {
                    "$upper": {"$path": "org.departments[*].name"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["organization"]["name"] == "TechCorp"
        assert result["organization"]["departments"][0]["budget_formatted"] == "1.000.000"
        assert result["organization"]["departments"][0]["name_upper"] == "ENGINEERING"


class TestDataTransformationPipelines:
    """Multi-step data transformation pipelines."""

    def test_api_response_normalization(self):
        """Normalize API response into standard format."""
        payload = {
            "id": 12345,
            "user": {
                "email_address": "john@example.com",
                "full_name": "JOHN DOE"
            },
            "orders": [
                {
                    "order_id": "ORD-001",
                    "amount_cents": 10050,
                    "created_date": "2025-02-27"
                }
            ]
        }
        
        spec = {
            "map": {
                "user_id": "id",
                "email": "user.email_address"
            },
            "defaults": {
                "name": {
                    "$capitalize": {"$path": "user.full_name"}
                },
                "orders[*].order_code": {
                    "$upper": {"$path": "orders[*].order_id"}
                },
                "orders[*].amount": {
                    "$div": {
                        "value": {"$path": "orders[*].amount_cents"},
                        "by": 100
                    }
                },
                "normalized_date": {"$now": "date"}
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["user_id"] == 12345
        assert result["email"] == "john@example.com"
        assert result["name"] == "John doe"
        assert result["orders"][0]["order_code"] == "ORD-001"
        assert result["orders"][0]["amount"] == 100.5

    def test_financial_statement_generation(self):
        """Generate financial statement from transaction data."""
        payload = {
            "transactions": [
                {"type": "income", "amount": 5000},
                {"type": "expense", "amount": 1000},
                {"type": "expense", "amount": 500}
            ]
        }
        
        spec = {
            "defaults": {
                "total_income": 5000,
                "total_expenses": 1500,
                "net_result": {
                    "$sub": {
                        "value": 5000,
                        "by": 1500
                    }
                },
                "balance_formatted": {
                    "$format": {
                        "value": {
                            "$sub": {
                                "value": 5000,
                                "by": 1500
                            }
                        },
                        "number": {
                            "decimals": 2,
                            "thousand": ".",
                            "decimal": ","
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["net_result"] == 3500.0
        assert result["balance_formatted"] == "3.500,00"


class TestMultiLevelDataMerging:
    """Merging data across multiple levels."""

    def test_merge_deeply_nested_arrays(self):
        """Merge deeply nested array structures."""
        payload = {
            "companies": [
                {
                    "departments": [
                        {
                            "teams": [
                                {
                                    "members": [
                                        {"name": "Alice", "salary": 5000},
                                        {"name": "Bob", "salary": 4500}
                                    ]
                                },
                                {
                                    "members": [
                                        {"name": "Charlie", "salary": 4800}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "departments": [
                        {
                            "teams": [
                                {
                                    "members": [
                                        {"name": "Diana", "salary": 3500}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        spec = {
            "map": {
                "all_employees[*]": "companies[*].departments[*].teams[*].members[*].name",
                "all_salaries[*]": "companies[*].departments[*].teams[*].members[*].salary"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["all_employees"] == ["Alice", "Bob", "Charlie", "Diana"]
        assert result["all_salaries"] == [5000, 4500, 4800, 3500]

    def test_flatten_and_format_data(self):
        """Flatten nested data and apply formatting."""
        payload = {
            "divisions": [
                {
                    "regions": [
                        {
                            "sales_amount": 15000.50
                        },
                        {
                            "sales_amount": 22000.75
                        }
                    ]
                },
                {
                    "regions": [
                        {
                            "sales_amount": 8500.25
                        }
                    ]
                }
            ]
        }
        
        spec = {
            "map": {
                "sales[*]": "divisions[*].regions[*].sales_amount"
            },
            "defaults": {
                "sales_formatted[*]": {
                    "$format": {
                        "value": {"$path": "divisions[*].regions[*].sales_amount"},
                        "number": {
                            "decimals": 2,
                            "thousand": ".",
                            "decimal": ","
                        }
                    }
                },
                "total_sales": {
                    "$add": {
                        "value": 15000.50,
                        "by": {
                            "$add": {
                                "value": 22000.75,
                                "by": 8500.25
                            }
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["sales"] == [15000.50, 22000.75, 8500.25]
        assert result["sales_formatted"] == ["15.000,50", "22.000,75", "8.500,25"]


class TestMixedOperatorsAndPaths:
    """Mix all operator types with complex paths."""

    def test_comprehensive_transformation(self):
        """Comprehensive transformation with all features."""
        payload = {
            "company": "TechCorp",
            "year": 2025,
            "departments": [
                {
                    "name": "engineering",
                    "budget": 1000000,
                    "headcount": 50,
                    "employees": [
                        {"name": "alice", "salary": 5000},
                        {"name": "bob", "salary": 4500}
                    ]
                },
                {
                    "name": "sales",
                    "budget": 500000,
                    "headcount": 25,
                    "employees": [
                        {"name": "charlie", "salary": 3500}
                    ]
                }
            ]
        }
        
        spec = {
            "map": {
                "company": "company",
                "period": "year",
                "departments[*].name": "departments[*].name",
                "departments[*].budget": "departments[*].budget",
                "departments[*].headcount": "departments[*].headcount"
            },
            "defaults": {
                "departments[*].name_upper": {
                    "$upper": {"$path": "departments[*].name"}
                },
                "departments[*].budget_per_person": {
                    "$div": {
                        "value": {"$path": "departments[*].budget"},
                        "by": {"$path": "departments[*].headcount"}
                    }
                },
                "departments[*].budget_formatted": {
                    "$format": {
                        "value": {"$path": "departments[*].budget"},
                        "number": {
                            "decimals": 0,
                            "thousand": ".",
                            "decimal": ","
                        }
                    }
                },
                "departments[*].employee_count": 1,  # Simplified
                "total_budget": {
                    "$add": {
                        "value": 1000000,
                        "by": 500000
                    }
                },
                "generated_at": {"$now": "datetime"}
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["company"] == "TechCorp"
        assert result["period"] == 2025
        assert result["departments"][0]["name_upper"] == "ENGINEERING"
        assert result["departments"][0]["budget_per_person"] == 20000.0
        assert result["departments"][0]["budget_formatted"] == "1.000.000"
        assert result["total_budget"] == 1500000.0
        assert result["generated_at"] is not None
