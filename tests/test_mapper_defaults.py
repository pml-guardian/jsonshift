from jsonshift import Mapper


def test_defaults_create_structure():
    spec = {
        "defaults": {
            "a[*].b[*].c.value": 1
        }
    }

    out = Mapper().transform(spec, {})

    assert out == {
        "a": [
            {
                "b": [
                    {
                        "c": {"value": 1}
                    }
                ]
            }
        ]
    }


def test_defaults_do_not_override_existing():
    payload = {"a": {"value": 10}}
    spec = {
        "map": {"a.value": "a.value"},
        "defaults": {"a.value": 99}
    }

    out = Mapper().transform(spec, payload)
    assert out["a"]["value"] == 10