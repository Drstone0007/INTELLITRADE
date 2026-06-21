"""
Intellitrade — 31 parallel prediction models.

Each model independently predicts direction (LONG/SHORT/FLAT).
Models use different technical indicators, timeframes, and parameterizations
to create genuine diversity. The consensus across all 31 is the edge.
"""

import math
import random
from typing import Any, Dict, List, Tuple


def _compute_rsi(closes: List[float], period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = [closes[i] - closes[i - 1] for i in range(-period, 0)]
    gains = sum(d for d in deltas if d > 0) / period
    losses = sum(-d for d in deltas if d < 0) / period
    if losses == 0:
        return 100.0
    rs = gains / losses
    return 100.0 - (100.0 / (1.0 + rs))


def _compute_ema(closes: List[float], period: int) -> float:
    if len(closes) < period:
        return closes[-1]
    multiplier = 2.0 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]:
        ema = (price - ema) * multiplier + ema
    return ema


def _compute_macd(closes: List[float]) -> Tuple[float, float]:
    fast = _compute_ema(closes, 12)
    slow = _compute_ema(closes, 26)
    macd_line = fast - slow
    signal = _compute_ema([macd_line] * 5 + [macd_line], 9) if len(closes) < 35 else _compute_ema(closes[-35:], 9)
    return macd_line, signal


def _compute_bb_position(highs: List[float], lows: List[float], closes: List[float], period: int = 20) -> float:
    if len(closes) < period:
        return 0.5
    sma = sum(closes[-period:]) / period
    variance = sum((c - sma) ** 2 for c in closes[-period:]) / period
    std = math.sqrt(variance)
    upper = sma + 2 * std
    lower = sma - 2 * std
    if upper == lower:
        return 0.5
    return (closes[-1] - lower) / (upper - lower)


def _compute_atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(highs) < 2:
        return 0.0
    trs = []
    for i in range(-period, 0):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        trs.append(max(hl, hc, lc))
    return sum(trs) / len(trs)


def _compute_volume_trend(volumes: List[float], period: int = 5) -> float:
    if len(volumes) < period + 1:
        return 0.0
    recent = sum(volumes[-period:]) / period
    prior = sum(volumes[-(period * 2):-period]) / period
    return (recent - prior) / prior if prior > 0 else 0.0


def _compute_obv(closes: List[float], volumes: List[float]) -> float:
    obv = 0.0
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv += volumes[i]
        elif closes[i] < closes[i - 1]:
            obv -= volumes[i]
    return obv


def _direction(raw: float, threshold: float = 0.0) -> str:
    if raw > threshold:
        return "LONG"
    elif raw < -threshold:
        return "SHORT"
    return "FLAT"


def _noise() -> float:
    return random.uniform(-0.5, 0.5)


def _stochastic(highs: List[float], lows: List[float], closes: List[float], k_period: int = 14):
    if len(closes) < k_period:
        return 50.0
    hh = max(highs[-k_period:])
    ll = min(lows[-k_period:])
    if hh == ll:
        return 50.0
    return (closes[-1] - ll) / (hh - ll) * 100


# --- 31 Model Definitions ---

