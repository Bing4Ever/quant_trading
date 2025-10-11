#!/usr/bin/env python3

import sys
import time
import schedule
import logging
from datetime import datetime, timedelta
from pathlib import Path
from config import config
from data import DataFetcher
from risk_management.risk_manager import RiskManager
from strategies.mean_reversion_strategy import MeanReversionStrategy


# 添加项目根目录到路径
project_root = Path(__file__).parent.parent  # 向上一级到项目根目录
sys.path.insert(0, str(project_root))


class AdvancedTradingEngine:
    """高级交易引擎 - 集成风险管理"""

    def __init__(self):
        """初始化交易引擎"""
        # 基础配置
        self.initial_capital = float(config.get_env("INITIAL_CAPITAL", 100000.0))
        self.current_capital = self.initial_capital
        self.paper_trading = config.get_env("PAPER_TRADING", True)

        # 初始化组件
        self.data_fetcher = DataFetcher()
        self.strategy = MeanReversionStrategy()
        self.risk_manager = RiskManager(
            max_position_size=0.2,  # 单只股票最大仓位20%
            stop_loss_pct=0.05,  # 止损5%
            take_profit_pct=0.15,  # 止盈15%
            max_daily_loss=0.02,  # 日最大亏损2%
        )

        # 交易池
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

        # 手续费
        self.commission_rate = 0.001  # 0.1%

        # 交易记录
        self.trade_history = []

        # 设置日志
        self.setup_logging()

        # 更新风险管理器的日初资金
        self.risk_manager.update_daily_capital(self.current_capital)

        self.logger.info("高级交易引擎初始化完成")
        self.logger.info("初始资金: $%.2f", self.initial_capital)
        self.logger.info("监控股票: %s", ", ".join(self.watch_list))

    def setup_logging(self):
        """设置日志"""
        # 确保logs目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        log_level = config.get_env("LOG_LEVEL", "INFO")
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler("logs/advanced_trading.log", encoding="utf-8"),
                logging.StreamHandler(),
            ],
        )
        self.logger = logging.getLogger("AdvancedTrading")

    def get_current_prices(self) -> dict:
        """获取当前价格"""
        prices = {}
        for symbol in self.watch_list:
            try:
                data = self.data_fetcher.fetch_stock_data(
                    symbol,
                    (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d"),
                )
                if not data.empty:
                    prices[symbol] = float(data["Close"].iloc[-1])
                else:
                    self.logger.warning("无法获取 %s 的价格数据", symbol)
            except (ValueError, KeyError, TypeError) as e:
                self.logger.error("获取 %s 价格失败: %s", symbol, e)

        return prices

    def analyze_market(self):
        """市场分析和信号生成"""
        signals = {}

        for symbol in self.watch_list:
            try:
                # 获取历史数据
                data = self.data_fetcher.fetch_stock_data(
                    symbol,
                    (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
                    datetime.now().strftime("%Y-%m-%d"),
                )

                if data.empty or len(data) < 20:
                    continue

                # 生成交易信号
                strategy_signals = self.strategy.generate_signals(data)

                if not strategy_signals.empty:
                    latest_signal = strategy_signals.iloc[-1]
                    signals[symbol] = {
                        "action": latest_signal["Signal"],
                        "price": float(data["Close"].iloc[-1]),
                        "confidence": abs(latest_signal.get("Confidence", 0.5)),
                    }

            except (ValueError, KeyError, TypeError) as e:
                self.logger.error("分析 %s 失败: %s", symbol, e)

        return signals

    def execute_trade(self, symbol: str, action: str, price: float) -> bool:
        """执行交易"""
        try:
            if not self.risk_manager.can_open_position(symbol, action, self.current_capital):
                return False

            if action == "BUY":
                return self._execute_buy(symbol, price)
            elif action == "SELL":
                return self._execute_sell(symbol, price)
            else:
                self.logger.warning("未知交易动作: %s", action)
                return False
        except (ValueError, KeyError, TypeError) as e:
            self.logger.error("执行交易失败 %s %s: %s", symbol, action, e)
            return False

    def _execute_buy(self, symbol: str, price: float) -> bool:
        """辅助方法: 执行买入逻辑"""
        quantity = self.risk_manager.calculate_position_size(symbol, price, self.current_capital)
        if quantity <= 0:
            return False

        trade_value = quantity * price
        commission = trade_value * self.commission_rate
        total_cost = trade_value + commission

        if total_cost > self.current_capital:
            self.logger.warning("资金不足，无法买入 %s", symbol)
            return False

        if self.paper_trading:
            self.logger.info("[模拟] 买入 %s: %d股 @ $%.2f", symbol, quantity, price)
        else:
            self.logger.info("[实盘] 买入 %s: %d股 @ $%.2f", symbol, quantity, price)

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
        """辅助方法: 执行卖出逻辑"""
        position_info = self.risk_manager.get_position_info(symbol)
        if not position_info or position_info["quantity"] <= 0:
            return False

        quantity = position_info["quantity"]
        trade_value = quantity * price
        commission = trade_value * self.commission_rate
        net_proceeds = trade_value - commission

        if self.paper_trading:
            self.logger.info("[模拟] 卖出 %s: %d股 @ $%.2f", symbol, quantity, price)
        else:
            self.logger.info("[实盘] 卖出 %s: %d股 @ $%.2f", symbol, quantity, price)

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
                "pnl": trade_record["pnl"] if trade_record else 0,
            }
        )
        return True

    def risk_check(self):
        """风险检查和止损止盈"""
        current_prices = self.get_current_prices()

        for symbol in self.risk_manager.get_all_positions().keys():
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]

            # 检查止损
            if self.risk_manager.should_stop_loss(symbol, current_price):
                self.logger.warning("触发止损: %s", symbol)
                self.execute_trade(symbol, "SELL", current_price)
                continue

            # 检查止盈
            if self.risk_manager.should_take_profit(symbol, current_price):
                self.logger.info("触发止盈: %s", symbol)
                self.execute_trade(symbol, "SELL", current_price)

    def scan_and_trade(self):
        """市场扫描和交易执行"""
        try:
            self.logger.info("开始市场扫描...")

            # 风险检查
            self.risk_check()

            # 检查日亏损限制
            if self.risk_manager.check_daily_loss_limit(self.current_capital):
                self.logger.error("触发日亏损限制，停止交易")
                return

            # 市场分析
            signals = self.analyze_market()

            # 执行交易
            for symbol, signal_info in signals.items():
                action = signal_info["action"]
                price = signal_info["price"]
                confidence = signal_info["confidence"]

                # 只有高置信度的信号才执行
                if confidence > 0.6:
                    if action in ["BUY", "SELL"]:
                        self.execute_trade(symbol, action, price)

        except (ValueError, KeyError, TypeError) as e:
            self.logger.error("市场扫描失败: %s", e)

    def generate_daily_report(self):
        """生成日报"""
        try:
            # 计算当日表现
            daily_return = (
                self.current_capital - self.initial_capital
            ) / self.initial_capital

            # 获取持仓信息
            positions = self.risk_manager.get_all_positions()
            current_prices = self.get_current_prices()

            # 计算投资组合风险
            portfolio_risk = self.risk_manager.calculate_portfolio_risk(
                current_prices, self.current_capital
            )

            # 获取当日交易
            daily_trades = self.risk_manager.get_daily_trades()

            self.logger.info("=" * 50)
            self.logger.info("日报总结")
            self.logger.info("=" * 50)
            self.logger.info("当前资金: $%.2f", self.current_capital)
            self.logger.info("总收益率: %.2f%%", daily_return * 100)
            self.logger.info("持仓数量: %d", len(positions))
            self.logger.info("今日交易: %d笔", len(daily_trades))
            self.logger.info("总敞口: $%.2f", portfolio_risk['total_exposure'])
            self.logger.info("敞口比率: %.1f%%", portfolio_risk['exposure_ratio'] * 100)

            # 持仓详情
            if positions:
                self.logger.info("\n持仓详情:")
                for symbol, position in positions.items():
                    if symbol in current_prices:
                        current_price = current_prices[symbol]
                        unrealized_pnl = (
                            current_price - position["entry_price"]
                        ) * position["quantity"]
                        self.logger.info(
                            "  %s: %d股 @ $%.2f (现价: $%.2f, 浮盈: $%.2f)",
                            symbol,
                            position["quantity"],
                            position["entry_price"],
                            current_price,
                            unrealized_pnl
                        )

        except (ValueError, KeyError, TypeError) as e:
            self.logger.error("生成日报失败: %s", e)

    def start_trading(self):
        """启动交易"""
        self.logger.info("启动量化交易系统...")

        # 设置定时任务
        schedule.every().hour.do(self.scan_and_trade)  # 每小时扫描
        schedule.every().day.at("09:30").do(
            lambda: self.risk_manager.update_daily_capital(self.current_capital)
        )  # 每日更新资金
        schedule.every().day.at("16:00").do(self.generate_daily_report)  # 每日报告

        # 立即执行一次
        self.scan_and_trade()
        self.generate_daily_report()

        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("交易系统已停止")
        except (ValueError, TypeError, RuntimeError, OSError) as e:
            self.logger.error("交易系统异常: %s", e)

def main():
    """主函数"""
    try:
        # 初始化交易引擎
        engine = AdvancedTradingEngine()

        # 启动交易
        engine.start_trading()

    except KeyboardInterrupt:
        print("\n交易系统已手动停止")
    except (ValueError, TypeError, RuntimeError, OSError) as e:
        print("系统启动失败: %s", e)

if __name__ == "__main__":
    main()
