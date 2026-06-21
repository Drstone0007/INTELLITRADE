# Monitor — Wallet & Market Watch

## Description
Discover, analyze, and track profitable Polymarket wallets. Score them by win rate, volume, and P&L.

## Usage
```bash
# Discover top wallets on Polymarket
python polyarb_main.py wallets discover --min-trades 5 --limit 30

# Add a wallet to watchlist
python polyarb_main.py wallets add 0x1234...

# List watched wallets with scores
python polyarb_main.py wallets list

# Remove a wallet
python polyarb_main.py wallets remove 0x1234...
```

## Scoring Labels
| Score Range | Label  | Description              |
|-------------|--------|--------------------------|
| 100+        | ELITE  | Top-tier consistent winner |
| 70-99       | PRO    | Strong track record      |
| 40-69       | SOLID  | Decent performer         |
| 20-39       | NOVICE | Early stage / low volume |
| <20         | RISKY  | Unproven or negative P&L |
