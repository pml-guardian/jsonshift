"""Test wildcards and deep nesting."""
import pytest
from jsonshift import Mapper


class TestSimpleWildcards:
    """Test simple wildcard [*] operations."""

    def test_wildcard_on_flat_list(self):
        """Wildcard on simple array."""
        payload = {"numbers": [1, 2, 3, 4, 5]}
        spec = {"map": {"results[*]": "numbers[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["results"] == [1, 2, 3, 4, 5]

    def test_wildcard_on_list_of_objects(self):
        """Wildcard extracts field from each object."""
        payload = {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
                {"id": 3, "name": "Charlie"}
            ]
        }
        spec = {"map": {"ids[*]": "users[*].id"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["ids"] == [1, 2, 3]

    def test_wildcard_multiple_fields(self):
        """Wildcard with multiple field extractions."""
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
        
        assert len(result["users_out"]) == 2
        assert result["users_out"][0] == {"id": 1, "name": "Alice"}
        assert result["users_out"][1] == {"id": 2, "name": "Bob"}


class TestDoubleWildcards:
    """Test double nested wildcards [*].[*]."""

    def test_double_wildcard_flattening(self):
        """Double wildcard flattens nested arrays."""
        payload = {
            "groups": [
                {
                    "items": [
                        {"value": 1},
                        {"value": 2}
                    ]
                },
                {
                    "items": [
                        {"value": 3}
                    ]
                }
            ]
        }
        spec = {"map": {"all_values[*]": "groups[*].items[*].value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["all_values"] == [1, 2, 3]

    def test_double_wildcard_object_structure(self):
        """Double wildcard preserves structure."""
        payload = {
            "departments": [
                {
                    "name": "Engineering",
                    "members": [
                        {"id": 1},
                        {"id": 2}
                    ]
                },
                {
                    "name": "Sales",
                    "members": [
                        {"id": 3}
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "depts[*].dept_name": "departments[*].name",
                "depts[*].member_ids[*]": "departments[*].members[*].id"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["depts"][0]["dept_name"] == "Engineering"
        assert result["depts"][0]["member_ids"] == [1, 2]
        assert result["depts"][1]["dept_name"] == "Sales"
        assert result["depts"][1]["member_ids"] == [3]


class TestTripleWildcards:
    """Test triple nested wildcards [*].[*].[*]."""

    def test_triple_wildcard_flattening(self):
        """Triple wildcard flattens three levels."""
        payload = {
            "companies": [
                {
                    "departments": [
                        {
                            "teams": [
                                {"id": 1},
                                {"id": 2}
                            ]
                        },
                        {
                            "teams": [
                                {"id": 3}
                            ]
                        }
                    ]
                },
                {
                    "departments": [
                        {
                            "teams": [
                                {"id": 4}
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {"map": {"all_team_ids[*]": "companies[*].departments[*].teams[*].id"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["all_team_ids"] == [1, 2, 3, 4]

    def test_triple_wildcard_complex_structure(self):
        """Triple wildcard with complex structure."""
        payload = {
            "a": [
                {
                    "b": [
                        {
                            "c": [
                                {"value": 100, "name": "A"},
                                {"value": 200, "name": "B"}
                            ]
                        }
                    ]
                },
                {
                    "b": [
                        {
                            "c": [
                                {"value": 300, "name": "C"}
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "values[*]": "a[*].b[*].c[*].value",
                "names[*]": "a[*].b[*].c[*].name"
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["values"] == [100, 200, 300]
        assert result["names"] == ["A", "B", "C"]


class TestQuadrupleWildcards:
    """Test quadruple nested wildcards [*].[*].[*].[*]."""

    def test_quadruple_wildcard(self):
        """Quadruple wildcard four levels deep."""
        payload = {
            "level1": [
                {
                    "level2": [
                        {
                            "level3": [
                                {
                                    "level4": [
                                        {"id": 1},
                                        {"id": 2}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {"map": {"ids[*]": "level1[*].level2[*].level3[*].level4[*].id"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["ids"] == [1, 2]

    def test_quadruple_wildcard_real_world(self):
        """Quadruple wildcard in realistic structure."""
        payload = {
            "organizations": [
                {
                    "divisions": [
                        {
                            "departments": [
                                {
                                    "teams": [
                                        {"member_count": 5},
                                        {"member_count": 3}
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {"map": {"counts[*]": "organizations[*].divisions[*].departments[*].teams[*].member_count"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["counts"] == [5, 3]


class TestMixedIndexAndWildcard:
    """Test mixing fixed indices with wildcards."""

    def test_index_then_wildcard(self):
        """Fixed index followed by wildcard."""
        payload = {
            "departments": [
                {
                    "name": "Engineering",
                    "members": [{"id": 1}, {"id": 2}]
                },
                {
                    "name": "Sales",
                    "members": [{"id": 3}]
                }
            ]
        }
        spec = {"map": {"eng_member_ids[*]": "departments[0].members[*].id"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["eng_member_ids"] == [1, 2]

    def test_wildcard_then_index(self):
        """Wildcard followed by fixed index."""
        payload = {
            "departments": [
                {
                    "members": [
                        {"id": 1, "name": "Alice"},
                        {"id": 2, "name": "Bob"}
                    ]
                },
                {
                    "members": [
                        {"id": 3, "name": "Charlie"}
                    ]
                }
            ]
        }
        spec = {"map": {"first_in_each[*]": "departments[*].members[0].name"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["first_in_each"] == ["Alice", "Charlie"]

    def test_alternating_index_wildcard(self):
        """Alternating indices and wildcards."""
        payload = {
            "companies": [
                {
                    "offices": [
                        {
                            "floors": [
                                {"rooms": [{"num": 1}, {"num": 2}]},
                                {"rooms": [{"num": 3}]}
                            ]
                        },
                        {
                            "floors": [
                                {"rooms": [{"num": 4}, {"num": 5}]}
                            ]
                        }
                    ]
                }
            ]
        }
        spec = {"map": {"room_nums[*]": "companies[0].offices[*].floors[0].rooms[*].num"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["room_nums"] == [1, 2, 4, 5]


class TestWildcardWithOptional:
    """Test wildcard behavior with optional."""

    def test_optional_field_in_wildcard(self):
        """Optional field inside wildcard array."""
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

    def test_optional_in_double_wildcard(self):
        """Optional in double wildcard context."""
        payload = {
            "departments": [
                {
                    "members": [
                        {"id": 1, "phone": "555-1234"},
                        {"id": 2}
                    ]
                },
                {
                    "members": [
                        {"id": 3, "phone": "555-5678"}
                    ]
                }
            ]
        }
        spec = {
            "map": {
                "member_ids[*]": "departments[*].members[*].id",
                "phones[*]": {
                    "path": "departments[*].members[*].phone",
                    "optional": True
                }
            }
        }
        
        result = Mapper().transform(spec, payload)
        
        assert result["member_ids"] == [1, 2, 3]
        assert result["phones"] == ["555-1234", "555-5678"]


class TestWildcardStructureCreation:
    """Test creating structures with wildcards."""

    def test_create_array_with_defaults(self):
        """Create array structure with defaults."""
        spec = {
            "defaults": {
                "items[*].status": "pending"
            }
        }
        
        result = Mapper().transform(spec, {})
        
        assert "items" in result
        assert len(result["items"]) > 0

    def test_fixed_index_creates_empty_elements(self):
        """Fixed index creates empty elements before it."""
        payload = {"value": "test"}
        spec = {"map": {"items[3]": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert len(result["items"]) == 4
        assert result["items"][0] == {}
        assert result["items"][3] == "test"

    def test_nested_array_creation(self):
        """Create nested array structures."""
        payload = {"value": 100}
        spec = {"map": {"a[*].b[*].c": "value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert "a" in result
        assert isinstance(result["a"], list)
        assert isinstance(result["a"][0]["b"], list)


class TestEmptyAndEdgeWildcards:
    """Test wildcard edge cases."""

    def test_wildcard_on_empty_array(self):
        """Wildcard on empty array returns empty result."""
        payload = {"items": []}
        spec = {"map": {"results[*]": "items[*]"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result.get("results", []) == [] or "results" not in result

    def test_wildcard_preserves_order(self):
        """Wildcard preserves array order."""
        payload = {
            "items": [
                {"value": "z"},
                {"value": "a"},
                {"value": "m"}
            ]
        }
        spec = {"map": {"values[*]": "items[*].value"}}
        
        result = Mapper().transform(spec, payload)
        
        assert result["values"] == ["z", "a", "m"]

    def test_wildcard_deep_nesting_without_error(self):
        """Wildcard works with very deep nesting."""
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
