"""Compare equal-weight and capped inverse-volatility synthetic allocations."""

from __future__ import annotations

import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any


ASSETS = ("equity", "bonds", "commodities", "cash")


def generate_returns(seed: int = 19, count: int = 252) -> list[dict[str, Any]]:
    if count < 30:
        raise ValueError("count must be at least 30")
    rng = random.Random(seed)
    dates: list[date] = []
    current = date(2023, 1, 2)
    while len(dates) < count:
        if current.weekday() < 5:
            dates.append(current)
        current += timedelta(days=1)

    rows = []
    for day in dates:
        common = rng.gauss(0.0, 0.004)
        row: dict[str, Any] = {"date": day.isoformat()}
        row["equity"] = 0.00045 + common + rng.gauss(0.0, 0.012)
        row["bonds"] = 0.00012 - 0.25 * common + rng.gauss(0.0, 0.005)
        row["commodities"] = 0.00025 + 0.35 * common + rng.gauss(0.0, 0.009)
        row["cash"] = 0.00006 + rng.gauss(0.0, 0.00025)
        rows.append(row)
    return rows


def _mean(values: list[float]) -> float:
    return sum(values) / len(values)


def _volatility(values: list[float]) -> float:
    mean = _mean(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / max(1, len(values) - 1))


def _risk_statistics(values: list[float]) -> dict[str, float | None]:
    wealth = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for value in values:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        max_drawdown = max(max_drawdown, (peak - wealth) / peak)
    sorted_returns = sorted(values)
    cutoff = max(1, math.ceil(len(values) * 0.05))
    tail = sorted_returns[:cutoff]
    volatility = _volatility(values)
    downside = math.sqrt(sum(min(value, 0.0) ** 2 for value in values) / len(values))
    mean_return = _mean(values)
    years = len(values) / 252
    return {
        "total_return": wealth - 1.0,
        "annualized_geometric_return": wealth ** (1.0 / years) - 1.0 if wealth > 0 else None,
        "annualized_volatility": volatility * math.sqrt(252),
        "annualized_downside_deviation": downside * math.sqrt(252),
        "annualized_sharpe_zero_rf": (
            mean_return * 252 / (volatility * math.sqrt(252)) if volatility else None
        ),
        "maximum_drawdown": max_drawdown,
        "daily_win_rate": sum(value > 0 for value in values) / len(values),
        "best_daily_return": max(values),
        "worst_daily_return": min(values),
        "historical_var_95_daily": -sorted_returns[cutoff - 1],
        "historical_cvar_95_daily": -_mean(tail),
    }


def _capped_inverse_vol(weights_vol: list[float], cap: float) -> list[float]:
    """Allocate inverse-vol weights, redistributing any capped excess."""
    if not 0 < cap <= 1:
        raise ValueError("weight cap must be in (0, 1]")
    if cap * len(weights_vol) < 1.0:
        raise ValueError("weight cap is too small to allocate the full portfolio")
    inverse = [1.0 / value if value > 0 else 0.0 for value in weights_vol]
    if not any(inverse):
        raise ValueError("all estimated volatilities are zero")
    weights = [0.0] * len(inverse)
    remaining = set(range(len(inverse)))
    budget = 1.0
    while remaining:
        scale = budget / sum(inverse[index] for index in remaining)
        capped = [index for index in remaining if scale * inverse[index] > cap]
        if not capped:
            for index in remaining:
                weights[index] = scale * inverse[index]
            break
        for index in capped:
            weights[index] = cap
            budget -= cap
            remaining.remove(index)
        if budget <= 1e-12:
            break
    total = sum(weights)
    if total <= 0:
        raise ValueError("weight cap leaves no investable allocation")
    return [weight / total for weight in weights]


def analyze(
    rows: list[dict[str, Any]], lookback: int = 60, max_weight: float = 0.60
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if lookback < 2 or len(rows) <= lookback:
        raise ValueError("need more observations than the lookback (>= 2)")
    returns = [[float(row[asset]) for row in rows] for asset in ASSETS]
    if any(not math.isfinite(value) or value <= -1 for values in returns for value in values):
        raise ValueError("asset returns must be finite and greater than -100%")
    # Estimates use only the initial window; weights are held fixed thereafter.
    estimates = [_volatility(values[:lookback]) for values in returns]
    equal = [1.0 / len(ASSETS)] * len(ASSETS)
    inverse_vol = _capped_inverse_vol(estimates, max_weight)
    daily_rows: list[dict[str, Any]] = []
    series: dict[str, list[float]] = {"equal_weight": [], "inverse_vol": []}
    for day_index in range(lookback, len(rows)):
        daily: dict[str, Any] = {"date": rows[day_index]["date"]}
        for name, weights in (("equal_weight", equal), ("inverse_vol", inverse_vol)):
            value = sum(weights[i] * returns[i][day_index] for i in range(len(ASSETS)))
            series[name].append(value)
            daily[name] = value
        daily_rows.append(daily)

    metrics: dict[str, Any] = {
        "observations": len(rows),
        "estimation_observations": lookback,
        "max_weight": max_weight,
        "asset_estimated_annualized_volatility": {
            asset: estimates[index] * math.sqrt(252) for index, asset in enumerate(ASSETS)
        },
        "weights": {
            "equal_weight": dict(zip(ASSETS, equal)),
            "inverse_vol": dict(zip(ASSETS, inverse_vol)),
        },
        "strategies": {},
        "caveat": "Synthetic sample only; weights are fixed after an initial estimation window.",
    }
    for name, daily_returns in series.items():
        metrics["strategies"][name] = _risk_statistics(daily_returns)
    return daily_rows, metrics


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
