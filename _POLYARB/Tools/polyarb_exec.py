import json, logging, os, time
from dataclasses import dataclass, field
from typing import Any
from urllib.request import urlopen, Request

logger = logging.getLogger("polyarb.exec")

CLOB_BASE = "https://clob.polymarket.com"

def _fetch(url: str, data: dict | None = None, headers: dict | None = None, method: str = "GET"):
    for attempt in range(3):
        try:
            body = json.dumps(data).encode() if data else None
            req = Request(url, data=body, headers={
                "User-Agent": "polyarb/1.0", "Accept": "application/json",
                "Content-Type": "application/json", **(headers or {})
            }, method=method)
            with urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt < 2:
                time.sleep(2 ** attempt)
                continue
            raise

@dataclass
class ExecutedTrade:
    market_id: str
    token_id: str
    side: str
    price: float
    size: float
    order_id: str
    status: str
    timestamp: float
    tx_hash: str = ""

@dataclass
class TradeSignal:
    market_id: str
    token_id: str
    side: str  # BUY or SELL
    price: float
    size: float
    arb_type: str
    confidence: float
    reason: str

def place_order(headers: dict, token_id: str, side: str, price: float, size: float,
                tick_size: str = "0.01", neg_risk: bool = False) -> dict:
    url = f"{CLOB_BASE}/order"
    data = {
        "token_id": token_id,
        "side": side.upper(),
        "price": str(price),
        "size": str(size),
        "tick_size": tick_size,
        "neg_risk": neg_risk,
    }
    resp = _fetch(url, data=data, headers=headers, method="POST")
    return resp

def cancel_order(headers: dict, order_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/cancel-order", data={"order_id": order_id}, headers=headers, method="POST")

def get_order_status(headers: dict, order_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/orders/{order_id}", headers=headers)

def get_open_orders(headers: dict, market_id: str = "") -> list:
    params = f"?market={market_id}" if market_id else ""
    return _fetch(f"{CLOB_BASE}/orders{params}", headers=headers)

def send_heartbeat(headers: dict) -> dict:
    return _fetch(f"{CLOB_BASE}/heartbeat", headers=headers, method="POST")

def get_market_info(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/market?token_id={token_id}")

def get_tick_size(token_id: str) -> str:
    try:
        info = get_market_info(token_id)
        return info.get("tick_size", "0.01")
    except Exception:
        return "0.01"

def get_fee_rate(token_id: str) -> float:
    try:
        info = get_market_info(token_id)
        return float(info.get("fee_rate", 0.01))
    except Exception:
        return 0.01

def execute_signal(signal: TradeSignal, headers: dict) -> ExecutedTrade | None:
    try:
        tick_size = get_tick_size(signal.token_id)
        resp = place_order(headers, signal.token_id, signal.side, signal.price, signal.size, tick_size)
        order_id = resp.get("order_id", resp.get("id", ""))
        status = resp.get("status", "unknown")
        logger.info("Order placed: %s %.4f x %.4f = ID %s [%s]",
                     signal.side, signal.price, signal.size, order_id[:12], status)
        return ExecutedTrade(
            market_id=signal.market_id,
            token_id=signal.token_id,
            side=signal.side,
            price=signal.price,
            size=signal.size,
            order_id=order_id,
            status=status,
            timestamp=time.time(),
        )
    except Exception as e:
        logger.error("Order failed for %s: %s", signal.market_id, e)
        return None

def execute_multi_outcome_arb(opportunity: dict, headers: dict, budget_per_leg: float = 10.0) -> list[ExecutedTrade]:
    trades: list[ExecutedTrade] = []
    market_ids = opportunity.get("market_ids", [])
    prices = opportunity.get("prices", [])
    if not market_ids or not prices:
        return trades
    for mid, price in zip(market_ids, prices):
        sig = TradeSignal(
            market_id=mid,
            token_id="",
            side="BUY",
            price=price,
            size=budget_per_leg / price if price > 0 else 0,
            arb_type="multi_outcome",
            confidence=0.9,
            reason=f"Multi-outcome arb: {opportunity.get('event_title','')}",
        )
        t = execute_signal(sig, headers)
        if t:
            trades.append(t)
    return trades
