# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
import json, logging, os, threading, time, asyncio
from dataclasses import dataclass, field, asdict
from typing import Any, Callable
from urllib.request import urlopen, Request
from urllib.parse import urlencode

logger = logging.getLogger("polyarb.telegram")

CONFIG_FILE = os.path.expanduser("~/.claude/skills/_POLYARB/telegram_config.json")

@dataclass
class TelegramConfig:
    bot_token: str = ""
    chat_id: str = ""
    enabled: bool = False
    notify_arb: bool = True
    notify_copy: bool = True
    notify_errors: bool = True
    min_notify_profit_pct: float = 1.0

def load_config() -> TelegramConfig:
    if not os.path.exists(CONFIG_FILE):
        return TelegramConfig()
    with open(CONFIG_FILE) as f:
        d = json.load(f)
    return TelegramConfig(**d)

def save_config(cfg: TelegramConfig):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(asdict(cfg), f, indent=2)

def send_message(text: str) -> bool:
    cfg = load_config()
    if not cfg.enabled or not cfg.bot_token or not cfg.chat_id:
        return False
    try:
        url = f"https://api.telegram.org/bot{cfg.bot_token}/sendMessage"
        data = urlencode({"chat_id": cfg.chat_id, "text": text, "parse_mode": "Markdown"}).encode()
        req = Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
        with urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
            return resp.get("ok", False)
    except Exception as e:
        logger.warning("Telegram send failed: %s", e)
        return False

def notify_arb_opportunity(opp: dict):
    cfg = load_config()
    if not cfg.notify_arb:
        return
    profit = opp.get("profit_pct", 0)
    if profit < cfg.min_notify_profit_pct:
        return
    title = opp.get("event_title", "Unknown")
    arb_type = opp.get("arb_type", "?")
    msg = (
        f"⚡ *Arbitrage Found*\n"
        f"Type: {arb_type}\n"
        f"Market: {title}\n"
        f"Profit: {profit:.2f}%\n"
        f"Cost: ${opp.get('total_cost', 0)*100:.2f} → Payout: $100\n"
        f"Details: {opp.get('market_ids', [])}"
    )
    send_message(msg)

def notify_copy_trade(decision: dict):
    cfg = load_config()
    if not cfg.notify_copy:
        return
    wallet = decision.get("wallet", "")[:10] + "..."
    action = decision.get("action", "?")
    reason = decision.get("reason", "")
    size = decision.get("size_usd", 0)
    msg = (
        f"🔄 *Copy Trade*\n"
        f"Action: {action}\n"
        f"Wallet: {wallet}\n"
        f"Size: ${size:.2f}\n"
        f"Reason: {reason}"
    )
    send_message(msg)

def notify_error(msg_text: str):
    cfg = load_config()
    if not cfg.notify_errors:
        return
    send_message(f"⚠️ *Error*\n{msg_text}")

def notify_startup():
    send_message("🚀 *POLYARB Scanner Online*\nMonitoring markets and wallets...")

def notify_scan_summary(multi: int, pair: int, book: int, wallets: int, copies: int):
    msg = (
        f"📊 *Scan Summary*\n"
        f"Multi-outcome arb: {multi}\n"
        f"Yes/No pair arb: {pair}\n"
        f"Orderbook spreads: {book}\n"
        f"Wallets tracked: {wallets}\n"
        f"Copy trades queued: {copies}"
    )
    send_message(msg)
