"""The dashboard: the user's positions valued at today's prices, and their favourites.

Descriptive only: values, gains and losses against the user's own average cost, day moves and
past returns. Nothing here suggests what to buy or sell.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from .config import BENCHMARK
from .market import Fmp, MarketUnavailable

SPARK_SESSIONS = 63  # three months


def _ret(closes: list[float], sessions: int) -> float | None:
    if len(closes) <= sessions or not closes[-1 - sessions]:
        return None
    return closes[-1] / closes[-1 - sessions] - 1


def _since(bars: list[dict], days: int) -> float | None:
    """Return from the last close on or before ``days`` ago."""
    if not bars:
        return None
    cutoff = (date.fromisoformat(bars[-1]["date"]) - timedelta(days=days)).isoformat()
    before = [b for b in bars if b["date"] <= cutoff]
    if not before or not before[-1]["close"]:
        return None
    return bars[-1]["close"] / before[-1]["close"] - 1


def _ytd(bars: list[dict]) -> float | None:
    if not bars:
        return None
    year = bars[-1]["date"][:4]
    before = [b for b in bars if b["date"][:4] < year]
    return bars[-1]["close"] / before[-1]["close"] - 1 if before and before[-1]["close"] else None


def _facts(bars: list[dict]) -> dict:
    closes = [b["close"] for b in bars]
    return {
        "return_1m": _since(bars, 30),
        "return_3m": _since(bars, 91),
        "return_ytd": _ytd(bars),
        "return_1y": _since(bars, 365),
        "spark": [round(c, 4) for c in closes[-SPARK_SESSIONS:]],
    }


def holdings_history(positions: list[dict], histories: dict[str, list[dict]], bench: list[dict],
                     days: int = 365) -> dict:
    """Daily value of the current holdings over the last year, on the dates every holding and
    the benchmark have a close, and both rebased to 100. This is what today's portfolio would
    have done, not the user's real past performance: trades are not recorded."""
    tickers = [p["ticker"] for p in positions if histories.get(p["ticker"])]
    if not tickers or not bench:
        return {"dates": [], "value": [], "portfolio_rebased": [], "benchmark_rebased": []}
    cutoff = (date.fromisoformat(bench[-1]["date"]) - timedelta(days=days)).isoformat()
    by = {t: {b["date"]: b["close"] for b in histories[t]} for t in tickers}
    bench_by = {b["date"]: b["close"] for b in bench}
    dates = sorted(d for d in bench_by if d >= cutoff and all(d in by[t] for t in tickers))
    if not dates:
        return {"dates": [], "value": [], "portfolio_rebased": [], "benchmark_rebased": []}
    shares = {p["ticker"]: p["shares"] for p in positions}
    value = [sum(shares[t] * by[t][d] for t in tickers) for d in dates]
    return {
        "dates": dates,
        "value": [round(v, 2) for v in value],
        "portfolio_rebased": [round(v / value[0] * 100, 2) for v in value],
        "benchmark_rebased": [round(bench_by[d] / bench_by[dates[0]] * 100, 2) for d in dates],
        "benchmark": BENCHMARK,
    }


