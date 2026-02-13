from __future__ import annotations
import re
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple, Union
from dateutil.relativedelta import relativedelta
from .exceptions import MappingMissingError

_MISSING = object()
_INDEX = re.compile(r"^(?P<key>[^\[]+)\[(?P<index>\d+|\*)\]$")


def _parse_path(path: str) -> List[Tuple[str, Union[int, None]]]:
    parts = []

    for segment in path.split("."):
        m = _INDEX.match(segment)

        if m:
            idx = m.group("index")
            parts.append((m.group("key"), -1 if idx == "*" else int(idx)))

        else:
            parts.append((segment, None))

    return parts


def _ensure_list_size(lst: list, index: int) -> None:
    while len(lst) <= index:
        lst.append({})


def _get_value(obj: Any, tokens, index: int):
    current = obj

    for key, idx in tokens:
        if not isinstance(current, dict) or key not in current:
            return _MISSING

        current = current[key]

        if idx is not None:
            if not isinstance(current, list):
                return _MISSING

            pos = index if idx == -1 else idx

            if pos >= len(current):
                return _MISSING

            current = current[pos]

    return current


def _resolve_all(obj: Any, tokens: List[Tuple[str, Union[int, None]]]):
    if not tokens:
        return [obj]

    key, idx = tokens[0]
    rest = tokens[1:]

    if not isinstance(obj, dict) or key not in obj:
        return []

    current = obj[key]

    if idx is None:
        return _resolve_all(current, rest)

    if not isinstance(current, list):
        return []

    if idx == -1:
        results = []

        for item in current:
            sub = _resolve_all(item, rest)

            if sub:
                results.extend(sub)

            else:
                results.append(_MISSING)

        return results

    if idx < len(current):
        return _resolve_all(current[idx], rest)

    return []


def _set_value(obj: Dict[str, Any], tokens, value, index: int | None) -> None:
    key, idx = tokens[0]

    if idx is not None:
        lst = obj.setdefault(key, [])

        if idx == -1:
            pos = index

        else:
            pos = idx

        _ensure_list_size(lst, pos)
        target = lst[pos]

    else:
        target = obj.setdefault(key, {})

    if len(tokens) == 1:
        if idx is not None:
            lst[pos] = value

        else:
            obj[key] = value

        return

    _set_value(target, tokens[1:], value, index)


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))

    except (InvalidOperation, TypeError):
        raise ValueError("Math operators require numeric values")


def _resolve_path(path: str, payload: Dict[str, Any]):
    tokens = _parse_path(path)
    value = _get_value(payload, tokens, 0)

    if value is _MISSING:
        raise MappingMissingError(path, "dynamic")

    return value


def _resolve_now(expr):
    if not isinstance(expr, str):
        raise ValueError("$now must be a string")

    now = datetime.now()

    if expr == "datetime":
        return now

    if expr == "date":
        return now.date()

    if expr == "time":
        return now.time()

    if expr == "year":
        return now.year

    if expr == "month":
        return now.month

    if expr == "day":
        return now.day

    raise ValueError(f"Invalid $now value: {expr}")


def _resolve_concat(parts, payload):
    if not isinstance(parts, list):
        raise ValueError("$concat must be a list")

    out = []

    for part in parts:
        if isinstance(part, dict) and "$path" in part:
            value = _resolve_path(part["$path"], payload)

            if value is None:
                return None

            out.append(str(value))

        elif isinstance(part, str):
            out.append(part)

        else:
            raise ValueError("Invalid $concat element")

    return "".join(out)


def _resolve_add(expr, payload):
    value = _resolve_dynamic(expr["value"], payload)
    by = expr.get("by")

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        if not isinstance(by, dict):
            raise ValueError("$add.by must be an object for dates")

        return value + relativedelta(**by)

    return _resolve_math(expr, payload, "add")


def _resolve_math(expr, payload, op):
    value = _resolve_dynamic(expr["value"], payload)
    by = expr.get("by")

    if value is None:
        return None

    value = _to_decimal(value)
    by = _to_decimal(by)

    if op == "add":
        return float(value + by)

    if op == "sub":
        return float(value - by)

    if op == "mul":
        return float(value * by)

    if op == "div":
        if by == 0:
            raise ValueError("Division by zero")
        return float(value / by)

    if op == "pow":
        return float(value**by)

    raise ValueError("Invalid math operator")


