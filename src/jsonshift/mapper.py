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
        return None

    current = obj[key]

    if idx is None:
        return _resolve_all(current, rest)

    if not isinstance(current, list):
        return None

    if idx == -1:
        results = []

        for item in current:
            sub = _resolve_all(item, rest)

            if sub is None:
                results.append(_MISSING)

            else:
                results.extend(sub)

        return results

    if idx < len(current):
        return _resolve_all(current[idx], rest)

    return None


def _resolve_all_with_indices(obj: Any, tokens: List[Tuple[str, Union[int, None]]], current_indices: tuple = ()):
    if not tokens:
        return [(obj, current_indices)]

    key, idx = tokens[0]
    rest = tokens[1:]

    if not isinstance(obj, dict) or key not in obj:
        return None

    current = obj[key]

    if idx is None:
        return _resolve_all_with_indices(current, rest, current_indices)

    if not isinstance(current, list):
        return None

    if idx == -1:
        results = []

        for i, item in enumerate(current):
            subs = _resolve_all_with_indices(item, rest, current_indices + (i,))

            if subs is None:
                results.append((_MISSING, current_indices + (i,)))

            else:
                results.extend(subs)

        return results

    if idx < len(current):
        return _resolve_all_with_indices(current[idx], rest, current_indices)

    return None


def _set_value(obj: Dict[str, Any], tokens, value, index: int | None) -> None:
    key, idx = tokens[0]

    if idx is not None:
        lst = obj.setdefault(key, [])
        pos = index if idx == -1 else idx
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


def _set_value_indexed(obj: Dict[str, Any], tokens, value, wildcard_indices: list) -> None:
    wc_pos = [0]

    def _set(obj, tokens):
        key, idx = tokens[0]

        if idx is not None:
            lst = obj.setdefault(key, [])

            if idx == -1:
                pos = wildcard_indices[wc_pos[0]]
                wc_pos[0] += 1

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

        _set(target, tokens[1:])

    _set(obj, tokens)


def _count_wildcards(tokens) -> int:
    return sum(1 for _, idx in tokens if idx == -1)


def _to_decimal(value):
    if isinstance(value, Decimal):
        return value

    try:
        return Decimal(str(value))

    except (InvalidOperation, TypeError):
        raise ValueError("Math operators require numeric values")


def _resolve_path(path: str, payload: Dict[str, Any], index: int = 0):
    tokens = _parse_path(path)
    value = _get_value(payload, tokens, index)

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


def _resolve_concat(parts, payload, index: int = 0):
    if not isinstance(parts, list):
        raise ValueError("$concat must be a list")

    out = []

    for part in parts:
        value = _resolve_dynamic(part, payload, index)

        if value is _MISSING:
            return _MISSING

        if value is None:
            return None

        out.append(str(value))

    return "".join(out)


def _resolve_add(expr, payload, index: int = 0):
    value = _resolve_dynamic(expr["value"], payload, index)
    by = _resolve_dynamic(expr.get("by"), payload, index)

    if value is _MISSING:
        return _MISSING

    if value is None:
        return None

    if isinstance(value, (datetime, date)):
        if not isinstance(by, dict):
            raise ValueError("$add.by must be an object for dates")

        return value + relativedelta(**by)

    value = _to_decimal(value)
    by = _to_decimal(by)

    return float(value + by)


def _resolve_math(expr, payload, op, index: int = 0):
    value = _resolve_dynamic(expr["value"], payload, index)
    by = _resolve_dynamic(expr.get("by"), payload, index)

    if value is _MISSING:
        return _MISSING

    if value is None:
        return None

    value = _to_decimal(value)
    by = _to_decimal(by)

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


def _resolve_round(expr, payload, index: int = 0):
    value = _resolve_dynamic(expr["value"], payload, index)

    if value is _MISSING:
        return _MISSING

    if value is None:
        return None

    value = _to_decimal(value)
    nd = _resolve_dynamic(expr.get("ndigits", 0), payload, index)
    ndigits = int(nd)

    if ndigits >= 0:
        quant = Decimal("1").scaleb(-ndigits)

    else:
        quant = Decimal("1").scaleb(-ndigits)

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


def _resolve_format(expr, payload, index: int = 0):
    value = _resolve_dynamic(expr["value"], payload, index)

    if value is _MISSING:
        return _MISSING

    if value is None:
        return None

    if "date" in expr:
        cfg = expr["date"]

        if isinstance(value, str) and "parse" in cfg:
            try:
                value = datetime.strptime(value, cfg["parse"])

            except ValueError:
                raise ValueError("Invalid date format for parsing")

        if not isinstance(value, (datetime, date)):
            raise ValueError("$format.date requires date or datetime")

        if "strftime" in cfg:
            return value.strftime(cfg["strftime"])

        return value

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


def _string_op(expr, payload, fn, index: int = 0):
    value = _resolve_dynamic(expr, payload, index)

    if value is _MISSING:
        return _MISSING

    if value is None:
        return None

    return fn(str(value))


