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
import pandas as pd

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
            "timestamp": self.timestamp.isoformat(),
            "risk_type": self.risk_type.value,
            "level": self.level.value,
            "symbol": self.symbol,
            "message": self.message,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "action_required": self.action_required,
        }


@dataclass
class PositionLimits:
    """持仓限制"""

    max_position_value: float = 50000.0  # 单个持仓最大价值
    max_portfolio_concentration: float = 0.2  # 单个持仓占总资产比例上限
    max_sector_concentration: float = 0.3  # 单个行业占总资产比例上限
    max_daily_loss: float = 0.05  # 单日最大亏损比例
    max_total_exposure: float = 1.0  # 总敞口比例（1.0 = 100%资金）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "max_position_value": self.max_position_value,
            "max_portfolio_concentration": self.max_portfolio_concentration,
            "max_sector_concentration": self.max_sector_concentration,
            "max_daily_loss": self.max_daily_loss,
            "max_total_exposure": self.max_total_exposure,
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
            "portfolio_value": self.portfolio_value,
            "daily_pnl": self.daily_pnl,
            "total_exposure": self.total_exposure,
            "max_drawdown": self.max_drawdown,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "var_95": self.var_95,
            "var_99": self.var_99,
            "beta": self.beta,
            "correlation_risk": self.correlation_risk,
        }


