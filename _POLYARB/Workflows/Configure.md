# Configure — Settings Management

## Description
Configure copytrading thresholds and Telegram bot integration.

## Usage

### Copytrade Settings
```bash
# View current config
python polyarb_main.py copytrade status

# Enable copytrading
python polyarb_main.py copytrade enable

# Disable copytrading
python polyarb_main.py copytrade disable

# Set thresholds
python polyarb_main.py copytrade set --min-score 60 --max-size 200 --per-trade 50

# Scan for copy trades (dry-run)
python polyarb_main.py copytrade scan --lookback 24
```

### Telegram Bot
```bash
# Set bot token and chat ID
python polyarb_main.py telegram set --bot-token "YOUR_TOKEN" --chat-id "YOUR_CHAT_ID"

# Enable notifications
python polyarb_main.py telegram enable

# Test connection
python polyarb_main.py telegram test

# Start bot (sends startup message)
python polyarb_main.py telegram start
```
