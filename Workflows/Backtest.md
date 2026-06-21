# Backtest — Historical Performance Test

Runs the full 31-model consensus system on historical BTC data to evaluate performance.

## Voice Notification

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Backtest workflow in _INTELLITRADE to test historical performance"}' \
  > /dev/null 2>&1 &
```

Running **Backtest** in **_INTELLITRADE** to test historical performance...

## Execute

```bash
# 30-day default
python ~/.claude/skills/_INTELLITRADE/Tools/intellitrade_main.py backtest

# Custom period and symbol
python intellitrade_main.py backtest --symbol ETHUSDT --days 60
```

## Intent-to-Flag Mapping

| User Says | Flag | Effect |
|-----------|------|--------|
| "last 30 days" | `--days 30` | 30 days of history |
| "last 60 days" | `--days 60` | 60 days of history |
| "on ETH" | `--symbol ETHUSDT` | Test on Ethereum |
| (default) | BTCUSDT, 30 days | Standard backtest |

## Output

Results printed to console and saved to `~/.intellitrade/backtest_<symbol>_<days>d.json`:
- Total trades
- Win rate (%)
- Final balance (starting from 10,000 USDT)
- Return percentage
- Full equity curve with every candle's vote, signal, and balance
