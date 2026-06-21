# Analyze — Deep Dive

## Description
Analyze a specific wallet or market in detail.

## Usage

### Wallet Analysis
Use the Python API directly:
```python
from Tools import polyarb_wallets as w
from Tools import polyarb_api as api

# Full wallet profile
p = w.analyze_wallet("0x1234...")
print(f"Score: {p.score}, Win Rate: {p.win_rate:.0%}")
print(f"Trades: {p.total_trades}, Volume: ${p.total_volume:.0f}")
print(f"Label: {p.label}")

# Recent trades
trades = w.get_recent_trades("0x1234...", limit=20)
for t in trades:
    print(f"{t.side} {t.size}@{t.price} → ${t.size*t.price:.2f}")
```

### Market Analysis
```python
from Tools import polyarb_scanner as s
from Tools import polyarb_api as api

# Get event with all markets
events = api.get_events(limit=10)
opps = s.scan_multi_outcome_detailed(events)
for o in opps:
    print(f"{o.event_title}: {o.profit_pct:.2f}% profit")
    for label, price in zip(o.outcome_labels, o.prices):
        print(f"  {label}: ${price:.4f}")

# Check specific market
market = api.get_market_by_slug("will-bitcoin-reach-100k")
book = api.get_book(market[0].get("clobTokenId", ""))
```
