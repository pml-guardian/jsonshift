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

---

## 🧩 Installation

```bash
pip install jsonshift
# or for development:
pip install -e .[dev]
```

---

## 🚀 Complex example (Python)

```python
from jsonshift import Mapper

payload = {
    "customer_name": "John Doe",
    "cpf": "12345678901",
    "email": "JOHN@DOE.COM",
    "amount": 1500.0,
    "products": [
        {"id": "P-001", "name": "Notebook", "price": 4500.0},
        {"id": "P-002", "name": "Mouse", "price": 250.0}
    ]
}

spec = {
    "map": {
        "customer.name": "customer_name",
        "customer.cpf": "cpf",
        "customer.email": "email",

        "contract.products[*].code": "products[*].id",
        "contract.products[*].price": "products[*].price"
    },

    "defaults": {
        "contract.created_at": {"$now": "datetime"},
        "contract.currency": "BRL"
    }
}

out = Mapper().transform(spec, payload)
print(out)
```

---

## 🧠 Dynamic defaults

Dynamic expressions are supported **only inside `defaults`** and are resolved recursively.

All dynamic operators:

* are explicit
* are deterministic
* do not override existing values
* return `None` if any dependency resolves to `None`

---

## 🔹 `$path`

Explicitly resolves a value from the payload.

```json
{
  "defaults": {
    "user_id": { "$path": "id" }
  }
}
```

---

## 🔹 `$now`

Resolves the current time.

```json
{ "$now": "datetime" }
{ "$now": "date" }
{ "$now": "time" }
{ "$now": "year" }
{ "$now": "month" }
{ "$now": "day" }
```

---

## 🔹 `$concat`

Concatenates strings and resolved values.

```json
{
  "defaults": {
    "code": {
      "$concat": [
        "USR-",
        { "$path": "id" }
      ]
    }
  }
}
```

---

## 🔹 String transforms

```json
{ "$upper": { "$path": "name" } }
{ "$lower": { "$path": "email" } }
{ "$capitalize": { "$path": "first_name" } }
{ "$title": { "$path": "full_name" } }
```

---

## 🔢 Math operators

All math operators require numeric values.

### `$add`

```json
{
  "$add": {
    "value": 10,
    "by": 5
  }
}
```

### `$sub`, `$mul`, `$div`

```json
{
  "$mul": {
    "value": 100,
    "by": 0.92
  }
}
```

Division by zero raises an error.

---

## 📅 Date arithmetic with `$add`

`$add` also supports **date and datetime arithmetic**.

```json
{
  "$add": {
    "value": { "$now": "date" },
    "by": { "days": 5 }
  }
}
```

Supported units:

* `years`
* `months`
* `days`
* `hours`
* `minutes`
* `seconds`

---

## 🔢 `$round`

Rounds numeric values.

```json
{
  "$round": {
    "value": 3.14159,
    "ndigits": 2
  }
}
```

Works with composed expressions.

---

## 🎨 `$format`

### Date formatting (`strftime`)

```json
{
  "$format": {
    "value": { "$now": "datetime" },
    "strftime": "%Y-%m-%d"
  }
}
```

### Masks (CPF / CNPJ / custom)

```json
{
  "$format": {
    "value": "12345678901",
    "mask": "###.###.###-##"
  }
}
```

---

## 🔗 Composition

Operators can be nested freely.

```json
{
  "$round": {
    "value": {
      "$mul": {
        "value": 0.920066,
        "by": 100
      }
    },
    "ndigits": 2
  }
}
```

Result:

```json
92.01
```

---

## 📌 Notes

* Dynamic expressions are evaluated **only inside `defaults`**
* `$path` must be explicit
* Missing paths raise `MappingMissingError`
* If any resolved value is `None`, the result is `None`
* Defaults never override existing values

---

## 🖥️ Command-line interface (CLI)

```bash
jsonshift --spec examples/spec.json --input examples/payload.json
```

Or via stdin:

```bash
cat payload.json | jsonshift --spec spec.json
```

---

## 🧪 Testing

```bash
pytest -v
```

---

## 📄 License

MIT © 2025 Pedro Marques