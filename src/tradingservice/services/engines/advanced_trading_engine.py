#!/usr/bin/env python3
"""
 高级交易引擎。

 负责协调数据获取、策略评估、风险控制与订单执行，从而驱动自动化交易流程。
"""

from __future__ import annotations

import logging
import math
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple
from pprint import pformat

import schedule
import pandas as pd

from config import config
from src.tradingagent.modules.data_provider import DataProvider
from src.tradingagent.modules.risk_management import (
    TradingRiskManager as RiskManager,
)
from src.tradingagent.modules.strategies import MeanReversionStrategy

# 确保项目根目录被加入导入路径，便于加载交易代理相关模块。
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class AdvancedTradingEngine:
    """整合策略执行与风险控制的高阶交易循环。"""

    DEFAULT_SIGNAL_LOOKBACK_DAYS = 120
    DEFAULT_REQUIRED_SIGNAL_COLUMNS: Tuple[str, ...] = ("Signal",)

    def __init__(self) -> None:
        """初始化依赖组件、内部状态与日志系统。"""
        self.initial_capital = float(config.get_env("INITIAL_CAPITAL", 100_000.0))
        self.current_capital = self.initial_capital
        self.paper_trading = config.get_env("PAPER_TRADING", True)

        # 核心服务组件
        self.data_provider = DataProvider()
        self.strategy = MeanReversionStrategy()
        self.risk_manager = RiskManager(
            max_position_size=0.2,
            stop_loss_pct=0.05,
            take_profit_pct=0.15,
            max_daily_loss=0.02,
        )

        self.watch_list = [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "TSLA",
            "META",
            "NVDA",
            "NFLX",
        ]
        self.commission_rate = 0.001  # 0.1%
        self.trade_history: list[Dict[str, object]] = []
        self.signal_lookback_days = int(
            config.get("advanced_engine.signal_lookback_days", self.DEFAULT_SIGNAL_LOOKBACK_DAYS)
        )
        self.required_signal_columns = self._load_required_signal_columns()

        self.setup_logging()
        self.risk_manager.update_daily_capital(self.current_capital)

        self.logger.info("Advanced trading engine initialized.")
        self.logger.info("Initial capital: $%.2f", self.initial_capital)
        self.logger.info("Watch list: %s", ", ".join(self.watch_list))

    # --------------------------------------------------------------------- #
    # 基础设施相关
    # --------------------------------------------------------------------- #
    def setup_logging(self) -> None:
        """配置模块日志输出。"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_level = config.get_env("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level, logging.INFO),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "advanced_trading.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("AdvancedTrading")

    # --------------------------------------------------------------------- #
    # 数据拉取与信号生成
    # --------------------------------------------------------------------- #
    def get_current_prices(self) -> Dict[str, float]:
        """返回观察列表中每只股票的最新收盘价。"""
        prices: Dict[str, float] = {}
        for symbol in self.watch_list:
            try:
                data = self.data_provider.get_historical_data(
                    symbol,
                    (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d"),
                )
                if data is not None and not data.empty:
                    prices[symbol] = float(data["close"].iloc[-1])
                else:
                    self.logger.warning(
                        "No recent data found for %s when fetching current price.", symbol
                    )
            except (ValueError, KeyError, TypeError) as exc:
                self.logger.error("Failed to fetch current price for %s: %s", symbol, exc)

        return prices

    def analyze_market(
        self, *, required_columns: Optional[Iterable[str]] = None
    ) -> Dict[str, Dict[str, float]]:
        """为观察列表生成交易信号。"""
        signals: Dict[str, Dict[str, float]] = {}
        required = self._normalise_required_columns(required_columns)

        for symbol in self.watch_list:
            try:
                data = self.data_provider.get_historical_data(
                    symbol,
                    (
                        datetime.now() - timedelta(days=self.signal_lookback_days)
                    ).strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d"),
                )

                if data is None or data.empty or len(data) < 20:
                    continue

                strategy_signals = self.strategy.generate_signals(data)
                self.logger.debug("Generated signals for %s", pformat(strategy_signals))
                if (
                    not isinstance(strategy_signals, pd.DataFrame)
                    or strategy_signals.empty
                ):
                    continue

                missing_columns = [
                    column for column in required if column not in strategy_signals.columns
                ]
                if missing_columns:
                    self.logger.debug(
                        "Missing required columns %s for %s; skipping.",
                        ", ".join(missing_columns),
                        symbol,
                    )
                    continue

                clean_signals = strategy_signals.dropna(subset=required) if required else strategy_signals
                if clean_signals.empty:
                    self.logger.debug(
                        "No actionable signals for %s after dropping NaNs.", symbol
                    )
                    continue

                latest_signal = clean_signals.iloc[-1]
                action_column = required[0] if required else "Signal"
                action = latest_signal.get(action_column)
                if action is None or (isinstance(action, float) and math.isnan(action)):
                    self.logger.debug("Latest signal missing action for %s; skipping.", symbol)
                    continue

                confidence = latest_signal.get("Confidence")
                if confidence is None or (isinstance(confidence, float) and math.isnan(confidence)):
                    confidence = latest_signal.get("signal_strength", 0.5)

                signals[symbol] = {
                    "action": action,
                    "price": float(data["close"].iloc[-1]),
                    "confidence": abs(confidence),
                }
            except (ValueError, KeyError, TypeError) as exc:
                self.logger.error("Signal generation failed for %s: %s", symbol, exc)

        return signals

    def _load_required_signal_columns(self) -> Tuple[str, ...]:
        raw = config.get(
            "advanced_engine.required_signal_columns", self.DEFAULT_REQUIRED_SIGNAL_COLUMNS
        )
        if isinstance(raw, (list, tuple, set)):
            cleaned = tuple(str(col).strip() for col in raw if str(col).strip())
            return cleaned or self.DEFAULT_REQUIRED_SIGNAL_COLUMNS
        if isinstance(raw, str) and raw.strip():
            return (raw.strip(),)
        return self.DEFAULT_REQUIRED_SIGNAL_COLUMNS

    def _normalise_required_columns(
        self, required_columns: Optional[Iterable[str]]
    ) -> Tuple[str, ...]:
        if required_columns is None:
            return self.required_signal_columns
        cleaned = tuple(str(col).strip() for col in required_columns if str(col).strip())
        return cleaned

    # --------------------------------------------------------------------- #
    # 交易执行流程
    # --------------------------------------------------------------------- #
    def execute_trade(self, symbol: str, action: str, price: float) -> bool:
        """根据交易动作委派到具体的买入或卖出逻辑。"""
        try:
            if not self.risk_manager.can_open_position(
                symbol, action, self.current_capital
            ):
                return False

            if action == "BUY":
                return self._execute_buy(symbol, price)
            if action == "SELL":
                return self._execute_sell(symbol, price)

            self.logger.warning("Unsupported trade action requested: %s", action)
            return False

        except (ValueError, KeyError, TypeError) as exc:
            self.logger.error(
                "Trade execution failed for %s %s at %.2f: %s",
                action,
                symbol,
                price,
                exc,
            )
            return False

    def _execute_buy(self, symbol: str, price: float) -> bool:
        """提交模拟或纸面交易的买入指令。"""
        quantity = self.risk_manager.calculate_position_size(
            symbol, price, self.current_capital
        )
        if quantity <= 0:
            return False

        trade_value = quantity * price
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission

        if total_cost > self.current_capital:
            self.logger.warning(
                "Insufficient capital to open position %s (required %.2f, available %.2f)",
                symbol,
                total_cost,
                self.current_capital,
            )
            return False

        log_prefix = "[PAPER]" if self.paper_trading else "[LIVE]"
        self.logger.info("%s Buying %s: %d shares @ $%.2f", log_prefix, symbol, quantity, price)

        self.current_capital -= total_cost
        self.risk_manager.open_position(symbol, quantity, price)
        self.trade_history.append(
            {
                "time": datetime.now(),
                "symbol": symbol,
                "action": "BUY",
                "quantity": quantity,
                "price": price,
                "commission": commission,
                "capital": self.current_capital,
            }
        )
        return True

    def _execute_sell(self, symbol: str, price: float) -> bool:
        """提交模拟或纸面交易的卖出指令。"""
        position_info: Optional[Dict[str, float]] = self.risk_manager.get_position_info(
            symbol
        )
        if not position_info or position_info.get("quantity", 0) <= 0:
            return False

        quantity = int(position_info["quantity"])
        trade_value = quantity * price
        commission = trade_value * self.commission_rate
        net_proceeds = trade_value - commission

        log_prefix = "[PAPER]" if self.paper_trading else "[LIVE]"
        self.logger.info("%s Selling %s: %d shares @ $%.2f", log_prefix, symbol, quantity, price)

        self.current_capital += net_proceeds
        trade_record = self.risk_manager.close_position(symbol, price)
        self.trade_history.append(
            {
                "time": datetime.now(),
                "symbol": symbol,
                "action": "SELL",
                "quantity": quantity,
                "price": price,
                "commission": commission,
                "capital": self.current_capital,
                "pnl": trade_record["pnl"] if trade_record else 0.0,
            }
        )
        return True

    # --------------------------------------------------------------------- #
    # 风险控制
    # --------------------------------------------------------------------- #
    def risk_check(self) -> None:
        """对当前持仓进行止损与止盈检查。"""
        current_prices = self.get_current_prices()

        for symbol in self.risk_manager.get_all_positions():
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            if self.risk_manager.should_stop_loss(symbol, current_price):
                self.logger.warning("Stop-loss triggered for %s", symbol)
                self.execute_trade(symbol, "SELL", current_price)
                continue

            if self.risk_manager.should_take_profit(symbol, current_price):
                self.logger.info("Take-profit triggered for %s", symbol)
                self.execute_trade(symbol, "SELL", current_price)

    # --------------------------------------------------------------------- #
    # 主循环
    # --------------------------------------------------------------------- #
    def scan_and_trade(self) -> None:
        """执行一次完整的市场扫描并落实高置信度信号。"""
        try:
            self.logger.info("Starting scheduled market scan.")

            self.risk_check()

            if self.risk_manager.check_daily_loss_limit(self.current_capital):
                self.logger.error(
                    "Daily loss limit reached; halting trading until tomorrow."
                )
                return

            signals = self.analyze_market()

            for symbol, signal_info in signals.items():
                action = signal_info["action"]
                price = signal_info["price"]
                confidence = signal_info["confidence"]

                if confidence > 0.6 and action in {"BUY", "SELL"}:
                    self.execute_trade(symbol, action, price)

        except (ValueError, KeyError, TypeError) as exc:
            self.logger.error("Scheduled scan failed: %s", exc)

    def generate_daily_report(self) -> None:
        """输出每日绩效、风险度量与持仓概览。"""
        try:
            daily_return = (
                self.current_capital - self.initial_capital
            ) / self.initial_capital

            positions = self.risk_manager.get_all_positions()
            current_prices = self.get_current_prices()
            portfolio_risk = self.risk_manager.calculate_portfolio_risk(
                current_prices, self.current_capital
            )
            daily_trades = self.risk_manager.get_daily_trades()

            self.logger.info("=" * 50)
            self.logger.info("Daily Trading Report")
            self.logger.info("=" * 50)
            self.logger.info("Current capital: $%.2f", self.current_capital)
            self.logger.info("Daily return: %.2f%%", daily_return * 100)
            self.logger.info("Open positions: %d", len(positions))
            self.logger.info("Trades executed today: %d", len(daily_trades))
            self.logger.info("Total exposure: $%.2f", portfolio_risk["total_exposure"])
            self.logger.info(
                "Exposure ratio: %.1f%%", portfolio_risk["exposure_ratio"] * 100
            )

            if positions:
                self.logger.info("Open position details:")
                for symbol, position in positions.items():
                    if symbol not in current_prices:
                        continue
                    current_price = current_prices[symbol]
                    unrealized_pnl = (
                        current_price - position["entry_price"]
                    ) * position["quantity"]
                    self.logger.info(
                        "  %s: %d shares @ $%.2f (last $%.2f, unrealized PnL $%.2f)",
                        symbol,
                        position["quantity"],
                        position["entry_price"],
                        current_price,
                        unrealized_pnl,
                    )

        except (ValueError, KeyError, TypeError) as exc:
            self.logger.error("Failed to generate daily report: %s", exc)

    def start_trading(self) -> None:
        """启动调度器并持续运行交易循环。"""
        self.logger.info("Starting advanced trading engine loop.")

        schedule.every().hour.do(self.scan_and_trade)
        schedule.every().day.at("09:30").do(
            lambda: self.risk_manager.update_daily_capital(self.current_capital)
        )
        schedule.every().day.at("16:00").do(self.generate_daily_report)

        self.scan_and_trade()
        self.generate_daily_report()

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Trading loop interrupted by user.")
        except (ValueError, TypeError, RuntimeError, OSError) as exc:
            self.logger.error("Trading loop terminated unexpectedly: %s", exc)


def main() -> None:
    """命令行入口，便于单独运行引擎。"""
    try:
        engine = AdvancedTradingEngine()
        engine.start_trading()
    except KeyboardInterrupt:
        print("\nTrading loop interrupted by user request.")
    except (ValueError, TypeError, RuntimeError, OSError) as exc:
        print(f"Failed to start advanced trading engine: {exc}")


if __name__ == "__main__":
    main()
