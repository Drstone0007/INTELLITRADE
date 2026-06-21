# Blueprint: `_POLYARB` — Polymarket Arbitrage & Copytrade Engine

> *"Every prediction market has a price. Every price is wrong. Find the ones where the error is profitable."*

## Strategic Overview

**Mission**: Continuously extract risk-free returns from mispriced prediction markets on Polymarket by exploiting the mathematical inevitability that related outcome prices must sum to $1.00.

**Edge**: Polymarket is a decentralized exchange. Decentralized means slow, fragmented, and inefficient. The CLOB (Central Limit Order Book) doesn't auto-arbitrage multi-outcome events. Most traders are retail, emotional, and wrong. The agent moves faster, coldly, and never sleeps.

**Arbitrage Thesis**: For any event with N mutually exclusive outcomes, `sum(YES price for all outcomes) = $1.00` at all times in an efficient market. Any deviation is free money. Deviations exist because markets are not efficient — Polymarket confirms this daily.

---

## Arbitrage Strategies

### Strategy 1: Multi-Outcome Arbitrage (Primary)

**Detection**: Scan all events with 3+ markets. Compute `sum(YES prices)`. If `< $1.00`, opportunity exists.

**Execution**: Buy all outcomes simultaneously at market prices. Hold until resolution. Collect $1.00 per complete set.

**Example** (live from scan, Jun 2026):
```
Event: Ukraine election called by...?
  Outcome A: 0.011  (1.1%)
  Outcome B: 0.180  (18.0%)
  Outcome C: 0.075  (7.5%)
  ─────────────────────────
  Total:     0.266  (26.6%)
  Profit:    276.65% ← $0.266 → $1.00
```

**Risk**: Zero, if you hold to resolution. Every outcome set pays exactly $1.00 when resolved. The only risks are (1) the platform fails (exchange risk), and (2) the market never resolves (governance risk — mitigated by checking `endDate`).

**Optimal Execution**: The profit is locked at purchase time. Speed matters more than price improvement — the arb disappears as soon as arbitrageurs compete. Place market orders across all legs simultaneously.

---

### Strategy 2: Yes/No Pair Arbitrage (Secondary)

**Detection**: For binary markets, `P(Yes) + P(No)` should approximately equal $1.00. When `ask(Yes) + ask(No) < $1.00 - fees`, buy both.

**Execution**: Buy Yes and No simultaneously. The market pays $1.00 regardless of outcome.

**Profit Cap**: Typically 0.3-1.5%. These arbs are smaller and faster — tight spreads get arbed within seconds. Best for high-capacity automated execution.

---

### Strategy 3: Wallet Copytrading (Growth)

**Detection**: Track the 50 highest-scoring wallets on Polymarket. Score by:
- Win rate (PnL-positive trades / total trades)
- Total volume (capital deployment = conviction)
- Recency (last active within 7 days)
- Consistency (low variance in position sizing)

**Execution**: When an ELITE or PRO wallet enters a position, mirror it at a configurable fraction.

**Risk**: Copytrading carries execution risk — the wallet gets filled at their price, you get filled at yours, and slippage eats the edge. Mitigated by:
- Only copying wallets with score > 70
- Limiting to markets with tight spreads (< 2%)
- Capping per-trade exposure at $50

---

## The Self-Learning Loop

Every trade generates data. The learning module consumes it.

```
Trade → Record Signal → Wait for Resolution → Compute P&L → Analyze → Adjust Thresholds
```

### Threshold Adaptation Rules

| Condition | Action |
|-----------|--------|
| Win rate < 40% over last 20 trades | Raise `min_multi_outcome_profit` by 0.3%, raise `min_wallet_score` by 2 |
| Win rate > 70% over last 20 trades | Lower `min_multi_outcome_profit` by 0.2%, lower `min_wallet_score` by 1 |
| Specific arb type < 30% win rate | Flag for manual review, reduce allocation to 0 |
| Specific wallet consistently profitable | Increase copy allocation up to 2x default |

