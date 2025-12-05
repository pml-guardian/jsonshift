from __future__ import annotations
from typing import Any, Dict, List, Union
import re
from .exceptions import MappingMissingError, InvalidDestinationPath

_MISSING = object()
_INDEX = re.compile(r"\[(\d+)\]")


def _split_path(path: str) -> List[Union[str, int]]:
    """Split a dotted or indexed path like 'a.b[0].c' into tokens ['a', 'b', 0, 'c']."""
    if not isinstance(path, str) or not path:
        raise ValueError("Path must be a non-empty string.")
    parts: List[Union[str, int]] = []
    for chunk in path.split("."):
        while chunk:
            m = _INDEX.search(chunk)
            if not m:
                parts.append(chunk)
                break
            head = chunk[: m.start()]
            if head:
                parts.append(head)
            parts.append(int(m.group(1)))
            chunk = chunk[m.end():]
    return parts


def _get(obj: Any, path: str, *, default: Any = _MISSING) -> Any:
    """Safely retrieve a nested value from a dict/list structure following a dotted path."""
    cur = obj
    for tok in _split_path(path):
        try:
            if isinstance(tok, int):
                cur = cur[tok]
            else:
                cur = cur[tok] if isinstance(cur, dict) else getattr(cur, tok)
        except (KeyError, IndexError, AttributeError, TypeError):
            return default
    return cur


def _set(obj: Dict[str, Any], path: str, value: Any) -> None:
    """Set a nested value inside a dict following a dotted path."""
    tokens = _split_path(path)
    cur: Dict[str, Any] = obj
    for tok in tokens[:-1]:
        if isinstance(tok, int):
            raise InvalidDestinationPath(path)
        nxt = cur.get(tok)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[tok] = nxt
        cur = nxt
    last = tokens[-1]
    if isinstance(last, int):
        raise InvalidDestinationPath(path)
    cur[last] = value


class Mapper:
    """
    A minimal, deterministic JSON payload mapper.

    Rules:
      - If the source path does not exist → raise MappingMissingError.
      - If the source value is None → keep None (do not replace).
      - Defaults apply ONLY when the destination field is absent (not set by map).
        Defaults do not overwrite None or existing values.
    """

    def __init__(self) -> None:
        pass

    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        """Transform the given payload based on a mapping spec."""
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        out: Dict[str, Any] = {}

        # --- 1) Apply map (required sources)
        mapping = spec.get("map", {}) or {}
        if not isinstance(mapping, dict):
            raise TypeError("spec['map'] must be a dict of 'destination':'source'.")

        for dest, src in mapping.items():
            if not isinstance(dest, str) or not isinstance(src, str):
                raise TypeError("Mapping entries must be strings: dest:str -> source:str.")
            val = _get(payload, src, default=_MISSING)
            if val is _MISSING:
                raise MappingMissingError(source_path=src, dest_path=dest)
            _set(out, dest, val)  # Keep None as-is

        # --- 2) Apply defaults (only when destination is absent)
        defaults = spec.get("defaults", {}) or {}
        if not isinstance(defaults, dict):
            raise TypeError("spec['defaults'] must be a dict of 'destination':value.")
        for dest, fixed in defaults.items():
            if _get(out, dest, default=_MISSING) is _MISSING:
                _set(out, dest, fixed)

        return out