"""Test the [+] append index in destination paths."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestAppendBasics:
    """[+] appends a single resolved element to the end of a list."""

    def test_append_after_mapped_items(self):
        """`[+]` appends one element after the elements produced by `map`."""
        spec = {
            "map": {"events[*].x": "items[*].a"},
            "defaults": {
                "events[+]": {
                    "type": "099",
                    "date": {"$path": "contract.maturity_date"},
                    "status": "1",
                }
            },
        }
        payload = {"contract": {"maturity_date": "2026-03-10"}, "items": [{"a": 1}]}

        result = Mapper().transform(spec, payload)

        assert result["events"] == [
            {"x": 1},
            {"type": "099", "date": "2026-03-10", "status": "1"},
        ]

    def test_append_creates_missing_list(self):
        """`[+]` creates the list when it does not exist yet."""
        spec = {"defaults": {"events[+]": {"k": "v"}}}

        result = Mapper().transform(spec, {})

        assert result["events"] == [{"k": "v"}]

    def test_append_under_nested_path(self):
        """`[+]` works under a nested object path."""
        spec = {"defaults": {"contract.events[+]": {"type": "099"}}}

        result = Mapper().transform(spec, {})

        assert result["contract"]["events"] == [{"type": "099"}]

    def test_append_after_fixed_index(self):
        """`[+]` works when preceded by a fixed list index."""
        spec = {"defaults": {"groups[0].events[+]": {"type": "099"}}}

        result = Mapper().transform(spec, {})

        assert result["groups"][0]["events"] == [{"type": "099"}]


class TestAppendMultiple:
    """Each [+] entry appends exactly one element."""

    def test_two_append_entries_on_distinct_lists(self):
        """Two `[+]` entries (distinct keys) each append one element."""
        spec = {
            "defaults": {
                "events[+]": {"type": "099"},
                "logs[+]": {"level": "info"},
            }
        }

        result = Mapper().transform(spec, {})

        assert result["events"] == [{"type": "099"}]
        assert result["logs"] == [{"level": "info"}]

    def test_append_after_multiple_mapped_items(self):
        """`[+]` appends after several mapped elements, preserving order."""
        spec = {
            "map": {"events[*].x": "items[*].a"},
            "defaults": {"events[+]": {"type": "end"}},
        }
        payload = {"items": [{"a": 1}, {"a": 2}, {"a": 3}]}

        result = Mapper().transform(spec, payload)

        assert result["events"] == [
            {"x": 1},
            {"x": 2},
            {"x": 3},
            {"type": "end"},
        ]


class TestAppendTemplateResolution:
    """The [+] template is resolved recursively (deep)."""

    def test_template_resolves_path(self):
        """`$path` inside the template resolves against the payload."""
        spec = {"defaults": {"events[+]": {"date": {"$path": "due"}}}}

        result = Mapper().transform(spec, {"due": "2026-01-01"})

        assert result["events"] == [{"date": "2026-01-01"}]

    def test_template_resolves_if(self):
        """`$if` inside the template resolves against the payload."""
        spec = {
            "defaults": {
                "events[+]": {
                    "kind": {
                        "$if": {
                            "condition": {"$eq": [{"$path": "amount"}, 0]},
                            "then": "zero",
                            "else": "nonzero",
                        }
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"amount": 0})

        assert result["events"] == [{"kind": "zero"}]

    def test_template_resolves_len(self):
        """`$len` inside the template resolves against the payload."""
        spec = {"defaults": {"events[+]": {"size": {"$len": {"$path": "doc"}}}}}

        result = Mapper().transform(spec, {"doc": "52998224725"})

        assert result["events"] == [{"size": 11}]

    def test_template_resolves_nested_objects(self):
        """Deeply nested operators inside the template resolve."""
        spec = {
            "defaults": {
                "events[+]": {
                    "meta": {"who": {"$upper": {"$path": "name"}}},
                    "tags": ["x", {"$path": "code"}],
                }
            }
        }

        result = Mapper().transform(spec, {"name": "john", "code": "A1"})

        assert result["events"] == [{"meta": {"who": "JOHN"}, "tags": ["x", "A1"]}]

    def test_template_drops_missing_leaf(self):
        """A leaf resolving to _MISSING is dropped from the appended element."""
        spec = {
            "defaults": {
                "events[+]": {
                    "type": "099",
                    "extra": {"$path": "absent", "optional": True},
                }
            }
        }

        result = Mapper().transform(spec, {})

        assert result["events"] == [{"type": "099"}]


class TestAppendErrors:
    """[+] is write-only, terminal, and incompatible with wildcards."""

    def test_wildcard_before_append_raises(self):
        """`[*]` before `[+]` raises a clear error."""
        spec = {"defaults": {"a[*].b[+]": {"k": 1}}}

        with pytest.raises(ValueError, match=r"\[\+\] cannot be combined with wildcards"):
            Mapper().transform(spec, {"a": [{}]})

    def test_append_not_terminal_raises(self):
        """`[+]` that is not the final segment raises a clear error."""
        spec = {"defaults": {"a[+].b": "x"}}

        with pytest.raises(ValueError, match=r"\[\+\] is only supported as the final"):
            Mapper().transform(spec, {})

    def test_read_append_in_map_source_raises(self):
        """Using `[+]` to read (map source) raises ValueError."""
        spec = {"map": {"out": "items[+]"}}

        with pytest.raises(ValueError, match=r"\[\+\] is write-only"):
            Mapper().transform(spec, {"items": [1, 2]})


class TestAppendBackwardCompat:
    """Specs without [+] keep their exact previous behavior."""

    def test_plain_default_dict_not_deep_resolved(self):
        """A normal (non-`[+]`) default dict is stored as-is, not deep-resolved."""
        spec = {"defaults": {"meta": {"date": {"$path": "due"}}}}

        result = Mapper().transform(spec, {"due": "2026-01-01"})

        # Without [+], the literal dict is kept verbatim (operator NOT resolved).
        assert result["meta"] == {"date": {"$path": "due"}}

    def test_basic_mapping_unchanged(self):
        """A basic map still works exactly as before."""
        spec = {"map": {"customer.name": "name", "customer.cpf": "cpf"}}

        result = Mapper().transform(spec, {"name": "John", "cpf": "123"})

        assert result == {"customer": {"name": "John", "cpf": "123"}}
