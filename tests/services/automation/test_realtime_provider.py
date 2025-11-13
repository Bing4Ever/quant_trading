#!/usr/bin/env python3
"""Tests for realtime data provider helpers."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import importlib.util
import sys
import types

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

_AUTOMATION_DIR = PROJECT_ROOT / "src" / "tradingservice" / "services" / "automation"
_STUB_PACKAGE = "_codex_rt_provider"

_package_module = types.ModuleType(_STUB_PACKAGE)
_package_module.__path__ = [str(_AUTOMATION_DIR)]
sys.modules.setdefault(_STUB_PACKAGE, _package_module)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[arg-type]
    return module


_automation_models = _load_module(
    f"{_STUB_PACKAGE}.automation_models", _AUTOMATION_DIR / "automation_models.py"
)
sys.modules[f"{_STUB_PACKAGE}.automation_models"] = _automation_models

_realtime_provider = _load_module(
    f"{_STUB_PACKAGE}.realtime_provider", _AUTOMATION_DIR / "realtime_provider.py"
)
PollingDataProvider = _realtime_provider.PollingDataProvider


class _DummyLogger:
    def __init__(self) -> None:
        self.errors: List[str] = []

    def log_error(self, *_args: Any, **_kwargs: Any) -> None:
        self.errors.append("logged")

    def log_system_event(self, *_args: Any, **_kwargs: Any) -> None:
        pass


class _DummyDataProvider:
    VOLUME = 123_456

    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def get_historical_data(
        self,
        *,
        symbol: str,
        start_date: str,
        end_date: str,
        interval: str,
    ) -> pd.DataFrame:
        self.calls.append(
            {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "interval": interval,
            }
        )
        return pd.DataFrame([{"volume": self.VOLUME, "close": 100.0}])


def _build_polling_provider() -> PollingDataProvider:
    provider = PollingDataProvider.__new__(PollingDataProvider)  # type: ignore[misc]
    provider.logger = _DummyLogger()
    provider.data_provider = _DummyDataProvider()
    provider._last_prices = {}
    provider._last_volume = {}
    provider._volume_refresh = {}
    provider._volume_refresh_interval = timedelta(minutes=5)
    return provider


def test_refresh_volume_requests_intraday_window() -> None:
    provider = _build_polling_provider()

    volume = provider._refresh_volume("AAPL")

    assert volume == _DummyDataProvider.VOLUME
    call = provider.data_provider.calls[0]
    assert "T" in call["start_date"]
    assert "T" in call["end_date"]
    start_dt = datetime.fromisoformat(call["start_date"].replace("Z", "+00:00"))
    end_dt = datetime.fromisoformat(call["end_date"].replace("Z", "+00:00"))
    assert end_dt - start_dt == timedelta(minutes=5)
    assert call["interval"] == "1m"
    assert provider._last_volume["AAPL"] == _DummyDataProvider.VOLUME
    assert "AAPL" in provider._volume_refresh
