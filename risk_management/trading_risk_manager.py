"""
交易风险管理工具模块，适用于实时交易引擎。

本模块提供轻量级的实时风险控制功能，包括：
- 仓位大小和限制
- 止损和止盈检查
- 日亏损限制和简单的交易记录

适用场景：`advanced_trading_engine.py`、`quick_trading_engine.py` 以及其他需要在执行过程中进行即时风险决策的模块。
"""

from typing import Dict, Optional
from datetime import datetime
import logging


class RiskManager:
    """风险管理器"""

    def __init__(self,
                 max_position_size: float = 0.2,
                 stop_loss_pct: float = 0.05,
                 take_profit_pct: float = 0.15,
                 max_daily_loss: float = 0.02) -> None:
        """
        初始化风险管理器

        Args:
            max_position_size: 单只股票最大仓位比例
            stop_loss_pct: 止损百分比
            take_profit_pct: 止盈百分比
            max_daily_loss: 日最大亏损比例
        """
        self.max_position_size = max_position_size
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_daily_loss = max_daily_loss

        self.logger = logging.getLogger('RiskManager')

        # 跟踪数据
        self.positions: Dict[str, Dict] = {}
        self.daily_start_capital = 0.0
        self.daily_trades: list = []

    def update_daily_capital(self, capital: float) -> None:
        """更新日初资金"""
        self.daily_start_capital = capital
        self.daily_trades = []

    def calculate_position_size(self, symbol: str, price: float, total_capital: float) -> int:
        """
        计算建议仓位大小

        Args:
            symbol: 股票代码
            price: 当前价格
            total_capital: 总资金

        Returns:
            建议购买股数
        """
        max_investment = total_capital * self.max_position_size
        shares = int(max_investment / price)

        self.logger.info("仓位计算 %s: %d股 (投资额: $%.2f / 价格: $%.2f)",
                        symbol, shares, max_investment, price)
        return max(shares, 0)

    def should_stop_loss(self, symbol: str, current_price: float) -> bool:
        """
        检查是否应该止损

        Args:
            symbol: 股票代码
            current_price: 当前价格

        Returns:
            是否应该止损
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        entry_price = position['entry_price']

        if position['quantity'] > 0:  # 多头持仓
            loss_pct = (current_price - entry_price) / entry_price
            if loss_pct <= -self.stop_loss_pct:
                self.logger.warning("止损触发 %s: 亏损%.2f%% (阈值%.2f%%)",
                                  symbol, loss_pct * 100, self.stop_loss_pct * 100)
                return True

        elif position['quantity'] < 0:  # 空头持仓
            loss_pct = (entry_price - current_price) / entry_price
            if loss_pct <= -self.stop_loss_pct:
                self.logger.warning("空头止损触发 %s: 亏损%.2f%%", symbol, loss_pct * 100)
                return True

        return False

    def should_take_profit(self, symbol: str, current_price: float) -> bool:
        """
        检查是否应该止盈

        Args:
            symbol: 股票代码
            current_price: 当前价格

        Returns:
            是否应该止盈
        """
        if symbol not in self.positions:
            return False

        position = self.positions[symbol]
        entry_price = position['entry_price']

        if position['quantity'] > 0:  # 多头持仓
            profit_pct = (current_price - entry_price) / entry_price
            if profit_pct >= self.take_profit_pct:
                self.logger.info("止盈触发 %s: 盈利%.2f%% (阈值%.2f%%)",
                               symbol, profit_pct * 100, self.take_profit_pct * 100)
                return True

        elif position['quantity'] < 0:  # 空头持仓
            profit_pct = (entry_price - current_price) / entry_price
            if profit_pct >= self.take_profit_pct:
                self.logger.info("空头止盈触发 %s: 盈利%.2f%%", symbol, profit_pct * 100)
                return True

        return False

    def check_daily_loss_limit(self, current_capital: float) -> bool:
        """
        检查是否超过日亏损限制

        Args:
            current_capital: 当前资金

        Returns:
            是否超过限制
        """
        if self.daily_start_capital <= 0:
            return False

        daily_loss = (self.daily_start_capital - current_capital) / self.daily_start_capital

        if daily_loss >= self.max_daily_loss:
            self.logger.error("日亏损限制触发: 亏损%.2f%% (限制%.2f%%)",
                            daily_loss * 100, self.max_daily_loss * 100)
            return True

        return False

    def can_open_position(self, symbol: str, action: str, total_capital: float) -> bool:
        """
        检查是否可以开仓

        Args:
            symbol: 股票代码
            action: 交易动作 (BUY/SELL)
            total_capital: 总资金

        Returns:
            是否可以开仓
        """
        # 检查日亏损限制
        if self.check_daily_loss_limit(total_capital):
            self.logger.warning("日亏损限制阻止开仓 %s", symbol)
            return False

        # 检查是否已有反向持仓
        if symbol in self.positions:
            current_qty = self.positions[symbol]['quantity']
            if (action == 'BUY' and current_qty < 0) or (action == 'SELL' and current_qty > 0):
                self.logger.info("存在反向持仓 %s，将平仓后开新仓", symbol)
                return True
            if current_qty != 0:
                self.logger.warning("已有同向持仓 %s，拒绝重复开仓", symbol)
                return False

        return True

    def open_position(self, symbol: str, quantity: int, price: float) -> None:
        """
        开仓记录

        Args:
            symbol: 股票代码
            quantity: 数量 (正数为多头，负数为空头)
            price: 开仓价格
        """
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': price,
            'entry_time': datetime.now()
        }

        direction = "多头" if quantity > 0 else "空头"
        self.logger.info("开仓记录 %s: %s %d股 @ $%.2f", symbol, direction, abs(quantity), price)

    def close_position(self, symbol: str, exit_price: float) -> Optional[Dict]:
        """
        平仓记录

        Args:
            symbol: 股票代码
            exit_price: 平仓价格

        Returns:
            交易记录
        """
        if symbol not in self.positions:
            return None

        position = self.positions[symbol]
        entry_price = position['entry_price']
        quantity = position['quantity']

        # 计算盈亏
        if quantity > 0:  # 多头
            pnl = (exit_price - entry_price) * quantity
        else:  # 空头
            pnl = (entry_price - exit_price) * abs(quantity)

        pnl_pct = pnl / (entry_price * abs(quantity))

        trade_record = {
            'symbol': symbol,
            'quantity': quantity,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': position['entry_time'],
            'exit_time': datetime.now()
        }

        # 记录交易
        self.daily_trades.append(trade_record)

        # 删除持仓记录
        del self.positions[symbol]

        direction = "多头" if quantity > 0 else "空头"
        self.logger.info("平仓记录 %s: %s %d股 @ $%.2f, 盈亏: $%.2f (%.2f%%)",
                        symbol, direction, abs(quantity), exit_price, pnl, pnl_pct * 100)

        return trade_record

    def get_position_info(self, symbol: str) -> Optional[Dict]:
        """获取持仓信息"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> Dict:
        """获取所有持仓"""
        return self.positions.copy()

    def get_daily_trades(self) -> list:
        """获取当日交易记录"""
        return self.daily_trades.copy()

    def calculate_portfolio_risk(self, current_prices: Dict[str, float], total_capital: float) -> Dict:
        """
        计算投资组合风险指标

        Args:
            current_prices: 当前价格字典 {symbol: price}
            total_capital: 总资金

        Returns:
            风险指标字典
        """
        total_exposure = 0.0
        position_risks = {}

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                current_price = current_prices[symbol]
                position_value = abs(position['quantity']) * current_price
                total_exposure += position_value

                # 计算单个持仓风险
                entry_price = position['entry_price']
                unrealized_pnl = (current_price - entry_price) * position['quantity']
                unrealized_pnl_pct = unrealized_pnl / (entry_price * abs(position['quantity']))

                position_risks[symbol] = {
                    'exposure': position_value,
                    'exposure_pct': position_value / total_capital,
                    'unrealized_pnl': unrealized_pnl,
                    'unrealized_pnl_pct': unrealized_pnl_pct
                }

        portfolio_risk = {
            'total_exposure': total_exposure,
            'exposure_ratio': total_exposure / total_capital if total_capital > 0 else 0,
            'position_count': len(self.positions),
            'position_risks': position_risks
        }

        return portfolio_risk
