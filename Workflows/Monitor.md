# Monitor — Check Trading Status

Shows current state of the Intellitrade system: signals, positions, P&L, vote breakdown.

## Voice Notification

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Monitor workflow in _INTELLITRADE to check trading status"}' \
  > /dev/null 2>&1 &
```

Running **Monitor** in **_INTELLITRADE** to check trading status...

## Execute

```bash
python ~/.claude/skills/_INTELLITRADE/Tools/intellitrade_main.py monitor
```

Output includes:
- Current status (running/stopped)
- Last candle timestamp
- Current vote count (X/31)
- Active signal (LONG/SHORT/FLAT)
- Open positions
- 24h P&L
- Total trades and win rate
- Vote breakdown across all 31 models

## State File

The trading state is persisted at `~/.intellitrade/state.json` for programmatic access.

```bash
cat ~/.intellitrade/state.json | python3 -m json.tool
```
