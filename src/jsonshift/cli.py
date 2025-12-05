import json
import sys
from argparse import ArgumentParser, FileType
from .mapper import Mapper
from .array_mapper import ArrayMapper


def main():
    ap = ArgumentParser(description="jsonshift: simple and deterministic JSON payload mapper")
    ap.add_argument(
        "--spec",
        required=True,
        type=FileType("r"),
        help="Path to the JSON spec file (contains 'map' and optional 'defaults').",
    )
    ap.add_argument(
        "--input",
        type=FileType("r"),
        default=sys.stdin,
        help="Path to the input JSON payload (defaults to stdin).",
    )

    args = ap.parse_args()

    # Load spec and payload
    spec = json.load(args.spec)
    payload = json.load(args.input)

    # --- Detect if spec uses wildcard list mapping
    spec_text = json.dumps(spec)
    if "[*]" in spec_text:
        mapper = ArrayMapper()
    else:
        mapper = Mapper()

    # Perform mapping
    out = mapper.transform(spec, payload)

    # Print formatted JSON result to stdout
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()  # newline