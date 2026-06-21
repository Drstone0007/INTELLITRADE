# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
import json, logging, os, time, sys
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger("polyarb.agent")

AGENT_STATE_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/agent_state.json")

@dataclass
class AgentState:
    status: str = "IDLE"  # IDLE, SCANNING, ANALYZING, EXECUTING, MONITORING, SLEEPING, ERROR
    cycle_count: int = 0
    consecutive_errors: int = 0
    last_scan_time: float = 0
    last_execution_time: float = 0
    last_heartbeat: float = 0
    total_orders_placed: int = 0
    total_orders_filled: int = 0
    daily_orders: int = 0
    daily_pnl: float = 0.0
    errors_today: int = 0
    started_at: float = 0.0

class Agent:
    def __init__(self, private_key: str | None = None, interval: int = 300):
        self.private_key = private_key
        self.interval = interval
        self.state = self._load_state()
        self.auth_headers: dict | None = None
        self.creds = None
        self._running = True

    def _load_state(self) -> AgentState:
        if os.path.exists(AGENT_STATE_FILE):
            with open(AGENT_STATE_FILE) as f:
                return AgentState(**json.load(f))
        return AgentState(started_at=time.time())

    def _save_state(self):
        os.makedirs(os.path.dirname(AGENT_STATE_FILE), exist_ok=True)
        with open(AGENT_STATE_FILE, "w") as f:
            json.dump(self.state.__dict__, f, indent=2)

    def _transition(self, new_status: str):
        logger.info("AGENT: %s → %s", self.state.status, new_status)
        self.state.status = new_status
        self._save_state()

    def _ensure_auth(self):
        if not self.private_key:
            logger.warning("No private key configured — running in paper mode")
            return False
        if self.auth_headers:
            return True
        try:
            from polyarb_auth import ensure_auth
            self.creds, self.auth_headers = ensure_auth(self.private_key)
            logger.info("Authenticated to CLOB")
            return True
        except Exception as e:
            logger.error("Auth failed: %s", e)
            return False

    def _scan(self):
        from polyarb_scanner import full_scan
        return full_scan(max_events=50)

    def _analyze(self, scan_result: dict) -> list[dict]:
        from polyarb_learning import load_thresholds
        thresholds = load_thresholds()
        signals: list[dict] = []
        for opp in scan_result.get("multi_outcome", []):
            if opp.profit_pct >= thresholds.min_multi_outcome_profit:
                signals.append({**opp.__dict__, "confidence": 0.8, "action": "BUY_ALL"})
        for opp in scan_result.get("yes_no_pair", []):
            if opp.profit_pct >= thresholds.min_pair_profit:
                signals.append({**opp.__dict__, "confidence": 0.6, "action": "BUY_PAIR"})
        try:
            from polyarb_copytrade import scan_and_decide
            copy_decisions = scan_and_decide()
            for d in copy_decisions:
                signals.append({
                    "arb_type": "copy_trade",
                    "event_title": f"Copy {d.wallet[:12]}...",
                    "market_ids": [d.trade.market_id],
                    "prices": [d.trade.price],
                    "total_cost": d.size_usd / 100,
                    "profit_pct": 0,
                    "confidence": 0.7,
                    "action": "COPY",
                    "wallet": d.wallet,
                    "side": d.trade.side,
                    "size_usd": d.size_usd,
                })
        except Exception as e:
            logger.warning("Copy scan failed: %s", e)
        signals.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        return signals

    def _execute(self, signals: list[dict]):
        if not self.auth_headers:
            logger.info("Paper mode — would execute %d signals", len(signals))
            return
        from polyarb_exec import execute_signal, TradeSignal
        from polyarb_portfolio import TradeRecord, append_trade
        from polyarb_learning import log_signal, SignalRecord
        import uuid
        for sig in signals[:3]:
            sig_id = str(uuid.uuid4())[:12]
            market_ids = sig.get("market_ids", [])
            prices = sig.get("prices", [])
            if not market_ids or not prices:
                continue
            for mid, price in zip(market_ids, prices):
                ts = TradeSignal(
                    market_id=mid,
                    token_id="",
                    side=sig.get("side", "BUY"),
                    price=price,
                    size=sig.get("size_usd", 10) / max(price, 0.01),
                    arb_type=sig.get("arb_type", "unknown"),
                    confidence=sig.get("confidence", 0.5),
                    reason=sig.get("event_title", ""),
                )
                trade = execute_signal(ts, self.auth_headers)
                if trade:
                    self.state.total_orders_placed += 1
                    self.state.daily_orders += 1
                    append_trade(TradeRecord(
                        market_id=mid,
                        event_title=sig.get("event_title", ""),
                        side=trade.side,
                        price=trade.price,
                        size=trade.size,
                        cost=trade.price * trade.size,
                        order_id=trade.order_id,
                        timestamp=trade.timestamp,
                        arb_type=sig.get("arb_type", ""),
                    ))
                    log_signal(SignalRecord(
                        signal_id=sig_id,
                        arb_type=sig.get("arb_type", ""),
                        event_title=sig.get("event_title", ""),
                        market_id=mid,
                        predicted_profit_pct=sig.get("profit_pct", 0),
                        executed=True,
                        timestamp=time.time(),
                    ))
                    self._save_state()

    def _monitor(self):
        if not self.auth_headers:
            return
        from polyarb_exec import send_heartbeat, get_open_orders
        try:
            send_heartbeat(self.auth_headers)
            self.state.last_heartbeat = time.time()
        except Exception as e:
            logger.warning("Heartbeat failed: %s", e)
            self.auth_headers = None
            self._ensure_auth()

    def _report(self):
        from polyarb_portfolio import compute_portfolio, daily_report
        from polyarb_telegram import send_message
        try:
            p = compute_portfolio()
            report = daily_report()
            logger.info("\n" + report)
            try:
                send_message(report)
            except Exception:
                pass
        except Exception as e:
            logger.warning("Report failed: %s", e)

    def _learn(self):
        from polyarb_learning import learn_from_history
        try:
            thresholds = learn_from_history()
            logger.info("Thresholds: multi=%.1f%%, wallet_score=%.1f, exec=%d/%d prof=%.0f%%",
                         thresholds.min_multi_outcome_profit, thresholds.min_wallet_score,
                         thresholds.signals_executed, thresholds.signals_generated,
                         thresholds.profitable_signals / max(thresholds.signals_executed, 1) * 100)
        except Exception as e:
            logger.warning("Learning failed: %s", e)

    def _check_reset_daily(self):
        from datetime import datetime
        last = datetime.fromtimestamp(self.state.last_scan_time) if self.state.last_scan_time else None
        now = datetime.now()
        if last and (now.day != last.day or now.month != last.month):
            self.state.daily_orders = 0
            self.state.daily_pnl = 0.0
            self.state.errors_today = 0

    def cycle(self):
        self.state.cycle_count += 1
        self._check_reset_daily()
        try:
            self._transition("SCANNING")
            scan_result = self._scan()
            self.state.last_scan_time = time.time()
            self.state.consecutive_errors = 0

            self._transition("ANALYZING")
            signals = self._analyze(scan_result)

            if signals:
                self._transition("EXECUTING")
                self._execute(signals)
                self.state.last_execution_time = time.time()

            self._transition("MONITORING")
            self._monitor()

            if self.state.cycle_count % 12 == 0:
                self._transition("LEARNING")
                self._learn()

            if self.state.cycle_count % 288 == 0:
                self._transition("REPORTING")
                self._report()

            self._transition("SLEEPING")
        except Exception as e:
            self.state.consecutive_errors += 1
            self.state.errors_today += 1
            logger.error("Agent cycle %d failed: %s", self.state.cycle_count, e)
            from polyarb_telegram import notify_error
            try:
                notify_error(f"Cycle {self.state.cycle_count}: {e}")
            except Exception:
                pass
            self._transition("ERROR")
            if self.state.consecutive_errors >= 5:
                logger.critical("Too many consecutive errors — stopping agent")
                self._running = False

    def run(self):
        logger.info("Agent started (interval=%ds)", self.interval)
        try:
            self._ensure_auth()
        except Exception as e:
            logger.warning("Auth failed, running paper mode: %s", e)
        from polyarb_telegram import notify_startup
        try:
            notify_startup()
        except Exception:
            pass
        while self._running:
            self.cycle()
            for _ in range(int(self.interval / 5)):
                if not self._running:
                    break
                time.sleep(5)

    def stop(self):
        self._running = False
        logger.info("Agent stopping")
