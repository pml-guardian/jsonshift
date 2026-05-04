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
* Supports **conditional fields** using `$if` + comparison operators
* Supports **list membership checks** using `$any`

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

All math operators:

* accept `int`, `float`, or numeric `string`
* use `Decimal` internally
* return `float`

---

### `$add`, `$sub`, `$mul`, `$div`, `$pow`

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

### Date formatting

```json
{
  "$format": {
    "value": "2024-06-01",
    "date": {
      "parse": "%Y-%m-%d",
      "strftime": "%d/%m/%Y"
    }
  }
}
```

---

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

### 🔢 Number formatting

```json
{
  "$format": {
    "value": 10000,
    "number": {
      "decimals": 2,
      "thousand": ".",
      "decimal": ","
    }
  }
}
```

---

## 🔀 `$if`

Conditionally creates a field based on a `condition`. Returns the value of `then` when the condition is truthy, or `else` when it is falsy/null/absent. If `else` is omitted and the condition fails, **the field is not created**.

```json
{
  "defaults": {
    "doc_id": {
      "$if": {
        "condition": { "$path": "secondary_doc", "optional": true },
        "then": "2"
      }
    }
  }
}
```

With `else`:

```json
{
  "defaults": {
    "category": {
      "$if": {
        "condition": { "$gt": [{ "$path": "amount" }, 1000] },
        "then": "premium",
        "else": "standard"
      }
    }
  }
}
```

Both `then` and `else` accept any dynamic expression.

---

## ⚖️ Comparison operators

Return `true` or `false`. Designed to be used as the `condition` of `$if`, but can also stand alone as a field value.

| Operator | Meaning |
|---|---|
| `$eq` | equal (`==`) |
| `$ne` | not equal (`!=`) |
| `$gt` | greater than (`>`) |
| `$gte` | greater than or equal (`>=`) |
| `$lt` | less than (`<`) |
| `$lte` | less than or equal (`<=`) |

All operators receive a list of **exactly 2 elements**. Each element can be a static value or any dynamic expression.

```json
{ "$gt": [{ "$path": "score" }, 80] }
{ "$eq": [{ "$path": "status" }, "active"] }
{ "$gte": [{ "$path": "balance" }, { "$path": "minimum" }] }
```

If either operand resolves to `_MISSING`, the operator returns `_MISSING` and the field is skipped. For ordering operators (`$gt`, `$gte`, `$lt`, `$lte`), `null` on either side returns `false`. For `$eq`/`$ne`, `null` is a valid comparable value.

---

## 🔍 `$any`

Returns `true` if **at least one item** in a wildcard path matches a condition. Returns `false` if no items match or the path is absent.

```json
{ "$any": { "path": "alerts[*].alert_type.code", "eq": 1 } }
```

Supports all comparison operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`.

```json
{ "$any": { "path": "items[*].price", "gt": 100 } }
```

Works with nested wildcards:

```json
{ "$any": { "path": "orders[*].items[*].status", "eq": "pending" } }
```

Without a comparator, returns `true` if any value is truthy:

```json
{ "$any": { "path": "flags[*].active" } }
```

Commonly used as a `$if` condition:

```json
{
  "defaults": {
    "has_termination": {
      "$if": {
        "condition": { "$any": { "path": "alerts[*].alert_type.code", "eq": 1 } },
        "then": true,
        "else": false
      }
    }
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
* `$if` without `else` produces no field when the condition is falsy, null, or absent
* Comparison operators expect exactly 2 elements and return `true`/`false`
* `$any` returns `false` when the list is empty or the path is absent — never raises

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