def _resolve_round(expr, payload):
    value = _resolve_dynamic(expr["value"], payload)

    if value is None:
        return None

    value = _to_decimal(value)
    ndigits = int(expr["ndigits"])
    quant = Decimal("1." + "0" * ndigits)
    result = value.quantize(quant, rounding=ROUND_HALF_UP)

    return float(result)


def _apply_mask(value: str, mask: str) -> str:
    digits = iter(re.sub(r"\D", "", value))
    out = []

    for c in mask:
        if c == "#":
            out.append(next(digits, ""))

        else:
            out.append(c)

    return "".join(out)


def _resolve_format(expr, payload):
    value = _resolve_dynamic(expr["value"], payload)

    if value is None:
        return None

    if "strftime" in expr:
        if not hasattr(value, "strftime"):
            raise ValueError("$format.strftime requires date or datetime")

        return value.strftime(expr["strftime"])

    if "mask" in expr:
        return _apply_mask(str(value), expr["mask"])

    if "number" in expr:
        value = _to_decimal(value)
        decimals = expr["number"].get("decimals", 2)
        thousand = expr["number"].get("thousand", ".")
        decimal_sep = expr["number"].get("decimal", ",")
        value = value.quantize(Decimal("1." + "0" * decimals), rounding=ROUND_HALF_UP)
        parts = f"{value:.{decimals}f}".split(".")
        integer = f"{int(parts[0]):,}"

        if thousand != ",":
            integer = integer.replace(",", thousand)

        if decimals > 0:
            return integer + decimal_sep + parts[1]

        return integer

    raise ValueError("Invalid $format expression")


def _string_op(expr, payload, fn):
    value = _resolve_dynamic(expr, payload)

    if value is None:
        return None

    return fn(str(value))


def _resolve_dynamic(value, payload):
    if not isinstance(value, dict):
        return value

    if "$now" in value:
        return _resolve_now(value["$now"])

    if "$path" in value:
        return _resolve_path(value["$path"], payload)

    if "$concat" in value:
        return _resolve_concat(value["$concat"], payload)

    if "$add" in value:
        return _resolve_add(value["$add"], payload)

    if "$sub" in value:
        return _resolve_math(value["$sub"], payload, "sub")

    if "$mul" in value:
        return _resolve_math(value["$mul"], payload, "mul")

    if "$div" in value:
        return _resolve_math(value["$div"], payload, "div")

    if "$pow" in value:
        return _resolve_math(value["$pow"], payload, "pow")

    if "$round" in value:
        return _resolve_round(value["$round"], payload)

    if "$format" in value:
        return _resolve_format(value["$format"], payload)

    if "$upper" in value:
        return _string_op(value["$upper"], payload, str.upper)

    if "$lower" in value:
        return _string_op(value["$lower"], payload, str.lower)

    if "$capitalize" in value:
        return _string_op(value["$capitalize"], payload, str.capitalize)

    if "$title" in value:
        return _string_op(value["$title"], payload, str.title)

    return value


def _normalize(entry):
    if isinstance(entry, str):
        return {"path": entry, "optional": False}

    return {"path": entry["path"], "optional": entry.get("optional", False)}


class Mapper:
    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        output: Dict[str, Any] = {}

        for dest_path, entry in (spec.get("map") or {}).items():
            entry = _normalize(entry)
            src_tokens = _parse_path(entry["path"])
            dest_tokens = _parse_path(dest_path)
            optional = entry["optional"]
            values = _resolve_all(payload, src_tokens)

            if not values:
                if optional:
                    continue

                raise MappingMissingError(entry["path"], dest_path)

            for i, value in enumerate(values):
                if value is _MISSING:
                    if optional:
                        continue

                    raise MappingMissingError(entry["path"], dest_path)

                _set_value(output, dest_tokens, value, i)

        for dest_path, default in (spec.get("defaults") or {}).items():
            tokens = _parse_path(dest_path)
            resolved = _resolve_dynamic(default, payload)

            if _get_value(output, tokens, 0) is _MISSING:
                _set_value(output, tokens, resolved, 0)

        return output