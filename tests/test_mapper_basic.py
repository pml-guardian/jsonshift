import pytest
from jsonshift import Mapper, MappingMissingError


def test_basic_map_and_defaults():
    payload = {"name": "Ana", "cpf": "123", "amount": 1000}
    spec = {
        "map": {
            "customer.name": "name",
            "customer.cpf": "cpf",
            "contract.amount": "amount",
        },
        "defaults": {
            "contract.type": "CCB"
        }
    }

    out = Mapper().transform(spec, payload)

    assert out["customer"]["name"] == "Ana"
    assert out["customer"]["cpf"] == "123"
    assert out["contract"]["amount"] == 1000
    assert out["contract"]["type"] == "CCB"


def test_missing_source_raises():
    payload = {"name": "Ana"}
    spec = {"map": {"customer.cpf": "cpf"}}

    with pytest.raises(MappingMissingError):
        Mapper().transform(spec, payload)


def test_none_is_not_overwritten_by_default():
    payload = {"cpf": None}
    spec = {
        "map": {"customer.cpf": "cpf"},
        "defaults": {"customer.cpf": "XXX"}
    }

    out = Mapper().transform(spec, payload)
    assert out["customer"]["cpf"] is None