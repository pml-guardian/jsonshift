"""Test $if operator and comparison operators ($eq, $ne, $gt, $gte, $lt, $lte)."""
import pytest
from jsonshift import Mapper, MappingMissingError


class TestIfConditionPresence:
    """$if skips field when condition is missing or null."""

    def test_field_omitted_when_path_missing(self):
        """`$if` without `else` skips field when optional path is absent."""
        spec = {
            "defaults": {
                "doc_id": {
                    "$if": {
                        "condition": {"$path": "doc", "optional": True},
                        "then": "1",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {})

        assert "doc_id" not in result

    def test_field_created_when_path_present(self):
        """`$if` creates field when optional path exists."""
        spec = {
            "defaults": {
                "doc_id": {
                    "$if": {
                        "condition": {"$path": "doc", "optional": True},
                        "then": "1",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"doc": "base64content"})

        assert result["doc_id"] == "1"

    def test_field_omitted_when_path_is_null(self):
        """`$if` skips field when condition resolves to null."""
        spec = {
            "map": {"doc": "source_doc"},
            "defaults": {
                "doc_id": {
                    "$if": {
                        "condition": {"$path": "source_doc"},
                        "then": "1",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"source_doc": None})

        assert result["doc"] is None
        assert "doc_id" not in result

    def test_else_used_when_condition_missing(self):
        """`$if` uses `else` when condition is absent."""
        spec = {
            "defaults": {
                "status": {
                    "$if": {
                        "condition": {"$path": "active", "optional": True},
                        "then": "active",
                        "else": "inactive",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {})

        assert result["status"] == "inactive"

    def test_else_used_when_condition_null(self):
        """`$if` uses `else` when condition is null."""
        spec = {
            "defaults": {
                "status": {
                    "$if": {
                        "condition": {"$path": "flag"},
                        "then": "yes",
                        "else": "no",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"flag": None})

        assert result["status"] == "no"

    def test_then_used_when_condition_truthy(self):
        """`$if` uses `then` when condition is a truthy value."""
        spec = {
            "defaults": {
                "label": {
                    "$if": {
                        "condition": {"$path": "flag"},
                        "then": "yes",
                        "else": "no",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"flag": True})

        assert result["label"] == "yes"


class TestIfWithRealWorldUseCase:
    """$if guards dependent fields based on an optional document."""

    def test_dependent_fields_omitted_when_doc_absent(self):
        """Fields dependent on optional doc are all omitted when doc is missing."""
        payload = {"primary_doc": "base64abc"}
        spec = {
            "map": {
                "documents[0].content": "primary_doc",
                "documents[1].content": {"path": "secondary_doc", "optional": True},
            },
            "defaults": {
                "documents[0].id": "1",
                "documents[1].id": {
                    "$if": {
                        "condition": {"$path": "secondary_doc", "optional": True},
                        "then": "2",
                    }
                },
                "documents[1].name": {
                    "$if": {
                        "condition": {"$path": "secondary_doc", "optional": True},
                        "then": "document.pdf",
                    }
                },
            },
        }

        result = Mapper().transform(spec, payload)

        assert result["documents"][0]["id"] == "1"
        assert len(result["documents"]) == 1 or "id" not in result["documents"][1]
        assert len(result["documents"]) == 1 or "name" not in result["documents"][1]

    def test_dependent_fields_created_when_doc_present(self):
        """Fields dependent on optional doc are created when doc exists."""
        payload = {
            "primary_doc": "base64abc",
            "secondary_doc": "base64xyz",
        }
        spec = {
            "map": {
                "documents[0].content": "primary_doc",
                "documents[1].content": {"path": "secondary_doc", "optional": True},
            },
            "defaults": {
                "documents[0].id": "1",
                "documents[1].id": {
                    "$if": {
                        "condition": {"$path": "secondary_doc", "optional": True},
                        "then": "2",
                    }
                },
                "documents[1].name": {
                    "$if": {
                        "condition": {"$path": "secondary_doc", "optional": True},
                        "then": "document.pdf",
                    }
                },
            },
        }

        result = Mapper().transform(spec, payload)

        assert result["documents"][0]["id"] == "1"
        assert result["documents"][1]["id"] == "2"
        assert result["documents"][1]["name"] == "document.pdf"

    def test_dependent_fields_omitted_when_doc_null(self):
        """Fields dependent on optional doc are omitted when doc is null."""
        payload = {"primary_doc": "base64abc", "secondary_doc": None}
        spec = {
            "map": {
                "documents[0].content": "primary_doc",
                "documents[1].content": "secondary_doc",
            },
            "defaults": {
                "documents[1].id": {
                    "$if": {
                        "condition": {"$path": "secondary_doc"},
                        "then": "2",
                    }
                },
            },
        }

        result = Mapper().transform(spec, payload)

        assert result["documents"][1]["content"] is None
        assert "id" not in result["documents"][1]


class TestIfThenElseComposition:
    """$if composes with other operators in then/else."""

    def test_then_is_another_operator(self):
        """`then` can be any dynamic expression."""
        spec = {
            "defaults": {
                "name": {
                    "$if": {
                        "condition": {"$path": "active", "optional": True},
                        "then": {"$upper": {"$path": "raw_name"}},
                        "else": {"$lower": {"$path": "raw_name"}},
                    }
                }
            }
        }

        result_active = Mapper().transform(spec, {"active": True, "raw_name": "Alice"})
        result_inactive = Mapper().transform(spec, {"raw_name": "Alice"})

        assert result_active["name"] == "ALICE"
        assert result_inactive["name"] == "alice"

    def test_then_is_concat(self):
        """`then` can be a $concat expression."""
        spec = {
            "defaults": {
                "ref": {
                    "$if": {
                        "condition": {"$path": "doc", "optional": True},
                        "then": {"$concat": ["DOC-", {"$path": "doc_id"}]},
                    }
                }
            }
        }

        result = Mapper().transform(spec, {"doc": "x", "doc_id": "42"})

        assert result["ref"] == "DOC-42"

    def test_else_is_static_value(self):
        """`else` can be a plain static value."""
        spec = {
            "defaults": {
                "tier": {
                    "$if": {
                        "condition": {"$path": "premium", "optional": True},
                        "then": "gold",
                        "else": "basic",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {})

        assert result["tier"] == "basic"


class TestComparisonOperators:
    """Test $eq, $ne, $gt, $gte, $lt, $lte operators."""

    def test_eq_true(self):
        """`$eq` returns True when values are equal."""
        spec = {"defaults": {"r": {"$eq": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_eq_false(self):
        """`$eq` returns False when values differ."""
        spec = {"defaults": {"r": {"$eq": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 5})
        assert result["r"] is False

    def test_ne_true(self):
        """`$ne` returns True when values differ."""
        spec = {"defaults": {"r": {"$ne": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 5})
        assert result["r"] is True

    def test_ne_false(self):
        """`$ne` returns False when values are equal."""
        spec = {"defaults": {"r": {"$ne": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is False

    def test_gt_true(self):
        """`$gt` returns True when left > right."""
        spec = {"defaults": {"r": {"$gt": [{"$path": "x"}, 5]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_gt_false(self):
        """`$gt` returns False when left <= right."""
        spec = {"defaults": {"r": {"$gt": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is False

    def test_gte_equal(self):
        """`$gte` returns True when left == right."""
        spec = {"defaults": {"r": {"$gte": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_gte_greater(self):
        """`$gte` returns True when left > right."""
        spec = {"defaults": {"r": {"$gte": [{"$path": "x"}, 5]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_gte_false(self):
        """`$gte` returns False when left < right."""
        spec = {"defaults": {"r": {"$gte": [{"$path": "x"}, 20]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is False

    def test_lt_true(self):
        """`$lt` returns True when left < right."""
        spec = {"defaults": {"r": {"$lt": [{"$path": "x"}, 20]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_lt_false(self):
        """`$lt` returns False when left >= right."""
        spec = {"defaults": {"r": {"$lt": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is False

    def test_lte_equal(self):
        """`$lte` returns True when left == right."""
        spec = {"defaults": {"r": {"$lte": [{"$path": "x"}, 10]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_lte_less(self):
        """`$lte` returns True when left < right."""
        spec = {"defaults": {"r": {"$lte": [{"$path": "x"}, 20]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is True

    def test_lte_false(self):
        """`$lte` returns False when left > right."""
        spec = {"defaults": {"r": {"$lte": [{"$path": "x"}, 5]}}}
        result = Mapper().transform(spec, {"x": 10})
        assert result["r"] is False

    def test_compare_two_paths(self):
        """Comparison between two `$path` values."""
        spec = {"defaults": {"r": {"$gt": [{"$path": "a"}, {"$path": "b"}]}}}
        result = Mapper().transform(spec, {"a": 10, "b": 5})
        assert result["r"] is True

    def test_compare_string_equality(self):
        """String equality comparison."""
        spec = {"defaults": {"r": {"$eq": [{"$path": "status"}, "active"]}}}
        assert Mapper().transform(spec, {"status": "active"})["r"] is True
        assert Mapper().transform(spec, {"status": "inactive"})["r"] is False

    def test_compare_returns_missing_when_path_missing(self):
        """Comparison returns _MISSING when a path is absent — field skipped."""
        spec = {"defaults": {"r": {"$gt": [{"$path": "x", "optional": True}, 5]}}}
        result = Mapper().transform(spec, {})
        assert "r" not in result

    def test_eq_null_both_sides(self):
        """`$eq` handles null on both sides."""
        spec = {"defaults": {"r": {"$eq": [{"$path": "x"}, None]}}}
        assert Mapper().transform(spec, {"x": None})["r"] is True
        assert Mapper().transform(spec, {"x": 0})["r"] is False

    def test_ne_null(self):
        """`$ne` handles null comparison."""
        spec = {"defaults": {"r": {"$ne": [{"$path": "x"}, None]}}}
        assert Mapper().transform(spec, {"x": None})["r"] is False
        assert Mapper().transform(spec, {"x": "value"})["r"] is True

    def test_gt_with_null_returns_false(self):
        """`$gt` with null operand returns False."""
        spec = {"defaults": {"r": {"$gt": [{"$path": "x"}, 5]}}}
        result = Mapper().transform(spec, {"x": None})
        assert result["r"] is False


class TestIfWithComparisons:
    """$if condition using comparison operators."""

    def test_if_gt_then_else(self):
        """`$if` with `$gt` condition selects correct branch."""
        spec = {
            "defaults": {
                "category": {
                    "$if": {
                        "condition": {"$gt": [{"$path": "amount"}, 1000]},
                        "then": "premium",
                        "else": "standard",
                    }
                }
            }
        }

        assert Mapper().transform(spec, {"amount": 1500})["category"] == "premium"
        assert Mapper().transform(spec, {"amount": 500})["category"] == "standard"

    def test_if_eq_no_else(self):
        """`$if` with `$eq` — field absent when condition is False."""
        spec = {
            "defaults": {
                "tag": {
                    "$if": {
                        "condition": {"$eq": [{"$path": "status"}, "vip"]},
                        "then": "VIP",
                    }
                }
            }
        }

        assert Mapper().transform(spec, {"status": "vip"})["tag"] == "VIP"
        assert "tag" not in Mapper().transform(spec, {"status": "regular"})

    def test_if_lte_then_field(self):
        """`$if` with `$lte` condition."""
        spec = {
            "defaults": {
                "discount": {
                    "$if": {
                        "condition": {"$lte": [{"$path": "quantity"}, 5]},
                        "then": "0%",
                        "else": "10%",
                    }
                }
            }
        }

        assert Mapper().transform(spec, {"quantity": 3})["discount"] == "0%"
        assert Mapper().transform(spec, {"quantity": 10})["discount"] == "10%"

    def test_if_ne_condition(self):
        """`$if` with `$ne` condition."""
        spec = {
            "defaults": {
                "warning": {
                    "$if": {
                        "condition": {"$ne": [{"$path": "level"}, "ok"]},
                        "then": "check_required",
                    }
                }
            }
        }

        assert Mapper().transform(spec, {"level": "error"})["warning"] == "check_required"
        assert "warning" not in Mapper().transform(spec, {"level": "ok"})

    def test_if_then_is_math_operator(self):
        """`$if` condition with math in `then`."""
        spec = {
            "defaults": {
                "final_price": {
                    "$if": {
                        "condition": {"$gt": [{"$path": "qty"}, 10]},
                        "then": {"$mul": {"value": {"$path": "price"}, "by": 0.9}},
                        "else": {"$path": "price"},
                    }
                }
            }
        }

        bulk = Mapper().transform(spec, {"qty": 15, "price": 100})
        normal = Mapper().transform(spec, {"qty": 5, "price": 100})

        assert bulk["final_price"] == pytest.approx(90.0)
        assert normal["final_price"] == 100

    def test_if_condition_missing_path_skips_field(self):
        """`$if` with comparison on missing path — field skipped entirely."""
        spec = {
            "defaults": {
                "badge": {
                    "$if": {
                        "condition": {"$gt": [{"$path": "score", "optional": True}, 80]},
                        "then": "top",
                    }
                }
            }
        }

        result = Mapper().transform(spec, {})

        assert "badge" not in result


class TestIfErrorHandling:
    """$if and comparison error conditions."""

    def test_if_missing_condition_key_raises(self):
        """`$if` without `condition` raises ValueError."""
        spec = {"defaults": {"x": {"$if": {"then": "value"}}}}

        with pytest.raises(ValueError, match="condition"):
            Mapper().transform(spec, {})

    def test_compare_wrong_arity_raises(self):
        """Comparison with wrong number of operands raises ValueError."""
        spec = {"defaults": {"r": {"$gt": [1, 2, 3]}}}

        with pytest.raises(ValueError):
            Mapper().transform(spec, {})

    def test_compare_not_list_raises(self):
        """Comparison with non-list operand raises ValueError."""
        spec = {"defaults": {"r": {"$gt": {"a": 1}}}}

        with pytest.raises(ValueError):
            Mapper().transform(spec, {})
