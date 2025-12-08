import pytest
from jsonshift import Mapper, MappingMissingError, InvalidDestinationPath


def test_basic_map_and_defaults():
    payload = {"name": "Ana", "cpf": "123", "amount": 1000, "installments": 12}
    spec = {
        "map": {
            "customer.name": "name",
            "customer.cpf": "cpf",
            "contract.amount": "amount",
            "contract.installments": "installments",
        },
        "defaults": {"contract.type": "CCB"},
    }
    out = Mapper().transform(spec, payload)
    assert out["customer"]["name"] == "Ana"
    assert out["contract"]["type"] == "CCB"


def test_missing_source_raises():
    payload = {"name": "Ana"}
    spec = {"map": {"customer.cpf": "cpf"}}
    with pytest.raises(MappingMissingError):
        Mapper().transform(spec, payload)


def test_none_is_kept():
    payload = {"cpf": None}
    spec = {"map": {"customer.cpf": "cpf"}, "defaults": {"customer.cpf": "XXX"}}
    out = Mapper().transform(spec, payload)
    assert "cpf" in out["customer"]
    assert out["customer"]["cpf"] is None  # defaults do not overwrite None


def test_indexed_read_and_invalid_dest_index():
    payload = {"emails": ["a@x.com", "b@x.com"]}
    spec_ok = {"map": {"contact.email": "emails[0]"}}
    out = Mapper().transform(spec_ok, payload)
    assert out["contact"]["email"] == "a@x.com"

    spec_bad = {"map": {"contact.emails[0]": "emails[0]"}}
    with pytest.raises(InvalidDestinationPath):
        Mapper().transform(spec_bad, payload)