The agent doesn't need retraining. It adjusts its own decision boundaries in real time based on what's working and what isn't.

---

## Agent State Machine

```
          ┌──────────┐
          │  SLEEP   │ ◄────────────────────────────┐
          └────┬─────┘                              │
               │ interval expires                    │
               ▼                                    │
          ┌──────────┐                              │
          │  SCAN    │── error ──► ┌───────┐        │
          └────┬─────┘            │ ERROR │        │
               │ data             └───┬───┘        │
               ▼                     │             │
          ┌──────────┐               │ < 5 errors  │
          │ ANALYZE  │───────────────┘             │
          └────┬─────┘                             │
               │ signals found                     │
               ▼                                   │
          ┌──────────┐                             │
          │ EXECUTE  │                             │
          └────┬─────┘                             │
               │                                   │
               ▼                                   │
          ┌──────────┐                             │
          │ MONITOR  │                             │
          └────┬─────┘                             │
               │ every 12 cycles                   │
               ▼                                   │
          ┌──────────┐                             │
          │  LEARN   │─────────────────────────────┘
          └──────────┘
```

---

## CLOB Authentication Flow

Polymarket requires EIP-712 typed data signatures for API access. The flow:

```
┌────────┐     ┌─────────┐     ┌───────────┐
│ Wallet │────►│ L1 Auth │────►│ L2 Session │
│ (PK)   │     │ (create │     │ (auth for  │
│        │     │  API    │     │  requests) │
│        │     │  creds) │     │           │
└────────┘     └─────────┘     └─────┬─────┘
                                     │
          ┌──────────────────────────┤
          │              │           │
          ▼              ▼           ▼
    ┌──────────┐  ┌──────────┐  ┌────────┐
    │ Place    │  │ Cancel   │  │ Heart- │
    │ Order    │  │ Order    │  │ beat   │
    └──────────┘  └──────────┘  └────────┘
```

**Step 1**: Sign `{"action": "create_api_key", "timestamp": now}` with the wallet → POST to `/auth` → receive API key, secret, passphrase.

**Step 2**: Sign `{"action": "authentication", "apiKey": key, "timestamp": now}` → receive session. Attach `POLY_API_KEY`, `POLY_SIGNATURE`, `POLY_TIMESTAMP`, `POLY_PASSPHRASE` headers to all subsequent requests.

**Step 3**: Orders are EIP-712 signed with the Order type. The signature proves authorization without exposing the private key to Polymarket's servers.

All signing happens locally. The private key never leaves the machine.

---

## Wallet Scoring Matrix

```
Score = (win_rate × 100) + min(volume / 1000, 50) + min(trades / 10, 30) + max(min(PnL / 100, 20), -20)

Score Range    Label    Description
─────────────────────────────────────────────────
100+           ELITE    Top-tier consistent winner
70-99          PRO      Strong track record
40-69          SOLID    Decent performer
20-39          NOVICE   Early stage / low volume
< 20           RISKY    Unproven or negative P&L
```

Only wallets scoring PRO or above trigger copytrade signals. The threshold auto-adjusts — if PRO copytrades lose money, the agent raises the floor to 75+, effectively only copying ELITE wallets.

---

## Telegram Communication Protocol

The bot sends structured messages for every event:

| Event | Format | Frequency |
|-------|--------|-----------|
| Scan complete | 📊 Scan summary | Every cycle |
| Arbitrage found | ⚡ Arb detail | Per opportunity |
| Copy trade queued | 🔄 Copy signal | Per decision |
| Trade executed | ✅ Execution | Per order |
| Error | ⚠️ Error detail | Per failure |
| Daily report | 📊 P&L summary | Every 288 cycles |

Messages are Markdown-formatted. The bot token and chat ID are stored locally in `telegram_config.json` (gitignored).

---

---

*INTELLITRADE — DrTelemon Elite Tech Conglomerate*
*Engineering the asymmetric edge. Systems over outcomes. Mathematics over emotion.*
