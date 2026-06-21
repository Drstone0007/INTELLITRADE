# Run — Start the Live Trader

Starts the Intellitrade consensus-driven trading loop.

## Voice Notification

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Run workflow in _INTELLITRADE to start live trading"}' \
  > /dev/null 2>&1 &
```

Running **Run** in **_INTELLITRADE** to start live trading...

## Prerequisites

1. Exchange API keys configured: `python intellitrade_main.py configure`
2. All dependencies installed: `pip install ccxt numpy`
3. (Optional) MiroFish available for extended model paths

## Execute

```bash
python ~/.claude/skills/_INTELLITRADE/Tools/intellitrade_main.py run
```

The trader will:
- Connect to the configured exchange
- Begin streaming 5-minute BTC candles
- Run 31 parallel prediction models on each new candle
- Count votes and check the 28/31 consensus threshold
- Execute trades via Kelly criterion when signals fire
- Save state to `~/.intellitrade/state.json`

## Stop

Press `Ctrl+C` to stop. State is saved on exit.

## Intent-to-Flag Mapping

| User Says | Flag | Effect |
|-----------|------|--------|
| (default) | (none) | Uses config values |
| "paper trade" | `--paper` | Paper trading mode |
