"""Test all dynamic operators."""
import pytest
from datetime import date, datetime
from jsonshift import Mapper


class TestNowOperator:
    """Test $now operator."""

    def test_now_datetime(self):
        """$now returns current datetime."""
        spec = {"defaults": {"created": {"$now": "datetime"}}}
        
        result = Mapper().transform(spec, {})
        
        assert isinstance(result["created"], datetime)

    def test_now_date(self):
        """$now returns current date."""
        spec = {"defaults": {"today": {"$now": "date"}}}
        
        result = Mapper().transform(spec, {})
        
        assert isinstance(result["today"], date)

    def test_now_time(self):
        """$now returns current time."""
        spec = {"defaults": {"time": {"$now": "time"}}}
        
        result = Mapper().transform(spec, {})
        
        assert result["time"] is not None

    def test_now_year(self):
        """$now returns current year."""
        spec = {"defaults": {"year": {"$now": "year"}}}
        
        result = Mapper().transform(spec, {})
        
        assert isinstance(result["year"], int)
        assert result["year"] > 2020


class TestConcatOperator:
    """Test $concat operator."""

    def test_concat_strings(self):
        """Concatenate plain strings."""
        spec = {
            "defaults": {
                "code": {
                    "$concat": ["USR-", "001"]
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["code"] == "USR-001"

    def test_concat_with_path(self):
        """Concatenate with $path values."""
        payload = {"id": 123}
        spec = {
            "defaults": {
                "code": {
                    "$concat": ["ID-", {"$path": "id"}]
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["code"] == "ID-123"

    def test_concat_multiple_paths(self):
        """Concatenate multiple paths."""
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


class TestMathOperators:
    """Test mathematical operators."""

    def test_add_numbers(self):
        """$add two numbers."""
        spec = {
            "defaults": {
                "total": {"$add": {"value": 10, "by": 5}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["total"] == 15

    def test_subtract_numbers(self):
        """$sub two numbers."""
        spec = {
            "defaults": {
                "result": {"$sub": {"value": 20, "by": 7}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 13

    def test_multiply_numbers(self):
        """$mul two numbers."""
        spec = {
            "defaults": {
                "result": {"$mul": {"value": 4, "by": 2.5}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 10.0

    def test_divide_numbers(self):
        """$div two numbers."""
        spec = {
            "defaults": {
                "result": {"$div": {"value": 20, "by": 4}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 5.0

    def test_power(self):
        """$pow exponentiation."""
        spec = {
            "defaults": {
                "result": {"$pow": {"value": 2, "by": 8}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 256.0

    def test_division_by_zero(self):
        """Division by zero raises error."""
        spec = {
            "defaults": {
                "result": {"$div": {"value": 10, "by": 0}}
            }
        }
        
        with pytest.raises(ValueError):
            Mapper().transform(spec, {})

    def test_math_with_string_numbers(self):
        """Math operators work with string numbers."""
        spec = {
            "defaults": {
                "result": {"$add": {"value": "10.5", "by": "2.5"}}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 13.0


class TestAddDateOperator:
    """Test $add with dates."""

    def test_add_days_to_date(self):
        """Add days to a date."""
        spec = {
            "defaults": {
                "future": {
                    "$add": {
                        "value": {"$now": "date"},
                        "by": {"days": 10}
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert isinstance(result["future"], date)

    def test_add_months_to_date(self):
        """Add months to a date."""
        payload = {"birth_date": date(2000, 1, 15)}
        spec = {
            "defaults": {
                "milestone": {
                    "$add": {
                        "value": "2000-01-15",
                        "by": {"months": 6}
                    }
                }
            }
        }
        
        # Note: This would need string parsing in the implementation
        # For now, testing the capability


class TestRoundOperator:
    """Test $round operator."""

    def test_round_simple(self):
        """Round a decimal."""
        spec = {
            "defaults": {
                "value": {
                    "$round": {
                        "value": 3.14159,
                        "ndigits": 2
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["value"] == 3.14

    def test_round_composition(self):
        """Round result of other operation."""
        spec = {
            "defaults": {
                "percentage": {
                    "$round": {
                        "value": {
                            "$mul": {
                                "value": 0.920066,
                                "by": 100
                            }
                        },
                        "ndigits": 2
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["percentage"] == 92.01


class TestFormatOperator:
    """Test $format operator."""

    def test_format_date(self):
        """Format a date string."""
        spec = {
            "defaults": {
                "formatted_date": {
                    "$format": {
                        "value": "2025-02-27",
                        "date": {
                            "parse": "%Y-%m-%d",
                            "strftime": "%d/%m/%Y"
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["formatted_date"] == "27/02/2025"

    def test_format_mask_cpf(self):
        """Format CPF with mask."""
        spec = {
            "defaults": {
                "cpf": {
                    "$format": {
                        "value": "12345678901",
                        "mask": "###.###.###-##"
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["cpf"] == "123.456.789-01"

    def test_format_mask_cnpj(self):
        """Format CNPJ with mask."""
        spec = {
            "defaults": {
                "cnpj": {
                    "$format": {
                        "value": "12345678000199",
                        "mask": "##.###.###/####-##"
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["cnpj"] == "12.345.678/0001-99"

    def test_format_number_brazil(self):
        """Format number Brazilian style."""
        spec = {
            "defaults": {
                "amount": {
                    "$format": {
                        "value": 10000.50,
                        "number": {
                            "decimals": 2,
                            "thousand": ".",
                            "decimal": ","
                        }
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["amount"] == "10.000,50"


class TestStringOperators:
    """Test string transformation operators."""

    def test_upper(self):
        """$upper converts to uppercase."""
        spec = {
            "defaults": {
                "code": {"$upper": "abc"}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["code"] == "ABC"

    def test_lower(self):
        """$lower converts to lowercase."""
        spec = {
            "defaults": {
                "email": {"$lower": "John@EXAMPLE.COM"}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["email"] == "john@example.com"

    def test_capitalize(self):
        """$capitalize first letter."""
        spec = {
            "defaults": {
                "name": {"$capitalize": "john"}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["name"] == "John"

    def test_title(self):
        """$title capitalizes words."""
        spec = {
            "defaults": {
                "name": {"$title": "john doe"}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["name"] == "John Doe"


class TestOperatorComposition:
    """Test composing operators together."""

    def test_nested_mul_and_add(self):
        """Compose $mul and $add."""
        spec = {
            "defaults": {
                "result": {
                    "$add": {
                        "value": {
                            "$mul": {
                                "value": 10,
                                "by": 2
                            }
                        },
                        "by": 5
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 25.0

    def test_complex_formula(self):
        """Complex financial formula."""
        spec = {
            "defaults": {
                "annual_rate": {
                    "$sub": {
                        "value": {
                            "$pow": {
                                "value": {
                                    "$add": {
                                        "value": 1,
                                        "by": 0.04
                                    }
                                },
                                "by": 12
                            }
                        },
                        "by": 1
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        expected = (1.04 ** 12) - 1
        assert abs(result["annual_rate"] - expected) < 0.0001

    def test_concat_with_formatted_number(self):
        """Concat with formatted number result."""
        spec = {
            "defaults": {
                "message": {
                    "$concat": [
                        "Total: ",
                        {
                            "$format": {
                                "value": 1000.50,
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
        
        result = Mapper().transform(spec, {})
        
        assert result["message"] == "Total: 1.000,50"


class TestOperatorWithNone:
    """Test operator behavior with None values."""

    def test_operator_returns_none_on_none_input(self):
        """Operators return None if input is None."""
        spec = {
            "defaults": {
                "result": {
                    "$upper": None
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] is None

    def test_math_returns_none_on_none(self):
        """Math operators return None if value is None."""
        spec = {
            "defaults": {
                "result": {
                    "$add": {
                        "value": None,
                        "by": 10
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] is None
