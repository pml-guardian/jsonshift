"""Test path parsing and resolution."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestSimplePaths:
    """Test simple path resolution."""

    def test_resolve_simple_field(self):
        """Resolve simple field without nesting."""
        payload = {"name": "John"}
        spec = {"map": {"user": "name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"] == "John"

    def test_resolve_nested_field(self):
        """Resolve nested field with dots."""
        payload = {"user": {"name": "John"}}
        spec = {"map": {"extracted": "user.name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["extracted"] == "John"

    def test_resolve_three_level_nesting(self):
        """Resolve three levels deep."""
        payload = {"a": {"b": {"c": "value"}}}
        spec = {"map": {"result": "a.b.c"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "value"


class TestIndexedPaths:
    """Test indexed path resolution."""

    def test_resolve_index_zero(self):
        """Resolve first element of array."""
        payload = {"items": ["first", "second"]}
        spec = {"map": {"result": "items[0]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == "first"

    def test_resolve_specific_index(self):
        """Resolve specific array index."""
        payload = {"items": [10, 20, 30, 40]}
        spec = {"map": {"result": "items[2]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == 30

    def test_resolve_nested_indexed_path(self):
        """Resolve nested path with index."""
        payload = {
            "users": [
                {"name": "Alice"},
                {"name": "Bob"}
            ]
        }
        spec = {"map": {"second_user": "users[1].name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["second_user"] == "Bob"


class TestWildcardPaths:
    """Test wildcard path resolution."""

    def test_simple_wildcard(self):
        """Resolve wildcard [*] on simple array."""
        payload = {"ids": [1, 2, 3]}
        spec = {"map": {"results[*]": "ids[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["results"] == [1, 2, 3]

    def test_wildcard_on_objects(self):
        """Resolve wildcard on array of objects."""
        payload = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        spec = {"map": {"ids[*]": "users[*].id"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["ids"] == [1, 2]

    def test_wildcard_preserves_structure(self):
        """Wildcard preserves object structure."""
        payload = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
        spec = {
            "map": {
                "users_out[*].id": "users[*].id",
                "users_out[*].name": "users[*].name"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["users_out"][0]["id"] == 1
        assert result["users_out"][0]["name"] == "Alice"
        assert result["users_out"][1]["id"] == 2
        assert result["users_out"][1]["name"] == "Bob"


class TestOptionalPaths:
    """Test optional path resolution."""

    def test_optional_missing_field(self):
        """Optional missing field doesn't cause error."""
        payload = {"name": "John"}
        spec = {
            "map": {
                "user.name": "name",
                "user.nickname": {
                    "path": "nickname",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["name"] == "John"
        assert "nickname" not in result["user"]

    def test_optional_present_field(self):
        """Optional present field is used."""
        payload = {"name": "John", "nickname": "Johnny"}
        spec = {
            "map": {
                "user.name": "name",
                "user.nickname": {
                    "path": "nickname",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["user"]["nickname"] == "Johnny"

    def test_optional_in_wildcard(self):
        """Optional works inside wildcard arrays."""
        payload = {
            "users": [
                {"id": 1, "nickname": "alice"},
                {"id": 2},
                {"id": 3, "nickname": "charlie"}
            ]
        }
        spec = {
            "map": {
                "ids[*]": "users[*].id",
                "nicknames[*]": {
                    "path": "users[*].nickname",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["ids"] == [1, 2, 3]
        assert result["nicknames"] == ["alice", "charlie"]


class TestComplexPathCombinations:
    """Test complex path combinations."""

    def test_mixed_index_and_wildcard(self):
        """Mix indexed and wildcard paths."""
        payload = {
            "departments": [
                {
                    "name": "Engineering",
                    "members": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"}
                    ]
                },
                {
                    "name": "Sales",
                    "members": [
                        {"id": 3, "name": "Charlie"}
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "eng_members[*]": "departments[0].members[*].id"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["eng_members"] == [1, 2]

    def test_multiple_wildcards_nested(self):
        """Multiple wildcards in single path."""
        payload = {
            "groups": [
                {
                    "users": [
                        {"id": 1},
                        {"id": 2}
                    ]
                },
                {
                    "users": [
                        {"id": 3}
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "all_ids[*]": "groups[*].users[*].id"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["all_ids"] == [1, 2, 3]

    def test_deep_path_with_multiple_indices(self):
        """Deep path with multiple fixed indices."""
        payload = {
            "data": [
                {
                    "items": [
                        {"values": [10, 20, 30]}
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "result": "data[0].items[0].values[1]"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["result"] == 20


class TestPathWithMissingElements:
    """Test path resolution with missing elements."""

    def test_missing_intermediate_key(self):
        """Missing intermediate key raises error."""
        payload = {"user": {}}
        spec = {"map": {"name": "user.profile.name"}}
        
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, payload)

    def test_missing_array_index(self):
        """Array index out of bounds raises error."""
        payload = {"items": [1, 2]}
        spec = {"map": {"result": "items[5]"}}
        
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, payload)

    def test_optional_missing_nested(self):
        """Optional missing nested path."""
        payload = {"user": {}}
        spec = {
            "map": {
                "name": {
                    "path": "user.profile.name",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert "name" not in result


class TestPathCreation:
    """Test path creation in output."""

    def test_create_simple_nested(self):
        """Create simple nested structure."""
        payload = {"value": 10}
        spec = {"map": {"a.b.c": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["a"]["b"]["c"] == 10

    def test_create_array_at_index(self):
        """Create array structure at specific index."""
        payload = {"value": "test"}
        spec = {"map": {"items[2]": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert len(result["items"]) == 3
        assert result["items"][0] == {}
        assert result["items"][1] == {}
        assert result["items"][2] == "test"

    def test_create_nested_array_structure(self):
        """Create nested array structures."""
        payload = {"value": 100}
        spec = {"map": {"a[0].b[1].c": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["a"][0]["b"][1]["c"] == 100
