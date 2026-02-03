from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from dateutil.relativedelta import relativedelta

from .exceptions import MappingMissingError


_MISSING = object()
_INDEX = re.compile(r"^(?P<key>[^\[]+)\[(?P<index>\d+|\*)\]$")


# ------------------------------------------------------------------ paths


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


def _set_value(obj: Dict[str, Any], tokens, value, index: int) -> None:
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


# ----------------------------------------------------------- dynamic values


def _resolve_path(path: str, payload: Dict[str, Any]):
    tokens = _parse_path(path)
    value = _get_value(payload, tokens, 0)
    if value is _MISSING:
        raise MappingMissingError(path, "dynamic")
    return value


def _resolve_now(value):
    if not isinstance(value, dict) or "$now" not in value:
        return value

    now = datetime.now()
    expr = value["$now"]

    if isinstance(expr, str):
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
        raise ValueError(f"Invalid $now type: {expr}")

    if not isinstance(expr, dict):
        raise ValueError("Invalid $now expression")

    kind = expr.get("type", "datetime")
    add = expr.get("add")

    if kind == "datetime":
        base = now
    elif kind == "date":
        base = now.date()
    elif kind == "time":
        base = now.time()
    elif kind == "year":
        return now.year
    elif kind == "month":
        return now.month
    elif kind == "day":
        return now.day
    else:
        raise ValueError(f"Invalid $now type: {kind}")

    if add:
        delta = relativedelta(
            years=add.get("years", 0),
            months=add.get("months", 0),
            days=add.get("days", 0),
            hours=add.get("hours", 0),
            minutes=add.get("minutes", 0),
            seconds=add.get("seconds", 0),
        )
        base = base + delta

    return base


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


def _resolve_format(expr, payload):
    if not isinstance(expr, dict):
        raise ValueError("$format must be an object")

    template = expr.get("template")
    args = expr.get("args", {})

    if not isinstance(template, str) or not isinstance(args, dict):
        raise ValueError("Invalid $format structure")

    resolved = {}
    for key, value in args.items():
        v = _resolve_path(value["$path"], payload)
        if v is None:
            return None
        resolved[key] = v

    return template.format(**resolved)


def _string_op(expr, payload, fn):
    value = (
        _resolve_path(expr["$path"], payload)
        if isinstance(expr, dict) and "$path" in expr
        else expr
    )
    if value is None:
        return None
    return fn(str(value))


def _resolve_dynamic(value, payload):
    if not isinstance(value, dict):
        return value

    if "$now" in value:
        return _resolve_now(value)
    if "$concat" in value:
        return _resolve_concat(value["$concat"], payload)
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


# ------------------------------------------------------------------- mapper


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

            has_star = any(idx == -1 for _, idx in src_tokens)

            if has_star:
                src_key = src_tokens[0][0]
                src_list = payload.get(src_key)

                if not isinstance(src_list, list):
                    if optional:
                        continue
                    raise MappingMissingError(entry["path"], dest_path)

                for i in range(len(src_list)):
                    value = _get_value(payload, src_tokens, i)
                    if value is _MISSING:
                        if optional:
                            continue
                        raise MappingMissingError(entry["path"], dest_path)
                    _set_value(output, dest_tokens, value, i)
            else:
                value = _get_value(payload, src_tokens, 0)
                if value is _MISSING:
                    if optional:
                        continue
                    raise MappingMissingError(entry["path"], dest_path)
                _set_value(output, dest_tokens, value, 0)

        for dest_path, default in (spec.get("defaults") or {}).items():
            tokens = _parse_path(dest_path)
            resolved = _resolve_dynamic(default, payload)
            if _get_value(output, tokens, 0) is _MISSING:
                _set_value(output, tokens, resolved, 0)

        return output