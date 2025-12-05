from __future__ import annotations
from typing import Any, Dict
from .mapper import Mapper, _get, _set, _MISSING
from .exceptions import MappingMissingError


class ArrayMapper(Mapper):
    """
    Supports wildcard list mappings like:
        "dest[*].id": "source[*].product_id"
    """

    def transform(self, spec: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(spec, dict):
            raise TypeError("spec must be a dict.")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        out: Dict[str, Any] = {}

        mapping = spec.get("map", {}) or {}
        defaults = spec.get("defaults", {}) or {}

        # ------------------------------------------------------
        # 1) APPLY MAPPING
        # ------------------------------------------------------
        for dest, src in mapping.items():

            # ---------- WILDCARD SOURCE ----------
            if "[*]" in src:
                src_prefix, src_suffix = src.split("[*]", 1)
                src_prefix = src_prefix.rstrip(".")
                src_suffix = src_suffix.lstrip(".")

                # --------- DESTINATION WILDCARD FIX ----------
                # Path to the list (before [*])
                list_path = dest.split("[*]")[0].rstrip(".")

                # Suffix after wildcard
                dest_suffix = dest.split("[*]", 1)[1].lstrip(".")

                # Load source list
                src_list = _get(payload, src_prefix, default=_MISSING)
                if src_list is _MISSING:
                    raise MappingMissingError(src, dest)
                if not isinstance(src_list, list):
                    raise TypeError(
                        f"Expected list at '{src_prefix}', got {type(src_list)}"
                    )

                # Load or initialize destination list
                existing_list = _get(out, list_path, default=None)
                if isinstance(existing_list, list):
                    dest_list = existing_list
                else:
                    dest_list = [{} for _ in src_list]

                # Ensure same size
                while len(dest_list) < len(src_list):
                    dest_list.append({})

                # Fill each entry
                for i, item in enumerate(src_list):
                    val = _get(item, src_suffix, default=_MISSING)
                    if val is _MISSING:
                        raise MappingMissingError(src, dest)

                    if dest_suffix:
                        _set(dest_list[i], dest_suffix, val)
                    else:
                        dest_list[i] = val

                # Save list back
                _set(out, list_path, dest_list)

            # ---------- NORMAL MAPPING ----------
            else:
                val = _get(payload, src, default=_MISSING)
                if val is _MISSING:
                    raise MappingMissingError(src, dest)
                _set(out, dest, val)

        # ------------------------------------------------------
        # 2) APPLY DEFAULTS
        # ------------------------------------------------------
        for dest, fixed in defaults.items():

            # defaults with wildcard
            if "[*]" in dest:
                list_path = dest.split("[*]")[0].rstrip(".")
                dest_suffix = dest.split("[*]", 1)[1].lstrip(".")

                dest_list = _get(out, list_path, default=None)
                if not isinstance(dest_list, list):
                    continue

                for obj in dest_list:
                    if _get(obj, dest_suffix, default=_MISSING) is _MISSING:
                        _set(obj, dest_suffix, fixed)

            # defaults without wildcard
            else:
                if _get(out, dest, default=_MISSING) is _MISSING:
                    _set(out, dest, fixed)

        return out