def build(doc: dict, market: Fmp) -> dict:
    positions = doc.get("positions", [])
    watchlist = doc.get("watchlist", [])
    held = [p["ticker"] for p in positions]
    tickers = list(dict.fromkeys(held + watchlist + [BENCHMARK]))
    notes: list[str] = []

    quotes = market.quotes(tickers) if tickers else {}

    def history(t: str) -> list[dict]:
        try:
            return market.history(t)
        except MarketUnavailable:
            return []

    def profile(t: str) -> dict:
        try:
            return market.profile(t)
        except MarketUnavailable:
            return {}

    with ThreadPoolExecutor(max_workers=8) as pool:
        histories = dict(zip(tickers, pool.map(history, tickers)))
        profiles = dict(zip(held, pool.map(profile, held)))

    rows = []
    for p in positions:
        q = quotes.get(p["ticker"], {})
        price = q.get("price")
        value = price * p["shares"] if price is not None else None
        cost = p["avg_cost"] * p["shares"] if p.get("avg_cost") is not None else None
        prof = profiles.get(p["ticker"], {})
        rows.append({
            "ticker": p["ticker"],
            "name": q.get("name") or prof.get("name") or p["ticker"],
            "sector": ("ETF / fund" if prof.get("is_etf") else prof.get("sector")) or "Other",
            "shares": p["shares"],
            "avg_cost": p.get("avg_cost"),
            "price": price,
            "value": value,
            "cost": cost,
            "pnl": value - cost if value is not None and cost is not None else None,
            "pnl_pct": value / cost - 1 if value is not None and cost else None,
            "day_change": q["change"] * p["shares"] if q.get("change") is not None else None,
            "day_change_pct": q.get("change_pct") / 100 if q.get("change_pct") is not None else None,
            **_facts(histories.get(p["ticker"], [])),
        })
        if price is None:
            notes.append(f"No price for {p['ticker']} right now.")

    total_value = sum(r["value"] for r in rows if r["value"] is not None)
    for r in rows:
        r["weight"] = r["value"] / total_value if r["value"] is not None and total_value else None
    with_cost = [r for r in rows if r["cost"] is not None and r["value"] is not None]
    total_cost = sum(r["cost"] for r in with_cost)
    day = sum(r["day_change"] for r in rows if r["day_change"] is not None)
    sectors: dict[str, float] = {}
    for r in rows:
        if r["value"] is not None:
            sectors[r["sector"]] = sectors.get(r["sector"], 0.0) + r["value"]

    watch = []
    for t in watchlist:
        q = quotes.get(t, {})
        bars = histories.get(t, [])
        high, price = q.get("year_high"), q.get("price")
        watch.append({
            "ticker": t,
            "name": q.get("name") or t,
            "price": price,
            "day_change_pct": q.get("change_pct") / 100 if q.get("change_pct") is not None else None,
            "from_high_52w": price / high - 1 if price is not None and high else None,
            "year_low": q.get("year_low"), "year_high": high,
            **_facts(bars),
        })
        if price is None:
            notes.append(f"No price for {t} right now.")

    movers = sorted((x for x in rows + watch if x.get("day_change_pct") is not None),
                    key=lambda x: x["day_change_pct"])
    bench_q = quotes.get(BENCHMARK, {})
    return {
        "totals": {
            "value": total_value if rows else None,
            "cost": total_cost if with_cost else None,
            "pnl": total_value_with_cost(with_cost) - total_cost if with_cost else None,
            "pnl_pct": (total_value_with_cost(with_cost) / total_cost - 1) if with_cost and total_cost else None,
            "day_change": day if rows else None,
            "day_change_pct": day / (total_value - day) if rows and total_value - day else None,
            "positions": len(rows),
            "cost_covers": len(with_cost),
        },
        "positions": sorted(rows, key=lambda r: -(r["value"] or 0)),
        "sectors": sorted(({"sector": k, "value": v, "weight": v / total_value} for k, v in sectors.items()),
                          key=lambda s: -s["value"]) if total_value else [],
        "history": holdings_history(positions, histories, histories.get(BENCHMARK, [])),
        "watchlist": watch,
        "movers": {"up": [m["ticker"] for m in reversed(movers[-3:]) if m["day_change_pct"] > 0],
                   "down": [m["ticker"] for m in movers[:3] if m["day_change_pct"] < 0]},
        "benchmark": {"ticker": BENCHMARK, "price": bench_q.get("price"),
                      "day_change_pct": bench_q.get("change_pct") / 100 if bench_q.get("change_pct") is not None else None,
                      **_facts(histories.get(BENCHMARK, []))},
        "notes": notes,
    }


def total_value_with_cost(rows: list[dict]) -> float:
    """Value of the positions that have an average cost, so gains compare like with like."""
    return sum(r["value"] for r in rows)