MODELS: List[Dict[str, Any]] = [
    # RSI-based models with varying periods
    {"name": "RSI_14", "desc": "RSI(14) mean reversion", "periods": [14]},
    {"name": "RSI_7", "desc": "RSI(7) faster mean reversion", "periods": [7]},
    {"name": "RSI_21", "desc": "RSI(21) slower mean reversion", "periods": [21]},
    {"name": "RSI_30", "desc": "RSI(30) trend filter", "periods": [30]},

    # MACD variants
    {"name": "MACD_std", "desc": "MACD(12,26,9) standard", "periods": [12, 26, 9]},
    {"name": "MACD_fast", "desc": "MACD(6,13,5) fast", "periods": [6, 13, 5]},
    {"name": "MACD_slow", "desc": "MACD(21,55,13) slow", "periods": [21, 55, 13]},

    # Bollinger Band position
    {"name": "BB_20", "desc": "BB(20) position mean reversion", "periods": [20]},
    {"name": "BB_10", "desc": "BB(10) short-term squeeze", "periods": [10]},
    {"name": "BB_50", "desc": "BB(50) wide channels", "periods": [50]},

    # Moving average crossovers
    {"name": "MA_9_21", "desc": "MA(9) x MA(21) fast cross", "periods": [9, 21]},
    {"name": "MA_21_55", "desc": "MA(21) x MA(55) med cross", "periods": [21, 55]},
    {"name": "MA_50_200", "desc": "MA(50) x MA(200) slow cross", "periods": [50, 200]},

    # Stochastic oscillators
    {"name": "STOCH_14", "desc": "Stochastic(14) fast", "periods": [14]},
    {"name": "STOCH_7", "desc": "Stochastic(7) very fast", "periods": [7]},
    {"name": "STOCH_21", "desc": "Stochastic(21) slow", "periods": [21]},

    # Volume-based
    {"name": "VOL_ratio", "desc": "Volume ratio surge detection", "periods": [5]},
    {"name": "VOL_OBV", "desc": "On-balance volume trend", "periods": [0]},

    # ATR/volatility
    {"name": "ATR_14", "desc": "ATR(14) volatility breakout", "periods": [14]},
    {"name": "ATR_7", "desc": "ATR(7) short vol breakout", "periods": [7]},

    # Price action
    {"name": "PA_engulf", "desc": "Engulfing pattern detector", "periods": [2]},
    {"name": "PA_wick", "desc": "Wick ratio rejection", "periods": [3]},
    {"name": "PA_momentum", "desc": "Momentum(5) continuation", "periods": [5]},
    {"name": "PA_momentum_10", "desc": "Momentum(10) swing", "periods": [10]},

    # Support/resistance
    {"name": "SR_swing", "desc": "Swing low/high bounce", "periods": [10]},
    {"name": "SR_range", "desc": "Range-bound mean reversion", "periods": [20]},

    # Combined / composite
    {"name": "COMBO_1", "desc": "RSI+BB+MACD composite A", "periods": [14, 20, 12]},
    {"name": "COMBO_2", "desc": "RSI+BB+MACD composite B", "periods": [7, 10, 6]},
    {"name": "COMBO_3", "desc": "RSI+BB+MACD composite C", "periods": [21, 50, 21]},

    # Statistical
    {"name": "STAT_zscore", "desc": "Z-score deviation from mean", "periods": [20]},
    {"name": "STAT_skew", "desc": "Short-term skew detector", "periods": [5]},
]


