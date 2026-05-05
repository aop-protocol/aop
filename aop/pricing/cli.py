"""``python -m aop.pricing`` CLI: estimate, list, set."""

from __future__ import annotations

import argparse
import json
import sys

from . import (
    PriceEntry,
    all_prices,
    compute_cost,
    estimate_cost_usd,
    register_price,
)


def main(argv: list = None) -> int:
    parser = argparse.ArgumentParser("aop.pricing")
    sub = parser.add_subparsers(dest="cmd", required=True)

    est = sub.add_parser("estimate", help="Estimate cost for a (provider, model, tokens) call")
    est.add_argument("--provider", required=True)
    est.add_argument("--model", required=True)
    est.add_argument("--prompt", type=int, default=0)
    est.add_argument("--completion", type=int, default=0)
    est.add_argument("--cached", type=int, default=0)

    ls = sub.add_parser("list", help="List all prices in the book")

    se = sub.add_parser("set", help="Override a price at runtime")
    se.add_argument("--provider", required=True)
    se.add_argument("--model", required=True)
    se.add_argument("--input-per-million", type=float, required=True)
    se.add_argument("--output-per-million", type=float, required=True)

    args = parser.parse_args(argv)

    if args.cmd == "estimate":
        cost = compute_cost(provider=args.provider, model=args.model,
                            prompt_tokens=args.prompt,
                            completion_tokens=args.completion,
                            cached_input_tokens=args.cached)
        print(json.dumps(cost, indent=2) if cost else "no price for that model")
        return 0

    if args.cmd == "list":
        for (prov, mdl), entry in sorted(all_prices().items()):
            print(f"{prov:>10} / {mdl:<55}  in={entry.input_per_million:>7.3f}/M "
                  f"out={entry.output_per_million:>7.3f}/M")
        return 0

    if args.cmd == "set":
        register_price(PriceEntry(
            provider=args.provider, model=args.model,
            input_per_million=args.input_per_million,
            output_per_million=args.output_per_million,
        ))
        print("ok")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
