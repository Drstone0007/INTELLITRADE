---
name: _INTELLITRADE
description: "Consensus-driven BTC trading system — feeds 5-min candles into 31 parallel MiroFish-style prediction paths, executes only when 28/31 models agree. Kelly criterion position sizing. USE WHEN btc trade, crypto trading, consensus trading, intellitrade, mirofish trade, 31 models, parallel prediction, trading agent, automated trading, kelly criterion. NOT FOR stock trading (use a stock-specific strategy), manual trading signals, or backtesting only without live execution."
---

# _INTELLITRADE

Consensus-driven BTC trading agent. Runs 31 parallel prediction paths on 5-minute candles. Trades fire only when 28/31 models agree. Below 26 votes the trade dies instantly. Position sizing via Kelly criterion.

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:31337/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running WORKFLOWNAME in _INTELLITRADE"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running **WorkflowName** in **_INTELLITRADE**...
   ```

**Full documentation:** `~/.claude/PAI/DOCUMENTATION/Notifications/NotificationSystem.md`

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Run** | "run trader", "start trading", "intellitrade run" | `Workflows/Run.md` |
| **Monitor** | "check status", "monitor trades", "show pnl", "intellitrade status" | `Workflows/Monitor.md` |
| **Configure** | "configure", "setup", "set api key", "intellitrade config" | `Workflows/Configure.md` |
| **Backtest** | "backtest", "test strategy", "historical test", "intellitrade backtest" | `Workflows/Backtest.md` |

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Intellitrade Orchestrator               │
├─────────────────────────────────────────────────────────┤
│   Data Layer  │  Model Layer  │  Consensus  │ Execution │
├───────────────┼──────────────┼─────────────┼───────────┤
│ Binance/CCXT  │ Model 1..31  │ Vote Engine │ Order Mgr │
│ 5-min candles │              │ 28/31 thresh│ Kelly     │
│ OHLCV streams │ parallel     │ 26 kill     │ Slippage  │
└───────────────┴──────────────┴─────────────┴───────────┘
```

### Core Principle

Not prediction. **Consensus.** Each model independently predicts direction (long/short/flat). Only when 28+ of 31 converge does a signal fire. Below 26 votes the signal dies instantly. Most days the system stays flat.

### Key Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Candle interval | 5 min | Captures micro-structure noise without overfitting |
| Model count | 31 | Prime number prevents vote-splitting artifacts |
| Fire threshold | 28/31 | ~90% consensus — extreme selectivity |
| Kill threshold | ≤26/31 | Instant signal death, no second-guessing |
| Position sizing | Kelly criterion | Optimal growth over time |
| Max positions | 1 at a time | Single concentrated bets only |

## Examples

**Example 1: Run the live trader**
```
User: "Start Intellitrade"
→ Invokes Run workflow
→ Connects to exchange, begins 5-min candle loop
→ Runs 31 models in parallel on each candle
→ Outputs: signals, P&L, current positions
```

**Example 2: Check trading status**
```
User: "How is Intellitrade doing?"
→ Invokes Monitor workflow
→ Shows: current signal, open positions, daily P&L, model vote breakdown
```

**Example 3: Backtest on historical data**
```
User: "Backtest Intellitrade on last 30 days of BTC data"
→ Invokes Backtest workflow
→ Downloads 30 days of 5-min candles
→ Runs full simulation
→ Outputs: equity curve, win rate, max drawdown, Sharpe ratio
```

## Gotchas

- MiroFish is a social simulation platform, not a crypto trading simulator. This system implements the parallel-prediction pattern independently.
- The 31 models use different parameterizations of the same underlying indicators — diversity comes from parameter spread, not fundamentally different model architectures.
- API keys are stored in `~/.intellitrade/config.json` — never hardcode them.
- Exchange rate limits must be respected. The data fetcher uses adaptive throttling.
- Kelly criterion can suggest very large positions during high-conviction periods — use a fractional Kelly (0.25-0.5) in production.
- The system has no opinion on most candles — expect 80%+ flat time.
- Backtest results are NOT guaranteed to predict live performance. Market regimes shift.

---

*INTELLITRADE — DrTelemon Elite Tech Conglomerate*
*Engineering the asymmetric edge. Systems over outcomes. Mathematics over emotion.*
*Proprietary. Unauthorized distribution is a violation of intellectual property.*
