#!/usr/bin/env python3
"""
围绕 TaskManager 实时订单对账逻辑的单元测试。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tradingagent import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
)
from src.tradingagent.core.interfaces import IBroker
import importlib.util
import importlib.machinery

def _load_task_manager():
    module_path = PROJECT_ROOT / "src" / "tradingservice" / "services" / "orchestration" / "task_manager.py"
    module_name = "src.tradingservice.services.orchestration.task_manager"

    # 构建最小包结构，避免触发 src.tradingservice.__init__ 的重型依赖
    package_roots = {
        "src": PROJECT_ROOT / "src",
        "src.tradingservice": PROJECT_ROOT / "src" / "tradingservice",
        "src.tradingservice.services": PROJECT_ROOT / "src" / "tradingservice" / "services",
        "src.tradingservice.services.orchestration": PROJECT_ROOT / "src" / "tradingservice" / "services" / "orchestration",
    }

    for pkg_name, pkg_path in package_roots.items():
        if pkg_name not in sys.modules:
            module = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(pkg_name, loader=None))
            module.__file__ = str(pkg_path / "__init__.py")
            module.__path__ = [str(pkg_path)]
            sys.modules[pkg_name] = module

    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
        submodule_search_locations=[str(module_path.parent)],
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "src.tradingservice.services.orchestration"
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module

task_manager_module = _load_task_manager()
TaskManager = task_manager_module.TaskManager


class FakeBroker(IBroker):
    """
    极简经纪商桩对象：在内存中记录订单，便于离线测试任务管理器。
    """

    def __init__(self) -> None:
        self.connected = True
        self.orders: Dict[str, Order] = {}
        self.status_overrides: Dict[str, OrderStatus] = {}
        self.balance = {"cash": 100_000.0, "equity": 100_000.0, "buying_power": 100_000.0}
        self.positions: List[Position] = []
        self.price_lookup: Dict[str, float] = {}

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self) -> bool:
        self.connected = False
        return True

    def is_connected(self) -> bool:
        return self.connected

    def submit_order(self, order: Order) -> bool:
        order.status = OrderStatus.PENDING
        self.orders[order.order_id] = order
        return True

    def cancel_order(self, order_id: str) -> bool:
        if order_id in self.orders:
            self.status_overrides[order_id] = OrderStatus.CANCELLED
            return True
        return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        order = self.orders.get(order_id)
        if not order:
            return None

        status = self.status_overrides.get(order_id, OrderStatus.PENDING)
        order.status = status
        terminal_status = {OrderStatus.FILLED}
        partial_status = getattr(OrderStatus, "PARTIAL_FILLED", None)
        if partial_status is not None:
            terminal_status.add(partial_status)
        if status in terminal_status:
            order.filled_quantity = order.quantity
            order.filled_price = self.price_lookup.get(order.symbol, 100.0)
        return order

    def get_account_balance(self) -> Dict[str, float]:
        return dict(self.balance)

    def get_positions(self) -> List[Position]:
        return list(self.positions)

    def get_current_price(self, symbol: str) -> Optional[float]:
        return self.price_lookup.get(symbol, 100.0)

    def get_latest_trade(self, symbol: str) -> Optional[Dict[str, Any]]:
        price = self.get_current_price(symbol)
        if price is None:
            return None
        return {"symbol": symbol, "price": price, "size": 1.0, "timestamp": "simulated"}

    def get_historical_bars(
        self,
        symbol: str,
        start,
        end,
        interval: str,
        *,
        adjustment: str = "raw",
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return []


def test_task_manager_reconcile_returns_filled_updates():
    broker = FakeBroker()
    manager = TaskManager(broker=broker)

    result = manager.process_realtime_signal(
        symbol="AAPL",
        strategy_name="stub",
        action="buy",
        signal_strength=1.0,
        confidence=0.9,
        reason="unit-test",
    )

    order_id = result.get("order_id")
    assert order_id is not None
    assert order_id in manager.executor.pending_orders

    # 模拟经纪商回填成交，以验证对账流程
    broker.status_overrides[order_id] = OrderStatus.FILLED
    broker.price_lookup["AAPL"] = 123.45

    updates = manager.reconcile_orders()
    assert updates, "应当返回已成交订单的对账结果"

    update = updates[0]
    assert update["order_id"] == order_id
    assert update["status"] == OrderStatus.FILLED.value
    assert update["order"]["filled_price"] == 123.45
    assert order_id not in manager.executor.pending_orders
    risk_snapshot = update.get("risk_snapshot") or {}
    assert risk_snapshot.get("equity")  # 应返回最新权益数据
    assert manager.risk_controller.daily_trades, "应记录成交到风控日内交易列表"
