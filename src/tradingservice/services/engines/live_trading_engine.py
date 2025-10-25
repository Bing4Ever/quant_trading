#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""实时交易引擎 - 提供实时市场扫描和交易功能"""

import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import schedule
from src.tradingagent.modules import DataManager
from src.tradingagent.modules.strategies import MeanReversionStrategy
from src.tradingagent import BacktestEngine
from src.tradingservice.services.analysis import PerformanceAnalyzer
from src.tradingagent.core.interfaces import IBroker
from config import config

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent  # 向上一级到项目根目录
sys.path.insert(0, str(PROJECT_ROOT))




class LiveTradingEngine:
    """
    实时交易引擎
    
    提供市场扫描、信号生成、交易执行和投资组合管理功能
    """

    def __init__(self):
        """初始化交易引擎"""
        self.setup_logging()
        self.data_provider = DataManager()
        self.strategy = MeanReversionStrategy()
        self.initial_capital = float(config.get_env("INITIAL_CAPITAL", 100000.0))
        self.current_capital = self.initial_capital
        self.positions = {}  # {symbol: quantity}
        self.commission_rate = 0.001  # 0.1%手续费
        self.paper_trading = config.get_env("PAPER_TRADING", True)

        # 交易标的池
        self.symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]

        self.logger.info("交易引擎初始化完成 - 模拟交易: %s", self.paper_trading)
        self.logger.info("初始资金: $%.2f", self.initial_capital)

    def setup_logging(self):
        """设置日志"""
        log_level = config.get_env("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/trading.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("LiveTrading")

    def get_latest_data(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """
        获取最新数据
        
        Args:
            symbol (str): 股票代码
            days (int): 获取天数，默认60天
            
        Returns:
            pd.DataFrame: 股票数据
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            data = self.data_provider.get_historical_data(
                symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
            return data if data is not None else pd.DataFrame()
        except (ValueError, KeyError, AttributeError, TypeError) as e:
            self.logger.error("获取 %s 数据失败: %s", symbol, e)
            return pd.DataFrame()

    def analyze_symbol(self, symbol: str) -> dict:
        """
        分析单个股票
        
        Args:
            symbol (str): 股票代码
            
        Returns:
            dict: 包含分析结果的字典
        """
        try:
            # 获取数据
            data = self.get_latest_data(symbol)
            if data.empty:
                return {"symbol": symbol, "signal": 0, "action": "HOLD"}

            # 生成信号
            signals = self.strategy.generate_signals(data)
            latest_signal = signals["signal"].iloc[-1] if not signals.empty else 0
            latest_price = data["close"].iloc[-1]

            # 确定交易行为
            action = "HOLD"
            if latest_signal == 1:
                action = "BUY"
            elif latest_signal == -1:
                action = "SELL"

            return {
                "symbol": symbol,
                "price": latest_price,
                "signal": latest_signal,
                "action": action,
                "data": data,
                "signals": signals,
            }

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            self.logger.error("分析 %s 失败: %s", symbol, e)
            return {"symbol": symbol, "signal": 0, "action": "HOLD"}

    def calculate_position_size(self, price: float) -> int:
        """
        计算仓位大小
        
        Args:
            price (float): 股票价格
            
        Returns:
            int: 应购买的股数
        """
        max_position_value = self.current_capital * 0.2  # 单只股票最大20%仓位
        shares = int(max_position_value / price)
        return max(shares, 0)

    def execute_trade(
        self, symbol: str, action: str, price: float, quantity: int = None
    ):
        """
        执行交易
        
        Args:
            symbol (str): 股票代码
            action (str): 交易动作 ('BUY', 'SELL', 'HOLD')
            price (float): 交易价格
            quantity (int, optional): 交易数量
        """
        if action == "HOLD":
            return

        current_position = self.positions.get(symbol, 0)

        if action == "BUY" and current_position <= 0:
            if quantity is None:
                quantity = self.calculate_position_size(price)
            if quantity > 0:
                cost = quantity * price * (1 + self.commission_rate)
                if cost <= self.current_capital:
                    self.positions[symbol] = quantity
                    self.current_capital -= cost
                    self.logger.info(
                        "买入 %s: %d股 @ $%.2f, 成本: $%.2f",
                        symbol, quantity, price, cost
                    )

        elif action == "SELL" and current_position > 0:
            quantity = current_position
            proceeds = quantity * price * (1 - self.commission_rate)
            self.positions[symbol] = 0
            self.current_capital += proceeds
            self.logger.info(
                "卖出 %s: %d股 @ $%.2f, 收入: $%.2f",
                symbol, quantity, price, proceeds
            )

    def scan_market(self):
        """扫描市场并执行交易"""
        self.logger.info("开始市场扫描...")

        for symbol in self.symbols:
            try:
                analysis = self.analyze_symbol(symbol)

                self.logger.info(
                    "%s: 价格=$%.2f, 信号=%d, 行动=%s",
                    symbol,
                    analysis.get("price", 0),
                    analysis.get("signal", 0),
                    analysis.get("action", "HOLD"),
                )

                if self.paper_trading:
                    self.execute_trade(
                        symbol, analysis["action"], analysis.get("price", 0)
                    )

            except (ValueError, KeyError, AttributeError, TypeError) as e:
                self.logger.error("处理 %s 时出错: %s", symbol, e)

        # 显示当前状态
        self.show_portfolio_status()

    def show_portfolio_status(self):
        """显示投资组合状态"""
        total_value = self.current_capital

        for symbol, quantity in self.positions.items():
            if quantity > 0:
                try:
                    latest_data = self.get_latest_data(symbol, 1)
                    if not latest_data.empty:
                        current_price = latest_data["close"].iloc[-1]
                        position_value = quantity * current_price
                        total_value += position_value
                        self.logger.info(
                            "持仓 %s: %d股 @ $%.2f = $%.2f",
                            symbol,
                            quantity,
                            current_price,
                            position_value,
                        )
                except (ValueError, KeyError, AttributeError, TypeError):
                    pass

        profit_loss = total_value - self.initial_capital
        profit_pct = (profit_loss / self.initial_capital) * 100

        self.logger.info("投资组合总价值: $%.2f", total_value)
        self.logger.info("盈亏: $%.2f (%.2f%%)", profit_loss, profit_pct)
        self.logger.info("-" * 50)

    def run_backtest_analysis(self, symbol: str = "AAPL"):
        """运行回测分析"""
        self.logger.info("开始 %s 回测分析...", symbol)

        try:
            # 获取更长期的历史数据
            data = self.get_latest_data(symbol, 365)
            if data.empty:
                self.logger.error("无法获取历史数据")
                return

            # 运行回测
            engine = BacktestEngine(initial_capital=100000)
            results = engine.run_backtest(self.strategy, data)

            # 生成报告
            returns = pd.Series(engine.daily_returns)
            analyzer = PerformanceAnalyzer(returns)
            report = analyzer.generate_report()

            self.logger.info("\n%s 回测报告:\n%s", symbol, report)

            return results

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            self.logger.error("回测分析失败: %s", e)
            return None


def display_menu():
    """显示主菜单"""
    menu_separator = "=" * 60
    print(f"\n{menu_separator}")
    print("🚀 量化交易系统已启动")
    print(menu_separator)
    print("选项:")
    print("1. 运行一次市场扫描")
    print("2. 启动定时任务（每小时扫描一次）")
    print("3. 查看投资组合状态")
    print("4. 运行回测分析")
    print("5. 退出")
    print(menu_separator)


def handle_choice(choice: str, trading_engine: LiveTradingEngine) -> bool:
    """
    处理用户选择
    
    Args:
        choice (str): 用户输入的选择
        trading_engine (LiveTradingEngine): 交易引擎实例
        
    Returns:
        bool: 是否继续运行程序
    """
    if choice == "1":
        trading_engine.scan_market()
    elif choice == "2":
        print("启动定时任务...")
        schedule.every().hour.do(trading_engine.scan_market)
        print("定时任务已启动，每小时扫描一次市场")
        print("按 Ctrl+C 停止")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n定时任务已停止")
    elif choice == "3":
        trading_engine.show_portfolio_status()
    elif choice == "4":
        symbol = input("请输入股票代码 (默认AAPL): ").strip().upper()
        if not symbol:
            symbol = "AAPL"
        trading_engine.run_backtest_analysis(symbol)
    elif choice == "5":
        print("再见！")
        return False
    else:
        print("无效选择，请重新输入")
    return True


def main():
    """主函数 - 启动实时交易引擎"""
    os.makedirs("logs", exist_ok=True)
    trading_engine = LiveTradingEngine()
    trading_engine.run_backtest_analysis("AAPL")
    display_menu()

    running = True
    while running:
        try:
            choice = input("\n请选择操作 (1-5): ").strip()
            running = handle_choice(choice, trading_engine)
        except KeyboardInterrupt:
            print("\n程序已停止")
            break
        except ValueError as ve:
            print("输入错误: %s", ve)
        except RuntimeError as re:
            print("运行时错误: %s", re)


if __name__ == "__main__":
    main()
