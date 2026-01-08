import json
import sys
from argparse import ArgumentParser, FileType
from datetime import date, datetime, time

from .mapper import Mapper


def _json_default(obj):
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


def main():
    ap = ArgumentParser(description="jsonshift: deterministic JSON payload mapper")
    ap.add_argument(
        "--spec",
        required=True,
        type=FileType("r"),
        help="Path to the JSON spec file.",
    )
    ap.add_argument(
        "--input",
        type=FileType("r"),
        default=sys.stdin,
        help="Path to the input JSON payload (defaults to stdin).",
    )

    args = ap.parse_args()

    spec = json.load(args.spec)
    payload = json.load(args.input)

    out = Mapper().transform(spec, payload)

    json.dump(
        out,
        sys.stdout,
        ensure_ascii=False,
        indent=2,
        default=_json_default,
    )
    print()