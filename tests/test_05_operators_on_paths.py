"""Test operators applied to $path and wildcard paths (NEW)."""
import pytest
from jsonshift import Mapper


class TestStringOperatorsOnPath:
    """Test string operators with $path."""

    def test_upper_on_path(self):
        """Apply $upper to $path value."""
        payload = {"name": "john"}
        spec = {
            "defaults": {
                "name_upper": {
                    "$upper": {"$path": "name"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["name_upper"] == "JOHN"

    def test_lower_on_path(self):
        """Apply $lower to $path value."""
        payload = {"email": "John@Example.COM"}
        spec = {
            "defaults": {
                "email_lower": {
                    "$lower": {"$path": "email"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["email_lower"] == "john@example.com"

    def test_capitalize_on_path(self):
        """Apply $capitalize to $path value."""
        payload = {"title": "hello world"}
        spec = {
            "defaults": {
                "title_cap": {
                    "$capitalize": {"$path": "title"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["title_cap"] == "Hello world"

    def test_title_on_path(self):
        """Apply $title to $path value."""
        payload = {"full_name": "john doe smith"}
        spec = {
            "defaults": {
                "full_name_title": {
                    "$title": {"$path": "full_name"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["full_name_title"] == "John Doe Smith"


class TestStringOperatorsOnWildcard:
    """Test string operators on wildcard paths."""

    def test_upper_on_wildcard_path(self):
        """Apply $upper to each item in wildcard."""
        payload = {
            "names": ["alice", "bob", "charlie"]
        }
        spec = {
            "defaults": {
                "names_upper[*]": {
                    "$upper": {"$path": "names[*]"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["names_upper"] == ["ALICE", "BOB", "CHARLIE"]

    def test_upper_on_wildcard_object_path(self):
        """Apply $upper to wildcard object field."""
        payload = {
            "users": [
                {"email": "alice@example.com"},
                {"email": "bob@example.com"}
            ]
        }
        spec = {
            "defaults": {
                "emails_upper[*]": {
                    "$upper": {"$path": "users[*].email"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["emails_upper"] == ["ALICE@EXAMPLE.COM", "BOB@EXAMPLE.COM"]

    def test_lower_on_double_wildcard(self):
        """Apply $lower to double wildcard."""
        payload = {
            "departments": [
                {
                    "codes": ["ABC", "DEF"]
                },
                {
                    "codes": ["GHI"]
                }
            ]
        }
        spec = {
            "defaults": {
                "codes_lower[*]": {
                    "$lower": {"$path": "departments[*].codes[*]"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["codes_lower"] == ["abc", "def", "ghi"]


class TestConcatOperatorOnPath:
    """Test $concat with $path."""

    def test_concat_with_path_value(self):
        """Concatenate $path value with literals."""
        payload = {"id": 123}
        spec = {
            "defaults": {
                "code": {
                    "$concat": [
                        "ID-",
                        {"$path": "id"}
                    ]
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["code"] == "ID-123"

    def test_concat_multiple_paths(self):
        """Concatenate multiple $path values."""
        payload = {"first": "John", "last": "Doe"}
        spec = {
            "defaults": {
                "full_name": {
                    "$concat": [
                        {"$path": "first"},
                        " ",
                        {"$path": "last"}
                    ]
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["full_name"] == "John Doe"


class TestMathOperatorsOnPath:
    """Test math operators with $path."""

    def test_add_with_path_values(self):
        """$add using $path values."""
        payload = {"price": 100, "tax": 10}
        spec = {
            "defaults": {
                "total": {
                    "$add": {
                        "value": {"$path": "price"},
                        "by": {"$path": "tax"}
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["total"] == 110.0

    def test_multiply_with_path(self):
        """$mul using $path values."""
        payload = {"quantity": 10, "unit_price": 5.5}
        spec = {
            "defaults": {
                "total": {
                    "$mul": {
                        "value": {"$path": "quantity"},
                        "by": {"$path": "unit_price"}
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["total"] == 55.0

    def test_discount_calculation(self):
        """Real-world discount calculation."""
        payload = {"original_price": 100, "discount_rate": 0.15}
        spec = {
            "defaults": {
                "discount_amount": {
                    "$mul": {
                        "value": {"$path": "original_price"},
                        "by": {"$path": "discount_rate"}
                    }
                },
                "final_price": {
                    "$sub": {
                        "value": {"$path": "original_price"},
                        "by": {
                            "$mul": {
                                "value": {"$path": "original_price"},
                                "by": {"$path": "discount_rate"}
                            }
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["discount_amount"] == 15.0
        assert result["final_price"] == 85.0


class TestFormatOperatorOnPath:
    """Test $format with $path."""

    def test_format_date_from_path(self):
        """Format date from $path."""
        payload = {"birth_date": "1990-05-15"}
        spec = {
            "defaults": {
                "formatted_birth": {
                    "$format": {
                        "value": {"$path": "birth_date"},
                        "date": {
                            "parse": "%Y-%m-%d",
                            "strftime": "%d/%m/%Y"
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["formatted_birth"] == "15/05/1990"

    def test_format_cpf_from_path(self):
        """Format CPF mask from $path."""
        payload = {"cpf": "12345678901"}
        spec = {
            "defaults": {
                "cpf_formatted": {
                    "$format": {
                        "value": {"$path": "cpf"},
                        "mask": "###.###.###-##"
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["cpf_formatted"] == "123.456.789-01"

    def test_format_number_from_path(self):
        """Format number from $path Brazilian style."""
        payload = {"amount": 1500.50}
        spec = {
            "defaults": {
                "amount_formatted": {
                    "$format": {
                        "value": {"$path": "amount"},
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
        
        assert result["amount_formatted"] == "1.500,50"


class TestOperatorsOnOptionalPath:
    """Test operators with optional $path."""

    def test_operator_on_optional_missing_path(self):
        """Operator with optional missing $path."""
        payload = {"name": "john"}
        spec = {
            "defaults": {
                "nickname_upper": {
                    "$upper": {
                        "$path": "nickname",
                        "optional": True
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert "nickname_upper" not in result or result["nickname_upper"] is None

    def test_operator_on_optional_present_path(self):
        """Operator with optional present $path."""
        payload = {"name": "john", "nickname": "johnny"}
        spec = {
            "defaults": {
                "nickname_upper": {
                    "$upper": {
                        "$path": "nickname",
                        "optional": True
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["nickname_upper"] == "JOHNNY"


class TestChainedOperators:
    """Test chaining operators together."""

    def test_upper_then_concat(self):
        """Chain $upper and $concat."""
        payload = {"prefix": "user", "id": 123}
        spec = {
            "defaults": {
                "code": {
                    "$concat": [
                        {
                            "$upper": {"$path": "prefix"}
                        },
                        "-",
                        {"$path": "id"}
                    ]
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["code"] == "USER-123"

    def test_format_then_concat(self):
        """Format then concatenate."""
        payload = {"amount": 1000.5}
        spec = {
            "defaults": {
                "message": {
                    "$concat": [
                        "Total: ",
                        {
                            "$format": {
                                "value": {"$path": "amount"},
                                "number": {
                                    "decimals": 2,
                                    "thousand": ".",
                                    "decimal": ","
                                }
                            }
                        }
                    ]
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["message"] == "Total: 1.000,50"

    def test_calculation_then_format(self):
        """Calculate then format result."""
        payload = {"price": 100, "quantity": 3}
        spec = {
            "defaults": {
                "total_formatted": {
                    "$format": {
                        "value": {
                            "$mul": {
                                "value": {"$path": "price"},
                                "by": {"$path": "quantity"}
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
        
        assert result["total_formatted"] == "300,00"


class TestOperatorOnWildcardPath:
    """Test operators on complete wildcard paths."""

    def test_calculation_on_wildcard(self):
        """Apply calculation to wildcard array."""
        payload = {
            "items": [
                {"price": 100, "quantity": 2},
                {"price": 50, "quantity": 3}
            ]
        }
        spec = {
            "defaults": {
                "totals[*]": {
                    "$mul": {
                        "value": {"$path": "items[*].price"},
                        "by": {"$path": "items[*].quantity"}
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["totals"] == [200.0, 150.0]

    def test_format_on_wildcard(self):
        """Apply formatting to wildcard array."""
        payload = {
            "amounts": [1000.5, 2500.75, 100.1]
        }
        spec = {
            "defaults": {
                "amounts_formatted[*]": {
                    "$format": {
                        "value": {"$path": "amounts[*]"},
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
        
        assert result["amounts_formatted"] == ["1.000,50", "2.500,75", "100,10"]

    def test_complex_operation_on_double_wildcard(self):
        """Complex operation on double wildcard."""
        payload = {
            "departments": [
                {
                    "items": [
                        {"price": 100, "tax_rate": 0.15},
                        {"price": 50, "tax_rate": 0.15}
                    ]
                }
            ]
        }
        spec = {
            "defaults": {
                "taxes[*]": {
                    "$mul": {
                        "value": {"$path": "departments[*].items[*].price"},
                        "by": {"$path": "departments[*].items[*].tax_rate"}
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["taxes"] == [15.0, 7.5]
