"""
Multi-strategy runner.

Coordinates market-data retrieval, strategy execution, and result aggregation.
"""

from __future__ import annotations

import concurrent.futures
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta

from ..data_provider.data_fetcher import DataFetcher
from .base_strategy import BaseStrategy
from .mean_reversion_strategy import MeanReversionStrategy
from .moving_average_strategy import MovingAverageStrategy
from .strategies_models import StrategyResult

logger = logging.getLogger(__name__)

try:
    from .rsi_strategy import RSIStrategy
except ImportError:  # pragma: no cover - optional dependency
    RSIStrategy = None  # type: ignore[assignment]

try:
    from .bollinger_bands_strategy import BollingerBandsStrategy
except ImportError:  # pragma: no cover - optional dependency
    BollingerBandsStrategy = None  # type: ignore[assignment]


class MultiStrategyRunner:
    """Run multiple trading strategies over shared market data."""

    def __init__(self, data_fetcher: Optional[DataFetcher] = None) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_fetcher = data_fetcher or DataFetcher()
        self.strategies: Dict[str, BaseStrategy] = self._initialize_strategies()
        self.results: Dict[str, StrategyResult] = {}

    # ------------------------------------------------------------------ #
    # Strategy management
    # ------------------------------------------------------------------ #
    def _initialize_strategies(self) -> Dict[str, BaseStrategy]:
        strategies: Dict[str, BaseStrategy] = {}

        try:
            strategies["moving_average"] = MovingAverageStrategy(
                short_window=10,
                long_window=30,
            )
            strategies["mean_reversion"] = MeanReversionStrategy(
                bb_period=20,
                bb_std=2.0,
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70,
            )

            if RSIStrategy is not None:
                strategies["rsi"] = RSIStrategy(
                    period=14,
                    oversold=30,
                    overbought=70,
                )
            else:  # pragma: no cover - optional import
                self.logger.info("RSI strategy unavailable; skipping registration.")

            if BollingerBandsStrategy is not None:
                strategies["bollinger_bands"] = BollingerBandsStrategy(
                    period=20,
                    std_dev=2.0,
                )
            else:  # pragma: no cover - optional import
                self.logger.info("Bollinger Bands strategy unavailable; skipping registration.")

        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Failed to initialise strategies: %s", exc)

        # Simple aliases for backwards compatibility
        aliases: Dict[str, Optional[BaseStrategy]] = {
            "ma": strategies.get("moving_average"),
            "mr": strategies.get("mean_reversion"),
        }
        for alias, strategy in aliases.items():
            if strategy is not None and alias not in strategies:
                strategies[alias] = strategy

        return strategies

    def add_strategy(self, name: str, strategy: BaseStrategy) -> None:
        self.strategies[name] = strategy
        self.logger.info("Registered strategy: %s", name)

    def remove_strategy(self, name: str) -> None:
        if name in self.strategies:
            del self.strategies[name]
            self.logger.info("Removed strategy: %s", name)

    # ------------------------------------------------------------------ #
    # Market data
    # ------------------------------------------------------------------ #
    def get_market_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = self._resolve_period_start(period, end_date)

        try:
            data = self.data_fetcher.fetch_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
            )
        except Exception as exc:
            self.logger.error("Failed to fetch market data for %s: %s", symbol, exc)
            raise

        if data is None or data.empty:
            raise ValueError(f"No market data returned for symbol {symbol}")

        data = data.copy()
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        if getattr(data.index, "tz", None) is not None:
            data.index = data.index.tz_convert(None)
        data.index.name = "date"
        data.sort_index(inplace=True)

        data.columns = [str(col).lower().replace(" ", "_") for col in data.columns]
        required = {"open", "high", "low", "close", "volume"}
        missing = required - set(data.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        data = data.dropna(subset=["open", "high", "low", "close"])
        if len(data) < 20:
            raise ValueError(f"Insufficient data points ({len(data)}) for strategy execution")

        return data

    @staticmethod
    def _resolve_period_start(period: str, end_date: datetime) -> Optional[datetime]:
        if not period:
            return end_date - timedelta(days=365)

        period = period.lower()
        if period == "max":
            return None

        match = re.fullmatch(r"(\d+)([a-z]+)", period)
        if not match:
            return end_date - timedelta(days=365)

        value = int(match.group(1))
        unit = match.group(2)

        if unit in {"y", "yr", "yrs", "year", "years"}:
            return end_date - relativedelta(years=value)
        if unit in {"mo", "mon", "month", "months"}:
            return end_date - relativedelta(months=value)
        if unit in {"w", "wk", "week", "weeks"}:
            return end_date - timedelta(weeks=value)
        if unit in {"d", "day", "days"}:
            return end_date - timedelta(days=value)

        return end_date - timedelta(days=365)

    # ------------------------------------------------------------------ #
    # Strategy execution
    # ------------------------------------------------------------------ #
    def run_single_strategy(
        self,
        strategy_name: str,
        strategy: BaseStrategy,
        symbol: str,
        data: pd.DataFrame,
    ) -> StrategyResult:
        self.logger.info("Running %s on %s", strategy_name, symbol)

        if not strategy.validate_data(data):
            raise ValueError(f"Invalid data provided to strategy {strategy_name}")

        signals = strategy.generate_signals(data)
        if signals.empty:
            raise ValueError(f"No signals generated by strategy {strategy_name}")

        try:
            backtest_results = strategy.backtest(data)
        except Exception as exc:
            self.logger.error("Backtest failed for %s on %s: %s", strategy_name, symbol, exc)
            raise

        metadata = {
            "last_signal_at": signals.index[-1] if not signals.empty else None,
            "run_at": datetime.now(),
        }

        result = StrategyResult(
            strategy_name=strategy_name,
            symbol=symbol,
            total_return=backtest_results.get("total_return", 0.0),
            sharpe_ratio=backtest_results.get("sharpe_ratio", 0.0),
            max_drawdown=backtest_results.get("max_drawdown", 0.0),
            win_rate=backtest_results.get("win_rate", 0.0),
            total_trades=backtest_results.get("total_trades", 0),
            avg_trade_return=backtest_results.get("avg_trade_return", 0.0),
            volatility=backtest_results.get("volatility", 0.0),
            calmar_ratio=backtest_results.get("calmar_ratio", 0.0),
            sortino_ratio=backtest_results.get("sortino_ratio", 0.0),
            trades=backtest_results.get("trades", []),
            signals=signals,
            portfolio_value=backtest_results.get("portfolio_values", pd.Series()),
            metadata=metadata,
        )

        return result

    def run_all_strategies(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        selected_strategies: Optional[Iterable[str]] = None,
        use_threads: bool = True,
    ) -> Dict[str, StrategyResult]:
        data = self.get_market_data(symbol, period=period, interval=interval)

        strategies_to_run = (
            {name: self.strategies[name] for name in selected_strategies if name in self.strategies}
            if selected_strategies
            else self.strategies
        )

        if not strategies_to_run:
            raise ValueError("No strategies available to run.")

        self.results = {}

        if use_threads and len(strategies_to_run) > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_map = {
                    executor.submit(self.run_single_strategy, name, strategy, symbol, data): name
                    for name, strategy in strategies_to_run.items()
                }
                for future in concurrent.futures.as_completed(future_map):
                    name = future_map[future]
                    try:
                        self.results[name] = future.result()
                    except Exception as exc:
                        self.logger.error("Strategy %s failed: %s", name, exc)
        else:
            for name, strategy in strategies_to_run.items():
                self.results[name] = self.run_single_strategy(name, strategy, symbol, data)

        return self.results

    # ------------------------------------------------------------------ #
    # Reporting helpers
    # ------------------------------------------------------------------ #
    def generate_comparison_report(self) -> pd.DataFrame:
        if not self.results:
            return pd.DataFrame()

        records = []
        for name, result in self.results.items():
            records.append(
                {
                    "strategy": name,
                    "symbol": result.symbol,
                    "total_return": result.total_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "total_trades": result.total_trades,
                    "avg_trade_return": result.avg_trade_return,
                    "volatility": result.volatility,
                    "calmar_ratio": result.calmar_ratio,
                    "sortino_ratio": result.sortino_ratio,
                }
            )

        df = pd.DataFrame(records)
        if not df.empty:
            df.sort_values("sharpe_ratio", ascending=False, inplace=True)
        return df

    def get_best_strategy(self) -> Tuple[Optional[str], Optional[StrategyResult]]:
        if not self.results:
            return None, None
        best_name = max(self.results, key=lambda name: self.results[name].sharpe_ratio)
        return best_name, self.results[best_name]

    def get_performance_summary(self) -> Dict[str, Any]:
        if not self.results:
            return {}

        total_returns = [res.total_return for res in self.results.values()]
        sharpe_ratios = [res.sharpe_ratio for res in self.results.values()]
        drawdowns = [res.max_drawdown for res in self.results.values()]

        best_name, best_result = self.get_best_strategy()

        summary: Dict[str, Any] = {
            "strategy_count": len(self.results),
            "avg_return": float(np.mean(total_returns)),
            "best_return": max(total_returns),
            "worst_return": min(total_returns),
            "avg_sharpe": float(np.mean(sharpe_ratios)),
            "best_sharpe": best_result.sharpe_ratio if best_result else 0.0,
            "avg_drawdown": float(np.mean(drawdowns)),
            "worst_drawdown": min(drawdowns),
            "best_strategy": best_name,
        }
        return summary

    def export_results(self, filename: Optional[str] = None) -> str:
        if not self.results:
            raise ValueError("No strategy results to export.")

        filename = filename or f"multi_strategy_results_{datetime.now():%Y%m%d_%H%M%S}.xlsx"

        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            report = self.generate_comparison_report()
            report.to_excel(writer, sheet_name="comparison", index=False)

            for name, result in self.results.items():
                if result.trades:
                    pd.DataFrame(result.trades).to_excel(writer, sheet_name=f"{name}_trades", index=False)
                if not result.signals.empty:
                    result.signals.to_excel(writer, sheet_name=f"{name}_signals")
                if not result.portfolio_value.empty:
                    result.portfolio_value.to_frame(name="portfolio_value").to_excel(
                        writer,
                        sheet_name=f"{name}_portfolio",
                    )

        self.logger.info("Exported results to %s", filename)
        return filename

    def clear_results(self) -> None:
        self.results.clear()
        self.logger.info("Cleared strategy results cache.")


def create_default_runner() -> MultiStrategyRunner:
    """Convenience helper for default runner creation."""
    return MultiStrategyRunner()


def quick_analysis(symbol: str, period: str = "1y") -> Dict[str, StrategyResult]:
    runner = create_default_runner()
    return runner.run_all_strategies(symbol=symbol, period=period)
