from __future__ import annotations

import argparse
import json
from pathlib import Path

from .reports import create_reports
from .study import analyze, generate_returns, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare simple synthetic allocations.")
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--observations", type=int, default=252)
    parser.add_argument("--lookback", type=int, default=60)
    parser.add_argument("--max-weight", type=float, default=0.60)
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--reports", type=Path, default=Path("reports"))
    args = parser.parse_args()
    source = generate_returns(args.seed, args.observations)
    result, metrics = analyze(source, args.lookback, args.max_weight)
    args.output.mkdir(parents=True, exist_ok=True)
    write_csv(args.output / "synthetic_returns.csv", source)
    write_csv(args.output / "portfolio_returns.csv", result)
    (args.output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    create_reports(args.reports, result, metrics)
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
