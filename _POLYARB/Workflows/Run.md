# Run — Full Scan & Loop

## Description
Execute a full arbitrage scan across all Polymarket market types, or run the continuous monitoring loop.

## Usage
```bash
# One-shot scan (all arb types)
python polyarb_main.py scan

# Continuous loop (default 300s interval)
python polyarb_main.py loop --interval 300

# Scan with tighter thresholds
python polyarb_main.py scan --min-multi 1.0 --min-pair 0.5 --min-spread 2.0
```

## Output
- `multi_outcome` — 3+ outcome events where sum(YES prices) < $1.00
- `yes_no_pair` — Binary markets where bid+ask complementarity is broken
- `orderbook` — Wide bid/ask spreads on individual tokens
- Real-time Telegram notifications if configured
