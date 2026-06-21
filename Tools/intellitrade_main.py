# INTELLITRADE — Drtlemon Elite Tech Conglomerate. Proprietary.
"""
Intellitrade — consensus-driven BTC trading system.

Runs 31 parallel prediction paths on 5-minute candles.
Trades fire only when 28/31 models agree. Below 26 votes the trade dies instantly.
Position sizing via Kelly criterion.

Usage:
    python intellitrade_main.py run          # Start live trading loop
    python intellitrade_main.py monitor      # Show current status
    python intellitrade_main.py backtest     # Run historical test
    python intellitrade_main.py configure    # Setup API keys
"""

import argparse
import json
import os
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".intellitrade"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}


def save_config(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


def cmd_configure(args):
    cfg = load_config()
    for key, prompt, default in [
        ("exchange_api_key", "Exchange API key", ""),
        ("exchange_secret", "Exchange secret", ""),
        ("exchange_name", "Exchange name (binance/coinbase/kraken)", "binance"),
        ("mirofish_path", "MiroFish installation path", str(Path.home() / "MiroFish-Offline")),
        ("max_candles", "Max candles to keep in memory", "1000"),
        ("kelly_fraction", "Kelly fraction (0.1-1.0)", "0.5"),
        ("model_count", "Number of parallel models (default 31)", "31"),
        ("fire_threshold", "Consensus threshold (default 28)", "28"),
        ("kill_threshold", "Kill threshold (default 26)", "26"),
    ]:
        current = str(cfg.get(key, default))
        val = input(f"{prompt} [{current}]: ").strip()
        if val:
            cfg[key] = val

    save_config(cfg)
    print(f"Configuration saved to {CONFIG_FILE}")


def cmd_monitor(args):
    cfg = load_config()
    state_file = CONFIG_DIR / "state.json"
    if not state_file.exists():
        print("No trading state found. Start the trader first with 'run'.")
        return

    state = json.loads(state_file.read_text())
    print(f"\n=== Intellitrade Status ===")
    print(f"  Status:        {state.get('status', 'unknown')}")
    print(f"  Candle:        {state.get('last_candle', 'N/A')}")
    print(f"  Current vote:  {state.get('current_vote', 'N/A')}/{cfg.get('model_count', 31)}")
    print(f"  Signal:        {state.get('signal', 'FLAT')}")
    print(f"  Position:      {state.get('position', 'NONE')}")
    print(f"  P&L (24h):     {state.get('pnl_24h', 0):.2f} USDT")
    print(f"  Total trades:  {state.get('total_trades', 0)}")
    print(f"  Win rate:      {state.get('win_rate', 0):.1f}%")
    print(f"  Balance:       {state.get('balance', 0):.2f} USDT")

    votes = state.get('vote_breakdown', {})
    if votes:
        print(f"\n  Vote breakdown:")
        for direction, count in sorted(votes.items()):
            print(f"    {direction}: {count}")


def cmd_backtest(args):
    print("\n=== Intellitrade Backtest ===")
    print("  This runs the full 31-model consensus system on historical data.")

    from intellitrade_data import fetch_historical_candles
    from intellitrade_models import run_model_batch
    from intellitrade_consensus import ConsensusEngine

    cfg = load_config()
    symbol = args.symbol or "BTCUSDT"
    days = args.days or 30
    model_count = int(cfg.get("model_count", 31))
    fire_thresh = int(cfg.get("fire_threshold", 28))
    kill_thresh = int(cfg.get("kill_threshold", 26))

    print(f"\n  Symbol:   {symbol}")
    print(f"  Period:   {days} days")
    print(f"  Models:   {model_count}")
    print(f"  Fire at:  {fire_thresh}/{model_count}")
    print(f"  Kill at:  {kill_thresh}/{model_count}")
    print()

    candles = fetch_historical_candles(symbol, days * 24 * 60)
    print(f"  Loaded {len(candles)} candles\n")

    engine = ConsensusEngine(fire_thresh, kill_thresh, model_count)
    results = []
    balance = 10_000.0
    position = 0.0
    trades = 0
    wins = 0

    for i in range(model_count, len(candles)):
        window = candles[i - model_count : i]
        predictions = run_model_batch(window, model_count)
        vote = engine.count_votes(predictions)
        signal = engine.decide(vote)

        close = window[-1]["close"]
        if signal == "LONG" and position == 0:
            pos_size = balance * 0.5 / close
            position = pos_size
            trades += 1
            entry_price = close
        elif signal == "SHORT" and position == 0:
            pos_size = balance * 0.5 / close
            position = -pos_size
            trades += 1
            entry_price = close
        elif signal == "FLAT" and position != 0:
            pnl = position * (close - entry_price)
            balance += pnl
            if pnl > 0:
                wins += 1
            position = 0

        results.append({
            "time": window[-1]["time"],
            "close": close,
            "vote": vote,
            "signal": signal,
            "balance": balance,
        })

    win_rate = (wins / trades * 100) if trades > 0 else 0
    print(f"\n=== Backtest Results ===")
    print(f"  Trades:       {trades}")
    print(f"  Win rate:     {win_rate:.1f}%")
    print(f"  Final bal:    {balance:.2f} USDT")
    print(f"  Return:       {(balance - 10000) / 10000 * 100:.1f}%")

    out_file = CONFIG_DIR / f"backtest_{symbol}_{days}d.json"
    out_file.write_text(json.dumps({
        "symbol": symbol,
        "days": days,
        "model_count": model_count,
        "trades": trades,
        "win_rate": round(win_rate, 1),
        "final_balance": round(balance, 2),
        "return_pct": round((balance - 10000) / 10000 * 100, 1),
        "results": results,
    }, indent=2, default=str))
    print(f"\n  Full results saved to {out_file}")


def cmd_run(args):
    print("\n=== Intellitrade Live Trader ===")
    print("  Starting consensus-driven BTC trading loop...")
    print("  31 parallel prediction paths | 28/31 fire threshold | Kelly sizing\n")

    from intellitrade_data import CandleStream
    from intellitrade_models import run_model_batch
    from intellitrade_consensus import ConsensusEngine
    from intellitrade_exec import TradeExecutor

    cfg = load_config()
    model_count = int(cfg.get("model_count", 31))
    fire_thresh = int(cfg.get("fire_threshold", 28))
    kill_thresh = int(cfg.get("kill_threshold", 26))
    kelly_frac = float(cfg.get("kelly_fraction", 0.5))

    stream = CandleStream("BTCUSDT", interval="5m")
    engine = ConsensusEngine(fire_thresh, kill_thresh, model_count)
    executor = TradeExecutor(kelly_fraction=kelly_frac)

    buffer = []
    candle_count = 0

    try:
        for candle in stream:
            buffer.append(candle)
            if len(buffer) < model_count:
                continue

            candle_count += 1
            window = buffer[-model_count:]
            predictions = run_model_batch(window, model_count)
            vote = engine.count_votes(predictions)
            signal = engine.decide(vote)

            # Save state
            state = {
                "status": "running",
                "last_candle": candle["time"],
                "current_vote": vote,
                "signal": signal,
                "position": "NONE",
                "pnl_24h": 0,
                "total_trades": executor.total_trades,
                "win_rate": executor.win_rate,
                "balance": executor.balance,
                "vote_breakdown": engine.last_breakdown,
            }

            if signal != "FLAT":
                price = candle["close"]
                order = executor.execute(signal, price)
                state["position"] = f"{'LONG' if order['side'] == 'buy' else 'SHORT'} @ {order['price']:.2f}"
                print(f"  SIGNAL: {signal} @ {price:.2f} | Size: {order['size']:.4f} BTC | Vote: {vote}/{model_count}")

            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            (CONFIG_DIR / "state.json").write_text(json.dumps(state, indent=2, default=str))

            if candle_count % 12 == 0:
                print(f"  [{candle['time']}] Vote: {vote}/{model_count} | Signal: {signal} | Bal: {executor.balance:.2f}")

    except KeyboardInterrupt:
        print("\n  Trader stopped by user.")
        state["status"] = "stopped"
        (CONFIG_DIR / "state.json").write_text(json.dumps(state, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Intellitrade — consensus-driven BTC trading")
    parser.set_defaults(func=lambda _: parser.print_help())

    sub = parser.add_subparsers()

    p_run = sub.add_parser("run", help="Start live trading loop")
    p_run.set_defaults(func=cmd_run)

    p_mon = sub.add_parser("monitor", aliases=["status"], help="Show current trading status")
    p_mon.set_defaults(func=cmd_monitor)

    p_bt = sub.add_parser("backtest", help="Run historical backtest")
    p_bt.add_argument("--symbol", default="BTCUSDT", help="Trading pair")
    p_bt.add_argument("--days", type=int, default=30, help="Days of history")
    p_bt.set_defaults(func=cmd_backtest)

    p_cfg = sub.add_parser("configure", aliases=["config"], help="Configure API keys and settings")
    p_cfg.set_defaults(func=cmd_configure)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
