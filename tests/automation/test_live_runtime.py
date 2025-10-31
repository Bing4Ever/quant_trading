#!/usr/bin/env python3
"""
针对 LiveTradingRuntime 组合逻辑的单元测试。
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.tradingagent import Order, OrderStatus
from src.tradingagent.core.interfaces import IBroker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _bootstrap_packages() -> None:
    package_roots: Dict[str, Path] = {
        "src": PROJECT_ROOT / "src",
        "src.tradingservice": PROJECT_ROOT / "src" / "tradingservice",
        "src.tradingservice.services": PROJECT_ROOT / "src" / "tradingservice" / "services",
        "src.tradingservice.services.automation": PROJECT_ROOT / "src" / "tradingservice" / "services" / "automation",
        "src.tradingservice.services.orchestration": PROJECT_ROOT / "src" / "tradingservice" / "services" / "orchestration",
    }

    for pkg_name, pkg_path in package_roots.items():
        if pkg_name not in sys.modules:
            module = importlib.util.module_from_spec(importlib.machinery.ModuleSpec(pkg_name, loader=None))
            module.__file__ = str(pkg_path / "__init__.py")
            module.__path__ = [str(pkg_path)]
            sys.modules[pkg_name] = module


def _load_module(module_name: str, relative_path: str, package_name: str):
    module_path = PROJECT_ROOT / "src" / relative_path
    spec = importlib.util.spec_from_file_location(
        module_name,
        module_path,
        submodule_search_locations=[str(module_path.parent)],
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package_name
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    parent = sys.modules.get(package_name)
    if parent is not None:
        setattr(parent, module_name.rsplit(".", 1)[-1], module)
    return module


_bootstrap_packages()

task_manager_module = _load_module(
    "src.tradingservice.services.orchestration.task_manager",
    "tradingservice/services/orchestration/task_manager.py",
    "src.tradingservice.services.orchestration",
)
orchestration_pkg = sys.modules["src.tradingservice.services.orchestration"]
for attr in ("Task", "TaskManager", "TaskStatus"):
    if hasattr(task_manager_module, attr):
        setattr(orchestration_pkg, attr, getattr(task_manager_module, attr))

live_runtime_module = _load_module(
    "src.tradingservice.services.automation.live_runtime",
    "tradingservice/services/automation/live_runtime.py",
    "src.tradingservice.services.automation",
)
automation_pkg = sys.modules["src.tradingservice.services.automation"]
if hasattr(live_runtime_module, "LiveTradingRuntime"):
    setattr(automation_pkg, "LiveTradingRuntime", live_runtime_module.LiveTradingRuntime)

LiveTradingRuntime = live_runtime_module.LiveTradingRuntime


class StubBroker(IBroker):
    def __init__(self) -> None:
        self.connected = True

    def connect(self) -> bool:
        self.connected = True
        return True

    def disconnect(self) -> bool:
        self.connected = False
        return True

    def is_connected(self) -> bool:
        return self.connected

    def submit_order(self, order: Order) -> bool:  # pragma: no cover - 未在该测试中调用
        order.status = OrderStatus.PENDING
        return True

    def cancel_order(self, order_id: str) -> bool:  # pragma: no cover - 未在该测试中调用
        return True

    def get_order_status(self, order_id: str) -> Optional[Order]:  # pragma: no cover
        return None

    def get_account_balance(self) -> Dict[str, float]:
        return {"cash": 100_000.0, "equity": 100_000.0, "buying_power": 100_000.0}

    def get_positions(self) -> List:
        return []

    def get_current_price(self, symbol: str) -> Optional[float]:
        return 100.0


class StubProvider:
    def __init__(self) -> None:
        self._callbacks: List[Callable] = []
        self.is_connected = False
        self.subscribed: List[str] = []

    def add_callback(self, callback: Callable) -> None:
        self._callbacks.append(callback)

    def connect(self) -> bool:
        self.is_connected = True
        return True

    def disconnect(self) -> None:
        self.is_connected = False

    def subscribe(self, symbols: List[str]) -> None:
        self.subscribed.extend(symbols)


def test_live_trading_runtime_wires_monitor_and_broker():
    broker = StubBroker()
    provider = StubProvider()

    runtime = LiveTradingRuntime(
        broker=broker,
        data_provider=provider,
        provider="yfinance",
    )

    runtime.start(["AAPL"], strategies={})

    status = runtime.status()
    assert status["broker_connected"] is True
    assert provider.is_connected is True
    assert provider.subscribed == ["AAPL"]

    runtime.stop()
    assert provider.is_connected is False
