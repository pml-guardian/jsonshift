# ✨ jsonshift

A lightweight Python package to **convert one JSON payload into another** using a declarative mapping spec defined in JSON.

Designed for **deterministic system integrations**, data pipelines, and API adapters.

---

## ⚙️ Engine rules

* If the **source path does not exist** → raises **`MappingMissingError`**
  *(unless `optional: true` is set)*

* If the **source value is `null` / `None`** → the destination receives **`None`**
  *(defaults do NOT override `None`)*

* `defaults` only fill values when the **destination field is absent**
  *(never overwrite existing values or `None`)*

* Supports:
  * dotted paths
  * indexed paths (`[0]`)
  * wildcard paths (`[*]`)
  * automatic list creation
  * infinite nesting depth

* Supports **optional mappings** using `optional: true`

* Supports dynamic defaults:
  * `{ "$now": "date" }`
  * `{ "$now": "datetime" }`
  * `{ "$now": "time" }`

---

## 🧩 Installation

```bash
pip install jsonshift
# or for development:
pip install -e .[dev]
````

---

## 🚀 Complex example (Python)

```python
from jsonshift import Mapper

payload = {
    "customer_name": "John Doe",
    "cpf": "12345678901",
    "email": "john@doe.com",
    "amount": 1500.0,
    "installments": 6,
    "products": [
        {"id": "P-001", "name": "Notebook", "price": 4500.0},
        {"id": "P-002", "name": "Mouse", "price": 250.0}
    ]
}

spec = {
    "map": {
        "customer.name": "customer_name",
        "customer.cpf": "cpf",
        "customer.email": {
            "path": "email",
            "optional": True
        },

        "contract.amount": "amount",
        "contract.installments": "installments",

        "contract.products[*].code": "products[*].id",
        "contract.products[*].title": "products[*].name",
        "contract.products[*].price": "products[*].price",

        "contract.main_product[0].code": "products[0].id",
        "contract.main_product[0].title": "products[0].name"
    },

    "defaults": {
        "contract.type": "CCB",
        "contract.origin": "ORQ",

        "contract.created_date": {"$now": "date"},
        "contract.created_at": {"$now": "datetime"},
        "contract.created_time": {"$now": "time"},

        "contract.products[*].currency": "BRL"
    }
}

out = Mapper().transform(spec, payload)
print(out)
```

Output (example):

```json
{
  "customer": {
    "name": "John Doe",
    "cpf": "12345678901",
    "email": "john@doe.com"
  },
  "contract": {
    "amount": 1500.0,
    "installments": 6,
    "type": "CCB",
    "origin": "ORQ",
    "created_date": "2025-01-08",
    "created_at": "2025-01-08T12:00:00",
    "created_time": "12:00:00",
    "products": [
      {
        "code": "P-001",
        "title": "Notebook",
        "price": 4500.0,
        "currency": "BRL"
      },
      {
        "code": "P-002",
        "title": "Mouse",
        "price": 250.0,
        "currency": "BRL"
      }
    ],
    "main_product": [
      {
        "code": "P-001",
        "title": "Notebook"
      }
    ]
  }
}
```

---

## 🖥️ Command-line interface (CLI)

Using the same example from `examples/`:

```bash
jsonshift --spec examples/spec.json --input examples/payload.json
```

Or via `stdin`:

```bash
cat examples/payload.json | jsonshift --spec examples/spec.json
```

The output structure is identical to the Python example above.

---

## 🧪 Testing

```bash
pytest -v
```

---

## 📄 License

MIT © 2025 Pedro Marques