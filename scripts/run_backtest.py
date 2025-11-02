#!/usr/bin/env python3
"""Utility script for running strategy backtests from the command line."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config as app_config  # noqa: E402  (after sys.path)

from src.tradingagent.modules.data_provider import DataFetcher  # noqa: E402
from src.tradingagent.modules.backtesting import BacktestEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Strategy utilities
# ---------------------------------------------------------------------------

def _build_strategy(name: str):
    """Return an instantiated strategy based on the provided name."""
    name = (name or "mean_reversion").lower()

    if name in {"mean", "mean_reversion"}:
        from src.tradingagent.modules.strategies.mean_reversion_strategy import (  # noqa: E402
            MeanReversionStrategy,
        )

        return MeanReversionStrategy()

    if name in {"ma", "moving_average"}:
        from src.tradingagent.modules.strategies.moving_average_strategy import (  # noqa: E402
            MovingAverageStrategy,
        )

        return MovingAverageStrategy()

    if name in {"rsi"}:
        from src.tradingagent.modules.strategies.rsi_strategy import RSIStrategy  # noqa: E402

        return RSIStrategy()

    if name in {"bollinger", "bollinger_bands"}:
        from src.tradingagent.modules.strategies.bollinger_bands_strategy import (  # noqa: E402
            BollingerBandsStrategy,
        )

        return BollingerBandsStrategy()

    if name in {"multi", "multi_strategy"}:
        from src.tradingagent.modules.strategies.multi_strategy_runner import (  # noqa: E402
            MultiStrategyRunner,
        )

        return MultiStrategyRunner()

    raise ValueError(f"Unknown strategy '{name}'")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _collect_data(fetcher: DataFetcher, symbols: Iterable[str], start: str, end: str) -> Dict[str, pd.DataFrame]:
    """Fetch historical data for the requested symbols."""
    data: Dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        print(f"Fetching data for {symbol}...")
        frame = fetcher.fetch_stock_data(symbol, start_date=start, end_date=end)
        if frame is None or frame.empty:
            raise ValueError(f"No data returned for symbol '{symbol}'.")
        # Ensure chronological order and timezone-naive index
        frame = frame.sort_index()
        if getattr(frame.index, "tz", None) is not None:
            frame.index = frame.index.tz_localize(None)
        data[symbol] = frame
    if not data:
        raise ValueError("No valid symbols provided.")
    return data


def _summarise_results(results: Dict[str, Any]) -> Dict[str, Any]:
    """Create a serialisable summary out of backtest results."""
    summary: Dict[str, Any] = {}

    for key, value in results.items():
        if isinstance(value, (int, float)):
            summary[key] = float(value)

    equity_curve = results.get("portfolio_values")
    if isinstance(equity_curve, pd.DataFrame):
        summary["equity_curve"] = equity_curve.reset_index().to_dict(orient="records")

    trades = results.get("trades")
    if trades:
        trade_rows = []
        for trade in trades:
            trade_rows.append(
                {
                    "symbol": trade.symbol,
                    "entry_date": trade.entry_date.isoformat() if trade.entry_date else None,
                    "exit_date": trade.exit_date.isoformat() if trade.exit_date else None,
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "quantity": trade.quantity,
                    "pnl": trade.pnl,
                    "return_pct": trade.return_pct,
                    "side": trade.trade_type,
                }
            )
        summary["trades"] = trade_rows

    returns = results.get("daily_returns")
    if isinstance(returns, pd.Series):
        summary["daily_returns"] = {str(idx): float(val) for idx, val in returns.items()}

    return summary


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a strategy backtest")
    parser.add_argument("symbol", nargs="*", help="Symbols to backtest (e.g. AAPL MSFT)")
    parser.add_argument("--strategy", default="mean_reversion", help="Strategy name (mean_reversion, moving_average, rsi, bollinger, multi)")
    parser.add_argument("--start", dest="start_date", help="Backtest start date (YYYY-MM-DD)")
    parser.add_argument("--end", dest="end_date", help="Backtest end date (YYYY-MM-DD)")
    parser.add_argument("--provider", default=None, help="Market data provider (default from config)")
    parser.add_argument("--capital", type=float, default=None, help="Initial capital for the backtest")
    parser.add_argument("--output", help="Optional path to save the JSON summary")
    parser.add_argument("--benchmark", help="Optional benchmark symbol for comparison")
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])

    symbols = args.symbol or app_config.get("backtesting.symbols", ["AAPL"])
    if isinstance(symbols, str):
        symbols = [sym.strip() for sym in symbols.split(",") if sym.strip()]
    if not symbols:
        raise ValueError("At least one symbol must be provided")

    start_date = args.start_date or app_config.get("backtesting.start_date")
    end_date = args.end_date or app_config.get("backtesting.end_date")

    # Instantiate strategy and data fetcher
    strategy = _build_strategy(args.strategy)
    provider = args.provider or app_config.get("market_data.default_provider", "yfinance")
    fetcher = DataFetcher(provider=provider)

    market_data = _collect_data(fetcher, symbols, start_date, end_date)

    # Optional benchmark
    benchmark_data = None
    benchmark_symbol = args.benchmark or app_config.get("backtesting.benchmark")
    if benchmark_symbol:
        try:
            benchmark_data = fetcher.fetch_stock_data(benchmark_symbol, start_date=start_date, end_date=end_date)
        except Exception as exc:  # pragma: no cover - optional benchmark
            print(f"Warning: unable to fetch benchmark data ({exc})")

    engine = BacktestEngine(initial_capital=args.capital)
    results = engine.run_backtest(
        strategy=strategy,
        data=market_data,
        start_date=start_date,
        end_date=end_date,
        benchmark_data=benchmark_data,
    )

    summary = _summarise_results(results)
    summary["metadata"] = {
        "strategy": args.strategy,
        "symbols": symbols,
        "provider": provider,
        "start_date": start_date,
        "end_date": end_date,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    print("Backtest Summary:")
    for key in [
        "total_return",
        "annual_return",
        "volatility",
        "sharpe_ratio",
        "max_drawdown",
        "win_rate",
        "profit_factor",
        "final_capital",
        "total_trades",
    ]:
        if key in summary:
            print(f"  {key}: {summary[key]:.4f}")

    output_path = args.output
    if output_path:
        out_file = Path(output_path)
        out_file.write_text(json.dumps(summary, default=str, indent=2), encoding='utf-8')
        print(f"Summary written to {out_file.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
