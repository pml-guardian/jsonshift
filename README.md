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
  * append index (`[+]`) — destination only
  * automatic list creation
  * infinite nesting depth

* Supports **optional mappings** using `optional: true`
* Supports **conditional fields** using `$if` + comparison operators
* Supports **boolean composition** using `$and`, `$or`, `$not`, `$exists`
* Supports **list predicates** using `$any`, `$all`, `$find`, `$filter`
* Supports **string/list length** using `$len`
* Supports **appending list elements** using `[+]`

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

## 🧠 Wildcard defaults (broadcast)

A default whose **destination** uses a wildcard (`[*]`) is **broadcast across every
existing element** of that list, filling the field only where it is still absent:

```json
{
  "map":      { "recipient.signers[*].name": "people[*].name" },
  "defaults": { "recipient.signers[*].delivery_method": "email" }
}
```

Every signer produced by `map` receives `"delivery_method": "email"` — not just the
first. This works for static values and for non-wildcard `$path` defaults alike.
If no list exists at that position yet, a single element is created.

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

## 🔢 `$len`

Returns the length of a string, list or dict (number of keys).

```json
{ "$len": { "$path": "document" } }
```

Semantics:

* resolves the operand via the dynamic engine
* `_MISSING` → propagates (field skipped)
* `None` → `None`
* `str` / `list` / `dict` → `len(value)` (int)
* `int` / `float` / `bool` → raises `ValueError`

Typical use — derive a document type without mask hacks:

