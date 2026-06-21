# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
import json, time, logging
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import HTTPError

logger = logging.getLogger("polyarb.api")

GAMMA_BASE = "https://gamma-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
DATA_BASE = "https://data-api.polymarket.com/v1"

def _fetch(url: str, retries: int = 3) -> Any:
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": "polyarb/1.0", "Accept": "application/json"})
            with urlopen(req, timeout=15) as r:
                return json.loads(r.read().decode())
        except HTTPError as e:
            if e.code == 429 and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise

# ── Gamma API ──────────────────────────────────────────────

def get_events(limit: int = 100, closed: bool = False, tag: str | None = None) -> list[dict]:
    params = f"limit={limit}&closed={str(closed).lower()}"
    if tag:
        params += f"&tag={tag}"
    return _fetch(f"{GAMMA_BASE}/events?{params}")

def get_event(event_id: int) -> dict:
    return _fetch(f"{GAMMA_BASE}/events/{event_id}")

def get_event_by_slug(slug: str) -> list[dict]:
    return _fetch(f"{GAMMA_BASE}/events?slug={slug}")

def get_markets(limit: int = 100, closed: bool = False, tag: str | None = None) -> list[dict]:
    params = f"limit={limit}&closed={str(closed).lower()}"
    if tag:
        params += f"&tag={tag}"
    return _fetch(f"{GAMMA_BASE}/markets?{params}")

def get_market(market_id: str) -> dict:
    return _fetch(f"{GAMMA_BASE}/markets/{market_id}")

def get_market_by_slug(slug: str) -> list[dict]:
    return _fetch(f"{GAMMA_BASE}/markets?slug={slug}")

def get_market_by_token(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/market?token_id={token_id}")

# ── CLOB API ───────────────────────────────────────────────

def get_book(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/book?token_id={token_id}")

def get_price(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/price?token_id={token_id}")

def get_prices(token_ids: list[str]) -> dict:
    ids = ",".join(token_ids)
    return _fetch(f"{CLOB_BASE}/prices?token_ids={ids}")

def get_midpoint(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/midpoint?token_id={token_id}")

def get_spread(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/spread?token_id={token_id}")

def get_last_trade_price(token_id: str) -> dict:
    return _fetch(f"{CLOB_BASE}/last-trade-price?token_id={token_id}")

# ── Data API ───────────────────────────────────────────────

def get_user_positions(user: str) -> list[dict]:
    return _fetch(f"{DATA_BASE}/positions?user={user}")

def get_user_closed_positions(user: str) -> list[dict]:
    return _fetch(f"{DATA_BASE}/closed-positions?user={user}")

def get_user_activity(user: str, limit: int = 100) -> list[dict]:
    return _fetch(f"{DATA_BASE}/activity?user={user}&limit={limit}")

def get_user_trades(user: str, limit: int = 50) -> list[dict]:
    return _fetch(f"{DATA_BASE}/trades?user={user}&limit={limit}")

def get_user_value(user: str) -> dict:
    return _fetch(f"{DATA_BASE}/value?user={user}")

def get_leaderboard(limit: int = 50) -> list[dict]:
    return _fetch(f"{DATA_BASE}/leaderboard?limit={limit}")

def get_holders(market_id: str, limit: int = 50) -> list[dict]:
    return _fetch(f"{DATA_BASE}/holders?id={market_id}&limit={limit}")

def get_trades(market_id: str | None = None, limit: int = 100) -> list[dict]:
    if market_id:
        return _fetch(f"{DATA_BASE}/trades?market={market_id}&limit={limit}")
    return _fetch(f"{DATA_BASE}/trades?limit={limit}")

def get_open_interest() -> list[dict]:
    return _fetch(f"{DATA_BASE}/oi")