class RiskCalculator:
    """Risk metric calculator utilities."""

    def __init__(self) -> None:
        self.logger = TradingLogger(__name__)

    @staticmethod
    def _to_array(data) -> np.ndarray:
        if data is None:
            return np.array([])
        if isinstance(data, pd.Series):
            return data.dropna().to_numpy()
        if isinstance(data, (list, tuple, np.ndarray)):
            return np.asarray(data, dtype=float)
        try:
            return np.asarray(list(data), dtype=float)
        except Exception:  # pragma: no cover - defensive
            return np.array([])

    def calculate_var(self, returns, confidence_level: float = 0.95) -> float:
        series = self._to_array(returns)
        if series.size == 0:
            return 0.0
        percentile = np.percentile(series, (1 - confidence_level) * 100)
        return float(percentile)

    def calculate_portfolio_var(self, returns, confidence: float = 0.95) -> float:
        return self.calculate_var(returns, confidence_level=confidence)

    def calculate_max_drawdown(self, portfolio_values) -> float:
        values = self._to_array(portfolio_values)
        if values.size < 2:
            return 0.0
        peaks = np.maximum.accumulate(values)
        drawdown = (values - peaks) / peaks
        return float(drawdown.min())

    def calculate_volatility(self, returns, annualized: bool = True) -> float:
        series = self._to_array(returns)
        if series.size < 2:
            return 0.0
        vol = np.std(series)
        if annualized:
            vol *= np.sqrt(252)
        return float(vol)

    def calculate_sharpe_ratio(self, returns, risk_free_rate: float = 0.02) -> float:
        series = self._to_array(returns)
        if series.size < 2:
            return 0.0
        excess_returns = series - (risk_free_rate / 252)
        std = np.std(excess_returns)
        if std == 0:
            return 0.0
        return float(np.mean(excess_returns) / std * np.sqrt(252))

    def calculate_beta(self, stock_returns, market_returns) -> float:
        stock = self._to_array(stock_returns)
        market = self._to_array(market_returns)
        if stock.size == 0 or market.size == 0 or stock.size != market.size:
            return 1.0
        covariance = np.cov(stock, market)[0][1]
        market_variance = np.var(market)
        if market_variance == 0:
            return 1.0
        return float(covariance / market_variance)

    def calculate_concentration_risk(self, positions) -> dict:
        if not positions:
            return {}
        concentration: dict[str, float] = {}
        total_value = 0.0
        for symbol, payload in positions.items():
            if isinstance(payload, dict):
                value = payload.get("value")
                if value is None:
                    quantity = payload.get("quantity", 0)
                    price = payload.get("price", 0)
                    value = quantity * price
            else:
                value = float(payload)
            try:
                value = float(value)
            except (TypeError, ValueError):
                value = 0.0
            concentration[symbol] = value
            total_value += value

        if total_value <= 0:
            return {symbol: 0.0 for symbol in concentration}

        for symbol, value in concentration.items():
            concentration[symbol] = value / total_value
        return concentration


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

    def __init__(
        self,
        risk_manager: Optional["RiskManager"] = None,
        limits: Optional[PositionLimits] = None,
        logger: Optional[TradingLogger] = None,
        notifier: Optional[NotificationManager] = None,
        check_interval: int = 60,
    ) -> None:
        """Initialise risk monitor with optional dependencies."""
        self.risk_manager = risk_manager
        self.logger = logger or TradingLogger(__name__)
        self.notification_manager = notifier or NotificationManager()
        self.limits = limits or getattr(risk_manager, "limits", PositionLimits())
        self.calculator = RiskCalculator()
        self.check_interval = check_interval

        # 历史数据存储
        self.historical_data = HistoricalData()

        # 当前风险状态
        self.current_alerts: List[RiskAlert] = []
        self.risk_metrics = RiskMetrics()

        # 监控标志
        self.is_monitoring = False
        self.is_running = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start risk monitoring."""
        if self.is_running:
            return

        self.is_monitoring = True
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        self.logger.log_system_event("风险监控启动", "")

        # 发送通知
        self.notification_manager.send_notification(
            "🛡️ 风险监控系统已启动", "风险监控启动"
        )

    def stop_monitoring(self):
        """Stop risk monitoring."""
        self.is_monitoring = False
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
            self.monitor_thread = None

        self.logger.log_system_event("风险监控停止", "")

        # 发送通知
        self.notification_manager.send_notification(
            "⏹️ 风险监控系统已停止", "风险监控停止"
        )

    def update_portfolio_data(
        self, portfolio_value: float, positions: Dict[str, float]
    ):
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
                time.sleep(self.check_interval)

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
                self.historical_data.portfolio_history
            )
            self.risk_metrics.max_drawdown = max_drawdown

        # 计算波动率
        if len(self.historical_data.returns_history) >= 10:
            returns_data = self.historical_data.returns_history
            self.risk_metrics.volatility = self.calculator.calculate_volatility(
                returns_data
            )
            self.risk_metrics.sharpe_ratio = self.calculator.calculate_sharpe_ratio(
                returns_data
            )
            self.risk_metrics.var_95 = self.calculator.calculate_var(
                returns_data, confidence_level=0.95
            )
            self.risk_metrics.var_99 = self.calculator.calculate_var(
                returns_data, confidence_level=0.99
            )

        concentrations = self.calculator.calculate_concentration_risk(positions)
        self.risk_metrics.correlation_risk = sum(
            value**2 for value in concentrations.values()
        )

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
                    message=(
                        f"Position size exceeds limit: ${position_value:,.2f} > "
                        f"${self.limits.max_position_value:,.2f}"
                    ),
                    current_value=position_value,
                    threshold=self.limits.max_position_value,
                    action_required=True,
                )
                self.current_alerts.append(alert)

    def _check_concentration_risk(
        self, positions: Dict[str, float], portfolio_value: float
    ):
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
                    message=(
                        f"Portfolio concentration too high: {concentration:.1%} > "
                        f"{self.limits.max_portfolio_concentration:.1%}"
                    ),
                    current_value=concentration,
                    threshold=self.limits.max_portfolio_concentration,
                    action_required=concentration > 0.3,
                )
                self.current_alerts.append(alert)

    def _check_drawdown_risk(self):
        """检查回撤风险"""
        if self.risk_metrics.max_drawdown < -0.15:  # 15%回撤阈值
            level = (
                RiskLevel.CRITICAL
                if self.risk_metrics.max_drawdown < -0.25
                else RiskLevel.HIGH
            )

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.DRAWDOWN,
                level=level,
                symbol="PORTFOLIO",
                message=f"Maximum drawdown: {self.risk_metrics.max_drawdown:.2%}",
                current_value=abs(self.risk_metrics.max_drawdown),
                threshold=0.15,
                action_required=self.risk_metrics.max_drawdown < -0.20,
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
                message=(
                    f"Daily loss exceeds limit: {daily_loss_pct:.2%} > "
                    f"{self.limits.max_daily_loss:.2%}"
                ),
                current_value=daily_loss_pct,
                threshold=self.limits.max_daily_loss,
                action_required=daily_loss_pct > 0.08,
            )
            self.current_alerts.append(alert)

    def _check_volatility_risk(self):
        """检查波动率风险"""
        if self.risk_metrics.volatility > 0.40:  # 40%年化波动率阈值
            level = (
                RiskLevel.HIGH
                if self.risk_metrics.volatility > 0.60
                else RiskLevel.MEDIUM
            )

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.VOLATILITY,
                level=level,
                symbol="PORTFOLIO",
                message=f"Portfolio volatility high: {self.risk_metrics.volatility:.1%}",
                current_value=self.risk_metrics.volatility,
                threshold=0.40,
                action_required=self.risk_metrics.volatility > 0.60,
            )
            self.current_alerts.append(alert)

    def _check_var_risk(self):
        """检查VaR风险"""
        if abs(self.risk_metrics.var_95) > 0.05:  # 5% VaR阈值
            level = (
                RiskLevel.HIGH
                if abs(self.risk_metrics.var_95) > 0.08
                else RiskLevel.MEDIUM
            )

            alert = RiskAlert(
                timestamp=datetime.now(),
                risk_type=RiskType.VAR,
                level=level,
                symbol="PORTFOLIO",
                message=f"95% VaR: {self.risk_metrics.var_95:.2%}",
                current_value=abs(self.risk_metrics.var_95),
                threshold=0.05,
                action_required=abs(self.risk_metrics.var_95) > 0.08,
            )
            self.current_alerts.append(alert)

    def _process_alerts(self):
        """处理风险警报"""
        critical_alerts = [
            alert for alert in self.current_alerts if alert.level == RiskLevel.CRITICAL
        ]
        high_alerts = [
            alert for alert in self.current_alerts if alert.level == RiskLevel.HIGH
        ]

        # 发送关键风险通知
        for alert in critical_alerts:
            self.logger.log_risk_event("CRITICAL", alert.symbol, alert.message)

            self.notification_manager.send_notification(
                f"🚨 CRITICAL RISK ALERT\n"
                f"Symbol: {alert.symbol}\n"
                f"Type: {alert.risk_type.value}\n"
                f"Message: {alert.message}",
                f"CRITICAL Risk - {alert.symbol}",
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
            "is_monitoring": self.is_monitoring,
            "alert_counts": alert_counts,
            "current_alerts": [alert.to_dict() for alert in self.current_alerts],
            "risk_metrics": self.risk_metrics.to_dict(),
            "limits": self.limits.to_dict(),
            "portfolio_size": len(self.historical_data.portfolio_history),
            "last_update": datetime.now().isoformat(),
        }


class RiskManager:
    """Enterprise risk manager providing portfolio level analytics."""

    DEFAULT_CONFIG = {
        "max_portfolio_var": 0.05,
        "max_position_size": 0.2,
        "max_daily_loss": 0.02,
        "max_drawdown": 0.2,
        "concentration_limit": 0.25,
        "correlation_threshold": 0.8,
        "max_total_exposure": 1.0,
        "monitor_interval": 60,
        "initial_capital": 100000.0,
    }

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        limits: Optional[PositionLimits] = None,
        logger: Optional[TradingLogger] = None,
        notifier: Optional[NotificationManager] = None,
    ) -> None:
        self.config: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        if config:
            self.config.update(config)

        self.logger = logger or TradingLogger(__name__)
        self.notifier = notifier or NotificationManager()
        self.calculator = RiskCalculator()

        base_capital = float(self.config.get("initial_capital", 100000.0))
        position_limit_value = self.config.get(
            "max_position_value",
            self.config.get("max_position_size", 0.2) * base_capital,
        )

        if limits is None:
            limits = PositionLimits(
                max_position_value=position_limit_value,
                max_portfolio_concentration=self.config.get(
                    "concentration_limit", 0.25
                ),
                max_sector_concentration=self.config.get("sector_limit", 0.3),
                max_daily_loss=self.config.get("max_daily_loss", 0.02),
                max_total_exposure=self.config.get("max_total_exposure", 1.0),
            )
        self.limits = limits

        self.portfolio_data: Dict[str, Any] = {
            "positions": {},
            "daily_pnl": 0.0,
            "initial_value": base_capital,
        }

        self.risk_callbacks: List[Callable] = []
        self.monitor = RiskMonitor(
            risk_manager=self,
            limits=self.limits,
            logger=self.logger,
            notifier=self.notifier,
            check_interval=self.config.get("monitor_interval", 60),
        )

    # ------------------------------------------------------------------ #
    # Lifecycle helpers
    # ------------------------------------------------------------------ #
    def start(self) -> None:
        self.monitor.start_monitoring()

    def stop(self) -> None:
        self.monitor.stop_monitoring()

    # ------------------------------------------------------------------ #
    # Portfolio management helpers
    # ------------------------------------------------------------------ #
    def update_portfolio(
        self, portfolio_value: float, positions: Dict[str, float]
    ) -> None:
        self.portfolio_data["positions"] = positions
        self.monitor.update_portfolio_data(portfolio_value, positions)

    def add_risk_callback(self, callback: Callable) -> None:
        self.risk_callbacks.append(callback)

    def get_status(self) -> Dict[str, Any]:
        return self.monitor.get_risk_summary()

    # ------------------------------------------------------------------ #
    # Risk analytics
    # ------------------------------------------------------------------ #
    def validate_position_size(
        self, symbol: str, position_value: float, portfolio_value: float
    ) -> Dict[str, Any]:
        limit_ratio = self.config.get("max_position_size", 0.2)
        limit_value = (
            portfolio_value * limit_ratio if portfolio_value > 0 else float("inf")
        )
        allowed = position_value <= limit_value
        reason = "Within limits" if allowed else "Position size exceeds limit"
        return {
            "symbol": symbol,
            "allowed": allowed,
            "reason": reason,
            "limit": limit_value,
            "value": position_value,
        }

    def check_daily_loss_limit(self) -> Dict[str, Any]:
        initial = float(self.portfolio_data.get("initial_value") or 0.0)
        daily_pnl = float(self.portfolio_data.get("daily_pnl") or 0.0)
        max_loss = self.config.get("max_daily_loss", 0.02)
        loss_pct = 0.0
        if initial > 0:
            loss_pct = max(0.0, -daily_pnl / initial)
        within_limit = loss_pct <= max_loss
        return {
            "within_limit": within_limit,
            "loss_pct": loss_pct,
            "limit": max_loss,
        }

    def calculate_portfolio_risk(
        self, positions: Dict[str, Dict[str, Any]], returns_data
    ) -> Dict[str, Any]:
        totals = {
            symbol: self._position_value(data) for symbol, data in positions.items()
        }
        total_value = sum(totals.values())

        if hasattr(returns_data, "mean"):
            portfolio_returns = returns_data.mean(axis=1)
        else:
            portfolio_returns = returns_data

        var_95 = self.calculator.calculate_var(portfolio_returns, confidence_level=0.95)
        var_99 = self.calculator.calculate_var(portfolio_returns, confidence_level=0.99)
        concentration = self.calculator.calculate_concentration_risk(positions)

        return {
            "var_95": var_95,
            "var_99": var_99,
            "concentration_risk": concentration,
            "total_exposure": total_value,
        }

    def should_block_trade(
        self,
        trade_signal: Dict[str, Any],
        current_portfolio: Dict[str, Dict[str, Any]],
        total_capital: float,
    ) -> Dict[str, Any]:
        position_value = trade_signal.get("price", 0.0) * trade_signal.get(
            "quantity", 0
        )
        max_ratio = self.config.get("max_position_size", 0.2)
        reasons: List[str] = []

        if total_capital > 0 and position_value > total_capital * max_ratio:
            reasons.append("Position size exceeds limit")

        current_value = sum(
            self._position_value(data) for data in current_portfolio.values()
        )
        if total_capital > 0:
            concentration = (current_value + position_value) / total_capital
            if concentration > self.config.get("concentration_limit", 0.25):
                reasons.append("Concentration limit exceeded")

        block = bool(reasons)
        reason = "; ".join(reasons) if reasons else "Within limits"
        return {"block": block, "reason": reason}

    def check_trade_risk(
        self,
        symbol: str,
        trade_value: float,
        portfolio_value: float,
        current_positions: Dict[str, float],
    ) -> Tuple[bool, str]:
        assessment = self.validate_position_size(symbol, trade_value, portfolio_value)
        if not assessment["allowed"]:
            return False, assessment["reason"]

        exposure = sum(current_positions.values()) + trade_value
        if portfolio_value > 0:
            total_exposure = exposure / portfolio_value
            if total_exposure > self.limits.max_total_exposure:
                return False, "Total exposure would exceed limit"

        return True, "Trade approved"

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _position_value(position: Dict[str, Any]) -> float:
        if position is None:
            return 0.0
        if "value" in position:
            return float(position.get("value") or 0.0)
        quantity = float(position.get("quantity", 0.0))
        price = float(position.get("price", 0.0))
        return quantity * price


# 示例用法
if __name__ == "__main__":
    # 创建风险管理器
    position_limits = PositionLimits(
        max_position_value=30000.0,
        max_portfolio_concentration=0.15,
        max_daily_loss=0.03,
    )

    risk_manager = RiskManager(position_limits)

    try:
        # 启动风险管理
        risk_manager.start()

        # 模拟投资组合更新
        TEST_PORTFOLIO_VALUE = 100000.0
        test_positions = {"AAPL": 25000.0, "MSFT": 20000.0, "GOOGL": 15000.0}

        risk_manager.update_portfolio(TEST_PORTFOLIO_VALUE, test_positions)

        # 检查交易风险
        can_trade, message = risk_manager.check_trade_risk(
            "AAPL", 10000.0, TEST_PORTFOLIO_VALUE, test_positions
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
