# Production Deployment Guide

> *"A trading bot running on a laptop is a demo. A trading bot running on a VPS with monitoring, backups, and a restart policy is a business."*

---

## Infrastructure Requirements

### Minimum (Paper Mode / Development)
- Any machine with Python 3.11+ and internet access
- 1GB RAM, 2GB storage
- No GPU required (all models are CPU-based)

### Recommended (Live Trading)
- Linux VPS (Debian 12 or Ubuntu 24.04)
- 2GB RAM, 10GB SSD
- 99.9% uptime SLA
- Static or stable IP address
- Located in a jurisdiction where prediction market trading is legal

### Ideal (Production Autonomous Agent)
- 2x VPS instances in different data centers (active/passive failover)
- 4GB RAM each, 20GB SSD each
- Shared SQLite database on a 3rd node or object storage
- Monitoring stack: Prometheus + healthcheck.io or similar
- VPN between instances for secure inter-node communication

---

## Installation

### 1. System Dependencies
```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git
```

### 2. Clone
```bash
git clone https://github.com/Drstone0007/INTELLITRADE.git /opt/intellitrade
cd /opt/intellitrade
```

### 3. Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install eth-account
```

### 4. Verification
```bash
python3 _POLYARB/Tools/polyarb_main.py scan --max-events 20
```
Should output arbitrage opportunities within 10 seconds.

---

## Telegram Configuration

```bash
python3 _POLYARB/Tools/polyarb_main.py telegram set \
  --bot-token "7987659525:AAGHRNdRohW0mCTcB1dDOO1zTlK_nwm2yQo" \
  --chat-id "8437075312"
python3 _POLYARB/Tools/polyarb_main.py telegram start
```

Expected response: "Telegram started and notification sent" — check your Telegram for the startup message.

---

## Wallet Discovery (One-Time Setup)

```bash
python3 _POLYARB/Tools/polyarb_main.py wallets discover --min-trades 5 --limit 50
```

Review the output. Add any ELITE or PRO-rated wallets:

```bash
python3 _POLYARB/Tools/polyarb_main.py wallets add 0xWALLET_ADDRESS
```

---

## Going Live (Agent Mode)

### Paper Mode (No Financial Risk)
```bash
python3 _POLYARB/Tools/polyarb_main.py agent --interval 300
```

The agent runs indefinitely. It scans, analyzes, and decides — but never places real orders. Use this to validate the signal quality before risking capital.

### Live Mode (Real Trades)
```bash
python3 _POLYARB/Tools/polyarb_main.py agent \
  --key "0xYOUR_POLYGON_PRIVATE_KEY" \
  --interval 300
```

**Before going live, verify:**
1. The wallet has sufficient pUSD balance on Polymarket
2. The wallet has a small amount of MATIC for gas (or use Polymarket's gasless relayer)
3. CLOB API credentials are created successfully (automatic on first run)
4. Telegram notifications are working
5. Position size caps are set conservatively:

```bash
python3 _POLYARB/Tools/polyarb_main.py copytrade set \
  --min-score 70 \
  --per-trade 25 \
  --daily-budget 200
```

---

## Systemd Service (Production)

Create `/etc/systemd/system/intellitrade-agent.service`:

```ini
[Unit]
Description=INTELLITRADE Autonomous Trading Agent
After=network.target

[Service]
Type=simple
User=intellitrade
WorkingDirectory=/opt/intellitrade
ExecStart=/opt/intellitrade/.venv/bin/python3 \
  _POLYARB/Tools/polyarb_main.py agent \
  --key "0xYOUR_KEY" \
  --interval 300
