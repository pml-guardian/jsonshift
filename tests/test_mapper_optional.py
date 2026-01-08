from jsonshift import Mapper


def test_optional_simple_field():
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

    out = Mapper().transform(spec, payload)
    assert out == {"user": {"name": "John"}}


def test_optional_inside_array():
    payload = {
        "users": [
            {"id": 1},
            {"id": 2, "phone": "9999"}
        ]
    }

    spec = {
        "map": {
            "items[*].phone": {
                "path": "users[*].phone",
                "optional": True
            }
        }
    }

    out = Mapper().transform(spec, payload)

    assert out == {
        "items": [
            {},
            {"phone": "9999"}
        ]
    }