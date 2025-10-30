"""
Unit tests for the realtime monitor coordination layer.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.tradingservice.services.automation import RealTimeMonitor
from src.tradingservice.services.automation.automation_models import TradingSignal
from src.tradingservice.services.automation.realtime_provider import RealTimeDataProvider


class _DummyProvider(RealTimeDataProvider):
    def connect(self) -> bool:  # pragma: no cover - simple stub
        self.is_connected = True
        return True

    def disconnect(self) -> None:  # pragma: no cover - simple stub
        self.is_connected = False

    def subscribe(self, symbols):  # pragma: no cover - simple stub
        self.subscribed = list(symbols)


class _RecordingTaskManager:
    def __init__(self):
        self.calls = []

    def process_realtime_signal(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "executed",
            "order_id": "test-order-1",
            "risk_check": "approved",
        }


def test_execute_signal_routes_to_task_manager_and_logs_result():
    task_manager = _RecordingTaskManager()
    monitor = RealTimeMonitor(data_provider=_DummyProvider(), task_manager=task_manager)

    signal = TradingSignal(
        symbol="AAPL",
        signal_type="BUY",
        strength=0.8,
        price=195.25,
        timestamp=datetime.now(timezone.utc),
        strategy_name="mean_reversion",
        confidence=0.9,
        metadata={
            "reason": "crossover confirmation",
            "target_price": 197.0,
            "extra": "value",
        },
    )

    result = monitor._execute_signal(signal)

    assert result is not None
    assert result["status"] == "executed"
    assert "order_id" in result
    assert "received_at" in result
    assert monitor.execution_log[-1] == result

    recorded = task_manager.calls[0]
    assert recorded["symbol"] == "AAPL"
    assert recorded["strategy_name"] == "mean_reversion"
    assert recorded["action"] == "buy"
    assert recorded["signal_strength"] == 0.8
    assert recorded["confidence"] == 0.9
    assert recorded["reason"] == "crossover confirmation"
    assert recorded["target_price"] == 197.0
    assert recorded["metadata"]["extra"] == "value"
