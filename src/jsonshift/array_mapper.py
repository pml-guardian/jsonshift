from __future__ import annotations
from typing import Any, Dict, List
from .mapper import Mapper, _get, _set, _MISSING
from .exceptions import MappingMissingError


class ArrayMapper(Mapper):
    """
    Extends Mapper with support for wildcard list mappings like:
        "dest[*].id": "source[*].product_id"
    """

    def transform(
        self, spec: Dict[str, Any], payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        out: Dict[str, Any] = {}

        mapping = spec.get("map", {}) or {}
        defaults = spec.get("defaults", {}) or {}

        # -----------------------------
        # 1) FIRST PASS → MAP VALUES
        # -----------------------------
        for dest, src in mapping.items():

            # -----------------------------
            # WILDCARD MAPPING (source[*])
            # -----------------------------
            if "[*]" in src:
                src_prefix, src_suffix = src.split("[*]", 1)
                dest_prefix, dest_suffix = dest.split("[*]", 1)

                src_prefix = src_prefix.rstrip(".")
                dest_prefix = dest_prefix.rstrip(".")
                src_suffix = src_suffix.lstrip(".")
                dest_suffix = dest_suffix.lstrip(".")

                # Load source list
                src_list = _get(payload, src_prefix, default=_MISSING)
                if src_list is _MISSING:
                    raise MappingMissingError(src, dest)
                if not isinstance(src_list, list):
                    raise TypeError(
                        f"Expected list at '{src_prefix}', got {type(src_list)}"
                    )

                # FIX → use _get instead of out.get
                existing_list = _get(out, dest_prefix, default=None)
                if isinstance(existing_list, list):
                    dest_list = existing_list
                else:
                    dest_list = [{} for _ in src_list]

                # Ensure same size
                while len(dest_list) < len(src_list):
                    dest_list.append({})

                # Fill each list entry
                for i, item in enumerate(src_list):
                    val = _get(item, src_suffix, default=_MISSING)
                    if val is _MISSING:
                        raise MappingMissingError(src, dest)

                    if dest_suffix:
                        _set(dest_list[i], dest_suffix, val)
                    else:
                        dest_list[i] = val

                # FIX → nested _set instead of out[dest_prefix] = ...
                _set(out, dest_prefix, dest_list)

            # -----------------------------
            # NORMAL NON-WILDCARD MAPPING
            # -----------------------------
            else:
                val = _get(payload, src, default=_MISSING)
                if val is _MISSING:
                    raise MappingMissingError(src, dest)

                _set(out, dest, val)

        # -----------------------------
        # 2) SECOND PASS → DEFAULTS
        # -----------------------------
        for dest, fixed in defaults.items():

            # DEFAULTS WITH WILDCARD
            if "[*]" in dest:
                dest_prefix, dest_suffix = dest.split("[*]", 1)

                dest_prefix = dest_prefix.rstrip(".")
                dest_suffix = dest_suffix.lstrip(".")

                # FIX → use _get instead of out.get
                dest_list = _get(out, dest_prefix, default=None)
                if not isinstance(dest_list, list):
                    continue

                for obj in dest_list:
                    if _get(obj, dest_suffix, default=_MISSING) is _MISSING:
                        _set(obj, dest_suffix, fixed)

            # DEFAULTS WITHOUT WILDCARD
            else:
                if _get(out, dest, default=_MISSING) is _MISSING:
                    _set(out, dest, fixed)

        return out