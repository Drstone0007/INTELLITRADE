import json, logging, os, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("polyarb.learning")

SIGNAL_LOG = os.path.expanduser("~/.claude/skills/_POLYARB/signal_log.json")
THRESHOLDS_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/learned_thresholds.json")

@dataclass
class SignalRecord:
    signal_id: str
    arb_type: str
    event_title: str
    market_id: str
    predicted_profit_pct: float
    actual_pnl: float = 0.0
    executed: bool = False
    profitable: bool = False
    timestamp: float = 0.0
    completed_at: float = 0.0

@dataclass
class LearnedThresholds:
    min_multi_outcome_profit: float = 0.5
    min_pair_profit: float = 0.3
    min_wallet_score: float = 50.0
    max_position_size: float = 100.0
    arbitrage_confidence: float = 0.7
    wallet_copy_confidence: float = 0.6
    signals_generated: int = 0
    signals_executed: int = 0
    profitable_signals: int = 0
    last_updated: float = 0.0

def load_signal_log() -> list[SignalRecord]:
    if not os.path.exists(SIGNAL_LOG):
        return []
    with open(SIGNAL_LOG) as f:
        return [SignalRecord(**s) for s in json.load(f)]

def save_signal_log(records: list[SignalRecord]):
    os.makedirs(os.path.dirname(SIGNAL_LOG), exist_ok=True)
    with open(SIGNAL_LOG, "w") as f:
        json.dump([r.__dict__ for r in records], f, indent=2)

def log_signal(sig: SignalRecord):
    records = load_signal_log()
    records.append(sig)
    save_signal_log(records)

def mark_executed(signal_id: str, pnl: float = 0.0):
    records = load_signal_log()
    for r in records:
        if r.signal_id == signal_id:
            r.executed = True
            r.actual_pnl = pnl
            r.profitable = pnl > 0
            r.completed_at = time.time()
            break
    save_signal_log(records)

def load_thresholds() -> LearnedThresholds:
    if not os.path.exists(THRESHOLDS_FILE):
        return LearnedThresholds()
    with open(THRESHOLDS_FILE) as f:
        return LearnedThresholds(**json.load(f))

def save_thresholds(t: LearnedThresholds):
    t.last_updated = time.time()
    os.makedirs(os.path.dirname(THRESHOLDS_FILE), exist_ok=True)
    with open(THRESHOLDS_FILE, "w") as f:
        json.dump(t.__dict__, f, indent=2)

def learn_from_history():
    signals = load_signal_log()
    thresholds = load_thresholds()
    executed = [s for s in signals if s.executed]
    profitable = [s for s in executed if s.profitable]
    thresholds.signals_generated = len(signals)
    thresholds.signals_executed = len(executed)
    thresholds.profitable_signals = len(profitable)
    if not executed:
        save_thresholds(thresholds)
        return thresholds
    profit_rate = len(profitable) / max(len(executed), 1)
    if profit_rate < 0.4 and thresholds.min_multi_outcome_profit < 5.0:
        thresholds.min_multi_outcome_profit = round(thresholds.min_multi_outcome_profit + 0.3, 2)
        thresholds.min_wallet_score = round(thresholds.min_wallet_score + 2.0, 1)
        logger.info("LEARN: Raising thresholds (profit rate %.0f%% < 40%%), multi now %.1f%%",
                     profit_rate * 100, thresholds.min_multi_outcome_profit)
    elif profit_rate > 0.7 and thresholds.min_multi_outcome_profit > 0.3:
        thresholds.min_multi_outcome_profit = round(thresholds.min_multi_outcome_profit - 0.2, 2)
        thresholds.min_wallet_score = round(thresholds.min_wallet_score - 1.0, 1)
        logger.info("LEARN: Lowering thresholds (profit rate %.0f%% > 70%%), multi now %.1f%%",
                     profit_rate * 100, thresholds.min_multi_outcome_profit)
    profitable_by_type: dict[str, int] = defaultdict(int)
    total_by_type: dict[str, int] = defaultdict(int)
    for s in executed:
        total_by_type[s.arb_type] += 1
        if s.profitable:
            profitable_by_type[s.arb_type] += 1
    for arb_type in total_by_type:
        rate = profitable_by_type.get(arb_type, 0) / total_by_type[arb_type]
        logger.info("LEARN: %s — %d/%d profitable (%.0f%%), adjust=%s",
                     arb_type, profitable_by_type.get(arb_type, 0), total_by_type[arb_type],
                     rate * 100, "KEEP" if rate > 0.5 else "WATCH")
    save_thresholds(thresholds)
    return thresholds

def get_adjusted_thresholds() -> dict:
    t = load_thresholds()
    return t.__dict__

def wallet_confidence(wallet_score: float, copy_history: list[dict]) -> float:
    if not copy_history:
        return min(wallet_score / 100, 0.5)
    wins = sum(1 for c in copy_history if c.get("profitable", False))
    total = len(copy_history)
    rate = wins / max(total, 1)
    return min(wallet_score / 100 * rate * 2, 0.95)
