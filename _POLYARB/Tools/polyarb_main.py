#!/usr/bin/env python3
# INTELLITRADE — DrTelemon Elite Tech Conglomerate. Proprietary.
import argparse, json, logging, os, sys, time
from datetime import datetime, timezone
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from polyarb_scanner import full_scan
from polyarb_wallets import (analyze_wallet, discover_top_wallets, add_wallet,
                              remove_wallet, load_watched_wallets, save_watched_wallets,
                              WalletProfile)
from polyarb_copytrade import scan_and_decide, CopytradeConfig, load_config as load_copy_config, save_config as save_copy_config
from polyarb_telegram import (TelegramConfig, load_config as load_tg_config,
                               save_config as save_tg_config,
                               send_message, notify_startup, notify_scan_summary)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s %(message)s")
logger = logging.getLogger("polyarb")

def cmd_scan(args):
    result = full_scan(max_events=args.max_events)
    total = sum(len(v) for v in result.values())
    print(json.dumps({k: [o.__dict__ for o in v] for k, v in result.items()}, indent=2))
    print(f"\nTotal opportunities found: {total}", file=sys.stderr)
    tg = load_tg_config()
    if tg.enabled:
        notify_scan_summary(
            len(result.get("multi_outcome", [])),
            len(result.get("yes_no_pair", [])),
            len(result.get("orderbook", [])),
            len(load_watched_wallets()),
            0,
        )

def cmd_wallets(args):
    if args.action == "list":
        wallets = load_watched_wallets()
        if not wallets:
            print("No watched wallets. Add with: polyarb wallets add <address>")
            return
        for i, w in enumerate(wallets, 1):
            try:
                p = analyze_wallet(w, max_trades=args.trades)
                print(f"{i}. {w}  Score={p.score}  WinRate={p.win_rate:.0%}  "
                      f"Trades={p.total_trades}  Vol=${p.total_volume:.0f}  Label={p.label}")
            except Exception as e:
                print(f"{i}. {w}  Error: {e}")
    elif args.action == "add":
        add_wallet(args.address)
        print(f"Added {args.address}")
    elif args.action == "remove":
        remove_wallet(args.address)
        print(f"Removed {args.address}")
    elif args.action == "discover":
        print(f"Discovering top wallets (min {args.min_trades} trades)...")
        profiles = discover_top_wallets(min_trades=args.min_trades, limit=args.limit)
        for i, p in enumerate(profiles[:20], 1):
            print(f"{i}. {p.address}  Score={p.score}  WinRate={p.win_rate:.0%}  "
                  f"Trades={p.total_trades}  Vol=${p.total_volume:.0f}  Label={p.label}")
        print(f"\n{len(profiles)} wallets found. Use 'polyarb wallets add <address>' to track.")

def cmd_copytrade(args):
    cfg = load_copy_config()
    if args.action == "status":
        print(json.dumps(cfg.__dict__, indent=2))
    elif args.action == "enable":
        cfg.enabled = True
        save_copy_config(cfg)
        print("Copytrading enabled")
    elif args.action == "disable":
        cfg.enabled = False
        save_copy_config(cfg)
        print("Copytrading disabled")
    elif args.action == "set":
        if args.min_score is not None:
            cfg.min_wallet_score = args.min_score
        if args.max_size is not None:
            cfg.max_position_size_usd = args.max_size
        if args.per_trade is not None:
            cfg.per_trade_cap_usd = args.per_trade
        if args.daily_budget is not None:
            cfg.daily_budget_usd = args.daily_budget
        save_copy_config(cfg)
        print("Config updated")
    elif args.action == "scan":
        decisions = scan_and_decide(max_wallets=args.max_wallets, lookback_hours=args.lookback)
        if not decisions:
            print("No copy trades to execute")
            return
        for d in decisions:
            print(f"COPY {d.wallet[:12]}... | ${d.size_usd:.2f} | {d.trade.market_id} | {d.reason}")
        print(f"\n{len(decisions)} copy trades queued")

def cmd_telegram(args):
    cfg = load_tg_config()
    if args.action == "status":
        print(json.dumps(cfg.__dict__, indent=2))
    elif args.action == "set":
        if args.bot_token:
            cfg.bot_token = args.bot_token
        if args.chat_id:
            cfg.chat_id = args.chat_id
        save_tg_config(cfg)
        print("Telegram config saved")
    elif args.action == "enable":
        cfg.enabled = True
        save_tg_config(cfg)
        print("Telegram notifications enabled")
    elif args.action == "disable":
        cfg.enabled = False
        save_tg_config(cfg)
        print("Telegram notifications disabled")
    elif args.action == "test":
        ok = send_message("🧪 Test message from POLYARB")
        print("Sent!" if ok else "Failed! Check bot_token and chat_id.")
    elif args.action == "start":
        cfg.enabled = True
        save_tg_config(cfg)
        notify_startup()
        print("Telegram started and notification sent")

