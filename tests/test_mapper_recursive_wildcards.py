from jsonshift import Mapper


def test_double_wildcard_nested():
    payload = {
        "groups": [
            {
                "users": [
                    {"id": 1},
                    {"id": 2},
                ]
            },
            {
                "users": [
                    {"id": 3},
                    {"id": 4},
                ]
            }
        ]
    }

    spec = {
        "map": {
            "ids[*]": "groups[*].users[*].id"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "ids": [1, 2, 3, 4]
    }


def test_triple_nested_wildcard():
    payload = {
        "a": [
            {
                "b": [
                    {
                        "c": [
                            {"value": 10},
                            {"value": 20}
                        ]
                    }
                ]
            }
        ]
    }

    spec = {
        "map": {
            "values[*]": "a[*].b[*].c[*].value"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "values": [10, 20]
    }


def test_nested_wildcard_with_optional():
    payload = {
        "groups": [
            {
                "users": [
                    {"id": 1},
                    {}
                ]
            }
        ]
    }

    spec = {
        "map": {
            "ids[*]": {
                "path": "groups[*].users[*].id",
                "optional": True
            }
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "ids": [1]
    }


def test_index_and_wildcard_combination():
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
                    {"id": 3},
                    {"id": 4}
                ]
            }
        ]
    }

    spec = {
        "map": {
            "second_user_ids[*]": "groups[*].users[1].id"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "second_user_ids": [2, 4]
    }


def test_deep_index_path():
    payload = {
        "a": [
            {
                "b": [
                    {"c": 100},
                    {"c": 200}
                ]
            }
        ]
    }

    spec = {
        "map": {
            "value": "a[0].b[1].c"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "value": 200
    }