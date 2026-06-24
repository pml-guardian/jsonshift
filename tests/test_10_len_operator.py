"""Test the $len operator (length of strings, lists and dicts)."""
import pytest
from jsonshift import Mapper


class TestLenBasics:
    """$len returns the length of strings, lists and dicts."""

    def test_len_of_string(self):
        """`$len` returns the number of characters in a string."""
        spec = {"defaults": {"size": {"$len": {"$path": "doc"}}}}

        result = Mapper().transform(spec, {"doc": "52998224725"})

        assert result["size"] == 11

    def test_len_of_longer_string(self):
        """`$len` counts every character (CNPJ has 14 digits)."""
        spec = {"defaults": {"size": {"$len": {"$path": "doc"}}}}

        result = Mapper().transform(spec, {"doc": "12345678000199"})

        assert result["size"] == 14

    def test_len_of_list(self):
        """`$len` returns the number of items in a resolved list."""
        spec = {"defaults": {"count": {"$len": {"$path": "items"}}}}

        result = Mapper().transform(spec, {"items": [1, 2, 3, 4]})

        assert result["count"] == 4

    def test_len_of_empty_list(self):
        """`$len` of an empty list is 0."""
        spec = {"defaults": {"count": {"$len": {"$path": "items"}}}}

        result = Mapper().transform(spec, {"items": []})

        assert result["count"] == 0

    def test_len_of_dict(self):
        """`$len` of a dict returns its number of keys."""
        spec = {"defaults": {"keys": {"$len": {"$path": "obj"}}}}

        result = Mapper().transform(spec, {"obj": {"a": 1, "b": 2}})

        assert result["keys"] == 2

    def test_len_of_literal_string(self):
        """`$len` accepts a plain literal value as its operand."""
        spec = {"defaults": {"size": {"$len": "abc"}}}

        result = Mapper().transform(spec, {})

        assert result["size"] == 3


class TestLenNoneAndMissing:
    """$len propagates None and _MISSING like other operators."""

    def test_len_of_none_returns_none(self):
        """`$len` returns None when the operand resolves to None."""
        spec = {"defaults": {"size": {"$len": {"$path": "doc"}}}}

        result = Mapper().transform(spec, {"doc": None})

        assert result["size"] is None

    def test_len_missing_skips_field(self):
        """`$len` propagates _MISSING when an optional path is absent (field omitted)."""
        spec = {"defaults": {"size": {"$len": {"$path": "doc", "optional": True}}}}

        result = Mapper().transform(spec, {})

        assert "size" not in result


class TestLenInvalidType:
    """$len rejects non-sized values."""

    def test_len_of_int_raises(self):
        """`$len` of an int raises ValueError."""
        spec = {"defaults": {"size": {"$len": {"$path": "n"}}}}

        with pytest.raises(ValueError):
            Mapper().transform(spec, {"n": 42})

    def test_len_of_float_raises(self):
        """`$len` of a float raises ValueError."""
        spec = {"defaults": {"size": {"$len": {"$path": "n"}}}}

        with pytest.raises(ValueError):
            Mapper().transform(spec, {"n": 3.14})

    def test_len_of_bool_raises(self):
        """`$len` of a bool raises ValueError (bool is not sized)."""
        spec = {"defaults": {"size": {"$len": {"$path": "flag"}}}}

        with pytest.raises(ValueError):
            Mapper().transform(spec, {"flag": True})


class TestLenComposition:
    """$len composes with conditions and other operators."""

    def test_len_inside_if_pf(self):
        """11-digit document resolves to PF via `$len` + `$eq` inside `$if`."""
        spec = {
            "defaults": {
                "person_type": {
                    "$if": {
                        "condition": {"$eq": [{"$len": {"$path": "borrower.document"}}, 11]},
                        "then": "PF",
                        "else": "PJ",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"borrower": {"document": "52998224725"}})

        assert result["person_type"] == "PF"

    def test_len_inside_if_pj(self):
        """14-digit document resolves to PJ via `$len` + `$eq` inside `$if`."""
        spec = {
            "defaults": {
                "person_type": {
                    "$if": {
                        "condition": {"$eq": [{"$len": {"$path": "borrower.document"}}, 11]},
                        "then": "PF",
                        "else": "PJ",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"borrower": {"document": "12345678000199"}})

        assert result["person_type"] == "PJ"

    def test_len_as_comparison_operand(self):
        """`$len` can feed an ordering comparison."""
        spec = {"defaults": {"long": {"$gt": [{"$len": {"$path": "name"}}, 3]}}}

        assert Mapper().transform(spec, {"name": "John"})["long"] is True
        assert Mapper().transform(spec, {"name": "Al"})["long"] is False
