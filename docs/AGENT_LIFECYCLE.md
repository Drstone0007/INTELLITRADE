# Agent Lifecycle — The 24/7 Autonomous Trading Loop

> *"The market never sleeps. Neither does the agent."*

## Overview

The agent is a state machine that runs in an infinite loop. Each cycle is one complete pass through the decision pipeline. The default interval is 300 seconds (5 minutes), meaning the agent executes 288 cycles per day and generates a full learning + reporting cycle every ~24 hours.

---

## State Definitions

### SLEEP
The default state between cycles. The agent may be idle for seconds or hours. No network activity. Minimal CPU.

**Duration**: Configurable (default 300s). Controlled by `--interval` flag.

---

### SCAN
The agent wakes and pulls live market data from three Polymarket APIs in parallel.

**Operations**:
- `GET /events?limit=50&closed=false` — active events with markets
- `GET /v1/leaderboard?limit=50` — top traders by PnL
- `POST /heartbeat` — keep CLOB session alive (if authenticated)

**Output**: Raw market data + current portfolio state

**Error handling**: If Gamma API is down, skip scan and re-enter SLEEP. If CLOB heartbeat fails, re-authenticate on next EXECUTE cycle.

**Performance target**: < 10 seconds

---

### ANALYZE
The agent analyzes scan results against learned thresholds to generate trade signals.

**Sub-operations**:
1. **Multi-outcome arb scan**: For each event with 3+ markets, compute `sum(YES prices)` vs `min_multi_outcome_profit` threshold. Filter opportunities with confidence > 0.5.
2. **Yes/No pair scan**: For single-market events, compute `P(Yes) + P(No)` vs `min_pair_profit`.
3. **Copytrade scan**: For each watched wallet scoring ≥ `min_wallet_score`, fetch recent trades. Score each trade against position size caps and daily budget.

**Scoring**: Each signal gets a confidence score:
```
confidence = predicted_profit × signal_quality × historical_success_rate
  where:
    predicted_profit = opportunity.profit_pct / 100
    signal_quality = 0.7 (arb) or wallet_score / 100 (copytrade)
    historical_success_rate = self-learning module output for this arb_type
```

**Output**: Sorted list of trade signals (max 3 per cycle)

**Error handling**: If wallet API fails, skip copytrade analysis but still process arb signals. Partial data is better than no data.

---

### EXECUTE
The agent converts signals into orders.

**Paper mode** (no private key): Log the signal and proceed. No wallet interaction.

**Live mode** (private key provided):
1. Look up token ID for each market
2. Determine tick size and fee rate from CLOB metadata
3. Create EIP-712 signed order payload
4. POST to `/order` on CLOB API
5. Log the order ID, price, size, and timestamp to `trade_log.json`

**Position sizing**:
- Multi-outcome arb: Split `per_trade_cap_usd` evenly across all outcomes
- Yes/No pair: Buy both sides at `per_trade_cap_usd / 2` each
- Copytrade: Use the wallet's position size, capped at `per_trade_cap_usd`

**Output**: ExecutedTrade records + Telegram notification

**Error handling**: If order placement fails with 403 (auth expired), re-authenticate and retry once. If order fails with insufficient balance, skip and flag for reporting.

---

### MONITOR
Between execution cycles, the agent maintains session health and checks order status.

**Operations**:
1. Send CLOB heartbeat (prevents auto-cancellation of open orders)
2. Every 12 cycles, check open order fills via `GET /orders`
3. Update portfolio state (open/closed positions, unrealized PnL)
4. Store state snapshot to `agent_state.json`

**Heartbeat**: Polymarket auto-cancels all open orders if no heartbeat for 5+ minutes. The agent heartbeats every cycle (default 300s, well within the limit).

**Output**: Updated `agent_state.json`, updated `portfolio.json`

---

### LEARN
Every 12 cycles (~1 hour), the agent audits its own performance and adjusts decision thresholds.

**Operations**:
1. Load `signal_log.json` — all signals generated
2. Filter to executed signals with completed outcomes
3. Compute profit rate per signal type:

```
arb_type_profit_rate = profitable_signals / total_executed_signals
```

4. Apply adaptation rules:

```
if profit_rate < 0.4:
    raise min_multi_outcome_profit += 0.3
    raise min_wallet_score += 2
elif profit_rate > 0.7:
    lower min_multi_outcome_profit -= 0.2
    lower min_wallet_score -= 1
```

5. Save updated thresholds to `learned_thresholds.json`

**Output**: Updated thresholds + log of what changed and why

---

### ERROR
The agent enters ERROR state on any unhandled exception.

**Recovery**:
- Consecutive errors < 5: Log the error, notify Telegram, re-enter SLEEP, retry on next cycle
- Consecutive errors ≥ 5: Halt the agent. Send critical alert to Telegram. Exit with code 1.

**Error classification**:
| Error type | Counts as consecutive? | Recovery |
|------------|----------------------|----------|
| Network timeout | Yes | Retry with backoff |
| API 4xx | No (skip cycle) | Continue |
| API 5xx | Yes | Retry |
| Auth failure | No | Re-auth on next cycle |
| Rate limit | No (skip cycle) | Wait and retry |

---

## Performance Profile

| Metric | Value |
|--------|-------|
| Cycle time (typical) | 5-15 seconds |
| Cycle time (max) | 30 seconds (API timeout) |
| Memory usage | ~50MB |
| CPU usage | ~2% (mostly idle) |
| Network usage | ~100KB per cycle |
| Battery impact (laptop) | Negligible |
| Annual downtime (projected) | < 4 hours (0.05%) |

---

## Lifecycle Diagram

```
        ┌─────────────────────────────────────────────────────┐
        │                   24 HOURS                          │
        │                                                     │
        │   ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌──────┐   │
        │   │SCAN │  │ANLZ │  │EXEC │  │MON  │  │LEARN │   │
        │   │ 5s  │→ │ 2s  │→ │ 3s  │→ │ 1s  │→ │ 2s   │   │
        │   └─────┘  └─────┘  └─────┘  └─────┘  └──────┘   │
        │      ↑                        ↑                    │
        │      └──────── 5 min ─────────┘                    │
        │                                                     │
        │  ── 288 cycles ──────────────────────────────────► │
        │  12 learns (every 1 hr)                             │
        │  1 report (every 24 hrs)                            │
        └─────────────────────────────────────────────────────┘
```
