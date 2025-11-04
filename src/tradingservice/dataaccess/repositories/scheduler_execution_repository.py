"""
调度执行结果仓储。

为自动调度任务的执行记录、生成的订单以及风险快照提供持久化能力。
"""

from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy.orm import Session

from ..models import (
    AutomationRiskSnapshot,
    AutomationTaskExecution,
    AutomationTaskOrder,
)


class SchedulerExecutionRepository:
    """面向调度执行结果的 SQLAlchemy 会话封装。"""

    def __init__(self, session: Session):
        self.session = session

    # --------------------------------------------------------------------- #
    # 对外接口
    # --------------------------------------------------------------------- #
    def record_execution(
        self,
        *,
        task_id: str,
        task_name: str,
        scheduler_status: str,
        orchestration_status: str,
        started_at: Optional[datetime],
        completed_at: Optional[datetime],
        execution_summary: Dict[str, Any],
        payload: Dict[str, Any],
        symbol_details: Dict[str, Any],
        account_snapshot: Optional[Dict[str, Any]],
        risk_snapshot: Optional[Dict[str, Any]],
        task_errors: Optional[Iterable[str]],
        orders: Iterable[Dict[str, Any]],
    ) -> AutomationTaskExecution:
        """以事务方式保存执行记录、订单信息与风险快照。"""
        execution = AutomationTaskExecution(
            task_id=task_id,
            task_name=task_name,
            scheduler_status=scheduler_status,
            orchestration_status=orchestration_status,
            started_at=started_at,
            completed_at=completed_at,
            executed_signals=_safe_int(execution_summary.get("executed_signals")),
            rejected_signals=_safe_int(execution_summary.get("rejected_signals")),
            total_signals=_safe_int(
                execution_summary.get("total_signals")
                or execution_summary.get("total")
            ),
            order_count=_safe_int(execution_summary.get("orders")),
            task_errors_json=_json_dump(task_errors or []),
            symbol_details_json=_json_dump(symbol_details or {}),
            summary_json=_json_dump(execution_summary or {}),
            account_snapshot_json=_json_dump(account_snapshot or {}),
            payload_json=_json_dump(payload or {}),
        )

        try:
            self.session.add(execution)
            self.session.flush()

            order_models = self._build_order_models(execution.id, orders)
            if order_models:
                self.session.add_all(order_models)
                execution.order_count = execution.order_count or len(order_models)

            if risk_snapshot:
                risk_model = self._build_risk_snapshot_model(
                    execution.id, risk_snapshot
                )
                self.session.add(risk_model)

            self.session.commit()
            self.session.refresh(execution)
            return execution
        except Exception:
            self.session.rollback()
            raise

    def close(self) -> None:
        """关闭底层 SQLAlchemy 会话。"""
        self.session.close()

    # ------------------------------------------------------------------ #
    # 内部辅助方法
    # ------------------------------------------------------------------ #
    def _build_order_models(
        self, execution_id: int, orders: Iterable[Dict[str, Any]]
    ) -> List[AutomationTaskOrder]:
        models: List[AutomationTaskOrder] = []
        for order in orders or []:
            if not isinstance(order, dict):
                continue

            order_id = str(order.get("id") or order.get("order_id") or "").strip()
            if not order_id:
                continue

            models.append(
                AutomationTaskOrder(
                    execution_id=execution_id,
                    order_id=order_id,
                    symbol=_safe_str(
                        order.get("symbol")
                        or order.get("instrument")
                        or order.get("ticker")
                    ),
                    action=_safe_str(
                        order.get("side")
                        or order.get("action")
                        or order.get("type")
                    ),
                    status=_safe_str(order.get("status")),
                    quantity=_safe_float(
                        order.get("quantity")
                        or order.get("qty")
                        or order.get("size")
                    ),
                    filled_quantity=_safe_float(
                        order.get("filled_quantity")
                        or order.get("filled_qty")
                        or order.get("filled_size")
                    ),
                    average_price=_safe_float(
                        order.get("filled_price")
                        or order.get("average_price")
                        or order.get("avg_fill_price")
                    ),
                    submitted_at=_parse_datetime(
                        order.get("submitted_at") or order.get("created_at")
                    ),
                    completed_at=_parse_datetime(
                        order.get("completed_at")
                        or order.get("updated_at")
                        or order.get("filled_at")
                    ),
                    raw_order_json=_json_dump(order),
                )
            )

        return models

    def _build_risk_snapshot_model(
        self, execution_id: int, snapshot: Dict[str, Any]
    ) -> AutomationRiskSnapshot:
        return AutomationRiskSnapshot(
            execution_id=execution_id,
            equity=_safe_float(snapshot.get("equity")),
            cash=_safe_float(snapshot.get("cash")),
            buying_power=_safe_float(
                snapshot.get("buying_power") or snapshot.get("buyingPower")
            ),
            exposure=_safe_float(snapshot.get("exposure")),
            maintenance_margin=_safe_float(
                snapshot.get("maintenance_margin")
                or snapshot.get("maintenanceMargin")
            ),
            raw_metrics_json=_json_dump(snapshot),
        )


# ---------------------------------------------------------------------- #
# 工具函数
# ---------------------------------------------------------------------- #
def _json_dump(data: Any) -> str:
    try:
        return json.dumps(data, ensure_ascii=False, default=_json_default)
    except TypeError:
        return json.dumps(str(data), ensure_ascii=False)


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)


def _parse_datetime(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value))
        except (ValueError, OSError):
            return None
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        candidate = candidate.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            return None
    return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> Optional[str]:
    if value is None:
        return None
    value_str = str(value).strip()
    return value_str or None