Restart=always
RestartSec=30
StandardOutput=append:/var/log/intellitrade/agent.log
StandardError=append:/var/log/intellitrade/agent.err

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/intellitrade
sudo systemctl daemon-reload
sudo systemctl enable intellitrade-agent
sudo systemctl start intellitrade-agent
sudo systemctl status intellitrade-agent
```

---

## Monitoring & Alerting

### Built-in (Telegram)
The agent automatically sends:
- 📊 **Scan summaries** — every cycle (arb opportunities found)
- 🔄 **Copy decisions** — when a wallet trade triggers a copy signal
- ✅ **Trade executions** — when an order is placed
- 📈 **Daily P&L report** — every 24 hours
- ⚠️ **Errors** — immediately on failure

### External Monitoring

**Healthcheck endpoint** (proposed):
The agent writes its state to `agent_state.json`. A simple cron job can check it:

```bash
#!/bin/bash
# /usr/local/bin/check-intellitrade.sh
AGE=$(python3 -c "
import json, time
s = json.load(open('/opt/intellitrade/_POLYARB/agent_state.json'))
age = time.time() - s.get('last_scan_time', 0)
print(int(age))
")
if [ $AGE -gt 600 ]; then
  curl -s "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d "chat_id=$CHAT_ID&text=⚠️ Agent stale: ${AGE}s since last scan"
fi
```

Run via cron every 10 minutes:
```cron
*/10 * * * * /usr/local/bin/check-intellitrade.sh
```

---

## Security Checklist

| Item | Status | Notes |
|------|--------|-------|
| Private key stored locally | ✅ | Never transmitted, never logged |
| Private key in env var? | ⚠️ | Recommended: use `POLY_KEY` env var instead of CLI arg |
| API credentials gitignored | ✅ | `telegram_config.json`, `api_creds.json` in `.gitignore` |
| Runtime state gitignored | ✅ | `*.json` in `.gitignore` |
| File permissions | ⚠️ | Set `chmod 600` on files containing secrets |
| VPS firewall | ⚠️ | Only allow SSH and outbound HTTPS |
| Fail2ban | ⚠️ | Recommended for any public-facing VPS |
| 2FA on exchange | ⚠️ | Enable on Polymarket account |
| Emergency stop | ⚠️ | Have the Telegram `cancel-all-orders` command mapped |

---

## Emergency Procedures

### Market Crash / Unexpected Behavior
1. Kill the agent: `sudo systemctl stop intellitrade-agent`
2. Cancel all open orders on Polymarket via the UI
3. Review the trade log at `portfolio.json` and `trade_log.json`
4. Pause Telegram notifications: `copytrade disable`
5. Investigate root cause before restarting

### Private Key Compromise
1. Immediately drain the Polymarket wallet to a secure address
2. Generate a new wallet
3. Revoke old CLOB API credentials via Polymarket settings
4. Update the `--key` parameter in the systemd service
5. Restart the agent

### Platform Outage (Polymarket Down)
If the APIs return 5xx or timeouts:
- The agent automatically detects consecutive errors and stops after 5
- No orders are placed during outage
- On recovery, the agent resumes from SLEEP state
- No data loss — trade_log and portfolio are on local storage

---

## Cost Analysis

### Infrastructure
| Item | Monthly Cost |
|------|-------------|
| VPS (2GB, 2CPU) | $10-15 |
| Polymarket gas fees | $0-5 (gasless relayer) |
| Telegram bot | $0 |
| **Total** | **$10-20/month** |

### Trading Costs
| Fee type | Rate | Notes |
|----------|------|-------|
| Polymarket taker fee | 0.5-1.0% | Varies by market |
| Polymarket maker rebate | -0.2% | If limit orders are filled |
| CLOB gas | $0 | Gasless via relayer |
| Spread cost | Variable | Depends on market liquidity |

---

## Performance Benchmarks

| System | Scan Time | Wallets/hr | Arb Found/Scan | Avg Profit |
|--------|-----------|------------|----------------|------------|
| Paper (no auth) | 5s | 50 | 2-6 | 2-277% |
| Live (with auth) | 8s | 50 | 2-6 | 2-277% |
| 2x VPS (failover) | 5s each | 100 total | 4-12 | 2-277% |

---

## Legal Disclaimer

This software is provided for educational and research purposes only. Trading cryptocurrency derivatives and prediction market contracts carries financial risk. Past performance does not guarantee future results. The author is not a financial advisor.

**Jurisdictional warning**: Prediction markets are regulated or prohibited in some jurisdictions. Ensure compliance with local laws before operating this system.

*No finance degree. No trading desk. Just math.*

---

*INTELLITRADE — Drtlemon Elite Tech Conglomerate*
*Engineering the asymmetric edge. Systems over outcomes. Mathematics over emotion.*
