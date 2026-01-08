from jsonshift import Mapper


def test_wildcard_list_mapping():
    payload = {
        "items": [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
        ]
    }

    spec = {
        "map": {
            "out[*].id": "items[*].id",
            "out[*].name": "items[*].name",
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "out": [
            {"id": 1, "name": "A"},
            {"id": 2, "name": "B"},
        ]
    }


def test_fixed_index_creation():
    payload = {"value": "x"}
    spec = {
        "map": {
            "items[2].value": "value"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "items": [{}, {}, {"value": "x"}]
    }