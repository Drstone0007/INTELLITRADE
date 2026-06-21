# Configure — Setup Intellitrade

Configures exchange API keys, model parameters, and trading preferences.

## Voice Notification

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Configure workflow in _INTELLITRADE to set up configuration"}' \
  > /dev/null 2>&1 &
```

Running **Configure** in **_INTELLITRADE** to set up configuration...

## Execute

```bash
python ~/.claude/skills/_INTELLITRADE/Tools/intellitrade_main.py configure
```

Prompts for:
- Exchange API key & secret
- Exchange name (binance, coinbase, kraken)
- MiroFish installation path
- Model count (default 31)
- Fire threshold (default 28)
- Kill threshold (default 26)
- Kelly fraction (default 0.5)

Config saved to `~/.intellitrade/config.json`.
