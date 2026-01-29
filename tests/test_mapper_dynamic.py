import pytest
from jsonshift import Mapper
from jsonshift.exceptions import MappingMissingError


# ---------- $concat ----------

def test_concat_literal_and_path():
    payload = {"id": 123}

    spec = {
        "defaults": {
            "code": {
                "$concat": [
                    "USR-",
                    {"$path": "id"}
                ]
            }
        }
    }

    out = Mapper().transform(spec, payload)
    assert out["code"] == "USR-123"


def test_concat_only_literals():
    spec = {
        "defaults": {
            "code": {
                "$concat": ["A", "-", "B"]
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["code"] == "A-B"


def test_concat_missing_path_raises():
    spec = {
        "defaults": {
            "code": {
                "$concat": [
                    "USR-",
                    {"$path": "id"}
                ]
            }
        }
    }

    with pytest.raises(MappingMissingError):
        Mapper().transform(spec, {})


# ---------- $upper / $lower ----------

def test_upper_with_path():
    payload = {"name": "John"}

    spec = {
        "defaults": {
            "name_upper": {
                "$upper": {"$path": "name"}
            }
        }
    }

    out = Mapper().transform(spec, payload)
    assert out["name_upper"] == "JOHN"


def test_lower_with_path():
    payload = {"email": "John@Email.COM"}

    spec = {
        "defaults": {
            "email": {
                "$lower": {"$path": "email"}
            }
        }
    }

    out = Mapper().transform(spec, payload)
    assert out["email"] == "john@email.com"


def test_upper_literal():
    spec = {
        "defaults": {
            "value": {
                "$upper": "abc"
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == "ABC"


# ---------- $format ----------

def test_format_with_multiple_paths():
    payload = {
        "id": 10,
        "cpf": "123"
    }

    spec = {
        "defaults": {
            "external_id": {
                "$format": {
                    "template": "{id}-{cpf}",
                    "args": {
                        "id": {"$path": "id"},
                        "cpf": {"$path": "cpf"}
                    }
                }
            }
        }
    }

    out = Mapper().transform(spec, payload)
    assert out["external_id"] == "10-123"


# ---------- interaction with defaults ----------

def test_dynamic_default_does_not_override_existing():
    payload = {"id": 1}

    spec = {
        "map": {
            "code": "id"
        },
        "defaults": {
            "code": {
                "$concat": ["X-", {"$path": "id"}]
            }
        }
    }

    out = Mapper().transform(spec, payload)
    assert out["code"] == 1