# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
"""
Intellitrade — Trade Execution layer.

Places orders when consensus fires. Tracks P&L, win rate, and balance.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from intellitrade_consensus import KellyCalculator


class TradeExecutor:
    def __init__(self, initial_balance: float = 10_000.0, kelly_fraction: float = 0.5):
        self.balance = initial_balance
        self.kelly_fraction = kelly_fraction
        self.position = 0.0
        self.entry_price = 0.0
        self.total_trades = 0
        self.wins = 0
        self.losses = 0
        self.trade_history: list = []

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return (self.wins / total * 100) if total > 0 else 0.0

    def execute(self, signal: str, price: float) -> Dict[str, Any]:
        if self.position != 0:
            self._close_position(price)

        if signal == "LONG":
            side = "buy"
        elif signal == "SHORT":
            side = "sell"
        else:
            return {"side": "none", "price": price, "size": 0}

        kelly = KellyCalculator.fraction(
            self.win_rate / 100 if self.total_trades > 0 else 0.5,
            avg_win=1.0,
            avg_loss=1.0,
        ) if self.total_trades > 0 else 0.5

        size = KellyCalculator.position_size(
            self.balance,
            kelly * self.kelly_fraction,
            price,
        )

        cost = size * price
        if cost > self.balance:
            size = self.balance / price
            cost = self.balance

        self.position = size if side == "buy" else -size
        self.entry_price = price

        if side == "buy":
            self.balance -= cost

        order = {
            "time": time.time(),
            "side": side,
            "price": price,
            "size": size,
            "cost": cost,
            "balance": self.balance,
        }
        self.trade_history.append(order)
        self.total_trades += 1
        return order

    def _close_position(self, price: float):
        if self.position == 0:
            return
        pnl = abs(self.position) * (price - self.entry_price)
        if self.position > 0:
            self.balance += abs(self.position) * price
        else:
            self.balance += abs(self.position) * price
        if pnl > 0:
            self.wins += 1
        else:
            self.losses += 1
        self.trade_history.append({
            "time": time.time(),
            "side": "close",
            "price": price,
            "pnl": round(pnl, 2),
            "balance": self.balance,
        })
        self.position = 0.0
