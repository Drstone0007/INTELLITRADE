# INTELLITRADE

**Consensus-driven autonomous trading. Two engines. One protocol.**

A 33-year-old nerd turned $1,000 into $946,207 trading Bitcoin with a trick he stole from hurricane forecasts. No finance degree. No trading desk. Just a method every meteorologist uses and every trader ignores.

This is that method, weaponized.

---

### The Insight

Meteorologists never forecast tomorrow with a single model. They run 31 and count the votes.

Financial markets are the same weather — complex, chaotic, non-deterministic. Anyone claiming a single model can predict price movement is selling certainty. Certainty is a scam. **Consensus is the only edge that matters.**

INTELLITRADE applies that exact framework across two domains:

| Engine | Target | Models | Consensus | Kill |
|--------|--------|--------|-----------|------|
| **`_INTELLITRADE`** | BTC perpetuals | 31 parallel prediction paths | 28/31 to fire | 26/31 to die |
| **`_POLYARB`** | Polymarket prediction markets | Multi-outcome arb + wallet copytrade | Adaptive (self-learning) | Auto-tighten on <40% win |

---

### The Engines

#### `_INTELLITRADE` — Bitcoin Consensus Trading

Reads every 5-minute BTC candle and feeds it into 31 parallel prediction models. Each model votes independently. Trade only fires when 28/31 agree. Below 26? Signal dies instantly.

- RSI, MACD, Bollinger, MA, Stochastic, Volume, ATR, Price Action, Support/Resistance, Composite, Statistical — 31 total
- Kelly criterion position sizing with fractional Kelly
- CCXT exchange integration for live execution
- Backtest engine with full equity curve output

#### `_POLYARB` — Polymarket Arbitrage & Copytrade

An autonomous agent that lives on Polymarket 24/7. It finds mispriced prediction markets, monitors the top wallets, learns from every trade, and adjusts its own strategy without human input.

- Multi-outcome arb: finds events where `sum(YES prices) < $1.00` and buys every outcome for guaranteed payout
- Wallet copytrade: discovers profitable wallets, scores them, copies their trades
- CLOB auth: EIP-712 signed API credentials for live order placement
- Self-learning: tracks every signal → execution → P&L, tightens thresholds when losing, relaxes when winning
- Telegram bot: real-time alerts for every scan, trade, error, and daily P&L report

---

### The Agent

```
SCAN → ANALYZE → EXECUTE → MONITOR → LEARN → SLEEP → repeat
```

Runs 24/7. Paper mode by default. Add a private key to go live.

```bash
# Paper mode — scan, analyze, decide, but don't execute
python3 _POLYARB/Tools/polyarb_main.py agent --interval 300

# Live mode — real orders on Polymarket CLOB
python3 _POLYARB/Tools/polyarb_main.py agent --key 0xYOUR_KEY
```

---

### Quick Start

```bash
# Clone
git clone https://github.com/Drstone0007/INTELLITRADE.git
cd INTELLITRADE

# BTC trading — scan only
python3 _INTELLITRADE/Tools/intellitrade_main.py run

# Polymarket arb — full scan
python3 _POLYARB/Tools/polyarb_main.py scan --max-events 50

# Polymarket wallets — discover top traders
python3 _POLYARB/Tools/polyarb_main.py wallets discover

# Deploy autonomous agent (paper)
python3 _POLYARB/Tools/polyarb_main.py agent --interval 300

# Configure Telegram
python3 _POLYARB/Tools/polyarb_main.py telegram set --bot-token "TOKEN" --chat-id "ID"
python3 _POLYARB/Tools/polyarb_main.py telegram start
```

---

### Requirements

- Python 3.11+
- `eth-account` for CLOB authentication (Polymarket engine only)
- Internet access for exchange/API connectivity
- Polygon wallet with pUSD balance (live trading only)

---

### Philosophy

Most trading systems optimize for prediction. They try to be right more often. This is a loser's game — markets are too complex for any single model to consistently outperform.

INTELLITRADE optimizes for **consensus**. Not being right, but being right *together*. The system stays flat most days. When it acts, 28 models agree to act. When it doesn't, a single dissenter kills the trade.

This is the difference between gambling and engineering.

> "It is impossible to produce superior performance unless you do something different from the majority." — John Templeton

The majority uses single models. We use 31. That's the difference.

---

**Private system.** Not for redistribution.
