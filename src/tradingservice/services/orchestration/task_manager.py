#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器模块 - 上层业务逻辑

提供统一的任务管理接口，整合调度、执行、监控等功能。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

import pandas as pd

from src.tradingagent import (
    OrderExecutor,
    SignalGenerator,
    DataManager,
    RiskController,
    TradingSignal,
    OrderStatus,
)
from src.tradingagent.core.brokers import BrokerFactory
from src.tradingagent.modules.data_provider.provider_adapter import SimpleMarketDataProvider
from src.tradingagent.modules.strategies.multi_strategy_runner import (
    MultiStrategyRunner,
    StrategyResult,
)
from .orch_models import Task, TaskStatus
from config import config as app_config


logger = logging.getLogger(__name__)

__all__ = ["TaskManager", "Task", "TaskStatus"]


class TaskManager:
    """任务管理器 - 业务逻辑层核心"""

    def __init__(self, broker: Optional[Any] = None, initial_capital: float = 100000.0):
        """
        初始化任务管理器

        Args:
            broker: 经纪商接口，如果为None则使用模拟经纪商
            initial_capital: 初始资金（用于模拟交易）
        """

        # 准备数据提供器, 便于不同券商复用
        data_provider = SimpleMarketDataProvider()

        if broker is not None:
            self.broker = broker
        else:
            broker_type, broker_params = app_config.resolve_broker(None)
            if broker_type == "simulation":
                broker_params.setdefault("initial_capital", initial_capital)
                broker_params.setdefault("data_provider", data_provider)

            self.broker = BrokerFactory.create(broker_type, **broker_params)
        self.data_manager = DataManager()
        self.signal_generator = SignalGenerator()
        self.executor = OrderExecutor(self.broker)
        self.risk_controller = RiskController(self.broker)
        self.strategy_runner = MultiStrategyRunner()
        self.analysis_period = app_config.get("tasks.analysis_period", "6mo")

        # 任务存储
        self.tasks: Dict[str, Task] = {}
        # 对账日志
        self.reconciliation_log: List[Dict[str, Any]] = []

        # 连接经纪商
        if not self.broker.is_connected():
            self.broker.connect()

        logger.info("任务管理器初始化完成")

    def create_task(
        self, task_id: str, name: str, symbols: List[str], strategies: List[str]
    ) -> Task:
        """
        创建新任务

        Args:
            task_id: 任务ID
            name: 任务名称
            symbols: 股票代码列表
            strategies: 策略列表

        Returns:
            Task: 任务对象
        """
        task = Task(
            task_id=task_id,
            name=name,
            symbols=symbols,
            strategies=strategies,
            status=TaskStatus.PENDING,
        )

        self.tasks[task_id] = task
        logger.info(f"创建任务: {name} ({task_id})")

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            Task: 任务对象
        """
        return self.tasks.get(task_id)

    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        列出所有任务

        Args:
            status_filter: 状态过滤

        Returns:
            List[Task]: 任务列表
        """
        tasks = list(self.tasks.values())

        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]

        return tasks

    def execute_task(self, task_id: str) -> bool:
        """
        执行任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False

        if task.status == TaskStatus.RUNNING:
            logger.warning(f"任务正在运行: {task_id}")
            return False

        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            logger.info(f"开始执行任务: {task.name}")

            summary = self._run_task_pipeline(task)

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = summary
            task.error = None

            logger.info(f"任务执行完成: {task.name}")
            return True

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            logger.error(f"任务执行失败: {task.name} - {e}")
            return False

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            logger.warning(f"任务已结束: {task_id}")
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()

        logger.info(f"任务已取消: {task.name}")
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功
        """
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            logger.info(f"删除任务: {task.name}")
            return True
        else:
            logger.error(f"任务不存在: {task_id}")
            return False

    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要

        Returns:
            Dict: 账户摘要信息
        """
        account_info = self.executor.get_account_info()
        risk_metrics = self.risk_controller.get_risk_metrics()
        order_stats = self.executor.get_order_statistics()
        signal_stats = self.signal_generator.get_signal_statistics()

        return {
            "account": account_info,
            "risk": risk_metrics,
            "orders": order_stats,
            "signals": signal_stats,
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        total_tasks = len(self.tasks)
        status_counts = {}

        for status in TaskStatus:
            count = sum(1 for t in self.tasks.values() if t.status == status)
            status_counts[status.value] = count

        return {
            "total_tasks": total_tasks,
            "status_breakdown": status_counts,
            "account_summary": self.get_account_summary(),
        }

    def _run_task_pipeline(self, task: Task) -> Dict[str, Any]:
        """
        执行完整的任务管线：运行策略、生成信号、风控校验、执行虚拟订单。
        """
        selected_strategies = self._resolve_strategy_names(task.strategies)
        executed_signals: List[Dict[str, Any]] = []
        rejected_signals: List[Dict[str, Any]] = []
        executed_orders: List[Dict[str, Any]] = []
        symbol_summaries: Dict[str, Any] = {}
        task_errors: List[str] = []

        for symbol in task.symbols:
            symbol_summary = {
                "strategies": {},
                "signals": [],
                "orders": [],
                "errors": [],
            }

            try:
                self.strategy_runner.clear_results()
                results = self.strategy_runner.run_all_strategies(
                    symbol=symbol,
                    period=self.analysis_period,
                    selected_strategies=selected_strategies,
                )

                performance_summary = self.strategy_runner.get_performance_summary() or {}
                symbol_summary["performance"] = {
                    key: self._safe_number(value)
                    for key, value in performance_summary.items()
                }

                for strategy_name, strategy_result in results.items():
                    symbol_summary["strategies"][strategy_name] = self._serialize_strategy_result(
                        strategy_result
                    )

                    signal_info = self._extract_actionable_signal(strategy_result)
                    if not signal_info:
                        continue

                    trade_quantity = self._determine_quantity(
                        symbol=symbol,
                        action=signal_info["action"],
                        signal_strength=signal_info["signal"],
                    )
                    if trade_quantity <= 0:
                        rejected_record = {
                            "symbol": symbol,
                            "strategy": strategy_name,
                            "action": signal_info["action"],
                            "reason": "Unable to determine executable quantity",
                        }
                        rejected_signals.append(rejected_record)
                        symbol_summary["signals"].append({**rejected_record, "status": "rejected"})
                        continue

                    strategy_payload = {
                        "signal": signal_info["signal"],
                        "confidence": signal_info["confidence"],
                        "reason": signal_info["reason"],
                        "target_price": signal_info["extras"].get("target_price"),
                    }

                    generated_signal = self.signal_generator.generate_signal(
                        symbol=symbol,
                        strategy_name=strategy_name,
                        strategy_result=strategy_payload,
                        quantity=trade_quantity,
                    )

                    if not generated_signal:
                        continue

                    generated_signal.quantity = trade_quantity

                    allowed, reason = self.risk_controller.validate_signal(generated_signal)
                    signal_record = generated_signal.to_dict()
                    signal_record["status"] = "approved" if allowed else "rejected"
                    signal_record["risk_check"] = reason

                    if not allowed:
                        rejected_signals.append(signal_record)
                        symbol_summary["signals"].append(signal_record)
                        continue

                    order_id = self.executor.execute_signal(generated_signal)
                    if not order_id:
                        signal_record["status"] = "execution_failed"
                        rejected_signals.append(signal_record)
                        symbol_summary["signals"].append(signal_record)
                        continue

                    order = self.executor.get_order(order_id)
                    if order:
                        self.risk_controller.record_trade(order)
                        order_dict = order.to_dict()
                        executed_orders.append(order_dict)
                        executed_signals.append(signal_record)
                        symbol_summary["signals"].append(
                            {**signal_record, "status": "executed", "order_id": order_id}
                        )
                        symbol_summary["orders"].append(order_dict)
                    else:
                        signal_record["status"] = "order_missing"
                        rejected_signals.append(signal_record)
                        symbol_summary["signals"].append(signal_record)

            except Exception as symbol_error:
                error_message = f"{symbol}: {symbol_error}"
                logger.exception("Symbol processing failed: %s", error_message)
                symbol_summary["errors"].append(error_message)
                task_errors.append(error_message)

            symbol_summaries[symbol] = symbol_summary

        self.executor.update_all_pending_orders()

        return {
            "task_id": task.task_id,
            "task_name": task.name,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": datetime.now().isoformat(),
            "symbols": symbol_summaries,
            "signals": {
                "executed": executed_signals,
                "rejected": rejected_signals,
                "total": len(executed_signals) + len(rejected_signals),
            },
            "orders": executed_orders,
            "account_snapshot": self.executor.get_account_info(),
            "risk_snapshot": self.risk_controller.get_risk_metrics(),
            "task_errors": task_errors,
        }

    def process_realtime_signal(
        self,
        *,
        symbol: str,
        strategy_name: str,
        action: str,
        signal_strength: float,
        confidence: float = 0.0,
        reason: str = "",
        target_price: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        处理外部实时信号，复用风控与执行链路。

        Args:
            symbol: 标的代码
            strategy_name: 信号来源策略名称
            action: 买入/卖出
            signal_strength: 信号强度（-1 到 1）
            confidence: 信号置信度
            reason: 信号说明
            target_price: 目标价格（用于限价单）
            metadata: 额外元信息

        Returns:
            dict: 含执行状态、风控结果、订单信息的记录
        """
        action = action.lower()
        result: Dict[str, Any] = {
            "symbol": symbol,
            "strategy": strategy_name,
            "action": action,
            "signal_strength": signal_strength,
            "confidence": confidence,
            "reason": reason,
        }
        if metadata:
            result["metadata"] = metadata

        if action not in {"buy", "sell"}:
            result["status"] = "ignored"
            result["risk_check"] = "Unsupported action"
            return result

        quantity = self._determine_quantity(symbol, action, signal_strength)
        result["quantity"] = quantity
        if quantity <= 0:
            result["status"] = "rejected"
            result["risk_check"] = "Unable to determine executable quantity"
            return result

        signal_value = signal_strength if action == "buy" else -abs(signal_strength)
        strategy_payload: Dict[str, Any] = {
            "signal": signal_value,
            "confidence": confidence,
            "reason": reason,
        }
        if target_price is not None:
            strategy_payload["target_price"] = target_price

        generated_signal = self.signal_generator.generate_signal(
            symbol=symbol,
            strategy_name=strategy_name,
            strategy_result=strategy_payload,
            quantity=quantity,
        )
        if not generated_signal:
            result["status"] = "ignored"
            result["risk_check"] = "Signal generator returned None"
            return result

        generated_signal.quantity = quantity
        signal_dict = generated_signal.to_dict()
        result["signal"] = signal_dict

        allowed, risk_reason = self.risk_controller.validate_signal(generated_signal)
        result["risk_check"] = risk_reason
        if not allowed:
            result["status"] = "rejected"
            return result

        order_id = self.executor.execute_signal(generated_signal)
        if not order_id:
            result["status"] = "execution_failed"
            return result

        order = self.executor.get_order(order_id)
        if order:
            terminal_states = {
                OrderStatus.FILLED,
                getattr(OrderStatus, "PARTIAL_FILLED", None),
            }
            if order.status in terminal_states:
                self.risk_controller.record_trade(order)
            order_dict = order.to_dict()
            result["status"] = "executed"
            result["order_id"] = order_id
            result["order"] = order_dict
            return result

        result["status"] = "order_missing"
        return result

    def reconcile_orders(self) -> List[Dict[str, Any]]:
        """
        轮询未完成订单的最新状态，并返回所有结束态的结果。

        Returns:
            List[Dict[str, Any]]: Order update payloads for downstream consumers.
        """
        if not self.executor.pending_orders:
            return []

        updates = self.executor.update_all_pending_orders()
        if not updates:
            return []

        terminal_statuses = {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
        partial_status = getattr(OrderStatus, "PARTIAL_FILLED", None)
        if partial_status is not None:
            terminal_statuses.add(partial_status)

        reconciled: List[Dict[str, Any]] = []
        timestamp = datetime.now(timezone.utc).isoformat()

        for order_id, status in updates.items():
            status_enum: Optional[OrderStatus] = None
            if isinstance(status, OrderStatus):
                status_enum = status
            elif status:
                try:
                    status_enum = OrderStatus(str(status))
                except ValueError:
                    status_enum = None

            if status_enum is None or status_enum not in terminal_statuses:
                continue

            order_obj = self.executor.get_order(order_id)
            order_payload = order_obj.to_dict() if order_obj else None

            if order_obj and status_enum in terminal_statuses:
                try:
                    self.risk_controller.record_trade(order_obj)
                except Exception as exc:  # pragma: no cover - 防御性
                    logger.error("记录成交失败: %s", exc)

            risk_snapshot = self.risk_controller.get_risk_metrics()

            reconciled.append(
                {
                    "order_id": order_id,
                    "status": status_enum.value,
                    "order": order_payload,
                    "risk_snapshot": risk_snapshot,
                    "updated_at": timestamp,
                }
            )
            self.reconciliation_log.append(reconciled[-1])

        if not reconciled:
            return []

        logger.info(
            "已对账实时订单: %s",
            ", ".join(
                f"{entry['order_id']} -> {entry['status']}" for entry in reconciled
            ),
        )
        self.risk_controller.update_peak_equity()
        return reconciled

    def get_reconciliation_log(self) -> List[Dict[str, Any]]:
        """返回历史对账记录。"""
        return list(self.reconciliation_log)

    def _resolve_strategy_names(self, requested: List[str]) -> Optional[List[str]]:
        """将用户输入策略名称映射为系统内策略名称。"""
        if not requested:
            return None

        normalized_map = {
            name.lower(): name for name in self.strategy_runner.strategies.keys()
        }

        resolved: List[str] = []
        for raw_name in requested:
            if not raw_name:
                continue
            lowered = raw_name.strip().lower()
            if lowered in ("all", "*"):
                return None
            if raw_name in self.strategy_runner.strategies:
                resolved.append(raw_name)
                continue
            if lowered in normalized_map:
                resolved.append(normalized_map[lowered])

        unique_resolved: List[str] = []
        seen = set()
        for name in resolved:
            if name not in seen:
                unique_resolved.append(name)
                seen.add(name)

        return unique_resolved or None

    def _extract_actionable_signal(self, strategy_result: StrategyResult) -> Optional[Dict[str, Any]]:
        """从策略结果中提取最新的可执行信号。"""
        signals_df = strategy_result.signals
        if signals_df is None or signals_df.empty or "signal" not in signals_df.columns:
            return None

        actionable = signals_df[signals_df["signal"] != 0]
        if actionable.empty:
            return None

        latest_index = actionable.index[-1]
        latest_row = actionable.iloc[-1]
        raw_signal = float(latest_row.get("signal", 0))

        if raw_signal == 0:
            return None

        timestamp = None
        if isinstance(latest_index, pd.Timestamp):
            timestamp = latest_index.to_pydatetime()
        elif hasattr(latest_index, "to_pydatetime"):
            timestamp = latest_index.to_pydatetime()

        sharpe_confidence = abs(strategy_result.sharpe_ratio)
        confidence = max(0.0, min(1.0, sharpe_confidence / 4.0))

        extras = {}
        for column in ("position", "ma_spread", "short_ma", "long_ma"):
            if column in latest_row:
                extras[column] = self._safe_number(latest_row[column])

        reason = f"Strategy {strategy_result.strategy_name} generated {('BUY' if raw_signal > 0 else 'SELL')} signal"

        return {
            "signal": raw_signal,
            "action": "buy" if raw_signal > 0 else "sell",
            "timestamp": timestamp.isoformat() if timestamp else None,
            "confidence": confidence,
            "extras": extras,
            "reason": reason,
        }

    def _determine_quantity(self, symbol: str, action: str, signal_strength: float) -> int:
        """根据持仓与资金情况计算下单数量。"""
        price = self.broker.get_current_price(symbol)
        if not price or price <= 0:
            return 0

        balance = self.broker.get_account_balance()
        equity = balance.get("equity") or balance.get("cash") or 0
        if equity <= 0:
            return 0

        base_risk_fraction = app_config.get("tasks.risk_per_trade", 0.02)
        quantity = int((equity * base_risk_fraction) / price)
        quantity = max(quantity, 1)

        if abs(signal_strength) < 1:
            quantity = max(int(quantity * abs(signal_strength)), 1)

        if action == "sell":
            positions = {pos.symbol: pos.quantity for pos in self.broker.get_positions()}
            available = positions.get(symbol, 0)
            if available <= 0:
                return 0
            quantity = min(quantity, available)

        return quantity

    def _serialize_strategy_result(self, result: StrategyResult) -> Dict[str, Any]:
        """将策略结果转换为可序列化字典。"""
        data = {
            "symbol": result.symbol,
            "total_return": self._safe_number(result.total_return),
            "sharpe_ratio": self._safe_number(result.sharpe_ratio),
            "max_drawdown": self._safe_number(result.max_drawdown),
            "win_rate": self._safe_number(result.win_rate),
            "total_trades": int(result.total_trades),
            "avg_trade_return": self._safe_number(result.avg_trade_return),
            "volatility": self._safe_number(result.volatility),
            "calmar_ratio": self._safe_number(result.calmar_ratio),
            "sortino_ratio": self._safe_number(result.sortino_ratio),
            "metadata": result.metadata or {},
        }
        if result.trades:
            data["trades"] = result.trades
        return data

    @staticmethod
    def _safe_number(value: Any) -> float:
        """尝试将数值转换为 float，失败时返回 0.0。"""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0
