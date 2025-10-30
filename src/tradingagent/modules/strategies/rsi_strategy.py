"""
RSI (相对强弱指数) 交易策略
基于RSI指标的超买超卖信号生成交易决策
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from .base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """RSI策略实现"""

    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        """
        初始化RSI策略

        Args:
            period: RSI计算周期
            oversold: 超卖阈值
            overbought: 超买阈值
        """
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.name = "RSI策略"

    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """计算RSI指标"""
        if period is None:
            period = self.period

        # 计算价格变化
        delta = prices.diff()

        # 分离上涨和下跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        signals = pd.DataFrame(index=data.index)
        signals["price"] = data["Close"]

        # 计算RSI
        signals["rsi"] = self.calculate_rsi(data["Close"], self.period)

        # 生成信号
        signals["signal"] = 0
        signals["position"] = 0

        # RSI超卖时买入信号
        signals.loc[signals["rsi"] < self.oversold, "signal"] = 1

        # RSI超买时卖出信号
        signals.loc[signals["rsi"] > self.overbought, "signal"] = -1

        # 计算持仓
        signals["position"] = (
            signals["signal"].replace(to_replace=0, method="ffill").fillna(0)
        )

        # 标记交易点
        signals["buy_signal"] = signals["signal"] == 1
        signals["sell_signal"] = signals["signal"] == -1

        return signals

    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据"""
        try:
            # 检查必要列
            required_columns = ["Open", "High", "Low", "Close", "Volume"]
            if not all(col in data.columns for col in required_columns):
                return False

            # 检查数据长度
            if len(data) < self.period + 10:
                return False

            # 检查数据质量
            if data["Close"].isnull().sum() > len(data) * 0.1:
                return False

            return True
        except Exception:
            return False

    def backtest(
        self, data: pd.DataFrame, signals: pd.DataFrame, initial_capital: float = 100000
    ) -> tuple:
        """回测策略"""
        try:
            portfolio = pd.DataFrame(index=signals.index)
            portfolio["price"] = signals["price"]
            portfolio["signal"] = signals["signal"]
            portfolio["position"] = signals["position"]

            # 初始化投资组合
            portfolio["holdings"] = 0
            portfolio["cash"] = initial_capital
            portfolio["total"] = initial_capital

            trades = []
            current_position = 0
            cash = initial_capital

            for i, (date, row) in enumerate(portfolio.iterrows()):
                price = row["price"]
                signal = row["signal"]

                if pd.isna(price) or price <= 0:
                    continue

                # 处理交易信号
                if signal == 1 and current_position <= 0:  # 买入信号
                    if cash > price:
                        shares_to_buy = int(cash * 0.95 / price)  # 95%资金买入
                        cost = shares_to_buy * price

                        if shares_to_buy > 0:
                            current_position += shares_to_buy
                            cash -= cost

                            trades.append(
                                {
                                    "date": date,
                                    "action": "BUY",
                                    "price": price,
                                    "shares": shares_to_buy,
                                    "cost": cost,
                                    "cash_after": cash,
                                    "position_after": current_position,
                                }
                            )

                elif signal == -1 and current_position > 0:  # 卖出信号
                    revenue = current_position * price
                    cash += revenue

                    trades.append(
                        {
                            "date": date,
                            "action": "SELL",
                            "price": price,
                            "shares": current_position,
                            "revenue": revenue,
                            "cash_after": cash,
                            "position_after": 0,
                        }
                    )

                    current_position = 0

                # 更新投资组合价值
                portfolio.loc[date, "holdings"] = current_position
                portfolio.loc[date, "cash"] = cash
                portfolio.loc[date, "total"] = cash + current_position * price

            # 计算投资组合价值序列
            portfolio_value = portfolio["total"]

            return portfolio_value, trades

        except Exception as e:
            self.logger.error(f"回测失败: {e}")
            return pd.Series(), []

    def calculate_performance_metrics(
        self, portfolio_value: pd.Series, trades: List[Dict]
    ) -> Dict[str, float]:
        """计算性能指标"""
        try:
            if portfolio_value.empty or len(portfolio_value) < 2:
                return self._get_empty_metrics()

            # 基础收益计算
            initial_value = portfolio_value.iloc[0]
            final_value = portfolio_value.iloc[-1]
            total_return = (final_value - initial_value) / initial_value

            # 日收益率
            returns = portfolio_value.pct_change().dropna()

            if len(returns) == 0:
                return self._get_empty_metrics()

            # 夏普比率
            if returns.std() != 0:
                sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
            else:
                sharpe_ratio = 0

            # 最大回撤
            cumulative = (1 + returns).cumprod()
            rolling_max = cumulative.expanding().max()
            drawdown = (cumulative - rolling_max) / rolling_max
            max_drawdown = drawdown.min()

            # 波动率
            volatility = returns.std() * np.sqrt(252)

            # 交易相关指标
            total_trades = len(trades)
            winning_trades = 0
            total_trade_return = 0

            if total_trades > 0:
                for i in range(0, len(trades), 2):
                    if i + 1 < len(trades):
                        buy_trade = trades[i]
                        sell_trade = trades[i + 1]

                        if (
                            buy_trade["action"] == "BUY"
                            and sell_trade["action"] == "SELL"
                        ):
                            trade_return = (
                                sell_trade["price"] - buy_trade["price"]
                            ) / buy_trade["price"]
                            total_trade_return += trade_return

                            if trade_return > 0:
                                winning_trades += 1

                win_rate = (
                    winning_trades / (total_trades // 2) if total_trades > 0 else 0
                )
                avg_trade_return = (
                    total_trade_return / (total_trades // 2) if total_trades > 0 else 0
                )
            else:
                win_rate = 0
                avg_trade_return = 0

            # 年化收益率
            trading_days = len(portfolio_value)
            years = trading_days / 252
            annualized_return = (
                (final_value / initial_value) ** (1 / years) - 1 if years > 0 else 0
            )

            # Calmar比率
            calmar_ratio = (
                annualized_return / abs(max_drawdown) if max_drawdown != 0 else 0
            )

            # Sortino比率
            negative_returns = returns[returns < 0]
            downside_deviation = negative_returns.std() * np.sqrt(252)
            sortino_ratio = (
                annualized_return / downside_deviation if downside_deviation != 0 else 0
            )

            return {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "volatility": volatility,
                "win_rate": win_rate,
                "total_trades": total_trades,
                "avg_trade_return": avg_trade_return,
                "calmar_ratio": calmar_ratio,
                "sortino_ratio": sortino_ratio,
            }

        except Exception as e:
            self.logger.error(f"性能指标计算失败: {e}")
            return self._get_empty_metrics()

    def _get_empty_metrics(self) -> Dict[str, float]:
        """返回空的性能指标"""
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "volatility": 0.0,
            "win_rate": 0.0,
            "total_trades": 0,
            "avg_trade_return": 0.0,
            "calmar_ratio": 0.0,
            "sortino_ratio": 0.0,
        }

    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数"""
        return {
            "period": self.period,
            "oversold": self.oversold,
            "overbought": self.overbought,
            "strategy_type": "RSI",
        }

    def set_parameters(self, **kwargs):
        """设置策略参数"""
        if "period" in kwargs:
            self.period = kwargs["period"]
        if "oversold" in kwargs:
            self.oversold = kwargs["oversold"]
        if "overbought" in kwargs:
            self.overbought = kwargs["overbought"]
