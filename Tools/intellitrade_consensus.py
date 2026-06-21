# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
"""
Intellitrade — Consensus Engine.

Counts votes from 31 parallel models, decides when to fire.
28/31 to fire. 26/31 to kill. Kelly criterion for position sizing.
"""

import math
from typing import Any, Dict, List


class ConsensusEngine:
    def __init__(self, fire_threshold: int = 28, kill_threshold: int = 26, total_models: int = 31):
        if fire_threshold <= kill_threshold:
            raise ValueError("fire_threshold must be > kill_threshold")
        self.fire_threshold = fire_threshold
        self.kill_threshold = kill_threshold
        self.total_models = total_models
        self.last_breakdown: Dict[str, int] = {}

    def count_votes(self, predictions: List[Dict[str, str]]) -> Dict[str, int]:
        vote = {"LONG": 0, "SHORT": 0, "FLAT": 0}
        for p in predictions:
            d = p.get("prediction", "FLAT")
            vote[d] = vote.get(d, 0) + 1
        self.last_breakdown = vote
        return vote

    def decide(self, vote: Dict[str, int]) -> str:
        total_voted = vote.get("LONG", 0) + vote.get("SHORT", 0)
        long_votes = vote.get("LONG", 0)
        short_votes = vote.get("SHORT", 0)

        if total_voted < self.kill_threshold:
            return "FLAT"

        if long_votes >= self.fire_threshold:
            return "LONG"
        elif short_votes >= self.fire_threshold:
            return "SHORT"

        return "FLAT"

    def confidence(self, vote: Dict[str, int]) -> float:
        long_votes = vote.get("LONG", 0)
        short_votes = vote.get("SHORT", 0)
        top = max(long_votes, short_votes)
        if top == 0:
            return 0.0
        return top / self.total_models


class KellyCalculator:
    @staticmethod
    def fraction(win_rate: float, avg_win: float, avg_loss: float) -> float:
        if avg_loss <= 0:
            return 0.0
        b = avg_win / avg_loss
        p = win_rate
        q = 1.0 - p
        if b <= 0:
            return 0.0
        kelly = (b * p - q) / b
        return max(0.0, min(kelly, 1.0))

    @staticmethod
    def position_size(balance: float, kelly_frac: float, price: float, max_risk_pct: float = 0.02) -> float:
        risk_cap = balance * max_risk_pct
        kelly_cap = balance * kelly_frac
        size = min(kelly_cap, risk_cap) / price
        return round(size, 6)