```json
{
  "defaults": {
    "person_type": {
      "$if": {
        "condition": { "$eq": [{ "$len": { "$path": "borrower.document" } }, 11] },
        "then": "PF",
        "else": "PJ"
      }
    }
  }
}
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

## 🧮 Boolean operators

`$and`, `$or` and `$not` compose any other expression and always return `true`/`false`.

```json
{ "$and": [{ "$eq": [{ "$path": "status" }, "active"] }, { "$gte": [{ "$path": "score" }, 80] }] }
{ "$or": [{ "$exists": "email" }, { "$exists": "phone" }] }
{ "$not": { "$eq": [{ "$path": "status" }, "canceled"] } }
```

**Truthiness**: only `null`, `false` and a missing value are falsy. `0`, `""` and `[]` are truthy —
the same rule `$any` already uses without a comparator.

Unlike the value operators (`$concat`, `$add`, ...), a missing operand does **not** propagate:
`_MISSING` is simply falsy. That is what makes `$not` missing-tolerant:

```json
{ "$not": { "$eq": [{ "$path": "code" }, 15] } }
```

With `$ne`, an absent `code` resolves to `_MISSING` and the field is skipped. With `$not` + `$eq`,
an absent `code` resolves to `true` — the reading "the code is not 15".

`$and` stops on the first falsy condition and `$or` on the first truthy one, so short-circuiting
can be used as a guard against `MappingMissingError`:

```json
{ "$and": [{ "$exists": "score" }, { "$gte": [{ "$path": "score" }, 700] }] }
```

`{ "$and": [] }` is `true` and `{ "$or": [] }` is `false`.

---

## 🔎 `$exists`

Returns `true`/`false` for the presence of a path. It **never raises** and never returns `_MISSING`.

```json
{ "$exists": "employments[0].termination_date" }
```

`null` counts as missing by default. To treat a present-but-null key as existing:

```json
{ "$exists": { "path": "phone", "null_is_missing": false } }
```

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

### `where` — predicate per item

A single comparator can only look at one field. `where` receives **one item at a time**, with the
item as the root, so several fields of the *same* item can be tested together:

```json
{
  "$any": {
    "path": "alerts[*]",
    "where": {
      "$and": [
        { "$not": { "$eq": [{ "$path": "alert_type.code" }, 15] } },
        { "$not": { "$lt": [{ "$path": "absence_end_date" }, { "$format": { "value": { "$now": "date" }, "date": { "strftime": "%Y-%m-%d" } } }] } }
      ]
    }
  }
}
```

Note the path ends in `[*]` (the item itself), not in a field.

Inside `where` every `$path` is **implicitly optional** — list items from a real API are
heterogeneous, so an absent field resolves to `_MISSING` (falsy) instead of raising. Write
`"optional": false` explicitly to opt back into strict behavior.

`where` cannot be combined with a comparator (`eq`, `ne`, `gt`, ...) in the same expression.

---

## 🔍 `$all`

Same form as `$any` (comparator or `where`), but returns `true` only when **every** item matches.
An empty list or an absent path returns `true`.

```json
{ "$all": { "path": "installments[*].status", "eq": "paid" } }
{ "$all": { "path": "items[*]", "where": { "$gte": [{ "$path": "value" }, 10] } } }
```

---

## 🎯 `$find`

Returns the **first matching item** instead of a boolean.

```json
{ "$find": { "path": "products[*]", "where": { "$eq": [{ "$path": "type_product" }, "LOAN"] } } }
```

`select` picks a value from the found item — a relative path, or any expression evaluated with
the item as the root:

```json
{
  "$find": {
    "path": "products[*]",
    "where": { "$eq": [{ "$path": "type_product" }, "LOAN"] },
    "select": "available_balance",
    "default": 0
  }
}
```

When nothing matches (or `select` resolves to nothing), `$find` returns `default` if declared,
otherwise `_MISSING` and the field is skipped.

---

## 🧹 `$filter`

Same form as `$find`, but returns **every** matching item as a list (empty when nothing matches).

```json
{ "$filter": { "path": "products[*]", "where": { "$eq": [{ "$path": "type_product" }, "LOAN"] }, "select": "id" } }
```

Combine with `$len` to count:

```json
{ "$len": { "$filter": { "path": "alerts[*]", "where": { "$ne": [{ "$path": "alert_type.code" }, 15] } } } }
```

---

## ➕ Append index `[+]`

A destination path may end in `[+]` to **append a new element** to the end of a list.
It is **write-only** (using `[+]` to read raises an error) and is meant for `defaults`.

Because `defaults` run **after** `map`, the new element is appended **after** the
elements produced by the mapping.

```json
{
  "map": { "events[*].x": "items[*].a" },
  "defaults": {
    "events[+]": {
      "type": "099",
      "date": { "$path": "contract.maturity_date" },
      "status": "1"
    }
  }
}
```

With `payload = {"contract": {"maturity_date": "2026-03-10"}, "items": [{"a": 1}]}`:

```json
{ "events": [ { "x": 1 }, { "type": "099", "date": "2026-03-10", "status": "1" } ] }
```

Rules:

* the `[+]` template is resolved **recursively** — every nested value passes through the
  dynamic engine (`$path`, `$if`, `$len`, `$concat`, … and literals), unlike a plain
  `defaults` value which only resolves at the top level
* a leaf resolving to `_MISSING` (e.g. an absent `optional` `$path`) is dropped from the element
* if the list does not exist yet, it is created
* each `[+]` entry appends exactly **one** element; to append to two different lists use two
  distinct keys (`events[+]` and `logs[+]`)
* fixed indices may precede `[+]` (e.g. `groups[0].events[+]`)
* `[+]` must be the **final** segment, and it **cannot** be combined with a wildcard `[*]`
  in the same path — both raise a clear `ValueError`

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
* `$and`, `$or`, `$not` and `$exists` always return `true`/`false` — `_MISSING` is falsy, not propagated
* `$exists` never raises and treats `null` as missing unless `null_is_missing: false`
* `$all` returns `true` for an empty list or an absent path
* `where` / `select` run with the item as the root and cannot read the outer payload
* Every `$path` inside `where` / `select` is optional unless `"optional": false` is explicit
* `$len` returns an int for str/list/dict, `None` for `None`, and raises for numbers/bools
* `[+]` is write-only, must be the final segment, and cannot be combined with `[*]`

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