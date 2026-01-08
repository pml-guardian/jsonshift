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

* Supports **dotted paths**, **indexed paths** (`[0]`, `[1]`) and **wildcards** (`[*]`)

* `ArrayMapper` supports:

  * wildcard list expansion (`[*]`)
  * fixed index creation (`[n]`)
  * automatic list creation
  * infinite nesting depth

* NEW: Support for **optional mappings** using `optional: true`

---

## 🧩 Installation

```bash
pip install jsonshift
# or for development:
pip install -e .
```

---

## 🚀 Basic usage (Mapper)

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
    "customer.cpf": "cpf",
    "contract.amount": "amount",
    "contract.installments": "installments"
  },
  "defaults": {
    "contract.type": "CCB",
    "contract.origin": "ORQ"
  }
}

out = Mapper().transform(spec, payload)
print(out)
```

Output:

```json
{
  "customer": {
    "name": "John Doe",
    "cpf": null
  },
  "contract": {
    "amount": 1000.0,
    "installments": 12,
    "type": "CCB",
    "origin": "ORQ"
  }
}
```

---

## 🧠 ArrayMapper — mapping lists with `[*]`

`ArrayMapper` extends `Mapper` and adds **powerful list handling**.

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
```

Output:

```json
{
  "new_products": [
    {
      "code": "P-001",
      "title": "Notebook",
      "price_brl": 4500.0,
      "available": 12,
      "currency": "BRL"
    },
    {
      "code": "P-002",
      "title": "Mouse Gamer",
      "price_brl": 250.0,
      "available": 100,
      "currency": "BRL"
    }
  ]
}
```

Each input list item maps to exactly **one output item**.
Defaults with wildcards apply **per element**, never globally.

---

## 🧩 Fixed indices (`[n]`) and list creation

You can explicitly control list positions:

```python
spec = {
    "map": {
        "items[0].name": "source.name_1",
        "items[1].name": "source.name_2"
    }
}
```

Lists are **automatically created and expanded** to fit the index.

---

## 🆕 Optional fields (`optional: true`)

Optional mappings allow **graceful degradation** when a source field is missing.

### Rules

* If the source exists → mapped normally
* If the source does NOT exist:

  * no error is raised
  * destination structure is preserved
  * the final field is NOT created

---

### Example — simple object

```python
from jsonshift import Mapper

payload = {
    "name": "John Doe"
}

spec = {
    "map": {
        "user.full_name": "name",
        "user.nickname": {
            "path": "nickname",
            "optional": True
        }
    }
}

out = Mapper().transform(spec, payload)
print(out)
```

Output:

```json
{
  "user": {
    "full_name": "John Doe"
  }
}
```

---

### Example — optional fields inside arrays

```python
from jsonshift.array_mapper import ArrayMapper

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

out = ArrayMapper().transform(spec, payload)
print(out)
```

Output:

```json
{
  "items": [
    {},
    {"phone": "9999"}
  ]
}
```

---

## 🧬 Defaults with wildcards (advanced)

Defaults can **create entire structures**, even without `map`:

```python
spec = {
    "defaults": {
        "a[*].b[*].c[*].value": 1
    }
}
```

Result:

```json
{
  "a": [
    {
      "b": [
        {
          "c": [
            {"value": 1}
          ]
        }
      ]
    }
  ]
}
```

---

## 🖥️ Command-line interface (CLI)

```bash
jsonshift --spec spec.json --input payload.json
cat payload.json | jsonshift --spec spec.json
```

---

## 📘 Spec format

```json
{
  "map": {
    "destination.path": "source.path",
    "destination[*].field": "source[*].field",
    "destination[0].field": "source.field"
  },
  "defaults": {
    "destination.path": "<fixed_value>",
    "destination[*].field": "<fixed_value>"
  }
}
```

---

## ⚠️ Error handling

* **`MappingMissingError`** — source path not found (unless optional)
* **`TypeError`** — wildcard source expected list but got non-list

---

## 🧪 Testing

```bash
pytest -v
```

Includes coverage for:

* Core `Mapper`
* `ArrayMapper` with wildcards and fixed indices
* Defaults auto-creation
* Optional mappings
* Deep nesting and mixed scenarios

---

## 📄 License

MIT © 2025 Pedro Marques