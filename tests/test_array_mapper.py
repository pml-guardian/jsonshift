import pytest
from jsonshift import ArrayMapper


def test_array_mapper_basic_list_transform():
    payload = {
        "products": [
            {"id": "P-001", "name": "Notebook Dell", "price": 4500.0, "stock": 12},
            {"id": "P-002", "name": "Mouse Gamer RGB", "price": 250.0, "stock": 100},
            {"id": "P-003", "name": "Cadeira Ergonômica", "price": 1200.0, "stock": 8},
        ]
    }

    spec = {
        "map": {
            "new_products[*].code": "products[*].id",
            "new_products[*].title": "products[*].name",
            "new_products[*].price_brl": "products[*].price",
            "new_products[*].available": "products[*].stock",
        },
        "defaults": {
            "new_products[*].currency": "BRL"
        }
    }

    out = ArrayMapper().transform(spec, payload)

    assert "new_products" in out
    assert isinstance(out["new_products"], list)
    assert len(out["new_products"]) == len(payload["products"])

    first = out["new_products"][0]
    assert first["code"] == "P-001"
    assert first["title"] == "Notebook Dell"
    assert first["price_brl"] == 4500.0
    assert first["available"] == 12
    assert first["currency"] == "BRL"

    for item in out["new_products"]:
        assert item["currency"] == "BRL"


def test_array_mapper_raises_on_missing_source():
    payload = {"products": [{"id": "P-001"}]}
    spec = {"map": {"new_products[*].title": "products[*].name"}}

    mapper = ArrayMapper()
    with pytest.raises(Exception):
        mapper.transform(spec, payload)