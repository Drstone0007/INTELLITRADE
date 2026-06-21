# _POLYARB — Polymarket Arbitrage Scanner & Copytrader

**Private skill.** Self-learning autonomous agent that finds mispriced prediction markets on Polymarket, monitors profitable wallets, and executes copytrades.

## Architecture

```
_POLYARB/
├── SKILL.md
├── Workflows/
│   ├── Run.md        — Full scan + continuous loop + autonomous agent
│   ├── Monitor.md    — Wallet discovery & tracking
│   ├── Configure.md  — Copytrade & Telegram config
│   └── Analyze.md    — Deep wallet/market analysis
└── Tools/
    ├── polyarb_main.py       — CLI entry point (9 commands)
    ├── polyarb_api.py        — Polymarket API wrapper (Gamma, CLOB, Data)
    ├── polyarb_scanner.py    — Multi-outcome & Yes/No pair arb detection
    ├── polyarb_wallets.py    — Wallet profiling + scoring engine
    ├── polyarb_copytrade.py  — Copytrading decision engine
    ├── polyarb_telegram.py   — Telegram bot notifications
    ├── polyarb_auth.py       — CLOB L1/L2 EIP-712 authentication
    ├── polyarb_exec.py       — Order placement, cancellation, heartbeat
    ├── polyarb_portfolio.py  — Trade log, P&L tracking, daily reports
    ├── polyarb_learning.py   — Self-learning feedback loop, threshold adj
    └── polyarb_agent.py      — 24/7 state machine agent
```

## Arbitrage Types

| Type | Detection | Target |
|------|-----------|--------|
| **Multi-outcome** | Sum of all YES token prices < $1.00 | Buy all outcomes → guaranteed $1.00 payout |
| **Yes/No pair** | `P(Yes) + P(No)` deviates from $1.00 | Arbitrage the complementarity |

## Wallet Scoring

Score = `win_rate*100 + volume_score + trade_count_score + pnl_score`

Labels: **ELITE** (100+) > **PRO** (70+) > **SOLID** (40+) > **NOVICE** (20+) > **RISKY** (<20)

## Autonomous Agent

State machine: **SCAN → ANALYZE → EXECUTE → MONITOR → LEARN → SLEEP**

- Runs 24/7 with configurable interval
- Paper mode by default (no real trades)
- Live mode: `--key YOUR_PRIVATE_KEY` for CLOB auth + real order placement
- Self-learning: adjusts thresholds every 12 cycles based on P&L history
- Auto-heartbeat keeps CLOB session alive
- Telegram daily reports
- Error recovery: retries with backoff, stops after 5 consecutive failures

## CLI Commands

```bash
python polyarb_main.py scan              # Find arb opportunities
python polyarb_main.py wallets discover  # Find top wallets
python polyarb_main.py wallets add <addr> # Track a wallet
python polyarb_main.py copytrade scan    # Find trades to copy
python polyarb_main.py telegram start    # Enable notifications
python polyarb_main.py portfolio status  # P&L, win rate, trade history
python polyarb_main.py learn run         # Run self-learning feedback
python polyarb_main.py loop              # Continuous scan loop
python polyarb_main.py agent --interval 300  # Autonomous agent (paper)
python polyarb_main.py agent --key 0x...    # Autonomous agent (live)
```

## API Dependencies

- `gamma-api.polymarket.com` — Market discovery (no auth)
- `clob.polymarket.com` — Prices, orderbooks, trading (read: no auth, write: L2 auth)
- `data-api.polymarket.com` — User positions, trades, leaderboard (no auth)

## Python Dependencies

- `eth-account` — EIP-712 typed data signing for CLOB auth + order signing
- Standard library only for all other operations

## Storage

Config files at `~/.claude/skills/_POLYARB/` (gitignored):
- `telegram_config.json` — Bot token + chat ID
- `api_creds.json` — CLOB API credentials (L1 signed)
- `watched_wallets.json` — Wallet watchlist
- `copytrade_config.json` — Copytrading thresholds
- `portfolio.json` — P&L snapshot
- `trade_log.json` — Full trade history
- `signal_log.json` — Signal generation history
- `learned_thresholds.json` — Self-adjusted thresholds
- `agent_state.json` — Agent state machine
