#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速启动交易脚本 - 用于快速测试和启动交易系统"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yfinance as yf

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent  # 向上一级到项目根目录
sys.path.insert(0, str(PROJECT_ROOT))

# pylint: disable=wrong-import-position,import-error
from src.tradingagent.modules import DataManager
from src.tradingagent.modules.risk_management import TradingRiskManager as RiskManager
from src.tradingagent.modules.strategies import MeanReversionStrategy

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("QuickTrading")


class QuickTradingEngine:
    """
    快速交易引擎 - 用于测试和演示

    提供简化的交易逻辑，适合快速测试策略和系统功能
    """

    def __init__(self, initial_capital: float = 100000) -> None:
        """
        初始化快速交易引擎

        Args:
            initial_capital (float): 初始资金，默认100,000
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # 初始化组件
        self.data_provider = DataManager()
        self.strategy = MeanReversionStrategy()
        self.risk_manager = RiskManager(
            max_position_size=0.3,  # 测试用更大仓位
            stop_loss_pct=0.03,  # 3%止损
            take_profit_pct=0.10,  # 10%止盈
            max_daily_loss=0.05,  # 5%日亏损限制
        )

        # 股票池
        self.symbols = ["AAPL", "MSFT", "GOOGL", "TSLA"]

        self.risk_manager.update_daily_capital(self.current_capital)

        logger.info("快速交易引擎初始化完成 - 初始资金: $%.2f", self.initial_capital)

    def get_price(self, symbol: str) -> float:
        """
        获取实时价格

        Args:
            symbol (str): 股票代码

        Returns:
            float: 股票价格，获取失败返回0.0
        """
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d", interval="1m")
            if not data.empty:
                return float(data["Close"].iloc[-1])
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.warning("获取 %s 价格失败: %s", symbol, str(e))
        return 0.0

    def analyze_symbol(self, symbol: str) -> dict:
        """
        分析单个股票

        Args:
            symbol (str): 股票代码

        Returns:
            dict: 包含分析结果的字典，失败时返回空字典
        """
        try:
            # 获取历史数据
            data = self.data_provider.get_historical_data(
                symbol,
                (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                datetime.now().strftime("%Y-%m-%d"),
            )

            if data is None or data.empty or len(data) < 20:
                return {}

            # 生成信号
            signals = self.strategy.generate_signals(data)

            if signals.empty:
                return {}

            latest_signal = signals.iloc[-1]
            current_price = self.get_price(symbol) or float(data["Close"].iloc[-1])

            return {
                "symbol": symbol,
                "signal": latest_signal["signal"],
                "price": current_price,
                "data": data,
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            logger.error("分析失败 %s: %s", symbol, str(e))
            return {}

    def simulate_trade(
        self, symbol: str, action: str, price: float, quantity: int
    ) -> bool:
        """
        模拟交易

        Args:
            symbol (str): 股票代码
            action (str): 交易动作 ('BUY' 或 'SELL')
            price (float): 交易价格
            quantity (int): 交易数量

        Returns:
            bool: 交易是否成功
        """
        if action == "BUY":
            cost = quantity * price * 1.001  # 包含手续费
            if cost <= self.current_capital:
                self.current_capital -= cost
                self.risk_manager.open_position(symbol, quantity, price)
                logger.info(
                    "买入成功 %s: %d股 @ $%.2f, 剩余资金: $%.2f",
                    symbol,
                    quantity,
                    price,
                    self.current_capital,
                )
                return True
        elif action == "SELL":
            position = self.risk_manager.get_position_info(symbol)
            if position and position["quantity"] > 0:
                proceeds = quantity * price * 0.999  # 扣除手续费
                self.current_capital += proceeds
                trade_record = self.risk_manager.close_position(symbol, price)
                if trade_record:
                    logger.info(
                        "卖出成功 %s: %d股 @ $%.2f, 盈亏: $%.2f, 资金: $%.2f",
                        symbol,
                        quantity,
                        price,
                        trade_record["pnl"],
                        self.current_capital,
                    )
                return True
        return False

    def _check_stop_conditions(self) -> None:
        """检查止损止盈条件"""
        positions = self.risk_manager.get_all_positions()
        for symbol in positions.items():
            current_price = self.get_price(symbol)
            if current_price > 0:
                quantity = positions[symbol]["quantity"]

                # 检查止损或止盈
                if self.risk_manager.should_stop_loss(
                    symbol, current_price
                ) or self.risk_manager.should_take_profit(symbol, current_price):
                    self.simulate_trade(symbol, "SELL", current_price, quantity)

    def _find_new_opportunities(self) -> None:
        """寻找新的交易机会"""
        for symbol in self.symbols:
            analysis = self.analyze_symbol(symbol)
            if not analysis:
                continue

            signal = analysis["signal"]
            price = analysis["price"]

            if signal == "BUY" and self.risk_manager.can_open_position(
                symbol, "BUY", self.current_capital
            ):
                quantity = self.risk_manager.calculate_position_size(
                    symbol, price, self.current_capital
                )
                if quantity > 0:
                    self.simulate_trade(symbol, "BUY", price, quantity)

    def run_analysis(self) -> None:
        """运行完整的市场分析和交易逻辑"""
        logger.info("开始市场分析...")

        # 检查持仓的止损止盈
        self._check_stop_conditions()

        # 分析新机会
        self._find_new_opportunities()

        # 显示当前状态
        self.show_status()

    def show_status(self) -> None:
        """显示当前投资组合状态和收益情况"""
        positions = self.risk_manager.get_all_positions()
        total_return = (
            self.current_capital - self.initial_capital
        ) / self.initial_capital

        logger.info("当前状态:")
        logger.info("   资金: $%.2f", self.current_capital)
        logger.info("   收益率: %.2f%%", total_return * 100)
        logger.info("   持仓: %d个", len(positions))

        if positions:
            logger.info("   持仓详情:")
            for symbol, pos in positions.items():
                current_price = self.get_price(symbol)
                if current_price > 0:
                    unrealized_pnl = (current_price - pos["entry_price"]) * pos[
                        "quantity"
                    ]
                    logger.info(
                        "     %s: %d股 @ $%.2f (现价: $%.2f, 浮盈: $%.2f)",
                        symbol,
                        pos["quantity"],
                        pos["entry_price"],
                        current_price,
                        unrealized_pnl,
                    )


def main() -> None:
    """主函数 - 启动快速交易测试"""
    logger.info("启动快速交易测试...")

    # 创建交易引擎
    engine = QuickTradingEngine()

    try:
        # 运行分析
        engine.run_analysis()

        # 如果用户想要继续监控
        while True:
            user_input = input("\n按回车继续分析，输入'q'退出: ").strip().lower()
            if user_input == "q":
                break

            engine.run_analysis()

    except KeyboardInterrupt:
        logger.info("交易测试已停止")
    except (ValueError, RuntimeError, OSError) as e:
        logger.error("运行错误: %s", str(e))

    # 最终报告
    final_return = (
        engine.current_capital - engine.initial_capital
    ) / engine.initial_capital
    logger.info(
        "最终结果: 收益率 %.2f%%, 最终资金 $%.2f",
        final_return * 100,
        engine.current_capital,
    )


if __name__ == "__main__":
    main()
