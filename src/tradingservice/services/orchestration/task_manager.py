#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task orchestration services.

This module wires together data, strategy, risk, and execution components
to provide an automated trading task manager.
"""

import logging
import math
from copy import deepcopy
from typing import Dict, List, Optional, Any, Tuple
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
    """Coordinates automated trading tasks through the full execution pipeline."""

    def __init__(self, broker: Optional[Any] = None, initial_capital: float = 100000.0):
        """
        Initialize the task manager and supporting services.

        Args:
            broker: Optional externally provided broker instance.
            initial_capital: Default capital used when creating a simulation broker.
        """

        # Provide a data provider when creating simulated brokers.
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
        self.broker_risk_limits = self._load_broker_risk_limits()
        self._cached_risk_state: Optional[Dict[str, Any]] = None

        self.tasks: Dict[str, Task] = {}
        self.reconciliation_log: List[Dict[str, Any]] = []

        if not self.broker.is_connected():
            self.broker.connect()

        logger.info("TaskManager initialised and broker connection established.")

    def create_task(
        self, task_id: str, name: str, symbols: List[str], strategies: List[str]
    ) -> Task:
        """
        Register a scheduled task with the orchestration layer.

        Args:
            task_id: Unique identifier for the task.
            name: Human readable task name.
            symbols: Instruments the task should process.
            strategies: Strategy identifiers the task should execute.

        Returns:
            Task: The newly created task metadata container.
        """
        task = Task(
            task_id=task_id,
            name=name,
            symbols=symbols,
            strategies=strategies,
            status=TaskStatus.PENDING,
        )

        self.tasks[task_id] = task
        logger.info("Registered task %s (%s)", name, task_id)

        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Look up an existing task by id.

        Args:
            task_id: Unique identifier for the task.

        Returns:
            Task: Task metadata if present, otherwise ``None``.
        """
        return self.tasks.get(task_id)

    def list_tasks(self, status_filter: Optional[TaskStatus] = None) -> List[Task]:
        """
        Return all registered tasks, optionally filtered by status.

        Args:
            status_filter: Optional status value to filter by.

        Returns:
            List[Task]: Collection of task metadata objects.
        """
        tasks = list(self.tasks.values())

        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]

        return tasks

    def execute_task(self, task_id: str) -> bool:
        """
        Execute a task through the orchestration pipeline.

        Args:
            task_id: Identifier of the task to run.

        Returns:
            bool: ``True`` when the task completes successfully, ``False`` otherwise.
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error("Task %s not found", task_id)
            return False

        if task.status == TaskStatus.RUNNING:
            logger.warning("Task %s is already running", task_id)
            return False

        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            logger.info("Starting task %s", task.name)

            summary = self._run_task_pipeline(task)

            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = summary
            task.error = None

            logger.info("Completed task %s", task.name)
            return True

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            logger.error("Task %s failed: %s", task.name, e)
            return False

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a running task if it is still in-flight.

        Args:
            task_id: Identifier of the task to cancel.

        Returns:
            bool: ``True`` when the task is cancelled, ``False`` otherwise.
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error("Task %s not found", task_id)
            return False

        if task.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        ]:
            logger.warning("Task %s cannot be cancelled in its current state", task_id)
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()

        logger.info("Cancelled task %s", task.name)
        return True

    def delete_task(self, task_id: str) -> bool:
        """
        Remove a task from the registry.

        Args:
            task_id: Identifier of the task to delete.

        Returns:
            bool: ``True`` when the task was deleted, ``False`` otherwise.
        """
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            logger.info("Deleted task %s", task.name)
            return True
        else:
            logger.error("Task %s not found", task_id)
            return False

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Collect a snapshot of account, risk, order, and signal statistics.

        Returns:
            Dict: Aggregated summary payload for downstream reporting.
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
        Gather high-level task statistics.

        Returns:
            Dict: Summary including task counts and account overview.
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
        Execute the end-to-end automation pipeline for a scheduled task.

        The pipeline clears previous strategy state, runs analytics, generates
        actionable signals, applies risk and broker limits, and finally
        dispatches orders while collecting execution summaries.
        """
        selected_strategies = self._resolve_strategy_names(task.strategies)
        executed_signals: List[Dict[str, Any]] = []
        rejected_signals: List[Dict[str, Any]] = []
        executed_orders: List[Dict[str, Any]] = []
        symbol_summaries: Dict[str, Any] = {}
        task_errors: List[str] = []

        self.refresh_broker_risk_limits()
        broker_limits_enabled = self.broker_risk_limits.get("enabled", False)
        positions_state: Dict[str, Dict[str, float]] = {}
        gross_exposure = 0.0
        equity = 0.0
        current_position_count = 0

        if broker_limits_enabled:
            cached_state = self._cached_risk_state or {}
            cached_positions = cached_state.get("positions_state") or {}
            if cached_positions:
                positions_state = {
                    symbol: {
                        "quantity": self._safe_number(data.get("quantity")),
                        "market_value": self._safe_number(data.get("market_value")),
                        "price": data.get("price"),
                    }
                    for symbol, data in cached_positions.items()
                }
                gross_exposure = cached_state.get("gross_exposure", 0.0)
                equity = cached_state.get("equity", 0.0)
                current_position_count = cached_state.get(
                    "position_count",
                    sum(
                        1
                        for entry in positions_state.values()
                        if not math.isclose(entry.get("quantity", 0.0), 0.0, abs_tol=1e-9)
                    ),
                )
            else:
                account_snapshot = self.executor.get_account_info()
                positions_state = self._build_positions_state(account_snapshot.get("positions") or [])
                gross_exposure = sum(abs(entry["market_value"]) for entry in positions_state.values())
                balance = account_snapshot.get("balance") or {}
                equity = self._safe_number(balance.get("equity"))
                current_position_count = sum(
                    1
                    for entry in positions_state.values()
                    if not math.isclose(entry.get("quantity", 0.0), 0.0, abs_tol=1e-9)
                )

        self._cached_risk_state = None

        for symbol in task.symbols:
            symbol_summary = {
                "strategies": {},
                "signals": [],
                "orders": [],
                "errors": [],
            }
            symbol_key = symbol.upper()

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

                    previous_entry_copy = None
                    previous_gross = gross_exposure
                    previous_position_count = current_position_count
                    broker_price: Optional[float] = None

                    if broker_limits_enabled:
                        broker_price = self._resolve_trade_price(symbol, generated_signal)
                        if broker_price is None or broker_price <= 0:
                            base_reason = signal_record.get("risk_check")
                            combined_reason = (
                                f"{base_reason} | Broker limits: Unable to resolve trade price"
                                if base_reason
                                else "Broker limits: Unable to resolve trade price"
                            )
                            signal_record["status"] = "risk_blocked"
                            signal_record["risk_check"] = combined_reason
                            rejected_signals.append(signal_record)
                            symbol_summary["signals"].append(signal_record)
                            continue

                        (
                            limit_allowed,
                            limit_reason,
                            new_qty,
                            new_market_value,
                            projected_gross,
                            projected_position_count,
                        ) = self._evaluate_broker_limits_for_trade(
                            symbol=symbol,
                            action=signal_info["action"],
                            quantity=trade_quantity,
                            price=broker_price,
                            positions_state=positions_state,
                            gross_exposure=gross_exposure,
                            equity=equity,
                            current_position_count=current_position_count,
                        )

                        if not limit_allowed:
                            base_reason = signal_record.get("risk_check")
                            combined_reason = (
                                f"{base_reason} | Broker limits: {limit_reason}"
                                if base_reason
                                else f"Broker limits: {limit_reason}"
                            )
                            signal_record["status"] = "risk_blocked"
                            signal_record["risk_check"] = combined_reason
                            rejected_signals.append(signal_record)
                            symbol_summary["signals"].append(signal_record)
                            continue

                        previous_entry_copy = deepcopy(positions_state.get(symbol_key)) if symbol_key in positions_state else None
                        previous_gross = gross_exposure
                        previous_position_count = current_position_count

                        if math.isclose(new_qty, 0.0, abs_tol=1e-9):
                            positions_state.pop(symbol_key, None)
                        else:
                            positions_state[symbol_key] = {
                                "quantity": new_qty,
                                "market_value": new_market_value,
                                "price": broker_price,
                            }
                        gross_exposure = projected_gross
                        current_position_count = projected_position_count

                    order_id = self.executor.execute_signal(generated_signal)
                    if not order_id:
                        if broker_limits_enabled:
                            if previous_entry_copy is None:
                                positions_state.pop(symbol_key, None)
                            else:
                                positions_state[symbol_key] = previous_entry_copy
                            gross_exposure = previous_gross
                            current_position_count = previous_position_count

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
                        if broker_limits_enabled:
                            if previous_entry_copy is None:
                                positions_state.pop(symbol_key, None)
                            else:
                                positions_state[symbol_key] = previous_entry_copy
                            gross_exposure = previous_gross
                            current_position_count = previous_position_count

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
        Process a single real-time signal through risk checks and optional execution.

        Args:
            symbol: Instrument symbol associated with the signal.
            strategy_name: Strategy that produced the signal.
            action: Desired side, e.g. ``\"buy\"`` or ``\"sell\"``.
            signal_strength: Magnitude of the signal, typically -1 to 1.
            confidence: Optional confidence score.
            reason: Human-readable explanation of the signal.
            target_price: Optional limit price hint.
            metadata: Arbitrary metadata to attach to the response payload.

        Returns:
            dict: Result payload capturing status, quantity decisions, and any errors.
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
        Poll outstanding orders and return status updates.

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
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.error("Failed to record trade during reconciliation: %s", exc)

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
            "Reconciled orders: %s",
            ", ".join(f"{entry['order_id']} -> {entry['status']}" for entry in reconciled),
        )
        self.risk_controller.update_peak_equity()
        return reconciled

    def get_reconciliation_log(self) -> List[Dict[str, Any]]:
        """Return the recorded order reconciliation events."""
        return list(self.reconciliation_log)

    def _resolve_strategy_names(self, requested: List[str]) -> Optional[List[str]]:
        """Normalise requested strategy identifiers against the runner registry."""
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
        """Return the most recent non-zero signal row from a strategy run."""
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
        """Calculate an executable quantity based on account state and action."""
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
        """Convert a strategy result object into a serialisable dictionary."""
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


    def refresh_broker_risk_limits(self) -> None:
        """Reload broker risk limit configuration."""
        self.broker_risk_limits = self._load_broker_risk_limits()

    def _load_broker_risk_limits(self) -> Dict[str, Any]:
        """Load broker risk limit settings from application config."""
        section = app_config.get("automation.broker_risk_limits", {})
        if not isinstance(section, dict):
            return {"enabled": False}

        def _safe_float(value: Any) -> Optional[float]:
            try:
                if value is None:
                    return None
                return float(value)
            except (TypeError, ValueError):
                return None

        def _safe_int(value: Any) -> Optional[int]:
            try:
                if value is None:
                    return None
                return int(value)
            except (TypeError, ValueError):
                return None

        portfolio_raw = section.get("portfolio") or {}
        per_symbol_raw = section.get("per_symbol") or {}

        portfolio_limits = {
            "max_gross_exposure": _safe_float(portfolio_raw.get("max_gross_exposure")),
            "max_symbol_percent": _safe_float(portfolio_raw.get("max_symbol_percent")),
            "max_position_count": _safe_int(portfolio_raw.get("max_position_count")),
            "max_single_order_notional": _safe_float(portfolio_raw.get("max_single_order_notional")),
        }

        parsed_symbol_limits: Dict[str, Dict[str, Optional[float]]] = {}
        for raw_key, raw_limits in per_symbol_raw.items():
            if not isinstance(raw_limits, dict):
                continue
            key = str(raw_key).upper()
            if key in {"DEFAULT", "*"}:
                key = "__DEFAULT__"
            parsed_symbol_limits[key] = {
                "max_position_qty": _safe_float(raw_limits.get("max_position_qty")),
                "max_position_notional": _safe_float(raw_limits.get("max_position_notional")),
                "max_order_notional": _safe_float(raw_limits.get("max_order_notional")),
            }

        return {
            "enabled": bool(section.get("enabled", False)),
            "strict": bool(section.get("strict", True)),
            "portfolio": portfolio_limits,
            "per_symbol": parsed_symbol_limits,
        }

    def _resolve_symbol_limits(self, symbol: str) -> Dict[str, Optional[float]]:
        """Return the configured limits for the given symbol (or defaults)."""
        limits = self.broker_risk_limits or {}
        per_symbol = limits.get("per_symbol") or {}
        key = symbol.upper()
        if key in per_symbol:
            return per_symbol[key]
        for fallback in ("__DEFAULT__", "DEFAULT", "*"):
            if fallback in per_symbol:
                return per_symbol[fallback]
        return {}

    def _build_positions_state(
        self, positions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """Normalise broker position payloads into internal state dict."""
        state: Dict[str, Dict[str, float]] = {}
        for entry in positions or []:
            symbol = str(entry.get("symbol") or "").upper()
            if not symbol:
                continue
            quantity = self._safe_number(entry.get("quantity"))
            current_price = entry.get("current_price")
            if current_price is None:
                current_price = entry.get("average_price")
            price_value = self._safe_number(current_price)
            market_value = entry.get("market_value")
            if market_value is None:
                market_value = quantity * price_value
            market_value = self._safe_number(market_value)
            state[symbol] = {
                "quantity": quantity,
                "market_value": market_value,
                "price": price_value if price_value > 0 else None,
            }
        return state

    def _resolve_trade_price(
        self, symbol: str, signal: TradingSignal
    ) -> Optional[float]:
        """Best-effort resolution of the trade price used for risk projections."""
        if signal.price is not None:
            price = self._safe_number(signal.price)
            return price if price > 0 else None

        price = None
        try:
            price = self._safe_number(self.broker.get_current_price(symbol))
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to query current price for %s: %s", symbol, exc)
        if price and price > 0:
            return price

        try:
            latest_trade = self.broker.get_latest_trade(symbol)
            if isinstance(latest_trade, dict):
                for key in ("price", "last", "trade_price", "close"):
                    candidate = latest_trade.get(key)
                    if candidate is not None:
                        price = self._safe_number(candidate)
                        if price > 0:
                            return price
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("Failed to query latest trade for %s: %s", symbol, exc)

        return None

    def _evaluate_broker_limits_for_trade(
        self,
        *,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        positions_state: Dict[str, Dict[str, float]],
        gross_exposure: float,
        equity: float,
        current_position_count: int,
    ) -> Tuple[bool, str, float, float, float, int]:
        """Check whether executing a trade would breach configured broker limits."""
        limits = self.broker_risk_limits or {}
        symbol_key = symbol.upper()
        direction = 1 if action.lower() == "buy" else -1 if action.lower() == "sell" else None
        if direction is None:
            return (
                False,
                f"Unsupported action {action}",
                positions_state.get(symbol_key, {}).get("quantity", 0.0),
                positions_state.get(symbol_key, {}).get("market_value", 0.0),
                gross_exposure,
                current_position_count,
            )

        qty = float(quantity)
        if qty <= 0:
            return (
                False,
                "Computed trade quantity is not positive",
                positions_state.get(symbol_key, {}).get("quantity", 0.0),
                positions_state.get(symbol_key, {}).get("market_value", 0.0),
                gross_exposure,
                current_position_count,
            )

        price = self._safe_number(price)
        if price <= 0:
            return (
                False,
                "Unable to resolve positive trade price for broker limit evaluation",
                positions_state.get(symbol_key, {}).get("quantity", 0.0),
                positions_state.get(symbol_key, {}).get("market_value", 0.0),
                gross_exposure,
                current_position_count,
            )

        existing_entry = positions_state.get(symbol_key, {"quantity": 0.0, "market_value": 0.0})
        existing_qty = self._safe_number(existing_entry.get("quantity"))
        existing_value = self._safe_number(existing_entry.get("market_value"))

        new_qty = existing_qty + direction * qty
        new_market_value = new_qty * price
        trade_notional = abs(qty * price)
        projected_gross = max(0.0, gross_exposure - abs(existing_value) + abs(new_market_value))

        had_position = not math.isclose(existing_qty, 0.0, abs_tol=1e-9)
        has_position = not math.isclose(new_qty, 0.0, abs_tol=1e-9)
        projected_position_count = current_position_count
        if not had_position and has_position:
            projected_position_count += 1
        elif had_position and not has_position:
            projected_position_count = max(0, projected_position_count - 1)

        if not limits.get("enabled", False):
            return True, "", new_qty, new_market_value, projected_gross, projected_position_count

        symbol_limits = self._resolve_symbol_limits(symbol_key)
        max_qty = symbol_limits.get("max_position_qty")
        if max_qty is not None and abs(new_qty) > max_qty + 1e-9:
            reason = (
                f"{symbol_key} position size {abs(new_qty):,.2f} exceeds configured "
                f"limit {max_qty:,.2f}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        max_notional = symbol_limits.get("max_position_notional")
        if max_notional is not None and abs(new_market_value) > max_notional + 1e-6:
            reason = (
                f"{symbol_key} exposure ${abs(new_market_value):,.2f} exceeds configured "
                f"limit ${max_notional:,.2f}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        max_order_notional = symbol_limits.get("max_order_notional")
        if max_order_notional is not None and trade_notional > max_order_notional + 1e-6:
            reason = (
                f"{symbol_key} order notional ${trade_notional:,.2f} exceeds configured "
                f"limit ${max_order_notional:,.2f}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        portfolio_limits = limits.get("portfolio") or {}
        max_single_order = portfolio_limits.get("max_single_order_notional")
        if max_single_order is not None and trade_notional > max_single_order + 1e-6:
            reason = (
                f"Order notional ${trade_notional:,.2f} exceeds broker-wide cap "
                f"${max_single_order:,.2f}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        max_gross = portfolio_limits.get("max_gross_exposure")
        if max_gross is not None and projected_gross > max_gross + 1e-6:
            reason = (
                f"Projected gross exposure ${projected_gross:,.2f} exceeds broker "
                f"limit ${max_gross:,.2f}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        max_symbol_percent = portfolio_limits.get("max_symbol_percent")
        if (
            max_symbol_percent is not None
            and equity > 0
            and abs(new_market_value) / equity > max_symbol_percent + 1e-6
        ):
            reason = (
                f"{symbol_key} allocation {abs(new_market_value) / equity:.2%} exceeds "
                f"broker limit {max_symbol_percent:.2%}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        max_position_count = portfolio_limits.get("max_position_count")
        if (
            max_position_count is not None
            and projected_position_count > max_position_count
        ):
            reason = (
                f"Projected open position count {projected_position_count} exceeds "
                f"broker cap {max_position_count}"
            )
            return False, reason, existing_qty, existing_value, gross_exposure, current_position_count

        return True, "", new_qty, new_market_value, projected_gross, projected_position_count

    def check_broker_risk_preconditions(self) -> Tuple[bool, str, Dict[str, Any]]:
        """Evaluate whether the current portfolio fits within broker risk limits."""
        self.refresh_broker_risk_limits()
        limits = self.broker_risk_limits or {}
        if not limits.get("enabled", False):
            self._cached_risk_state = None
            return True, "", {}

        account_info = self.executor.get_account_info()
        balance = account_info.get("balance") or {}
        positions_state = self._build_positions_state(account_info.get("positions") or [])

        equity = self._safe_number(balance.get("equity"))
        cash = self._safe_number(balance.get("cash"))
        gross_exposure = sum(abs(entry["market_value"]) for entry in positions_state.values())
        position_count = sum(
            1 for entry in positions_state.values() if not math.isclose(entry["quantity"], 0.0, abs_tol=1e-9)
        )

        context = {
            "equity": equity,
            "cash": cash,
            "gross_exposure": gross_exposure,
            "position_count": position_count,
            "positions": {symbol: dict(data) for symbol, data in positions_state.items()},
        }

        portfolio_limits = limits.get("portfolio") or {}
        max_gross = portfolio_limits.get("max_gross_exposure")
        if max_gross is not None and gross_exposure >= max_gross:
            reason = (
                f"Gross exposure ${gross_exposure:,.2f} already meets configured "
                f"cap ${max_gross:,.2f}"
            )
            logger.warning("Broker risk pre-check failed: %s", reason)
            self._cached_risk_state = context
            return False, reason, context

        max_position_count = portfolio_limits.get("max_position_count")
        if max_position_count is not None and position_count >= max_position_count:
            reason = (
                f"Open positions {position_count} already meet broker cap "
                f"{max_position_count}"
            )
            logger.warning("Broker risk pre-check failed: %s", reason)
            self._cached_risk_state = context
            return False, reason, context

        max_symbol_percent = portfolio_limits.get("max_symbol_percent")
        if max_symbol_percent is not None and equity > 0:
            for symbol_key, entry in positions_state.items():
                allocation = abs(entry["market_value"]) / equity
                if allocation > max_symbol_percent + 1e-6:
                    reason = (
                        f"{symbol_key} allocation {allocation:.2%} already exceeds "
                        f"broker cap {max_symbol_percent:.2%}"
                    )
                    logger.warning("Broker risk pre-check failed: %s", reason)
                    self._cached_risk_state = context
                    return False, reason, context

        for symbol_key, entry in positions_state.items():
            symbol_limits = self._resolve_symbol_limits(symbol_key)
            if not symbol_limits:
                continue
            max_qty = symbol_limits.get("max_position_qty")
            if max_qty is not None and abs(entry["quantity"]) > max_qty + 1e-9:
                reason = (
                    f"{symbol_key} position size {abs(entry['quantity']):,.2f} already "
                    f"exceeds configured limit {max_qty:,.2f}"
                )
                logger.warning("Broker risk pre-check failed: %s", reason)
                self._cached_risk_state = context
                return False, reason, context

            max_notional = symbol_limits.get("max_position_notional")
            if max_notional is not None and abs(entry["market_value"]) > max_notional + 1e-6:
                reason = (
                    f"{symbol_key} exposure ${abs(entry['market_value']):,.2f} already "
                    f"exceeds configured limit ${max_notional:,.2f}"
                )
                logger.warning("Broker risk pre-check failed: %s", reason)
                self._cached_risk_state = context
                return False, reason, context

        self._cached_risk_state = {
            "positions_state": {symbol: dict(data) for symbol, data in positions_state.items()},
            "equity": equity,
            "gross_exposure": gross_exposure,
            "position_count": position_count,
        }
        return True, "", context

    @staticmethod
    def _safe_number(value: Any) -> float:
        """Convert a value to float, returning 0.0 when conversion fails."""
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

