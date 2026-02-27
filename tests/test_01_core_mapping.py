"""Test core mapping functionality (map and defaults)."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestBasicMapping:
    """Test basic map functionality."""

    def test_simple_field_mapping(self):
        """Map a simple field."""
        payload = {"name": "John"}
        spec = {"map": {"user.name": "name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["name"] == "John"

    def test_multiple_fields_mapping(self):
        """Map multiple fields."""
        payload = {"name": "John", "email": "john@example.com"}
        spec = {
            "map": {
                "user.name": "name",
                "user.email": "email"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["name"] == "John"
        assert result["user"]["email"] == "john@example.com"

    def test_deep_nested_mapping(self):
        """Map into deeply nested structure."""
        payload = {"cpf": "12345678901"}
        spec = {
            "map": {
                "customer.document.type": "cpf"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["customer"]["document"]["type"] == "12345678901"


class TestDefaultsMapping:
    """Test defaults functionality."""

    def test_simple_default(self):
        """Set a simple default value."""
        spec = {
            "defaults": {
                "status": "active"
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["status"] == "active"

    def test_default_creates_structure(self):
        """Default can create nested structure."""
        spec = {
            "defaults": {
                "config.timeout": 30,
                "config.retries": 3
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert result["config"]["timeout"] == 30
        assert result["config"]["retries"] == 3

    def test_defaults_do_not_override_map(self):
        """Defaults do not override mapped values."""
        payload = {"status": "inactive"}
        spec = {
            "map": {"status": "status"},
            "defaults": {"status": "active"}
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["status"] == "inactive"


class TestErrorHandling:
    """Test error handling."""

    def test_missing_source_raises_error(self):
        """Missing source path raises MappingMissingError."""
        spec = {"map": {"user.name": "name"}}
        
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, {})

    def test_missing_optional_source_does_not_raise(self):
        """Missing optional source does not raise error."""
        spec = {
            "map": {
                "user.name": {
                    "path": "name",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert "user" not in result or "name" not in result.get("user", {})

    def test_none_value_is_preserved(self):
        """None value from source is preserved."""
        payload = {"name": None}
        spec = {"map": {"user.name": "name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["name"] is None

    def test_none_is_not_overwritten_by_default(self):
        """Default does not override None value."""
        payload = {"name": None}
        spec = {
            "map": {"user.name": "name"},
            "defaults": {"user.name": "Unknown"}
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["name"] is None


class TestMapAndDefaultsTogether:
    """Test map and defaults working together."""

    def test_complete_transformation(self):
        """Full map and defaults together."""
        payload = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30
        }
        spec = {
            "map": {
                "customer.name": "first_name",
                "customer.last_name": "last_name",
                "customer.age": "age"
            },
            "defaults": {
                "customer.status": "active",
                "customer.type": "individual"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["customer"]["name"] == "John"
        assert result["customer"]["last_name"] == "Doe"
        assert result["customer"]["age"] == 30
        assert result["customer"]["status"] == "active"
        assert result["customer"]["type"] == "individual"

    def test_map_then_defaults_order(self):
        """Map values take precedence over defaults."""
        payload = {"count": 5}
        spec = {
            "map": {"total.count": "count"},
            "defaults": {
                "total.count": 10,
                "total.page": 1
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["total"]["count"] == 5  # From map
        assert result["total"]["page"] == 1   # From defaults
