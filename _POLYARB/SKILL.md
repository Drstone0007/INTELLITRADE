# _POLYARB — Polymarket Arbitrage Scanner & Copytrader

**Private skill.** AI agent that finds mispriced prediction markets on Polymarket, monitors profitable wallets, and executes copytrades via Telegram.

## Architecture

```
_POLYARB/
├── SKILL.md
├── Workflows/
│   ├── Run.md        — Full scan + continuous loop
│   ├── Monitor.md    — Wallet discovery & tracking
│   ├── Configure.md  — Copytrade & Telegram config
│   └── Analyze.md    — Deep wallet/market analysis
└── Tools/
    ├── polyarb_main.py       — CLI entry point (4 commands)
    ├── polyarb_api.py        — Polymarket API wrapper
    ├── polyarb_scanner.py    — 3 arbitrage detection engines
    ├── polyarb_wallets.py    — Wallet profiling + scoring
    ├── polyarb_copytrade.py  — Copytrading decision engine
    └── polyarb_telegram.py   — Telegram bot notifications
```

## Arbitrage Types

| Type | Detection | Target |
|------|-----------|--------|
| **Multi-outcome** | Sum of all YES token prices < $1.00 | Buy all outcomes → guaranteed $1.00 payout |
| **Yes/No pair** | `P(Yes) + P(No)` deviates from $1.00 | Arbitrage the complementarity |
| **Orderbook spread** | Wide bid/ask on single token | Capture spread with limit orders |

## Wallet Scoring

Score = `win_rate*100 + volume_score + trade_count_score + pnl_score`

Labels: ELITE (100+) > PRO (70+) > SOLID (40+) > NOVICE (20+) > RISKY (<20)

## CLI Commands

```bash
python polyarb_main.py scan              # Find arb opportunities
python polyarb_main.py wallets discover  # Find top wallets
python polyarb_main.py wallets add <addr> # Track a wallet
python polyarb_main.py copytrade scan    # Find trades to copy
python polyarb_main.py telegram start    # Enable notifications
python polyarb_main.py loop --interval 300  # Continuous scan
```

## API Dependencies

- `gamma-api.polymarket.com` — Market discovery (no auth)
- `clob.polymarket.com` — Prices & orderbooks (no auth for reads)
- `data-api.polymarket.com` — User positions, trades, leaderboard (no auth)

## Storage

Config and state files stored at `~/.claude/skills/_POLYARB/`:
- `watched_wallets.json` — Wallet watchlist
- `copytrade_config.json` — Copytrading thresholds
- `telegram_config.json` — Telegram bot credentials