def predict(model_index: int, candles: List[Dict[str, Any]]) -> str:
    """Run a single prediction model on a candle window. Returns LONG/SHORT/FLAT."""
    model = MODELS[model_index]
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    name = model["name"]
    n = _noise()

    if name == "RSI_14":
        rsi = _compute_rsi(closes, 14) + n
        return _direction(50 - rsi, 10)
    elif name == "RSI_7":
        rsi = _compute_rsi(closes, 7) + n
        return _direction(50 - rsi, 8)
    elif name == "RSI_21":
        rsi = _compute_rsi(closes, 21) + n
        return _direction(50 - rsi, 12)
    elif name == "RSI_30":
        rsi = _compute_rsi(closes, 30) + n
        return _direction(50 - rsi, 15)

    elif name == "MACD_std":
        macd, signal = _compute_macd(closes)
        return _direction(macd - signal, 0.5)
    elif name == "MACD_fast":
        macd, signal = _compute_macd(closes[-30:])
        return _direction(macd - signal, 0.3)
    elif name == "MACD_slow":
        macd, signal = _compute_macd(closes)
        return _direction(macd - signal, 1.0)

    elif name in ("BB_20", "BB_10", "BB_50"):
        period = model["periods"][0]
        pos = _compute_bb_position(highs, lows, closes, period)
        if pos < 0.15:
            return "LONG"
        elif pos > 0.85:
            return "SHORT"
        return "FLAT"

    elif name == "MA_9_21":
        fast = _compute_ema(closes, 9)
        slow = _compute_ema(closes, 21)
        return _direction(fast - slow, 0.1)
    elif name == "MA_21_55":
        fast = _compute_ema(closes, 21)
        slow = _compute_ema(closes, 55)
        return _direction(fast - slow, 0.15)
    elif name == "MA_50_200":
        fast = _compute_ema(closes, 50)
        slow = _compute_ema(closes, 200) if len(closes) >= 200 else _compute_ema(closes, min(100, len(closes)))
        return _direction(fast - slow, 0.2)

    elif name in ("STOCH_14", "STOCH_7", "STOCH_21"):
        period = model["periods"][0]
        k = _stochastic(highs, lows, closes, period) + n
        if k < 20:
            return "LONG"
        elif k > 80:
            return "SHORT"
        return "FLAT"

    elif name == "VOL_ratio":
        vt = _compute_volume_trend(volumes)
        if vt > 0.5:
            return "LONG" if closes[-1] > closes[-2] else "SHORT"
        return "FLAT"
    elif name == "VOL_OBV":
        obv = _compute_obv(closes, volumes)
        return _direction(obv, 0)

    elif name in ("ATR_14", "ATR_7"):
        period = model["periods"][0]
        atr = _compute_atr(highs, lows, closes, period)
        avg_atr = atr / closes[-1]
        if avg_atr > 0.02:
            return _direction(closes[-1] - closes[-2], 0.0)
        return "FLAT"

    elif name == "PA_engulf":
        o = [c["open"] for c in candles]
        if len(closes) < 3:
            return "FLAT"
        if closes[-1] > o[-1] and closes[-2] < o[-2]:
            return "LONG"
        if closes[-1] < o[-1] and closes[-2] > o[-2]:
            return "SHORT"
        return "FLAT"
    elif name == "PA_wick":
        body = abs(closes[-1] - opens[-1])
        upper = highs[-1] - max(closes[-1], opens[-1])
        lower = min(closes[-1], opens[-1]) - lows[-1]
        if body > 0 and upper / body > 2:
            return "SHORT"
        if body > 0 and lower / body > 2:
            return "LONG"
        return "FLAT"
    elif name == "PA_momentum":
        mom = closes[-1] - closes[-5]
        return _direction(mom, 0.1)
    elif name == "PA_momentum_10":
        mom = closes[-1] - closes[-10]
        return _direction(mom, 0.2)

    elif name == "SR_swing":
        low_range = sum(lows[-10:]) / 10
        high_range = sum(highs[-10:]) / 10
        if closes[-1] <= low_range * 1.01:
            return "LONG"
        elif closes[-1] >= high_range * 0.99:
            return "SHORT"
        return "FLAT"
    elif name == "SR_range":
        highest = max(highs[-20:])
        lowest = min(lows[-20:])
        pos = (closes[-1] - lowest) / (highest - lowest) if highest != lowest else 0.5
        if pos < 0.2:
            return "LONG"
        elif pos > 0.8:
            return "SHORT"
        return "FLAT"

    elif name in ("COMBO_1", "COMBO_2", "COMBO_3"):
        rsi_p, bb_p, _ = model["periods"]
        rsi = _compute_rsi(closes, rsi_p)
        bb_pos = _compute_bb_position(highs, lows, closes, bb_p)
        macd, signal = _compute_macd(closes)
        score = 0
        if rsi < 40:
            score += 1
        elif rsi > 60:
            score -= 1
        if bb_pos < 0.25:
            score += 1
        elif bb_pos > 0.75:
            score -= 1
        if macd > signal:
            score += 1
        elif macd < signal:
            score -= 1
        if score >= 2:
            return "LONG"
        elif score <= -2:
            return "SHORT"
        return "FLAT"

    elif name == "STAT_zscore":
        mean = sum(closes[-20:]) / 20
        std = math.sqrt(sum((c - mean) ** 2 for c in closes[-20:]) / 20)
        if std == 0:
            return "FLAT"
        z = (closes[-1] - mean) / std
        if z < -2:
            return "LONG"
        elif z > 2:
            return "SHORT"
        return "FLAT"
    elif name == "STAT_skew":
        returns = [(closes[i] - closes[i - 1]) / closes[i - 1] for i in range(-5, 0)]
        mean_r = sum(returns) / len(returns)
        variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
        if variance == 0:
            return "FLAT"
        skew = sum((r - mean_r) ** 3 for r in returns) / (len(returns) * variance ** 1.5)
        if skew < -0.5:
            return "LONG"
        elif skew > 0.5:
            return "SHORT"
        return "FLAT"

    _opens = [c["open"] for c in candles]
    return "FLAT"


def run_model_batch(candles: List[Dict[str, Any]], model_count: int = 31) -> List[Dict[str, str]]:
    """Run all models on a candle window and return predictions."""
    results = []
    for i in range(min(model_count, len(MODELS))):
        try:
            direction = predict(i, candles)
            results.append({"model": MODELS[i]["name"], "prediction": direction})
        except Exception as e:
            results.append({"model": MODELS[i]["name"], "prediction": "FLAT", "error": str(e)})
    return results