def cmd_loop(args):
    interval = args.interval
    tg = load_tg_config()
    logger.info("Starting POLYARB loop (interval=%ds)", interval)
    if tg.enabled:
        notify_startup()
    while True:
        try:
            now = datetime.now(timezone.utc).isoformat()
            logger.info("=== Scan cycle %s ===", now)
            result = full_scan(max_events=args.max_events)
            multi = result.get("multi_outcome", [])
            pair = result.get("yes_no_pair", [])
            book = result.get("orderbook", [])
            logger.info("Found %d multi-outcome, %d pairs, %d book arb", len(multi), len(pair), len(book))
            if tg.enabled:
                notify_scan_summary(len(multi), len(pair), len(book), len(load_watched_wallets()), 0)
            for opp in multi[:3]:
                logger.info("ARB: %s — %.2f%% profit", opp.event_title, opp.profit_pct)
            decisions = scan_and_decide(max_wallets=args.max_wallets, lookback_hours=24)
            if decisions:
                logger.info("%d copy trades found", len(decisions))
            if tg.enabled and multi:
                for opp in multi[:1]:
                    from polyarb_telegram import notify_arb_opportunity
                    notify_arb_opportunity(opp.__dict__)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("Loop error: %s", e)
            from polyarb_telegram import notify_error
            notify_error(str(e))
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            break

def cmd_agent(args):
    from polyarb_agent import Agent
    agent = Agent(private_key=args.key, interval=args.interval)
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
        print("\nAgent stopped.")

def cmd_portfolio(args):
    from polyarb_portfolio import compute_portfolio, load_trades
    if args.action == "status":
        p = compute_portfolio()
        print(json.dumps(p.__dict__, indent=2))
    elif args.action == "trades":
        trades = load_trades()
        for t in trades[-20:]:
            pnl_str = f" PnL=${t.pnl:.2f}" if t.status == "closed" else ""
            print(f"{t.arb_type:20s} {t.side:5s} {t.price:>8.4f} x {t.size:>8.2f} | {t.status:8s}{pnl_str} | {t.event_title[:30]}")
        print(f"\nTotal trades: {len(trades)}")
    elif args.action == "report":
        from polyarb_portfolio import daily_report
        print(daily_report())

def cmd_learn(args):
    from polyarb_learning import learn_from_history, load_thresholds, get_adjusted_thresholds
    if args.action == "run":
        t = learn_from_history()
        print(f"Signals: {t.signals_generated} gen, {t.signals_executed} exec, {t.profitable_signals} profitable")
        print(f"Thresholds: multi={t.min_multi_outcome_profit}%, wallet_score={t.min_wallet_score}")
    elif args.action == "status":
        t = load_thresholds()
        print(json.dumps(t.__dict__, indent=2))

def main():
    parser = argparse.ArgumentParser(description="POLYARB — Polymarket Arbitrage Scanner & Copytrader")
    parser.add_argument("--json", action="store_true", help="JSON output")
    sub = parser.add_subparsers(dest="command")

    p_scan = sub.add_parser("scan", help="Scan for arbitrage opportunities")
    p_scan.add_argument("--min-multi", type=float, default=0.5, help="Min multi-outcome profit percent")
    p_scan.add_argument("--min-pair", type=float, default=0.3, help="Min yes/no pair profit percent")
    p_scan.add_argument("--min-spread", type=float, default=1.0, help="Min orderbook spread percent")
    p_scan.add_argument("--max-events", type=int, default=50, help="Max events to scan")
    p_scan.set_defaults(func=cmd_scan)

    p_wallets = sub.add_parser("wallets", help="Manage watched wallets")
    p_wallets.add_argument("action", choices=["list", "add", "remove", "discover"])
    p_wallets.add_argument("address", nargs="?", help="Wallet address")
    p_wallets.add_argument("--min-trades", type=int, default=5)
    p_wallets.add_argument("--limit", type=int, default=30)
    p_wallets.add_argument("--trades", type=int, default=50)
    p_wallets.set_defaults(func=cmd_wallets)

    p_copy = sub.add_parser("copytrade", help="Copytrading settings")
    p_copy.add_argument("action", choices=["status", "enable", "disable", "set", "scan"])
    p_copy.add_argument("--min-score", type=float)
    p_copy.add_argument("--max-size", type=float)
    p_copy.add_argument("--per-trade", type=float)
    p_copy.add_argument("--daily-budget", type=float)
    p_copy.add_argument("--max-wallets", type=int, default=20)
    p_copy.add_argument("--lookback", type=int, default=24)
    p_copy.set_defaults(func=cmd_copytrade)

    p_tg = sub.add_parser("telegram", help="Telegram bot config")
    p_tg.add_argument("action", choices=["status", "set", "enable", "disable", "test", "start"])
    p_tg.add_argument("--bot-token")
    p_tg.add_argument("--chat-id")
    p_tg.set_defaults(func=cmd_telegram)

    p_loop = sub.add_parser("loop", help="Continuous scan loop")
    p_loop.add_argument("--interval", type=int, default=300, help="Scan interval in seconds")
    p_loop.add_argument("--max-events", type=int, default=50)
    p_loop.add_argument("--max-wallets", type=int, default=20)
    p_loop.set_defaults(func=cmd_loop)

    p_agent = sub.add_parser("agent", help="Autonomous 24/7 agentic trading")
    p_agent.add_argument("--key", help="Private key for CLOB auth (or set POLY_KEY env)")
    p_agent.add_argument("--interval", type=int, default=300, help="Cycle interval seconds")
    p_agent.set_defaults(func=cmd_agent)

    p_portfolio = sub.add_parser("portfolio", help="Portfolio & trade tracking")
    p_portfolio.add_argument("action", choices=["status", "trades", "report"])
    p_portfolio.set_defaults(func=cmd_portfolio)

    p_learn = sub.add_parser("learn", help="Self-learning engine")
    p_learn.add_argument("action", choices=["run", "status"])
    p_learn.set_defaults(func=cmd_learn)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
