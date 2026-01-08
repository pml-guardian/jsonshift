from __future__ import annotations
from typing import Any, Dict, List, Tuple
from .mapper import Mapper, _get, _set, _MISSING, _normalize_mapping_entry
from .exceptions import MappingMissingError


def _parse_dest_path(path: str) -> List[Tuple[str, bool]]:
    parts: List[Tuple[str, bool]] = []
    for segment in path.split("."):
        if segment.endswith("[*]"):
            parts.append((segment[:-3], True))
        else:
            parts.append((segment, False))
    return parts


def _set_recursive(obj: Dict[str, Any], tokens, value, index: int) -> None:
    key, is_list = tokens[0]

    if is_list:
        lst = obj.setdefault(key, [])
        while len(lst) <= index:
            lst.append({})
        target = lst[index]
    else:
        target = obj.setdefault(key, {})

    if len(tokens) == 1:
        if is_list:
            obj[key][index] = value
        else:
            obj[key] = value
        return

    _set_recursive(target, tokens[1:], value, index)


def _apply_default_recursive(obj: Any, tokens, value) -> None:
    key, is_list = tokens[0]

    if is_list:
        lst = obj.get(key)
        if not isinstance(lst, list):
            return

        for item in lst:
            if len(tokens) == 1:
                if key not in obj:
                    obj[key] = []
                continue
            _apply_default_recursive(item, tokens[1:], value)
        return

    if len(tokens) == 1:
        if key not in obj:
            obj[key] = value
        return

    if key not in obj or not isinstance(obj[key], dict):
        return

    _apply_default_recursive(obj[key], tokens[1:], value)


class ArrayMapper(Mapper):
    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        output: Dict[str, Any] = {}
        mapping = spec.get("map", {}) or {}
        defaults = spec.get("defaults", {}) or {}

        for dest_path, entry in mapping.items():
            entry = _normalize_mapping_entry(entry)
            src_path = entry["path"]
            optional = entry["optional"]

            src_has_wildcard = "[*]" in src_path
            dest_has_wildcard = "[*]" in dest_path

            if src_has_wildcard or dest_has_wildcard:
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
                else:
                    src_list = [payload]
                    src_suffix = src_path

                dest_tokens = _parse_dest_path(dest_path)

                for index, element in enumerate(src_list):
                    if src_has_wildcard:
                        value = _get(element, src_suffix, default=_MISSING)
                    else:
                        value = _get(payload, src_suffix, default=_MISSING)

                    if value is _MISSING:
                        if optional:
                            continue
                        raise MappingMissingError(src_path, dest_path)

                    _set_recursive(output, dest_tokens, value, index)

                continue

            value = _get(payload, src_path, default=_MISSING)
            if value is _MISSING:
                if optional:
                    continue
                raise MappingMissingError(src_path, dest_path)

            _set(output, dest_path, value)

        for dest_path, default_value in defaults.items():
            if "[*]" in dest_path:
                tokens = _parse_dest_path(dest_path)
                _apply_default_recursive(output, tokens, default_value)
            else:
                if _get(output, dest_path, default=_MISSING) is _MISSING:
                    _set(output, dest_path, default_value)

        return output