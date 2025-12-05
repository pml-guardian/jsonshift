# ✨ jsonshift

A lightweight Python package to **convert one JSON payload into another** using a declarative mapping spec defined in JSON.

**Engine rules (designed for system integrations):**

* If the **source path does not exist** → raises **`MappingMissingError`**.
* If the **source value is `null` / `None`** → the destination receives **`None`** (not replaced).
* `defaults` only fills values when the **destination field is absent** (does not overwrite `None` or existing values).
* Supports **dotted and indexed paths**, e.g. `a.b[0].c`.
* Extended mapper (`ArrayMapper`) supports **wildcard list expansion** using `[*]`.

---

## 🧩 Installation

```bash
pip install jsonshift
# or for development:
pip install -e .
```

---

## 🚀 Basic usage

```python
from jsonshift import Mapper

payload = {
    "customer_name": "John Doe",
    "cpf": None,
    "amount": 1000.0,
    "installments": 12
}

spec = {
  "map": {
    "customer.name": "customer_name",
    "customer.cpf": "cpf",          # None is preserved
    "contract.amount": "amount",
    "contract.installments": "installments"
  },
  "defaults": {
    "contract.type": "CCB",
    "contract.origin": "ORQ"
  }
}

mapper = Mapper()
out = mapper.transform(spec, payload)
print(out)
# {
#   "customer": {"name": "John Doe", "cpf": null},
#   "contract": {"amount": 1000.0, "installments": 12, "type": "CCB", "origin": "ORQ"}
# }
```

---

## 🧠 ArrayMapper — mapping lists with `[*]`

The `ArrayMapper` extends `Mapper` and adds support for **wildcard list mappings**.
You can transform lists of objects using the same declarative spec syntax.

```python
from jsonshift.array_mapper import ArrayMapper

payload = {
    "products": [
        {"id": "P-001", "name": "Notebook", "price": 4500.0, "stock": 12},
        {"id": "P-002", "name": "Mouse Gamer", "price": 250.0, "stock": 100}
    ]
}

spec = {
    "map": {
        "new_products[*].code": "products[*].id",
        "new_products[*].title": "products[*].name",
        "new_products[*].price_brl": "products[*].price",
        "new_products[*].available": "products[*].stock"
    },
    "defaults": {
        "new_products[*].currency": "BRL"
    }
}

out = ArrayMapper().transform(spec, payload)
print(out)
# {
#   "new_products": [
#     {"code": "P-001", "title": "Notebook", "price_brl": 4500.0, "available": 12, "currency": "BRL"},
#     {"code": "P-002", "title": "Mouse Gamer", "price_brl": 250.0, "available": 100, "currency": "BRL"}
#   ]
# }
```

🧩 The same number of elements is preserved — each input list item becomes one transformed output item.
Defaults with wildcards (`new_products[*].currency`) apply individually to every object in the list.

---

## 🖥️ Command-line interface (CLI)

```bash
# Transform using JSON files
jsonshift --spec spec.json --input payload.json

# or via stdin
cat payload.json | jsonshift --spec spec.json
```

---

## ▶️ Example run (from the repository)

This repository includes ready-to-use files under the [`examples/`](./examples) folder.

```bash
# From the project root
jsonshift --spec examples/spec.json --input examples/payload.json
```

**Expected output:**

```json
{
  "customer": {
    "name": "John Doe",
    "cpf": "12345678901"
  },
  "contract": {
    "amount": 1500.0,
    "installments": 6,
    "type": "CCB",
    "origin": "ORQ"
  }
}
```

---

## 📘 Spec format

```json
{
  "map": {
    "destination.path": "source.path",
    "destination[*].field": "source[*].field"
  },
  "defaults": {
    "destination.path": "<fixed_value>",
    "destination[*].field": "<fixed_value>"
  }
}
```

---

## ⚠️ Error handling

* **`MappingMissingError`** — source path not found.
* **`InvalidDestinationPath`** — invalid destination (e.g., destination with index).
* **`TypeError`** — source list expected but got non-list in wildcard paths.

---

## 🧪 Testing

Run all unit tests:

```bash
pytest -v
```

Includes tests for:

* Core `Mapper`
* `ArrayMapper` wildcard behavior

---

## 📄 License

MIT © 2025 Pedro Marques