from datetime import datetime
from jsonshift import Mapper


def test_format_strftime_date():
    spec = {
        "defaults": {
            "created": {
                "$format": {
                    "value": {"$now": "datetime"},
                    "strftime": "%Y-%m-%d"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["created"], str)
    assert len(out["created"]) == 10


def test_format_mask_cpf():
    spec = {
        "defaults": {
            "cpf": {
                "$format": {
                    "value": "12345678901",
                    "mask": "###.###.###-##"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["cpf"] == "123.456.789-01"


def test_format_mask_cnpj():
    spec = {
        "defaults": {
            "cnpj": {
                "$format": {
                    "value": "12345678000199",
                    "mask": "##.###.###/####-##"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["cnpj"] == "12.345.678/0001-99"


def test_format_none_returns_none():
    spec = {
        "defaults": {
            "value": {
                "$format": {
                    "value": None,
                    "mask": "###"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] is None