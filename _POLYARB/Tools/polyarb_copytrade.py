# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
import json, logging, time, os
from dataclasses import dataclass, field, asdict
from typing import Any
import polyarb_api as api
from polyarb_wallets import WalletProfile, TradeEvent, analyze_wallet, get_recent_trades, load_watched_wallets

logger = logging.getLogger("polyarb.copytrade")

COPYTRADE_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/copytrade_config.json")

@dataclass
class CopytradeConfig:
    enabled: bool = False
    min_wallet_score: float = 50.0
    max_position_size_usd: float = 100.0
    per_trade_cap_usd: float = 50.0
    daily_budget_usd: float = 500.0
    min_confidence: float = 0.6
    copy_only_buys: bool = False
    copy_only_sells: bool = False
    allowed_markets: list[str] = field(default_factory=list)
    excluded_markets: list[str] = field(default_factory=list)

@dataclass
class CopyDecision:
    wallet: str
    trade: TradeEvent
    action: str  # COPY or SKIP
    reason: str
    size_usd: float = 0.0

def load_config() -> CopytradeConfig:
    if not os.path.exists(COPYTRADE_FILE):
        return CopytradeConfig()
    with open(COPYTRADE_FILE) as f:
        d = json.load(f)
    return CopytradeConfig(**d)

def save_config(cfg: CopytradeConfig):
    os.makedirs(os.path.dirname(COPYTRADE_FILE), exist_ok=True)
    with open(COPYTRADE_FILE, "w") as f:
        json.dump(asdict(cfg), f, indent=2)

def should_copy(wallet_profile: WalletProfile, trade: TradeEvent, cfg: CopytradeConfig) -> CopyDecision:
    if not cfg.enabled:
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP", reason="Copytrading disabled")
    if wallet_profile.score < cfg.min_wallet_score:
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP",
                            reason=f"Score {wallet_profile.score} < min {cfg.min_wallet_score}")
    if cfg.copy_only_buys and trade.side != "BUY":
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP", reason="Only copying buys")
    if cfg.copy_only_sells and trade.side != "SELL":
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP", reason="Only copying sells")
    if cfg.allowed_markets and trade.market_id not in cfg.allowed_markets:
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP", reason="Market not in allowed list")
    if trade.market_id in cfg.excluded_markets:
        return CopyDecision(wallet=trade.wallet, trade=trade, action="SKIP", reason="Market excluded")

    size_usd = min(trade.size * trade.price, cfg.max_position_size_usd)
    if size_usd > cfg.per_trade_cap_usd:
        size_usd = cfg.per_trade_cap_usd
    if size_usd <= 0:
        size_usd = cfg.per_trade_cap_usd

    return CopyDecision(
        wallet=trade.wallet,
        trade=trade,
        action="COPY",
        reason=f"Score {wallet_profile.score} | Win rate {wallet_profile.win_rate:.0%} | Copying ${size_usd:.2f}",
        size_usd=round(size_usd, 2),
    )

def scan_and_decide(max_wallets: int = 20, lookback_hours: int = 24) -> list[CopyDecision]:
    cfg = load_config()
    if not cfg.enabled:
        logger.info("Copytrading disabled")
        return []
    wallets = load_watched_wallets()
    if not wallets:
        logger.info("No watched wallets")
        return []
    decisions: list[CopyDecision] = []
    since = time.time() - lookback_hours * 3600
    for addr in wallets[:max_wallets]:
        try:
            profile = analyze_wallet(addr)
            trades = get_recent_trades(addr, since=since, limit=20)
            for t in trades:
                decision = should_copy(profile, t, cfg)
                if decision.action == "COPY":
                    decisions.append(decision)
        except Exception as e:
            logger.warning("Error processing wallet %s: %s", addr, e)
    decisions.sort(key=lambda d: d.trade.timestamp, reverse=True)
    return decisions
