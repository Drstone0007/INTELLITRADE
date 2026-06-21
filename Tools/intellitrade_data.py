# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
"""
Intellitrade — Market data layer.

Fetches BTC 5-minute candles from exchange APIs.
Supports live streaming via CCXT and historical batch downloads.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _load_exchange():
    try:
        import ccxt
    except ImportError:
        raise ImportError(
            "ccxt not installed. Install it:\n  pip install ccxt"
        )
    cfg_path = Path.home() / ".intellitrade" / "config.json"
    cfg = {}
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())

    exchange_id = cfg.get("exchange_name", "binance")
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({
        "apiKey": cfg.get("exchange_api_key", ""),
        "secret": cfg.get("exchange_secret", ""),
        "enableRateLimit": True,
        "options": {"defaultType": "spot"},
    })
    return exchange


def fetch_candles(
    symbol: str = "BTCUSDT",
    timeframe: str = "5m",
    limit: int = 500,
) -> List[Dict[str, Any]]:
    exchange = _load_exchange()
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    candles = []
    for entry in ohlcv:
        candles.append({
            "time": datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc).isoformat(),
            "timestamp": entry[0],
            "open": float(entry[1]),
            "high": float(entry[2]),
            "low": float(entry[3]),
            "close": float(entry[4]),
            "volume": float(entry[5]),
        })
    return candles


def fetch_historical_candles(
    symbol: str = "BTCUSDT",
    minutes_back: int = 43200,
    timeframe: str = "5m",
) -> List[Dict[str, Any]]:
    exchange = _load_exchange()
    limit = min(minutes_back // 5, 1000)
    since = exchange.milliseconds() - minutes_back * 60 * 1000
    all_candles = []

    while since < exchange.milliseconds():
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        if not ohlcv:
            break
        for entry in ohlcv:
            all_candles.append({
                "time": datetime.fromtimestamp(entry[0] / 1000, tz=timezone.utc).isoformat(),
                "timestamp": entry[0],
                "open": float(entry[1]),
                "high": float(entry[2]),
                "low": float(entry[3]),
                "close": float(entry[4]),
                "volume": float(entry[5]),
            })
        since = ohlcv[-1][0] + 1
        time.sleep(exchange.rateLimit / 1000)

    return all_candles


class CandleStream:
    """Live candle stream — yields new candles as they close."""

    def __init__(self, symbol: str = "BTCUSDT", interval: str = "5m"):
        self.symbol = symbol
        self.interval = interval
        self.exchange = _load_exchange()
        self._last_ts = 0

    def __iter__(self):
        return self

    def __next__(self) -> Dict[str, Any]:
        while True:
            try:
                ohlcv = self.exchange.fetch_ohlcv(
                    self.symbol, self.interval, limit=2
                )
                latest = ohlcv[-1]
                ts = latest[0]

                if ts > self._last_ts:
                    self._last_ts = ts
                    return {
                        "time": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                        "timestamp": ts,
                        "open": float(latest[1]),
                        "high": float(latest[2]),
                        "low": float(latest[3]),
                        "close": float(latest[4]),
                        "volume": float(latest[5]),
                    }

                time.sleep(10)
            except Exception as e:
                print(f"  [CandleStream] Error: {e}, retrying in 30s...")
                time.sleep(30)
