# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
import json, logging, time
from dataclasses import dataclass, field
from typing import Any
import polyarb_api as api

logger = logging.getLogger("polyarb.scanner")

@dataclass
class ArbOpportunity:
    arb_type: str
    event_id: int | None
    event_title: str
    market_ids: list[str]
    outcome_labels: list[str]
    prices: list[float]
    total_cost: float
    payout: float
    profit_pct: float
    profit_abs: float
    details: dict = field(default_factory=dict)

@dataclass
class WalletSignal:
    wallet: str
    market_id: str
    side: str
    price: float
    size: float
    confidence: float
    reason: str

def scan_multi_outcome_events(events: list[dict]) -> list[ArbOpportunity]:
    opps: list[ArbOpportunity] = []
    for ev in events:
        markets = ev.get("markets", [])
        if len(markets) < 3:
            continue
        yes_prices: list[float] = []
        labels: list[str] = []
        mids: list[str] = []
        for m in markets:
            try:
                op = json.loads(m.get("outcomePrices", "[0, 0]"))
                yes_p = float(op[0])
            except (json.JSONDecodeError, IndexError, TypeError, ValueError):
                continue
            if yes_p <= 0.001 or yes_p >= 0.999:
                continue
            yes_prices.append(yes_p)
            outcomes = json.loads(m.get("outcomes", '["Yes","No"]'))
            labels.append(outcomes[0] if outcomes else "?")
            mids.append(str(m.get("id", "")))
        if len(yes_prices) < 3:
            continue
        total_cost = sum(yes_prices)
        payout = 1.0
        profit = (payout - total_cost) / total_cost * 100 if total_cost > 0 else 0
        profit_abs = payout - total_cost
        if profit > 0:
            opps.append(ArbOpportunity(
                arb_type="multi_outcome",
                event_id=ev.get("id"),
                event_title=ev.get("title", "Untitled"),
                market_ids=mids,
                outcome_labels=labels,
                prices=yes_prices,
                total_cost=round(total_cost, 4),
                payout=payout,
                profit_pct=round(profit, 4),
                profit_abs=round(profit_abs, 6),
                details={"num_outcomes": len(yes_prices),
                         "closed": ev.get("closed", False)},
            ))
    opps.sort(key=lambda o: o.profit_pct, reverse=True)
    return opps

def scan_yes_no_pair(events: list[dict]) -> list[ArbOpportunity]:
    opps: list[ArbOpportunity] = []
    for ev in events:
        markets = ev.get("markets", [])
        if len(markets) != 1:
            continue
        m = markets[0]
        try:
            op = json.loads(m.get("outcomePrices", "[0.5, 0.5]"))
            yes_p = float(op[0])
            no_p = float(op[1])
        except (json.JSONDecodeError, IndexError, TypeError, ValueError):
            continue
        total_cost = yes_p + no_p
        profit = (1.0 - total_cost) / total_cost * 100 if total_cost > 0 else 0
        profit_abs = 1.0 - total_cost
        if profit > 0.1:
            opps.append(ArbOpportunity(
                arb_type="yes_no_pair",
                event_id=ev.get("id"),
                event_title=ev.get("title", "Untitled"),
                market_ids=[str(m.get("id", ""))],
                outcome_labels=["Yes", "No"],
                prices=[yes_p, no_p],
                total_cost=round(total_cost, 4),
                payout=1.0,
                profit_pct=round(profit, 4),
                profit_abs=round(profit_abs, 6),
                details={"enableOrderBook": m.get("enableOrderBook")},
            ))
    opps.sort(key=lambda o: o.profit_pct, reverse=True)
    return opps

def full_scan(max_events: int = 50) -> dict[str, list[ArbOpportunity]]:
    result: dict[str, list[ArbOpportunity]] = {}
    events = api.get_events(limit=max_events, closed=False)
    result["multi_outcome"] = scan_multi_outcome_events(events)
    result["yes_no_pair"] = scan_yes_no_pair(events)
    result["orderbook"] = []
    return result
