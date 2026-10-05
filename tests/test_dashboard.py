import pytest

from conftest import FakeFmp, sign_in
from markethub import dashboard


def doc(**kw):
    return {"positions": kw.get("positions", []), "watchlist": kw.get("watchlist", [])}


def test_values_gains_and_weights():
    d = dashboard.build(doc(positions=[{"ticker": "AAPL", "shares": 10, "avg_cost": 150.0},
                                       {"ticker": "MSFT", "shares": 5, "avg_cost": 500.0}]), FakeFmp())
    t = d["totals"]
    assert t["value"] == pytest.approx(10 * 200 + 5 * 400)
    assert t["cost"] == pytest.approx(1500 + 2500)
    assert t["pnl"] == pytest.approx(0.0)
    aapl = next(p for p in d["positions"] if p["ticker"] == "AAPL")
    assert aapl["pnl"] == pytest.approx(500) and aapl["pnl_pct"] == pytest.approx(1 / 3)
    assert sum(p["weight"] for p in d["positions"]) == pytest.approx(1.0)
    assert d["sectors"][0]["sector"] == "Technology" and d["sectors"][0]["weight"] == pytest.approx(1.0)
    # Day change: AAPL +1% of 2000 (20) and MSFT +1% of price per share (the fake's change) = 20 + 20.
    assert t["day_change"] == pytest.approx(10 * 2.0 + 5 * 4.0)


def test_positions_without_cost_are_left_out_of_gains():
    d = dashboard.build(doc(positions=[{"ticker": "AAPL", "shares": 10, "avg_cost": 100.0},
                                       {"ticker": "KO", "shares": 10, "avg_cost": None}]), FakeFmp())
    t = d["totals"]
    assert t["value"] == pytest.approx(2000 + 600)
    assert t["cost"] == pytest.approx(1000)
    assert t["pnl"] == pytest.approx(1000)  # KO has no cost, so it is not in the gain
    assert t["cost_covers"] == 1


def test_history_of_current_holdings_is_rebased():
    d = dashboard.build(doc(positions=[{"ticker": "AAPL", "shares": 1, "avg_cost": 1.0}]), FakeFmp())
    h = d["history"]
    assert h["dates"] and h["portfolio_rebased"][0] == 100.0 and h["benchmark_rebased"][0] == 100.0
    assert len(h["value"]) == len(h["dates"]) == len(h["benchmark_rebased"])


def test_watchlist_only():
    d = dashboard.build(doc(watchlist=["NVDA", "KO", "NOPE"]), FakeFmp())
    assert d["totals"]["value"] is None and d["positions"] == []
    nvda = d["watchlist"][0]
    assert nvda["price"] == 120.0 and nvda["from_high_52w"] == pytest.approx(1 / 1.1 - 1)
    assert len(nvda["spark"]) == dashboard.SPARK_SESSIONS
    assert any("NOPE" in n for n in d["notes"])
    assert "MSFT" not in d["movers"]["down"]


def test_dashboard_endpoint(client):
    sign_in(client)
    client.put("/api/portfolio", json={"positions": [{"ticker": "AAPL", "shares": 3, "avg_cost": 100}], "watchlist": ["MSFT"]})
    d = client.get("/api/dashboard").json()
    assert d["totals"]["value"] == pytest.approx(600)
    assert d["movers"]["down"] == ["MSFT"] and d["movers"]["up"] == ["AAPL"]
