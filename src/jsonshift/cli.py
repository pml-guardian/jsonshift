import json
import sys
from argparse import ArgumentParser, FileType
from .mapper import Mapper


def main():
    ap = ArgumentParser(description="jsonshift: deterministic JSON payload mapper")
    ap.add_argument("--spec", required=True, type=FileType("r"))
    ap.add_argument("--input", type=FileType("r"), default=sys.stdin)

    args = ap.parse_args()

    spec = json.load(args.spec)
    payload = json.load(args.input)

    out = Mapper().transform(spec, payload)
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    print()