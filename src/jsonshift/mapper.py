from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union
import re
from datetime import datetime
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


def _ensure_list_size(lst: list, index: int):
    while len(lst) <= index:
        lst.append({})


def _set_value(obj: Dict[str, Any], tokens, value, index: int):
    key, idx = tokens[0]

    if idx is not None:
        lst = obj.setdefault(key, [])
        if idx == -1:
            _ensure_list_size(lst, index)
            target = lst[index]
        else:
            _ensure_list_size(lst, idx)
            target = lst[idx]
    else:
        target = obj.setdefault(key, {})

    if len(tokens) == 1:
        if idx is not None:
            lst[index if idx == -1 else idx] = value
        else:
            obj[key] = value
        return

    _set_value(target, tokens[1:], value, index)


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


# ---------- DYNAMIC RESOLVERS ----------

def _resolve_now(value):
    if not isinstance(value, dict) or "$now" not in value:
        return value

    now = datetime.now()
    kind = value["$now"]

    if kind == "datetime":
        return now
    if kind == "date":
        return now.date()
    if kind == "time":
        return now.time()

    raise ValueError(f"Invalid $now type: {kind}")


def _resolve_path(path: str, payload: Dict[str, Any]):
    tokens = _parse_path(path)
    value = _get_value(payload, tokens, 0)
    if value is _MISSING:
        raise MappingMissingError(path, "dynamic")
    return value


def _resolve_concat(parts, payload):
    if not isinstance(parts, list):
        raise ValueError("$concat must be a list")

    out = []
    for part in parts:
        if isinstance(part, dict) and "$path" in part:
            out.append(str(_resolve_path(part["$path"], payload)))
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

    resolved = {
        key: _resolve_path(value["$path"], payload)
        for key, value in args.items()
    }

    return template.format(**resolved)


def _resolve_upper(expr, payload):
    if isinstance(expr, dict) and "$path" in expr:
        value = _resolve_path(expr["$path"], payload)
    else:
        value = expr
    return str(value).upper()


def _resolve_lower(expr, payload):
    if isinstance(expr, dict) and "$path" in expr:
        value = _resolve_path(expr["$path"], payload)
    else:
        value = expr
    return str(value).lower()


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
        return _resolve_upper(value["$upper"], payload)

    if "$lower" in value:
        return _resolve_lower(value["$lower"], payload)

    return value


def _normalize(entry):
    if isinstance(entry, str):
        return {"path": entry, "optional": False}
    return {
        "path": entry["path"],
        "optional": entry.get("optional", False),
    }


class Mapper:
    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        output: Dict[str, Any] = {}

        # -------- MAP --------
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

        # -------- DEFAULTS --------
        for dest_path, default in (spec.get("defaults") or {}).items():
            tokens = _parse_path(dest_path)
            default = _resolve_dynamic(default, payload)

            index = 0
            existing = _get_value(output, tokens, index)
            if existing is _MISSING:
                _set_value(output, tokens, default, index)

        return output