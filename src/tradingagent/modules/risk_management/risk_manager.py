#!/usr/bin/env python3
"""
企业级风险监控管理系统 - 综合风险分析和监控

此模块提供企业级的风险管理功能，包括：
- 实时风险监控和警报系统
- VaR (Value at Risk) 计算
- 投资组合风险分析 (夏普比率、Beta值、相关性)
- 多层次风险警报 (CRITICAL/HIGH/MEDIUM/LOW)
- 历史数据分析和风险回测
- 集中度风险和最大回撤监控

适用场景：
- 投资组合风险监控
- 企业级风险报告
- 监管合规检查
- 风险管理仪表板
- 高级风险分析系统

注意：此模块专注于监控和分析，不用于实时交易决策。
      实时交易风险控制请使用 trading_risk_manager.py
"""

import time
import threading
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple, Callable

import numpy as np

from src.common.logger import TradingLogger
from src.common.notification import NotificationManager


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(Enum):
    """风险类型"""
    POSITION_SIZE = "position_size"
    CONCENTRATION = "concentration"
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    CORRELATION = "correlation"
    VAR = "var"  # Value at Risk
    LEVERAGE = "leverage"


@dataclass
class RiskAlert:
    """风险警报"""
    timestamp: datetime
    risk_type: RiskType
    level: RiskLevel
    symbol: str
    message: str
    current_value: float
    threshold: float
    action_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'risk_type': self.risk_type.value,
            'level': self.level.value,
            'symbol': self.symbol,
            'message': self.message,
            'current_value': self.current_value,
            'threshold': self.threshold,
            'action_required': self.action_required
        }


@dataclass
class PositionLimits:
    """持仓限制"""
    max_position_value: float = 50000.0      # 单个持仓最大价值
    max_portfolio_concentration: float = 0.2  # 单个持仓占总资产比例上限
    max_sector_concentration: float = 0.3     # 单个行业占总资产比例上限
    max_daily_loss: float = 0.05             # 单日最大亏损比例
    max_total_exposure: float = 1.0          # 总敞口比例（1.0 = 100%资金）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'max_position_value': self.max_position_value,
            'max_portfolio_concentration': self.max_portfolio_concentration,
            'max_sector_concentration': self.max_sector_concentration,
            'max_daily_loss': self.max_daily_loss,
            'max_total_exposure': self.max_total_exposure
        }


@dataclass
class RiskMetrics:
    """风险指标"""
    portfolio_value: float = 0.0
    daily_pnl: float = 0.0
    total_exposure: float = 0.0
    max_drawdown: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    var_95: float = 0.0  # 95% VaR
    var_99: float = 0.0  # 99% VaR
    beta: float = 1.0
    correlation_risk: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'portfolio_value': self.portfolio_value,
            'daily_pnl': self.daily_pnl,
            'total_exposure': self.total_exposure,
            'max_drawdown': self.max_drawdown,
            'volatility': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'var_95': self.var_95,
            'var_99': self.var_99,
            'beta': self.beta,
            'correlation_risk': self.correlation_risk
        }


class RiskCalculator:
    """风险计算器"""

    def __init__(self):
        self.logger = TradingLogger(__name__)

    def calculate_portfolio_var(self, returns: List[float], confidence: float = 0.95) -> float:
        """计算投资组合VaR"""
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        return float(np.percentile(returns_array, (1 - confidence) * 100))

    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """计算最大回撤"""
        if not portfolio_values or len(portfolio_values) < 2:
            return 0.0

        values = np.array(portfolio_values)
        peak = np.maximum.accumulate(values)
        drawdown = (values - peak) / peak
        return float(np.min(drawdown))

    def calculate_volatility(self, returns: List[float], annualized: bool = True) -> float:
        """计算波动率"""
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        vol = np.std(returns_array)

        if annualized:
            # 假设252个交易日
            vol *= np.sqrt(252)

        return float(vol)

    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """计算夏普比率"""
        if not returns or len(returns) < 2:
            return 0.0

        returns_array = np.array(returns)
        excess_returns = returns_array - (risk_free_rate / 252)  # 日收益率

        if np.std(excess_returns) == 0:
            return 0.0

        return float(np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252))

    def calculate_beta(self, stock_returns: List[float], market_returns: List[float]) -> float:
        """计算Beta值"""
        if not stock_returns or not market_returns or len(stock_returns) != len(market_returns):
            return 1.0

        stock_array = np.array(stock_returns)
        market_array = np.array(market_returns)

        covariance = np.cov(stock_array, market_array)[0][1]
        market_variance = np.var(market_array)

        if market_variance == 0:
            return 1.0

        return float(covariance / market_variance)

    def calculate_concentration_risk(self, positions: Dict[str, float], total_value: float) -> float:
        """计算集中度风险"""
        if not positions or total_value <= 0:
            return 0.0

        weights = [pos_value / total_value for pos_value in positions.values()]
        # 使用赫芬达尔指数衡量集中度
        hhi = sum(w**2 for w in weights)
        return float(hhi)


