"""Test predicate operators: $and, $or, $not, $exists, $all, $find, $filter and $any/where."""
import pytest
from datetime import date
from jsonshift import Mapper, MappingMissingError


TODAY = {"$format": {"value": {"$now": "date"}, "date": {"strftime": "%Y-%m-%d"}}}

HAS_LEAVE_OF_ABSENCE = {
    "$any": {
        "path": "meta_data.alerts[*]",
        "where": {
            "$and": [
                {"$not": {"$eq": [{"$path": "alert_type.code"}, 15]}},
                {
                    "$or": [
                        {"$eq": [{"$path": "absence_end_date"}, ""]},
                        {"$not": {"$lt": [{"$path": "absence_end_date"}, TODAY]}},
                    ]
                },
            ]
        },
    }
}


def _has_leave_of_absence(meta_data: dict) -> bool:
    alerts = (meta_data or {}).get("alerts") or []
    today = date.today().strftime("%Y-%m-%d")
    alerts = [
        alert
        for alert in alerts
        if (alert.get("alert_type") or {}).get("code") != 15
        and (not alert.get("absence_end_date") or alert.get("absence_end_date") >= today)
    ]

    return len(alerts) > 0


class TestAndOperator:
    """$and returns True only when every condition is truthy."""

    def test_all_true(self):
        spec = {"defaults": {"ok": {"$and": [{"$eq": [1, 1]}, {"$gt": [5, 2]}]}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_one_false(self):
        spec = {"defaults": {"ok": {"$and": [{"$eq": [1, 1]}, {"$gt": [1, 2]}]}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_empty_list_is_true(self):
        spec = {"defaults": {"ok": {"$and": []}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_missing_is_falsy(self):
        spec = {"defaults": {"ok": {"$and": [{"$eq": [{"$path": "a", "optional": True}, 1]}]}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_reads_payload_values(self):
        spec = {
            "defaults": {
                "ok": {
                    "$and": [
                        {"$eq": [{"$path": "status"}, "active"]},
                        {"$gte": [{"$path": "score"}, 80]},
                    ]
                }
            }
        }
        assert Mapper().transform(spec, {"status": "active", "score": 90})["ok"] is True
        assert Mapper().transform(spec, {"status": "active", "score": 10})["ok"] is False

    def test_short_circuits_on_first_false(self):
        spec = {
            "defaults": {
                "ok": {"$and": [{"$exists": "absent"}, {"$gt": [{"$path": "absent"}, 1]}]}
            }
        }
        assert Mapper().transform(spec, {"other": 1})["ok"] is False

    def test_strict_path_after_a_true_condition_raises(self):
        spec = {"defaults": {"ok": {"$and": [{"$eq": [1, 1]}, {"$gt": [{"$path": "absent"}, 1]}]}}}
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, {})

    def test_zero_is_truthy(self):
        spec = {"defaults": {"ok": {"$and": [{"$path": "zero"}]}}}
        assert Mapper().transform(spec, {"zero": 0})["ok"] is True

    def test_null_is_falsy(self):
        spec = {"defaults": {"ok": {"$and": [{"$path": "nothing"}]}}}
        assert Mapper().transform(spec, {"nothing": None})["ok"] is False

    def test_not_a_list_raises(self):
        spec = {"defaults": {"ok": {"$and": {"$eq": [1, 1]}}}}
        with pytest.raises(ValueError, match=r"\$and must be a list"):
            Mapper().transform(spec, {})


class TestOrOperator:
    """$or returns True when at least one condition is truthy."""

    def test_one_true(self):
        spec = {"defaults": {"ok": {"$or": [{"$eq": [1, 2]}, {"$eq": [2, 2]}]}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_none_true(self):
        spec = {"defaults": {"ok": {"$or": [{"$eq": [1, 2]}, {"$eq": [3, 2]}]}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_empty_list_is_false(self):
        spec = {"defaults": {"ok": {"$or": []}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_short_circuits_on_first_true(self):
        spec = {"defaults": {"ok": {"$or": [{"$eq": [1, 1]}, {"$gt": [{"$path": "absent"}, 1]}]}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_not_a_list_raises(self):
        spec = {"defaults": {"ok": {"$or": "nope"}}}
        with pytest.raises(ValueError, match=r"\$or must be a list"):
            Mapper().transform(spec, {})


class TestNotOperator:
    """$not negates the truthiness of any expression."""

    def test_negates_true(self):
        spec = {"defaults": {"ok": {"$not": {"$eq": [1, 1]}}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_negates_false(self):
        spec = {"defaults": {"ok": {"$not": {"$eq": [1, 2]}}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_negates_missing_comparison(self):
        spec = {"defaults": {"ok": {"$not": {"$eq": [{"$path": "a", "optional": True}, 1]}}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_negates_null(self):
        spec = {"defaults": {"ok": {"$not": {"$path": "nothing"}}}}
        assert Mapper().transform(spec, {"nothing": None})["ok"] is True

    def test_negates_literal(self):
        spec = {"defaults": {"ok": {"$not": False}}}
        assert Mapper().transform(spec, {})["ok"] is True


class TestExistsOperator:
    """$exists checks presence without ever raising."""

    def test_present(self):
        spec = {"defaults": {"ok": {"$exists": "name"}}}
        assert Mapper().transform(spec, {"name": "John"})["ok"] is True

    def test_absent(self):
        spec = {"defaults": {"ok": {"$exists": "name"}}}
        assert Mapper().transform(spec, {})["ok"] is False

    def test_deep_absent_never_raises(self):
        spec = {"defaults": {"ok": {"$exists": "a.b.c.d"}}}
        assert Mapper().transform(spec, {"a": 1})["ok"] is False

    def test_null_is_missing_by_default(self):
        spec = {"defaults": {"ok": {"$exists": "phone"}}}
        assert Mapper().transform(spec, {"phone": None})["ok"] is False

    def test_null_counts_when_disabled(self):
        spec = {"defaults": {"ok": {"$exists": {"path": "phone", "null_is_missing": False}}}}
        assert Mapper().transform(spec, {"phone": None})["ok"] is True

    def test_empty_string_exists(self):
        spec = {"defaults": {"ok": {"$exists": "name"}}}
        assert Mapper().transform(spec, {"name": ""})["ok"] is True

    def test_indexed_path(self):
        spec = {"defaults": {"ok": {"$exists": "items[1].id"}}}
        assert Mapper().transform(spec, {"items": [{"id": 1}, {"id": 2}]})["ok"] is True
        assert Mapper().transform(spec, {"items": [{"id": 1}]})["ok"] is False

    def test_unknown_key_raises(self):
        spec = {"defaults": {"ok": {"$exists": {"path": "name", "nulls": True}}}}
        with pytest.raises(ValueError, match="does not support key"):
            Mapper().transform(spec, {"name": "John"})

    def test_invalid_expression_raises(self):
        spec = {"defaults": {"ok": {"$exists": 10}}}
        with pytest.raises(ValueError, match=r"\$exists must be a path string"):
            Mapper().transform(spec, {})


class TestAnyWhere:
    """$any with a per-item predicate."""

    def test_two_fields_of_the_same_item(self):
        spec = {
            "defaults": {
                "found": {
                    "$any": {
                        "path": "items[*]",
                        "where": {
                            "$and": [
                                {"$eq": [{"$path": "type"}, "A"]},
                                {"$gt": [{"$path": "value"}, 10]},
                            ]
                        },
                    }
                }
            }
        }
        assert Mapper().transform(spec, {"items": [{"type": "A", "value": 50}]})["found"] is True
        assert Mapper().transform(spec, {"items": [{"type": "A", "value": 1}]})["found"] is False
        assert Mapper().transform(spec, {"items": [{"type": "B", "value": 50}]})["found"] is False

    def test_does_not_mix_fields_across_items(self):
        spec = {
            "defaults": {
                "found": {
                    "$any": {
                        "path": "items[*]",
                        "where": {
                            "$and": [
                                {"$eq": [{"$path": "type"}, "A"]},
                                {"$gt": [{"$path": "value"}, 10]},
                            ]
                        },
                    }
                }
            }
        }
        payload = {"items": [{"type": "A", "value": 1}, {"type": "B", "value": 50}]}
        assert Mapper().transform(spec, payload)["found"] is False

    def test_missing_field_inside_where_does_not_raise(self):
        spec = {
            "defaults": {
                "found": {"$any": {"path": "items[*]", "where": {"$gt": [{"$path": "value"}, 10]}}}
            }
        }
        payload = {"items": [{"type": "A"}, {"type": "B", "value": 50}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_explicit_strict_path_inside_where_raises(self):
        spec = {
            "defaults": {
                "found": {
                    "$any": {
                        "path": "items[*]",
                        "where": {"$gt": [{"$path": "value", "optional": False}, 10]},
                    }
                }
            }
        }
        with pytest.raises(MappingMissingError):
            Mapper().transform(spec, {"items": [{"type": "A"}]})

    def test_absent_path_returns_false(self):
        spec = {
            "defaults": {
                "found": {"$any": {"path": "items[*]", "where": {"$eq": [{"$path": "id"}, 1]}}}
            }
        }
        assert Mapper().transform(spec, {})["found"] is False

    def test_nested_where(self):
        spec = {
            "defaults": {
                "found": {
                    "$any": {
                        "path": "orders[*]",
                        "where": {
                            "$any": {"path": "items[*]", "where": {"$eq": [{"$path": "sku"}, "X"]}}
                        },
                    }
                }
            }
        }
        payload = {"orders": [{"items": [{"sku": "Y"}]}, {"items": [{"sku": "X"}]}]}
        assert Mapper().transform(spec, payload)["found"] is True

    def test_legacy_comparator_still_works(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].code", "eq": 2}}}}
        assert Mapper().transform(spec, {"items": [{"code": 1}, {"code": 2}]})["found"] is True

    def test_where_with_comparator_raises(self):
        spec = {
            "defaults": {
                "found": {"$any": {"path": "items[*]", "where": {"$eq": [1, 1]}, "eq": 1}}
            }
        }
        with pytest.raises(ValueError, match="cannot combine 'where' with comparison operators"):
            Mapper().transform(spec, {"items": [{"code": 1}]})


class TestAllOperator:
    """$all returns True when every item matches."""

    def test_every_item_matches(self):
        spec = {"defaults": {"ok": {"$all": {"path": "items[*].code", "eq": 1}}}}
        assert Mapper().transform(spec, {"items": [{"code": 1}, {"code": 1}]})["ok"] is True

    def test_one_item_fails(self):
        spec = {"defaults": {"ok": {"$all": {"path": "items[*].code", "eq": 1}}}}
        assert Mapper().transform(spec, {"items": [{"code": 1}, {"code": 2}]})["ok"] is False

    def test_empty_list_is_true(self):
        spec = {"defaults": {"ok": {"$all": {"path": "items[*].code", "eq": 1}}}}
        assert Mapper().transform(spec, {"items": []})["ok"] is True

    def test_absent_path_is_true(self):
        spec = {"defaults": {"ok": {"$all": {"path": "items[*].code", "eq": 1}}}}
        assert Mapper().transform(spec, {})["ok"] is True

    def test_with_where(self):
        spec = {
            "defaults": {
                "ok": {"$all": {"path": "items[*]", "where": {"$gte": [{"$path": "value"}, 10]}}}
            }
        }
        assert Mapper().transform(spec, {"items": [{"value": 10}, {"value": 50}]})["ok"] is True
        assert Mapper().transform(spec, {"items": [{"value": 10}, {"value": 1}]})["ok"] is False

    def test_item_without_the_field_fails(self):
        spec = {
            "defaults": {
                "ok": {"$all": {"path": "items[*]", "where": {"$gte": [{"$path": "value"}, 10]}}}
            }
        }
        assert Mapper().transform(spec, {"items": [{"value": 10}, {}]})["ok"] is False

    def test_without_path_raises(self):
        spec = {"defaults": {"ok": {"$all": {"eq": 1}}}}
        with pytest.raises(ValueError, match=r"\$all must be an object with a 'path' key"):
            Mapper().transform(spec, {})


class TestFindOperator:
    """$find returns the first matching item."""

    def test_returns_the_item(self):
        spec = {
            "defaults": {
                "product": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                    }
                }
            }
        }
        payload = {"products": [{"type_product": "CARD"}, {"type_product": "LOAN", "authorized": True}]}
        assert Mapper().transform(spec, payload)["product"] == {
            "type_product": "LOAN",
            "authorized": True,
        }

    def test_select_reads_a_field_of_the_item(self):
        spec = {
            "defaults": {
                "is_loan_eligible": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "authorized",
                        "default": False,
                    }
                }
            }
        }
        payload = {
            "products": [
                {"type_product": "CARD", "authorized": True},
                {"type_product": "LOAN", "authorized": False},
            ]
        }
        assert Mapper().transform(spec, payload)["is_loan_eligible"] is False

    def test_select_nested_path(self):
        spec = {
            "defaults": {
                "balance": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "margin.available_balance",
                    }
                }
            }
        }
        payload = {"products": [{"type_product": "LOAN", "margin": {"available_balance": 1225.21}}]}
        assert Mapper().transform(spec, payload)["balance"] == 1225.21

    def test_select_expression(self):
        spec = {
            "defaults": {
                "product": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "loan"]},
                        "select": {"kind": {"$upper": {"$path": "type_product"}}, "ok": True},
                    }
                }
            }
        }
        payload = {"products": [{"type_product": "loan"}]}
        assert Mapper().transform(spec, payload)["product"] == {"kind": "LOAN", "ok": True}

    def test_no_match_skips_the_field(self):
        spec = {
            "defaults": {
                "product": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                    }
                }
            }
        }
        assert "product" not in Mapper().transform(spec, {"products": [{"type_product": "CARD"}]})

    def test_no_match_uses_default(self):
        spec = {
            "defaults": {
                "is_loan_eligible": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "authorized",
                        "default": False,
                    }
                }
            }
        }
        assert Mapper().transform(spec, {})["is_loan_eligible"] is False

    def test_missing_selection_uses_default(self):
        spec = {
            "defaults": {
                "is_loan_eligible": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "authorized",
                        "default": False,
                    }
                }
            }
        }
        assert Mapper().transform(spec, {"products": [{"type_product": "LOAN"}]})["is_loan_eligible"] is False

    def test_default_accepts_an_expression(self):
        spec = {
            "defaults": {
                "value": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "balance",
                        "default": {"$path": "fallback"},
                    }
                }
            }
        }
        assert Mapper().transform(spec, {"fallback": 7})["value"] == 7

    def test_legacy_comparator(self):
        spec = {"defaults": {"code": {"$find": {"path": "items[*].code", "gt": 1}}}}
        assert Mapper().transform(spec, {"items": [{"code": 1}, {"code": 5}]})["code"] == 5

    def test_first_match_wins(self):
        spec = {
            "defaults": {
                "id": {
                    "$find": {
                        "path": "items[*]",
                        "where": {"$eq": [{"$path": "type"}, "A"]},
                        "select": "id",
                    }
                }
            }
        }
        payload = {"items": [{"type": "B", "id": 1}, {"type": "A", "id": 2}, {"type": "A", "id": 3}]}
        assert Mapper().transform(spec, payload)["id"] == 2

    def test_unknown_key_raises(self):
        spec = {"defaults": {"x": {"$find": {"path": "items[*]", "wher": {"$eq": [1, 1]}}}}}
        with pytest.raises(ValueError, match="does not support operator 'wher'"):
            Mapper().transform(spec, {"items": []})


class TestFilterOperator:
    """$filter returns every matching item."""

    def test_returns_matching_items(self):
        spec = {
            "defaults": {
                "loans": {
                    "$filter": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                    }
                }
            }
        }
        payload = {
            "products": [
                {"type_product": "LOAN", "id": 1},
                {"type_product": "CARD", "id": 2},
                {"type_product": "LOAN", "id": 3},
            ]
        }
        assert Mapper().transform(spec, payload)["loans"] == [
            {"type_product": "LOAN", "id": 1},
            {"type_product": "LOAN", "id": 3},
        ]

    def test_select_projects_each_item(self):
        spec = {
            "defaults": {
                "ids": {
                    "$filter": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "id",
                    }
                }
            }
        }
        payload = {
            "products": [
                {"type_product": "LOAN", "id": 1},
                {"type_product": "CARD", "id": 2},
                {"type_product": "LOAN", "id": 3},
            ]
        }
        assert Mapper().transform(spec, payload)["ids"] == [1, 3]

    def test_items_without_the_selection_are_skipped(self):
        spec = {
            "defaults": {
                "ids": {"$filter": {"path": "products[*]", "select": "id"}}
            }
        }
        payload = {"products": [{"id": 1}, {"name": "x"}, {"id": 3}]}
        assert Mapper().transform(spec, payload)["ids"] == [1, 3]

    def test_no_match_returns_empty_list(self):
        spec = {
            "defaults": {
                "loans": {
                    "$filter": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                    }
                }
            }
        }
        assert Mapper().transform(spec, {"products": [{"type_product": "CARD"}]})["loans"] == []

    def test_absent_path_returns_empty_list(self):
        spec = {"defaults": {"loans": {"$filter": {"path": "products[*]"}}}}
        assert Mapper().transform(spec, {})["loans"] == []

    def test_count_with_len(self):
        spec = {
            "defaults": {
                "qty": {
                    "$len": {
                        "$filter": {
                            "path": "alerts[*]",
                            "where": {"$ne": [{"$path": "alert_type.code"}, 15]},
                        }
                    }
                }
            }
        }
        payload = {
            "alerts": [
                {"alert_type": {"code": 1}},
                {"alert_type": {"code": 15}},
                {"alert_type": {"code": 2}},
            ]
        }
        assert Mapper().transform(spec, payload)["qty"] == 2


class TestPredicateScoping:
    """Predicate bodies are evaluated with the item as the root."""

    def test_where_does_not_see_the_outer_payload(self):
        spec = {
            "defaults": {
                "found": {"$any": {"path": "items[*]", "where": {"$eq": [{"$path": "name"}, "root"]}}}
            }
        }
        payload = {"name": "root", "items": [{"name": "leaf"}]}
        assert Mapper().transform(spec, payload)["found"] is False

    def test_wildcard_inside_where_is_not_broadcast(self):
        spec = {
            "map": {"out[*].id": "items[*].id"},
            "defaults": {
                "out[*].has_code": {
                    "$any": {"path": "flags[*]", "where": {"$eq": [{"$path": "codes[*]"}, 1]}}
                }
            },
        }
        payload = {"items": [{"id": 1}, {"id": 2}], "flags": [{"codes": [1, 2]}]}
        assert Mapper().transform(spec, payload) == {
            "out": [{"id": 1, "has_code": True}, {"id": 2, "has_code": True}]
        }

    def test_plain_template_key_named_where_is_not_item_scoped(self):
        spec = {"defaults": {"out[*].label": {"where": {"$path": "items[*].name"}}}}
        payload = {"items": [{"name": "a"}, {"name": "b"}]}
        assert Mapper().transform(spec, payload) == {
            "out": [{"label": {"where": "a"}}, {"label": {"where": "b"}}]
        }

    def test_operand_of_a_legacy_comparator_still_reads_the_payload(self):
        spec = {"defaults": {"found": {"$any": {"path": "items[*].value", "gte": {"$path": "minimum"}}}}}
        payload = {"minimum": 10, "items": [{"value": 5}, {"value": 50}]}
        assert Mapper().transform(spec, payload)["found"] is True


class TestBooleanComposition:
    """The new operators compose with $if and with each other."""

    def test_and_or_not_as_if_condition(self):
        spec = {
            "defaults": {
                "slug": {
                    "$if": {
                        "condition": {
                            "$and": [
                                {"$exists": "document"},
                                {"$or": [{"$exists": "salary"}, {"$exists": "balance"}]},
                            ]
                        },
                        "then": "credit-guardian",
                        "else": "credit-guardian2",
                    }
                }
            }
        }
        assert Mapper().transform(spec, {"document": "1", "balance": 10})["slug"] == "credit-guardian"
        assert Mapper().transform(spec, {"document": "1"})["slug"] == "credit-guardian2"
        assert Mapper().transform(spec, {})["slug"] == "credit-guardian2"

    def test_guard_pattern_without_optional(self):
        spec = {
            "defaults": {
                "eligible": {
                    "$and": [{"$exists": "score"}, {"$gte": [{"$path": "score"}, 700]}]
                }
            }
        }
        assert Mapper().transform(spec, {"score": 800})["eligible"] is True
        assert Mapper().transform(spec, {"score": 100})["eligible"] is False
        assert Mapper().transform(spec, {})["eligible"] is False

    def test_not_exists_inside_or(self):
        spec = {
            "defaults": {
                "open_ended": {
                    "$or": [
                        {"$not": {"$exists": "end_date"}},
                        {"$gte": [{"$path": "end_date"}, "2026-01-01"]},
                    ]
                }
            }
        }
        assert Mapper().transform(spec, {})["open_ended"] is True
        assert Mapper().transform(spec, {"end_date": None})["open_ended"] is True
        assert Mapper().transform(spec, {"end_date": "2030-01-01"})["open_ended"] is True
        assert Mapper().transform(spec, {"end_date": "2020-01-01"})["open_ended"] is False


class TestLeaveOfAbsence:
    """Real-world case: has_leave_of_absence expressed entirely in the spec."""

    @pytest.mark.parametrize(
        "meta_data",
        [
            {},
            {"alerts": []},
            {"alerts": [{"alert_type": {"code": 15}}]},
            {"alerts": [{"alert_type": {"code": 15}, "absence_end_date": "2099-01-01"}]},
            {"alerts": [{"alert_type": {"code": 3}}]},
            {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": None}]},
            {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": ""}]},
            {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": "2020-01-01"}]},
            {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": "2099-01-01"}]},
            {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": date.today().strftime("%Y-%m-%d")}]},
            {"alerts": [{"alert_type": {}}]},
            {"alerts": [{"alert_type": None}]},
            {"alerts": [{"alert_type": {"code": None}}]},
            {"alerts": [{}]},
            {
                "alerts": [
                    {"alert_type": {"code": 15}},
                    {"alert_type": {"code": 3}, "absence_end_date": "2020-01-01"},
                ]
            },
            {
                "alerts": [
                    {"alert_type": {"code": 15}},
                    {"alert_type": {"code": 3}, "absence_end_date": "2099-01-01"},
                ]
            },
        ],
    )
    def test_matches_the_python_implementation(self, meta_data):
        spec = {"defaults": {"has_leave_of_absence": HAS_LEAVE_OF_ABSENCE}}
        result = Mapper().transform(spec, {"meta_data": meta_data})

        assert result["has_leave_of_absence"] is _has_leave_of_absence(meta_data)

    def test_without_meta_data(self):
        spec = {"defaults": {"has_leave_of_absence": HAS_LEAVE_OF_ABSENCE}}

        assert Mapper().transform(spec, {})["has_leave_of_absence"] is False

    def test_full_fallback_slug_payload(self):
        spec = {
            "map": {
                "document": "holder.document",
                "job_code": "employments[0].latest_competency.cbo",
                "employer_document": "employments[0].employer.document",
            },
            "defaults": {
                "slug": "credit-guardian2",
                "is_pep": {"$if": {"condition": {"$path": "holder.is_pep"}, "then": 1, "else": 0}},
                "has_leave_of_absence": HAS_LEAVE_OF_ABSENCE,
                "is_loan_eligible": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "authorized",
                        "default": False,
                    }
                },
                "available_balance": {
                    "$find": {
                        "path": "products[*]",
                        "where": {"$eq": [{"$path": "type_product"}, "LOAN"]},
                        "select": "available_balance",
                        "default": 0,
                    }
                },
                "termination_date": {"$path": "employments[0].termination_date", "optional": True},
                "prior_notice_date": {"$path": "employments[0].prior_notice_date", "optional": True},
                "base_margin_value": {"$path": "margin.base_margin_value", "optional": True},
            },
        }
        payload = {
            "holder": {"document": "36774557821", "is_pep": False},
            "employments": [
                {
                    "employer": {"document": "12345678000199"},
                    "latest_competency": {"cbo": "252105"},
                }
            ],
            "margin": {"base_margin_value": 3000.0},
            "products": [
                {"type_product": "CARD", "authorized": True, "available_balance": 100.0},
                {"type_product": "LOAN", "authorized": True, "available_balance": 1225.21},
            ],
            "meta_data": {"alerts": [{"alert_type": {"code": 3}, "absence_end_date": "2099-12-31"}]},
        }

        assert Mapper().transform(spec, payload) == {
            "document": "36774557821",
            "job_code": "252105",
            "employer_document": "12345678000199",
            "slug": "credit-guardian2",
            "is_pep": 0,
            "has_leave_of_absence": True,
            "is_loan_eligible": True,
            "available_balance": 1225.21,
            "base_margin_value": 3000.0,
        }
