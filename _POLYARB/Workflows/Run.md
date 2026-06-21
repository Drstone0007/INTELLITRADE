# Run — Full Scan, Loop & Autonomous Agent

## Description
Execute arbitrage scans, monitoring loops, or deploy the full autonomous 24/7 agent.

## Usage

### One-shot scan
```bash
python polyarb_main.py scan --max-events 50
```

### Continuous scan loop
```bash
python polyarb_main.py loop --interval 300
```

### Autonomous agent (paper mode — no real trades)
```bash
python polyarb_main.py agent --interval 300
```

### Autonomous agent (live — requires Polygon private key)
```bash
python polyarb_main.py agent --key YOUR_PRIVATE_KEY
```

## Agent Lifecycle
SCAN → ANALYZE → EXECUTE → MONITOR → LEARN → SLEEP → repeat

- **SCAN**: Fetches events, detects multi-outcome and Yes/No pair arb
- **ANALYZE**: Scores signals against learned thresholds, checks copytrade signals
- **EXECUTE**: Places orders on CLOB (paper or live), logs trades
- **MONITOR**: Heartbeat, order fills, error recovery
- **LEARN**: Every 12 cycles — backtests historical P&L, adjusts thresholds
- **SLEEP**: Configurable interval (default 300s)

## Learning
The agent tightens thresholds when win rate < 40% and relaxes when > 70%.

## Output
- `multi_outcome` — 3+ outcome events where sum(YES prices) < $1.00
- `yes_no_pair` — Binary markets where bid+ask complementarity is broken
- `copy_trade` — Signals from profitable wallet copytrading
- Real-time Telegram notifications