@dataclass
class HistoricalData:
    """历史数据存储"""
    portfolio_history: Optional[List[float]] = None
    returns_history: Optional[List[float]] = None
    daily_pnl_history: Optional[List[float]] = None

    def __post_init__(self):
        if self.portfolio_history is None:
            self.portfolio_history = []
        if self.returns_history is None:
            self.returns_history = []
        if self.daily_pnl_history is None:
            self.daily_pnl_history = []


class RiskMonitor:
    """风险监控器"""

    def __init__(self, limits: PositionLimits):
        self.logger = TradingLogger(__name__)
        self.notification_manager = NotificationManager()
        self.limits = limits
        self.calculator = RiskCalculator()

        # 历史数据存储
        self.historical_data = HistoricalData()

        # 当前风险状态
        self.current_alerts: List[RiskAlert] = []
        self.risk_metrics = RiskMetrics()

        # 监控标志
        self.is_monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """开始风险监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self.logger.log_system_event("风险监控启动", "")

        # 发送通知
        self.notification_manager.send_notification(
            "🛡️ 风险监控系统已启动",
            "风险监控启动"
        )

    def stop_monitoring(self):
        """停止风险监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)

        self.logger.log_system_event("风险监控停止", "")

        # 发送通知
        self.notification_manager.send_notification(
            "⏹️ 风险监控系统已停止",
            "风险监控停止"
        )

    def update_portfolio_data(self, portfolio_value: float, positions: Dict[str, float]):
        """更新投资组合数据"""
        # 更新历史数据
        if self.historical_data.portfolio_history:
            last_value = self.historical_data.portfolio_history[-1]
            daily_return = (portfolio_value - last_value) / last_value
            self.historical_data.returns_history.append(daily_return)

            daily_pnl = portfolio_value - last_value
            self.historical_data.daily_pnl_history.append(daily_pnl)

        self.historical_data.portfolio_history.append(portfolio_value)

        # 更新风险指标
        self._update_risk_metrics(portfolio_value, positions)

        # 检查风险
        self._check_all_risks(portfolio_value, positions)

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 检查当前风险状态
                self._process_alerts()

                # 等待1分钟
                time.sleep(60)

            except Exception as e:
                self.logger.log_error("风险监控异常", str(e))

    def _update_risk_metrics(self, portfolio_value: float, positions: Dict[str, float]):
        """更新风险指标"""
        self.risk_metrics.portfolio_value = portfolio_value

        if self.historical_data.daily_pnl_history:
            self.risk_metrics.daily_pnl = self.historical_data.daily_pnl_history[-1]

        # 计算总敞口
        if portfolio_value > 0:
            self.risk_metrics.total_exposure = sum(positions.values()) / portfolio_value
        else:
            self.risk_metrics.total_exposure = 0

        # 计算最大回撤
        if len(self.historical_data.portfolio_history) >= 2:
            max_drawdown = self.calculator.calculate_max_drawdown(
                self.historical_data.portfolio_history)
            self.risk_metrics.max_drawdown = max_drawdown

        # 计算波动率
        if len(self.historical_data.returns_history) >= 10:
            returns_data = self.historical_data.returns_history
            self.risk_metrics.volatility = self.calculator.calculate_volatility(returns_data)
            self.risk_metrics.sharpe_ratio = self.calculator.calculate_sharpe_ratio(returns_data)
            self.risk_metrics.var_95 = self.calculator.calculate_portfolio_var(returns_data, 0.95)
            self.risk_metrics.var_99 = self.calculator.calculate_portfolio_var(returns_data, 0.99)

        # 计算集中度风险
        concentration_risk = self.calculator.calculate_concentration_risk(positions, portfolio_value)
        self.risk_metrics.correlation_risk = concentration_risk

    def _check_all_risks(self, portfolio_value: float, positions: Dict[str, float]):
        """检查所有风险"""
        # 清除旧警报
        self.current_alerts.clear()

        # 检查持仓大小风险
        self._check_position_size_risk(positions)

        # 检查集中度风险
        self._check_concentration_risk(positions, portfolio_value)

        # 检查回撤风险
        self._check_drawdown_risk()

        # 检查日损失风险
        self._check_daily_loss_risk(portfolio_value)

        # 检查波动率风险
        self._check_volatility_risk()

        # 检查VaR风险
        self._check_var_risk()

    def _check_position_size_risk(self, positions: Dict[str, float]):
        """检查持仓大小风险"""
        for symbol, position_value in positions.items():
            if position_value > self.limits.max_position_value:
                alert = RiskAlert(
                    timestamp=datetime.now(),
                    risk_type=RiskType.POSITION_SIZE,
                    level=RiskLevel.HIGH,
                    symbol=symbol,
                    message=(f"Position size exceeds limit: ${position_value:,.2f} > "
                             f"${self.limits.max_position_value:,.2f}"),
                    current_value=position_value,
                    threshold=self.limits.max_position_value,
                    action_required=True
                )
                self.current_alerts.append(alert)

    def _check_concentration_risk(self, positions: Dict[str, float], portfolio_value: float):
        """检查集中度风险"""
        if portfolio_value <= 0:
            return

        for symbol, position_value in positions.items():
            concentration = position_value / portfolio_value

            if concentration > self.limits.max_portfolio_concentration:
                level = RiskLevel.CRITICAL if concentration > 0.5 else RiskLevel.HIGH

                alert = RiskAlert(
                    timestamp=datetime.now(),
                    risk_type=RiskType.CONCENTRATION,
                    level=level,
                    symbol=symbol,
                    message=(f"Portfolio concentration too high: {concentration:.1%} > "
                             f"{self.limits.max_portfolio_concentration:.1%}"),
                    current_value=concentration,
                    threshold=self.limits.max_portfolio_concentration,
                    action_required=concentration > 0.3
                )
                self.current_alerts.append(alert)

    def _check_drawdown_risk(self):
        """检查回撤风险"""
        if self.risk_metrics.max_drawdown < -0.15:  # 15%回撤阈值
            level = RiskLevel.CRITICAL if self.risk_metrics.max_drawdown < -0.25 else RiskLevel.HIGH

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.DRAWDOWN,
                level=level,
                symbol="PORTFOLIO",
                message=f"Maximum drawdown: {self.risk_metrics.max_drawdown:.2%}",
                current_value=abs(self.risk_metrics.max_drawdown),
                threshold=0.15,
                action_required=self.risk_metrics.max_drawdown < -0.20
            )
            self.current_alerts.append(alert)

    def _check_daily_loss_risk(self, portfolio_value: float):
        """检查日损失风险"""
        if not self.historical_data.daily_pnl_history:
            return

        last_pnl = self.historical_data.daily_pnl_history[-1]
        daily_loss_pct = abs(last_pnl) / portfolio_value if portfolio_value > 0 else 0

        if daily_loss_pct > self.limits.max_daily_loss:
            level = RiskLevel.CRITICAL if daily_loss_pct > 0.10 else RiskLevel.HIGH

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.DRAWDOWN,
                level=level,
                symbol="PORTFOLIO",
                message=(f"Daily loss exceeds limit: {daily_loss_pct:.2%} > "
                         f"{self.limits.max_daily_loss:.2%}"),
                current_value=daily_loss_pct,
                threshold=self.limits.max_daily_loss,
                action_required=daily_loss_pct > 0.08
            )
            self.current_alerts.append(alert)

    def _check_volatility_risk(self):
        """检查波动率风险"""
        if self.risk_metrics.volatility > 0.40:  # 40%年化波动率阈值
            level = RiskLevel.HIGH if self.risk_metrics.volatility > 0.60 else RiskLevel.MEDIUM

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.VOLATILITY,
                level=level,
                symbol="PORTFOLIO",
                message=f"Portfolio volatility high: {self.risk_metrics.volatility:.1%}",
                current_value=self.risk_metrics.volatility,
                threshold=0.40,
                action_required=self.risk_metrics.volatility > 0.60
            )
            self.current_alerts.append(alert)

    def _check_var_risk(self):
        """检查VaR风险"""
        if abs(self.risk_metrics.var_95) > 0.05:  # 5% VaR阈值
            level = RiskLevel.HIGH if abs(self.risk_metrics.var_95) > 0.08 else RiskLevel.MEDIUM

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.VAR,
                level=level,
                symbol="PORTFOLIO",
                message=f"95% VaR: {self.risk_metrics.var_95:.2%}",
                current_value=abs(self.risk_metrics.var_95),
                threshold=0.05,
                action_required=abs(self.risk_metrics.var_95) > 0.08
            )
            self.current_alerts.append(alert)

    def _process_alerts(self):
        """处理风险警报"""
        critical_alerts = [alert for alert in self.current_alerts if alert.level == RiskLevel.CRITICAL]
        high_alerts = [alert for alert in self.current_alerts if alert.level == RiskLevel.HIGH]

        # 发送关键风险通知
        for alert in critical_alerts:
            self.logger.log_risk_event("CRITICAL", alert.symbol, alert.message)

            self.notification_manager.send_notification(
                f"🚨 CRITICAL RISK ALERT\n"
                f"Symbol: {alert.symbol}\n"
                f"Type: {alert.risk_type.value}\n"
                f"Message: {alert.message}",
                f"CRITICAL Risk - {alert.symbol}"
            )

        # 发送高风险通知
        for alert in high_alerts:
            self.logger.log_risk_event("HIGH", alert.symbol, alert.message)

    def get_risk_summary(self) -> Dict[str, Any]:
        """获取风险摘要"""
        alert_counts = {level.value: 0 for level in RiskLevel}
        for alert in self.current_alerts:
            alert_counts[alert.level.value] += 1

        return {
            'is_monitoring': self.is_monitoring,
            'alert_counts': alert_counts,
            'current_alerts': [alert.to_dict() for alert in self.current_alerts],
            'risk_metrics': self.risk_metrics.to_dict(),
            'limits': self.limits.to_dict(),
            'portfolio_size': len(self.historical_data.portfolio_history),
            'last_update': datetime.now().isoformat()
        }


