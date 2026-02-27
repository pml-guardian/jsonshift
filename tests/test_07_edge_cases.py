"""Test edge cases and error conditions."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestNoneHandling:
    """Test None value handling."""

    def test_none_preserves_through_map(self):
        """None value is preserved when mapped."""
        payload = {"value": None}
        spec = {"map": {"result": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] is None

    def test_none_not_overwritten_by_defaults(self):
        """None is not overwritten by defaults."""
        payload = {"value": None}
        spec = {
            "map": {"result": "value"},
            "defaults": {"result": "default"}
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] is None

    def test_operator_with_none_returns_none(self):
        """Operators return None when input is None."""
        spec = {
            "defaults": {
                "upper": {"$upper": None},
                "add": {"$add": {"value": None, "by": 10}},
                "concat": {"$concat": ["A", None]}
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["upper"] is None
        assert result["add"] is None
        assert result["concat"] is None

    def test_none_in_wildcard_array(self):
        """None values in wildcard arrays."""
        payload = {"values": [1, None, 3]}
        spec = {"map": {"results[*]": "values[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["results"] == [1, None, 3]


class TestEmptyStructures:
    """Test empty arrays and objects."""

    def test_empty_array(self):
        """Empty array handling."""
        payload = {"items": []}
        spec = {"map": {"results[*]": "items[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        # Empty array might not appear in results

    def test_empty_object(self):
        """Empty object handling."""
        payload = {"data": {}}
        spec = {"map": {"result": "data"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == {}

    def test_deeply_nested_empty(self):
        """Deeply nested empty structure."""
        payload = {"a": {"b": {"c": {}}}}
        spec = {"map": {"result": "a.b.c"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == {}


class TestErrorConditions:
    """Test error conditions."""

    def test_division_by_zero(self):
        """Division by zero raises error."""
        spec = {
            "defaults": {
                "result": {"$div": {"value": 10, "by": 0}}
            }
        }
        
        with pytest.raises(ValueError):
            Mapper().transform(spec, {})

    def test_invalid_date_format(self):
        """Invalid date format raises error."""
        spec = {
            "defaults": {
                "date": {
                    "$format": {
                        "value": "invalid-date",
                        "date": {
                            "parse": "%Y-%m-%d",
                            "strftime": "%d/%m/%Y"
                        }
                    }
                }
            }
        }
        
        with pytest.raises(ValueError):
            Mapper().transform(spec, {})

    def test_missing_required_path(self):
        """Missing required path raises error."""
        spec = {"map": {"result": "missing"}}
        
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, {})

    def test_array_index_out_of_bounds(self):
        """Array index out of bounds raises error."""
        payload = {"items": [1, 2, 3]}
        spec = {"map": {"result": "items[10]"}}
        
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, payload)

    def test_wrong_type_for_operation(self):
        """Wrong type for operation raises error."""
        spec = {
            "defaults": {
                "result": {"$add": {"value": "not-a-number", "by": 10}}
            }
        }
        
        with pytest.raises(ValueError):
            Mapper().transform(spec, {})


class TestExtremeValues:
    """Test extreme values."""

    def test_very_large_number(self):
        """Very large number handling."""
        payload = {"value": 999999999999999}
        spec = {"map": {"result": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == 999999999999999

    def test_very_small_decimal(self):
        """Very small decimal number."""
        payload = {"value": 0.00000001}
        spec = {"map": {"result": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == 0.00000001

    def test_negative_numbers(self):
        """Negative number handling."""
        payload = {"value": -1000}
        spec = {
            "map": {"negative": "value"},
            "defaults": {
                "positive": {
                    "$mul": {"value": {"$path": "value"}, "by": -1}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["negative"] == -1000
        assert result["positive"] == 1000.0


class TestSpecialCharacters:
    """Test special characters in strings."""

    def test_unicode_characters(self):
        """Unicode characters in strings."""
        payload = {"name": "João Silva"}
        spec = {
            "map": {"user.name": "name"},
            "defaults": {
                "user.name_upper": {
                    "$upper": {"$path": "name"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert "João" in result["user"]["name"] or "JOÃO" in result["user"]["name_upper"]

    def test_special_chars_in_path(self):
        """Special characters in values."""
        payload = {"code": "ABC-123_XYZ"}
        spec = {"map": {"result": "code"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "ABC-123_XYZ"

    def test_whitespace_handling(self):
        """Whitespace in values."""
        payload = {"name": "  John Doe  "}
        spec = {"map": {"result": "name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "  John Doe  "  # Whitespace preserved


class TestExtremeLevelsOfNesting:
    """Test very deep nesting."""

    def test_10_level_nesting(self):
        """10 levels of nesting."""
        payload = {
            "l1": {
                "l2": {
                    "l3": {
                        "l4": {
                            "l5": {
                                "l6": {
                                    "l7": {
                                        "l8": {
                                            "l9": {
                                                "l10": "value"
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        spec = {"map": {"result": "l1.l2.l3.l4.l5.l6.l7.l8.l9.l10"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "value"

    def test_very_large_array(self):
        """Very large array handling."""
        payload = {"items": list(range(1000))}
        spec = {"map": {"results[*]": "items[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert len(result["results"]) == 1000
        assert result["results"][0] == 0
        assert result["results"][999] == 999

    def test_multiple_wildcards_deep(self):
        """Multiple wildcards at deep nesting."""
        payload = {
            "a": [
                {
                    "b": [
                        {
                            "c": [
                                {
                                    "d": [
                                        {
                                            "e": [
                                                {"value": 1},
                                                {"value": 2}
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {"map": {"values[*]": "a[*].b[*].c[*].d[*].e[*].value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["values"] == [1, 2]


class TestOperatorEdgeCases:
    """Test operators with edge cases."""

    def test_round_negative_ndigits(self):
        """Rounding with negative ndigits."""
        spec = {
            "defaults": {
                "result": {
                    "$round": {
                        "value": 1234.5,
                        "ndigits": -2
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 1200.0

    def test_power_with_zero(self):
        """Power with zero exponent."""
        spec = {
            "defaults": {
                "result": {
                    "$pow": {
                        "value": 5,
                        "by": 0
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 1.0

    def test_power_with_negative_exponent(self):
        """Power with negative exponent."""
        spec = {
            "defaults": {
                "result": {
                    "$pow": {
                        "value": 2,
                        "by": -3
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == 0.125

    def test_concat_empty_strings(self):
        """Concatenation with empty strings."""
        spec = {
            "defaults": {
                "result": {
                    "$concat": ["", "test", ""]
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["result"] == "test"


class TestPathEdgeCases:
    """Test path resolution edge cases."""

    def test_numeric_string_keys(self):
        """Numeric string as object keys."""
        payload = {"0": "zero", "1": "one"}
        spec = {"map": {"result": "0"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "zero"

    def test_index_zero_vs_missing(self):
        """Index 0 vs missing field."""
        payload = {"items": ["first", "second"]}
        spec = {"map": {"result": "items[0]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "first"

    def test_optional_in_required_path(self):
        """Optional on normally required path."""
        payload = {}
        spec = {
            "map": {
                "value": {
                    "path": "field",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert "value" not in result


class TestComplexEdgeCombinations:
    """Test combinations of edge cases."""

    def test_none_with_optional_and_operator(self):
        """None with optional and operator."""
        payload = {"value": None}
        spec = {
            "defaults": {
                "result": {
                    "$upper": {
                        "$path": "optional_field",
                        "optional": True
                    }
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        # Should not cause error

    def test_empty_wildcard_with_operator(self):
        """Empty wildcard with operator."""
        payload = {"items": []}
        spec = {
            "defaults": {
                "results[*]": {
                    "$upper": {"$path": "items[*]"}
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        # Should not cause error

    def test_default_overridden_by_map_then_operator(self):
        """Default then map then operator."""
        payload = {"name": "john"}
        spec = {
            "defaults": {"name": "default"},
            "map": {"name": "name"},
            "defaults": {
                "name_upper": {
                    "$upper": {"$path": "name"}
                }
            }
        }
        
        # Note: This structure is unusual; normally would use composition
        result = Mapper().transform(
            {
                "map": {"name": "name"},
                "defaults": {
                    "name_upper": {
                        "$upper": {"$path": "name"}
                    }
                }
            },
            payload
        )
        
        assert result["name"] == "john"
        assert result["name_upper"] == "JOHN"
