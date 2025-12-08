from __future__ import annotations
from typing import Any, Dict, List, Union
import re
from .exceptions import MappingMissingError, InvalidDestinationPath

_MISSING = object()
_INDEX = re.compile(r"\[(\d+)\]")


def _split_path(path: str) -> List[Union[str, int]]:
    if not isinstance(path, str) or not path:
        raise ValueError("Path must be a non-empty string.")
    parts: List[Union[str, int]] = []
    for segment in path.split("."):
        while segment:
            match = _INDEX.search(segment)
            if not match:
                parts.append(segment)
                break
            head = segment[: match.start()]
            if head:
                parts.append(head)
            parts.append(int(match.group(1)))
            segment = segment[match.end():]
    return parts


def _get(obj: Any, path: str, *, default: Any = _MISSING) -> Any:
    current = obj
    for token in _split_path(path):
        try:
            if isinstance(token, int):
                if not isinstance(current, list) or token >= len(current):
                    return default
                current = current[token]
            else:
                if isinstance(current, dict):
                    if token not in current:
                        return default
                    current = current[token]
                else:
                    current = getattr(current, token)
        except Exception:
            return default
    return current


def _set(obj: Dict[str, Any], path: str, value: Any) -> None:
    tokens = _split_path(path)
    current = obj
    for token in tokens[:-1]:
        if isinstance(token, int):
            raise InvalidDestinationPath(path)
        if token not in current or not isinstance(current[token], dict):
            current[token] = {}
        current = current[token]
    last = tokens[-1]
    if isinstance(last, int):
        raise InvalidDestinationPath(path)
    current[last] = value


def _normalize_mapping_entry(entry):
    if isinstance(entry, str):
        return {"path": entry, "optional": False}
    if isinstance(entry, dict):
        return {
            "path": entry["path"],
            "optional": entry.get("optional", False),
        }
    raise TypeError("Invalid mapping entry type")


class Mapper:
    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        output: Dict[str, Any] = {}

        mapping = spec.get("map", {}) or {}
        for dest_path, entry in mapping.items():
            entry = _normalize_mapping_entry(entry)
            src_path = entry["path"]
            value = _get(payload, src_path, default=_MISSING)

            if value is _MISSING:
                if entry["optional"]:
                    continue
                raise MappingMissingError(src_path, dest_path)

            _set(output, dest_path, value)

        defaults = spec.get("defaults", {}) or {}
        for dest_path, default_value in defaults.items():
            if _get(output, dest_path, default=_MISSING) is _MISSING:
                _set(output, dest_path, default_value)

        return output