class RiskManager:
    """风险管理器"""

    def __init__(self, limits: Optional[PositionLimits] = None):
        self.logger = TradingLogger(__name__)
        self.limits = limits or PositionLimits()
        self.monitor = RiskMonitor(self.limits)

        # 风险控制回调
        self.risk_callbacks: List[Callable] = []

    def start(self):
        """启动风险管理"""
        self.monitor.start_monitoring()
        self.logger.log_system_event("风险管理启动", "")

    def stop(self):
        """停止风险管理"""
        self.monitor.stop_monitoring()
        self.logger.log_system_event("风险管理停止", "")

    def update_portfolio(self, portfolio_value: float, positions: Dict[str, float]):
        """更新投资组合数据"""
        self.monitor.update_portfolio_data(portfolio_value, positions)

    def add_risk_callback(self, callback: Callable):
        """添加风险控制回调函数"""
        self.risk_callbacks.append(callback)

    def check_trade_risk(self, symbol: str, trade_value: float, portfolio_value: float,
                        current_positions: Dict[str, float]) -> Tuple[bool, str]:
        """检查交易风险"""
        # 检查单个持仓限制
        new_position_value = current_positions.get(symbol, 0) + trade_value
        if new_position_value > self.limits.max_position_value:
            return (False, f"Position size would exceed limit: ${new_position_value:,.2f} > "
                           f"${self.limits.max_position_value:,.2f}")

        # 检查集中度
        if portfolio_value > 0:
            new_concentration = new_position_value / portfolio_value
            if new_concentration > self.limits.max_portfolio_concentration:
                return (False, f"Portfolio concentration would exceed limit: "
                               f"{new_concentration:.1%} > {self.limits.max_portfolio_concentration:.1%}")

        # 检查总敞口
        if portfolio_value > 0:
            total_exposure = (sum(current_positions.values()) + trade_value) / portfolio_value
        else:
            total_exposure = 0
        if total_exposure > self.limits.max_total_exposure:
            return (False, f"Total exposure would exceed limit: {total_exposure:.1%} > "
                           f"{self.limits.max_total_exposure:.1%}")

        return True, "Trade approved"

    def get_status(self) -> Dict[str, Any]:
        """获取风险管理状态"""
        return self.monitor.get_risk_summary()


# 示例用法
if __name__ == "__main__":
    # 创建风险管理器
    position_limits = PositionLimits(
        max_position_value=30000.0,
        max_portfolio_concentration=0.15,
        max_daily_loss=0.03
    )

    risk_manager = RiskManager(position_limits)

    try:
        # 启动风险管理
        risk_manager.start()

        # 模拟投资组合更新
        TEST_PORTFOLIO_VALUE = 100000.0
        test_positions = {
            'AAPL': 25000.0,
            'MSFT': 20000.0,
            'GOOGL': 15000.0
        }

        risk_manager.update_portfolio(TEST_PORTFOLIO_VALUE, test_positions)

        # 检查交易风险
        can_trade, message = risk_manager.check_trade_risk(
            'AAPL', 10000.0, TEST_PORTFOLIO_VALUE, test_positions
        )
        print(f"Trade check: {can_trade}, {message}")

        # 获取风险状态
        status = risk_manager.get_status()
        print(f"Risk Status: {status}")

        # 等待一段时间
        time.sleep(5)

    finally:
        # 停止风险管理
        risk_manager.stop()
