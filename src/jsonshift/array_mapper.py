from __future__ import annotations
from typing import Any, Dict, List, Tuple, Union
import re
from .mapper import Mapper, _get, _MISSING, _normalize_mapping_entry
from .exceptions import MappingMissingError


_INDEX = re.compile(r"^(?P<key>[^\[]+)\[(?P<index>\d+|\*)\]$")


def _parse_dest_path(path: str) -> List[Tuple[str, Union[int, None]]]:
    parts = []
    for segment in path.split("."):
        m = _INDEX.match(segment)
        if m:
            key = m.group("key")
            idx = m.group("index")
            parts.append((key, -1 if idx == "*" else int(idx)))
        else:
            parts.append((segment, None))
    return parts


def _ensure_list_size(lst: list, index: int):
    while len(lst) <= index:
        lst.append({})


def _ensure_parent_structure(obj: Dict[str, Any], tokens, index: int):
    if len(tokens) <= 1:
        return

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

    _ensure_parent_structure(target, tokens[1:], index)


def _set_recursive(obj: Dict[str, Any], tokens, value, index: int):
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
            if idx == -1:
                lst[index] = value
            else:
                lst[idx] = value
        else:
            obj[key] = value
        return

    _set_recursive(target, tokens[1:], value, index)


def _apply_default_recursive(obj: Any, tokens, value):
    key, idx = tokens[0]

    if idx is not None:
        lst = obj.setdefault(key, [])
        if idx == -1:
            if not lst:
                lst.append({})
            targets = lst
        else:
            _ensure_list_size(lst, idx)
            targets = [lst[idx]]

        for item in targets:
            if len(tokens) == 1:
                continue
            _apply_default_recursive(item, tokens[1:], value)
        return

    if len(tokens) == 1:
        if key not in obj:
            obj[key] = value
        return

    if key not in obj or not isinstance(obj[key], dict):
        obj[key] = {}

    _apply_default_recursive(obj[key], tokens[1:], value)


class ArrayMapper(Mapper):
    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        output: Dict[str, Any] = {}

        for dest_path, entry in (spec.get("map") or {}).items():
            entry = _normalize_mapping_entry(entry)
            src_path = entry["path"]
            optional = entry["optional"]

            src_has_wildcard = "[*]" in src_path
            tokens = _parse_dest_path(dest_path)

            if src_has_wildcard:
                src_prefix, src_suffix = src_path.split("[*]", 1)
                src_prefix = src_prefix.rstrip(".")
                src_suffix = src_suffix.lstrip(".")

                src_list = _get(payload, src_prefix, default=_MISSING)
                if src_list is _MISSING:
                    if optional:
                        continue
                    raise MappingMissingError(src_path, dest_path)

                if not isinstance(src_list, list):
                    raise TypeError(f"Expected list at '{src_prefix}', got {type(src_list)}")

                for index, element in enumerate(src_list):
                    value = element if not src_suffix else _get(element, src_suffix, default=_MISSING)

                    if value is _MISSING:
                        if optional:
                            _ensure_parent_structure(output, tokens, index)
                            continue
                        raise MappingMissingError(src_path, dest_path)

                    _set_recursive(output, tokens, value, index)
            else:
                value = _get(payload, src_path, default=_MISSING)

                if value is _MISSING:
                    if optional:
                        _ensure_parent_structure(output, tokens, 0)
                        continue
                    raise MappingMissingError(src_path, dest_path)

                _set_recursive(output, tokens, value, 0)

        for dest_path, default_value in (spec.get("defaults") or {}).items():
            tokens = _parse_dest_path(dest_path)
            _apply_default_recursive(output, tokens, default_value)

        return output