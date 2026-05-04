"""Test $any operator."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestAnyBasic:
    """$any returns True when at least one item matches."""

    def test_match_first_item(self):
        spec = {"defaults": {"found": {"$any": {"path": "alerts[*].code", "eq": 1}}}}
        payload = {"alerts": [{"code": 1}, {"code": 2}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_match_last_item(self):
        spec = {"defaults": {"found": {"$any": {"path": "alerts[*].code", "eq": 2}}}}
        payload = {"alerts": [{"code": 1}, {"code": 2}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_no_match_returns_false(self):
        spec = {"defaults": {"found": {"$any": {"path": "alerts[*].code", "eq": 99}}}}
        payload = {"alerts": [{"code": 1}, {"code": 2}]}
        assert Mapper().transform(spec, payload)["found"] is False

    def test_empty_list_returns_false(self):
        spec = {"defaults": {"found": {"$any": {"path": "alerts[*].code", "eq": 1}}}}
        payload = {"alerts": []}
        assert Mapper().transform(spec, payload)["found"] is False

    def test_missing_path_returns_false(self):
        spec = {"defaults": {"found": {"$any": {"path": "alerts[*].code", "eq": 1}}}}
        payload = {}
        assert Mapper().transform(spec, payload)["found"] is False


class TestAnyComparators:
    """$any works with all comparison operators."""

    def test_ne(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "ne": 0}}}}
        payload = {"items": [{"val": 0}, {"val": 5}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_gt(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "gt": 10}}}}
        payload = {"items": [{"val": 5}, {"val": 15}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_gt_no_match(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "gt": 100}}}}
        payload = {"items": [{"val": 5}, {"val": 15}]}
        assert Mapper().transform(spec, payload)["found"] is False

    def test_gte(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "gte": 15}}}}
        payload = {"items": [{"val": 5}, {"val": 15}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_lt(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "lt": 3}}}}
        payload = {"items": [{"val": 1}, {"val": 10}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_lte(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "lte": 1}}}}
        payload = {"items": [{"val": 1}, {"val": 10}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_invalid_operator_raises(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].val", "contains": "x"}}}}
        payload = {"items": [{"val": "x"}]}
        with pytest.raises(ValueError, match="does not support operator"):
            Mapper().transform(spec, payload)


class TestAnyNoOperator:
    """$any without comparator checks for any truthy value."""

    def test_any_truthy(self):
        spec = {"defaults": {"found": {"$any": {"path": "flags[*].active"}}}}
        payload = {"flags": [{"active": False}, {"active": True}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_all_falsy_returns_false(self):
        spec = {"defaults": {"found": {"$any": {"path": "flags[*].active"}}}}
        payload = {"flags": [{"active": False}, {"active": None}]}
        assert Mapper().transform(spec, payload)["found"] is False


class TestAnyInIfCondition:
    """$any used as condition inside $if."""

    def test_any_as_if_condition_true(self):
        spec = {
            "defaults": {
                "has_termination": {
                    "$if": {
                        "condition": {"$any": {"path": "alerts[*].alert_type.code", "eq": 1}},
                        "then": True,
                        "else": False,
                    }
                }
            }
        }
        payload = {"alerts": [{"alert_type": {"code": 1}}, {"alert_type": {"code": 2}}]}
        assert Mapper().transform(spec, payload)["has_termination"] is True

    def test_any_as_if_condition_false(self):
        spec = {
            "defaults": {
                "has_termination": {
                    "$if": {
                        "condition": {"$any": {"path": "alerts[*].alert_type.code", "eq": 1}},
                        "then": True,
                        "else": False,
                    }
                }
            }
        }
        payload = {"alerts": [{"alert_type": {"code": 2}}, {"alert_type": {"code": 3}}]}
        assert Mapper().transform(spec, payload)["has_termination"] is False

    def test_any_as_if_condition_empty_alerts(self):
        spec = {
            "defaults": {
                "has_termination": {
                    "$if": {
                        "condition": {"$any": {"path": "alerts[*].alert_type.code", "eq": 1}},
                        "then": True,
                        "else": False,
                    }
                }
            }
        }
        payload = {"alerts": []}
        assert Mapper().transform(spec, payload)["has_termination"] is False

    def test_full_alert_spec(self):
        """Reproduces the real-world use case with has_termination, has_prior_notice, has_leave_of_absence."""
        spec = {
            "defaults": {
                "has_termination": {"$any": {"path": "alerts[*].alert_type.code", "eq": 1}},
                "has_prior_notice": {"$any": {"path": "alerts[*].alert_type.code", "eq": 2}},
                "has_leave_of_absence": {"$any": {"path": "alerts[*].alert_type.code", "eq": 2}},
            }
        }

        payload_with_code1 = {"alerts": [{"alert_type": {"code": 1}}]}
        result = Mapper().transform(spec, payload_with_code1)
        assert result["has_termination"] is True
        assert result["has_prior_notice"] is False
        assert result["has_leave_of_absence"] is False

        payload_with_code2 = {"alerts": [{"alert_type": {"code": 2}}]}
        result = Mapper().transform(spec, payload_with_code2)
        assert result["has_termination"] is False
        assert result["has_prior_notice"] is True
        assert result["has_leave_of_absence"] is True

        payload_empty = {"alerts": []}
        result = Mapper().transform(spec, payload_empty)
        assert result["has_termination"] is False
        assert result["has_prior_notice"] is False
        assert result["has_leave_of_absence"] is False