def _resolve_dynamic(value, payload, index: int = 0):
    if not isinstance(value, dict):
        return value

    if "$now" in value:
        return _resolve_now(value["$now"])

    if "$path" in value:
        optional = value.get("optional", False)

        try:
            return _resolve_path(value["$path"], payload, index)

        except MappingMissingError:
            if optional:
                return _MISSING

            raise

    if "$concat" in value:
        return _resolve_concat(value["$concat"], payload, index)

    if "$add" in value:
        return _resolve_add(value["$add"], payload, index)

    if "$sub" in value:
        return _resolve_math(value["$sub"], payload, "sub", index)

    if "$mul" in value:
        return _resolve_math(value["$mul"], payload, "mul", index)

    if "$div" in value:
        return _resolve_math(value["$div"], payload, "div", index)

    if "$pow" in value:
        return _resolve_math(value["$pow"], payload, "pow", index)

    if "$round" in value:
        return _resolve_round(value["$round"], payload, index)

    if "$format" in value:
        return _resolve_format(value["$format"], payload, index)

    if "$upper" in value:
        return _string_op(value["$upper"], payload, str.upper, index)

    if "$lower" in value:
        return _string_op(value["$lower"], payload, str.lower, index)

    if "$capitalize" in value:
        return _string_op(value["$capitalize"], payload, str.capitalize, index)

    if "$title" in value:
        return _string_op(value["$title"], payload, str.title, index)

    return value


def _collect_wildcard_paths(expr) -> List[str]:
    if not isinstance(expr, dict):
        return []

    if "$path" in expr and "[*]" in str(expr["$path"]):
        return [expr["$path"]]

    result = []

    for v in expr.values():
        if isinstance(v, dict):
            result.extend(_collect_wildcard_paths(v))

        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    result.extend(_collect_wildcard_paths(item))

    return result


def _has_wildcard_path(expr) -> bool:
    return bool(_collect_wildcard_paths(expr))


def _iter_all_values(payload, tokens):
    if not tokens:
        yield payload
        return

    key, idx = tokens[0]
    rest = tokens[1:]

    if not isinstance(payload, dict) or key not in payload:
        return

    current = payload[key]

    if idx is None:
        yield from _iter_all_values(current, rest)

    elif isinstance(current, list):
        if idx == -1:
            for item in current:
                yield from _iter_all_values(item, rest)

        elif idx < len(current):
            yield from _iter_all_values(current[idx], rest)


def _substitute_wildcard_paths(expr, subs: dict):
    if not isinstance(expr, dict):
        return expr

    if "$path" in expr and expr["$path"] in subs:
        return subs[expr["$path"]]

    result = {}

    for k, v in expr.items():
        if isinstance(v, dict):
            result[k] = _substitute_wildcard_paths(v, subs)

        elif isinstance(v, list):
            result[k] = [
                (
                    _substitute_wildcard_paths(item, subs)
                    if isinstance(item, dict)
                    else item
                )
                for item in v
            ]

        else:
            result[k] = v

    return result


def _resolve_dynamic_vectorized(expr, payload):
    wc_paths = list(dict.fromkeys(_collect_wildcard_paths(expr)))

    if not wc_paths:
        return _resolve_dynamic(expr, payload)

    path_values_map: Dict[str, list] = {}
    count: int | None = None

    for path in wc_paths:
        tokens = _parse_path(path)
        values = list(_iter_all_values(payload, tokens))
        path_values_map[path] = values
        count = len(values) if count is None else min(count, len(values))

    if not count:
        return []

    results = []

    for i in range(count):
        subs = {path: vals[i] for path, vals in path_values_map.items()}
        subst_expr = _substitute_wildcard_paths(expr, subs)
        results.append(_resolve_dynamic(subst_expr, payload))

    return results


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
            n_dest_wildcards = _count_wildcards(dest_tokens)

            if n_dest_wildcards > 1:
                items = _resolve_all_with_indices(payload, src_tokens)

                if items is None:
                    if optional:
                        continue

                    raise MappingMissingError(entry["path"], dest_path)

                dest_idx = 0

                for value, src_indices in items:
                    if value is _MISSING:
                        if optional:
                            continue

                        raise MappingMissingError(entry["path"], dest_path)

                    if len(src_indices) == n_dest_wildcards:
                        _set_value_indexed(output, dest_tokens, value, list(src_indices))

                    else:
                        _set_value(output, dest_tokens, value, dest_idx)
                        dest_idx += 1

            else:
                values = _resolve_all(payload, src_tokens)

                if values is None:
                    if optional:
                        continue

                    raise MappingMissingError(entry["path"], dest_path)

                dest_idx = 0

                for value in values:
                    if value is _MISSING:
                        if optional:
                            continue

                        raise MappingMissingError(entry["path"], dest_path)

                    _set_value(output, dest_tokens, value, dest_idx)
                    dest_idx += 1

        for dest_path, default in (spec.get("defaults") or {}).items():
            tokens = _parse_path(dest_path)
            has_wildcard_dest = any(idx == -1 for _, idx in tokens)

            if has_wildcard_dest and _has_wildcard_path(default):
                resolved = _resolve_dynamic_vectorized(default, payload)

                if isinstance(resolved, list):
                    for i, value in enumerate(resolved):
                        if value is _MISSING:
                            continue

                        if _get_value(output, tokens, i) is _MISSING:
                            _set_value(output, tokens, value, i)

                else:
                    if resolved is _MISSING:
                        continue

                    if _get_value(output, tokens, 0) is _MISSING:
                        _set_value(output, tokens, resolved, 0)

            else:
                resolved = _resolve_dynamic(default, payload)

                if resolved is _MISSING:
                    continue

                if _get_value(output, tokens, 0) is _MISSING:
                    _set_value(output, tokens, resolved, 0)

        return output
