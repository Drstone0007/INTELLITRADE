# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
import json, logging, os, time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("polyarb.portfolio")

TRADE_LOG = os.path.expanduser("~/.claude/skills/_POLYARB/trade_log.json")
PORTFOLIO_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/portfolio.json")

@dataclass
class TradeRecord:
    market_id: str
    event_title: str
    side: str
    price: float
    size: float
    cost: float
    order_id: str
    timestamp: float
    arb_type: str
    pnl: float = 0.0
    status: str = "open"
    exit_price: float = 0.0
    exit_timestamp: float = 0.0
    tags: list[str] = field(default_factory=list)

@dataclass
class Portfolio:
    balance_pusd: float = 0.0
    total_invested: float = 0.0
    total_pnl: float = 0.0
    total_pnl_pct: float = 0.0
    open_trades: int = 0
    closed_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    max_drawdown: float = 0.0
    peak_balance: float = 0.0
    daily_change: float = 0.0
    last_updated: float = 0.0
    history: list[dict] = field(default_factory=list)

def load_trades() -> list[TradeRecord]:
    if not os.path.exists(TRADE_LOG):
        return []
    with open(TRADE_LOG) as f:
        return [TradeRecord(**t) for t in json.load(f)]

def save_trades(trades: list[TradeRecord]):
    os.makedirs(os.path.dirname(TRADE_LOG), exist_ok=True)
    with open(TRADE_LOG, "w") as f:
        json.dump([t.__dict__ for t in trades], f, indent=2)

def append_trade(trade: TradeRecord):
    trades = load_trades()
    trades.append(trade)
    save_trades(trades)

def close_trade(order_id: str, exit_price: float, pnl: float):
    trades = load_trades()
    for t in trades:
        if t.order_id == order_id and t.status == "open":
            t.status = "closed"
            t.exit_price = exit_price
            t.pnl = pnl
            t.exit_timestamp = time.time()
            break
    save_trades(trades)

def load_portfolio() -> Portfolio:
    if not os.path.exists(PORTFOLIO_FILE):
        return Portfolio()
    with open(PORTFOLIO_FILE) as f:
        return Portfolio(**json.load(f))

def save_portfolio(p: Portfolio):
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    with open(PORTFOLIO_FILE, "w") as f:
        json.dump(p.__dict__, f, indent=2)

def compute_portfolio(headers: dict | None = None) -> Portfolio:
    trades = load_trades()
    p = Portfolio()
    open_count = 0
    closed_count = 0
    wins = 0
    losses = 0
    total_pnl = 0.0
    total_cost = 0.0
    peak = 0.0
    for t in trades:
        cost = t.cost if t.cost > 0 else t.size * t.price
        total_cost += cost
        if t.status == "closed":
            closed_count += 1
            total_pnl += t.pnl
            if t.pnl > 0:
                wins += 1
            else:
                losses += 1
        else:
            open_count += 1
    p.open_trades = open_count
    p.closed_trades = closed_count
    p.wins = wins
    p.losses = losses
    p.win_rate = wins / max(wins + losses, 1)
    p.total_invested = round(total_cost, 2)
    p.total_pnl = round(total_pnl, 2)
    p.total_pnl_pct = round(total_pnl / max(total_cost, 1) * 100, 2) if total_cost > 0 else 0.0
    p.peak_balance = peak
    p.max_drawdown = 0.0
    p.last_updated = time.time()
    save_portfolio(p)
    return p

def daily_report() -> str:
    p = compute_portfolio()
    trades = load_trades()
    today = time.time() - 86400
    today_trades = [t for t in trades if t.timestamp > today]
    lines = [
        f"📊 *Portfolio Report*",
        f"Balance: ${p.balance_pusd:.2f}",
        f"Total P&L: ${p.total_pnl:.2f} ({p.total_pnl_pct:.1f}%)",
        f"Win Rate: {p.win_rate:.0%} ({p.wins}W / {p.losses}L)",
        f"Open Trades: {p.open_trades}",
        f"Today's Trades: {len(today_trades)}",
    ]
    return "\n".join(lines)
