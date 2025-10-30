"""
Unit tests for the realtime signal monitor.
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from src.tradingservice.services.automation.signal_monitor import SignalMonitor


class _StubDataProvider:
    def __init__(self, frame: pd.DataFrame):
        self.frame = frame
        self.calls = []

    def get_historical_data(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.frame


def test_build_minute_frame_filters_to_lookback_window_and_normalizes_columns():
    base_end = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    index = pd.date_range(end=base_end, periods=180, freq="min", tz="UTC")
    frame = pd.DataFrame(
        {
            "Open": range(len(index)),
            "Close": range(len(index)),
            "Volume": [100] * len(index),
        },
        index=index,
    )

    provider = _StubDataProvider(frame)
    monitor = SignalMonitor(data_provider=provider, lookback_minutes=60)

    result = monitor._build_minute_frame("AAPL")

    assert not result.empty
    assert all(col.islower() for col in result.columns)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=monitor.lookback_window + 1)
    assert result.index.min() >= cutoff.replace(tzinfo=None)
    assert len(result) <= monitor.lookback_window + 5
