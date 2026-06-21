# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
import json, logging, time, os
from dataclasses import dataclass, field, asdict
from typing import Any
import polyarb_api as api

logger = logging.getLogger("polyarb.wallets")

WATCHED_WALLETS_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/watched_wallets.json")

@dataclass
class WalletProfile:
    address: str
    total_pnl: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    avg_position_size: float = 0.0
    total_volume: float = 0.0
    favorite_markets: list[str] = field(default_factory=list)
    last_active: float = 0.0
    score: float = 0.0
    label: str = ""

@dataclass
class TradeEvent:
    wallet: str
    market_id: str
    side: str
    price: float
    size: float
    timestamp: float
    outcome: str = ""
    pnl: float = 0.0

def load_watched_wallets() -> list[str]:
    if not os.path.exists(WATCHED_WALLETS_FILE):
        return []
    with open(WATCHED_WALLETS_FILE) as f:
        return json.load(f)

def save_watched_wallets(wallets: list[str]):
    os.makedirs(os.path.dirname(WATCHED_WALLETS_FILE), exist_ok=True)
    with open(WATCHED_WALLETS_FILE, "w") as f:
        json.dump(list(set(wallets)), f, indent=2)

def add_wallet(address: str):
    wallets = load_watched_wallets()
    if address not in wallets:
        wallets.append(address)
        save_watched_wallets(wallets)
        logger.info("Added wallet %s", address)

def remove_wallet(address: str):
    wallets = load_watched_wallets()
    if address in wallets:
        wallets.remove(address)
        save_watched_wallets(wallets)
        logger.info("Removed wallet %s", address)

def score_wallet(profile: WalletProfile) -> float:
    win_score = profile.win_rate * 100  # 0-100
    volume_score = min(profile.total_volume / 1000, 50)
    trade_count_score = min(profile.total_trades / 10, 30)
    pnl_score = max(min(profile.total_pnl / 100, 20), -20)
    s = win_score + volume_score + trade_count_score + pnl_score
    profile.score = round(s, 2)
    if s >= 100:
        profile.label = "ELITE"
    elif s >= 70:
        profile.label = "PRO"
    elif s >= 40:
        profile.label = "SOLID"
    elif s >= 20:
        profile.label = "NOVICE"
    else:
        profile.label = "RISKY"
    return s

def analyze_wallet(address: str, max_trades: int = 100) -> WalletProfile:
    profile = WalletProfile(address=address)
    try:
        pos = api.get_user_positions(address)
        value_data = api.get_user_value(address)
        trades = api.get_user_trades(address, limit=max_trades)
    except Exception as e:
        logger.warning("Failed to fetch data for %s: %s", address, e)
        return profile
    if isinstance(value_data, dict):
        profile.total_pnl = float(value_data.get("unrealizedPnl", 0)) + float(value_data.get("realizedPnl", 0))
    wins = 0
    losses = 0
    total_size = 0.0
    volume = 0.0
    for t in trades:
        side = t.get("side", "")
        size = abs(float(t.get("size", 0)))
        price = float(t.get("price", 0))
        total_size += size
        volume += size * price
        if side == "SELL":
            wins += 1
        elif side == "BUY":
            losses += 1
        if t.get("outcome"):
            if t["outcome"] == "YES":
                wins += 1
    profile.total_trades = len(trades)
    profile.wins = wins
    profile.losses = losses
    profile.win_rate = wins / max(wins + losses, 1)
    profile.total_volume = round(volume, 2)
    profile.avg_position_size = round(total_size / max(len(trades), 1), 4)
    if trades:
        profile.last_active = trades[0].get("timestamp", 0) if isinstance(trades[0], dict) else 0
    else:
        profile.last_active = 0
    score_wallet(profile)
    return profile

def discover_top_wallets(min_trades: int = 5, limit: int = 30) -> list[WalletProfile]:
    wallets = set()
    try:
        for entry in api.get_leaderboard(limit=50):
            addr = entry.get("proxyWallet", "") or entry.get("address", "")
            if addr:
                wallets.add(addr)
    except Exception as e:
        logger.warning("Leaderboard fetch failed: %s", e)
    profiles: list[WalletProfile] = []
    for addr in list(wallets)[:limit]:
        try:
            p = analyze_wallet(addr)
            if p.total_trades >= min_trades and p.total_volume > 0:
                profiles.append(p)
        except Exception as e:
            logger.warning("Skipping %s: %s", addr, e)
    profiles.sort(key=lambda p: p.score, reverse=True)
    return profiles

def get_recent_trades(address: str, since: float = 0, limit: int = 50) -> list[TradeEvent]:
    events: list[TradeEvent] = []
    try:
        raw = api.get_user_trades(address, limit=limit)
    except Exception:
        return events
    for t in raw:
        ts = float(t.get("timestamp", 0))
        if ts < since:
            continue
        events.append(TradeEvent(
            wallet=address,
            market_id=str(t.get("market", "")),
            side=t.get("side", "BUY"),
            price=float(t.get("price", 0)),
            size=float(t.get("size", 0)),
            timestamp=ts,
            outcome=t.get("outcome", ""),
            pnl=float(t.get("pnl", 0)),
        ))
    events.sort(key=lambda e: e.timestamp, reverse=True)
    return events
