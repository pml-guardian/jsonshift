from __future__ import annotations
from typing import Any, Dict
from .mapper import Mapper, _get, _set, _MISSING, _normalize_mapping_entry
from .exceptions import MappingMissingError


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

                dest_prefix, dest_suffix = dest_path.split("[*]", 1)
                dest_prefix = dest_prefix.rstrip(".")
                dest_suffix = dest_suffix.lstrip(".")

                existing_list = _get(output, dest_prefix, default=None)
                dest_list = existing_list if isinstance(existing_list, list) else [{} for _ in src_list]

                while len(dest_list) < len(src_list):
                    dest_list.append({})

                for index, element in enumerate(src_list):
                    if src_has_wildcard:
                        value = _get(element, src_suffix, default=_MISSING)
                    else:
                        value = _get(payload, src_path, default=_MISSING)

                    if value is _MISSING:
                        if optional:
                            continue
                        raise MappingMissingError(src_path, dest_path)

                    if dest_suffix:
                        _set(dest_list[index], dest_suffix, value)
                    else:
                        dest_list[index] = value

                _set(output, dest_prefix, dest_list)
                continue

            value = _get(payload, src_path, default=_MISSING)
            if value is _MISSING:
                if optional:
                    continue
                raise MappingMissingError(src_path, dest_path)

            _set(output, dest_path, value)

        for dest_path, default_value in defaults.items():
            if "[*]" in dest_path:
                dest_prefix, dest_suffix = dest_path.split("[*]", 1)
                dest_prefix = dest_prefix.rstrip(".")
                dest_suffix = dest_suffix.lstrip(".")
                dest_list = _get(output, dest_prefix, default=None)

                if not isinstance(dest_list, list):
                    continue

                for entry in dest_list:
                    if _get(entry, dest_suffix, default=_MISSING) is _MISSING:
                        _set(entry, dest_suffix, default_value)
            else:
                if _get(output, dest_path, default=_MISSING) is _MISSING:
                    _set(output, dest_path, default_value)

        return output