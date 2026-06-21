# Architecture Blueprint — INTELLITRADE

```
INTELLITRADE/
├── _INTELLITRADE/          # BTC consensus trading engine
│   ├── Tools/
│   │   ├── intellitrade_main.py       # CLI: run, monitor, backtest, configure
│   │   ├── intellitrade_models.py     # 31 prediction models (RSI, MACD, BB, MA, Stoch, Volume, ATR, PA, SR, Composite, Statistical)
│   │   ├── intellitrade_consensus.py  # Vote counter, 28/31 fire, 26/31 kill, Kelly sizing
│   │   ├── intellitrade_data.py       # Market data fetcher (CCXT)
│   │   └── intellitrade_exec.py       # Order execution
│   ├── Workflows/                     # Run, Monitor, Backtest, Configure
│   └── SKILL.md
│
├── _POLYARB/               # Polymarket arbitrage + copytrade engine
│   ├── Tools/
│   │   ├── polyarb_main.py           # CLI: 9 commands
│   │   ├── polyarb_api.py            # Polymarket API wrapper (Gamma, CLOB, Data)
│   │   ├── polyarb_scanner.py        # Multi-outcome & Yes/No pair arb detection
│   │   ├── polyarb_wallets.py        # Wallet profiling + scoring
│   │   ├── polyarb_copytrade.py      # Copytrading decision engine
│   │   ├── polyarb_telegram.py       # Telegram bot
│   │   ├── polyarb_auth.py           # CLOB L1/L2 EIP-712 auth
│   │   ├── polyarb_exec.py           # Order placement, heartbeat, management
│   │   ├── polyarb_portfolio.py      # P&L tracking, trade log, reports
│   │   ├── polyarb_learning.py       # Self-learning feedback loop
│   │   └── polyarb_agent.py          # 24/7 state machine
│   ├── Workflows/                     # Run, Monitor, Configure, Analyze
│   └── SKILL.md
│
└── docs/                              # This directory
    ├── BLUEPRINT_INTELLITRADE.md
    ├── BLUEPRINT_POLYARB.md
    ├── AGENT_LIFECYCLE.md
    └── DEPLOYMENT.md
```

## Communication Layer

```
┌─────────────────────────────────────────────────────────┐
│                    Telegram Bot                          │
│              @intellitadebot                             │
│         Notifications + Daily Reports                    │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│                    Agent (state machine)                 │
│         SCAN → ANALYZE → EXECUTE → MONITOR → LEARN       │
└────┬────────────┬──────────────┬───────────────────────┘
     │            │              │
┌────▼────┐ ┌────▼────┐   ┌────▼────────────┐
│ Gamma   │ │ CLOB    │   │ Data API         │
│ API     │ │ API     │   │ leaderboard/     │
│ events/ │ │ book/   │   │ positions/       │
│ markets │ │ order/  │   │ trades/activity  │
└─────────┘ └────┬────┘   └─────────────────┘
                 │
          ┌──────▼──────┐
          │ Polygon      │
          │ Blockchain   │
          │ (settlement) │
          └─────────────┘
```

## Data Flow

1. **Discovery**: Gamma API → events, markets, outcome prices
2. **Detection**: Scanner compares `sum(YES prices)` vs $1.00 threshold
3. **Valuation**: Self-learning module checks historical success of similar signals
4. **Authorization**: Auth module signs EIP-712 typed data with wallet private key
5. **Execution**: CLOB API places limit/market orders, relayer handles gasless settlement
6. **Monitoring**: Heartbeat every cycle, order status checks, position tracking
7. **Learning**: Every 12 cycles, the agent audits its P&L and adjusts thresholds
8. **Notification**: Telegram bot sends real-time updates on every state change

## Security Boundaries

| Layer | Risk | Mitigation |
|-------|------|------------|
| Private key | Full account access | Stored locally only, never transmitted |
| API credentials | Order placement | L2 scoped, rotating |
| Bot token | Telegram spam | Chat-ID scoped |
| Config files | Wallet addresses | Gitignored, local only |
