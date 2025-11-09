import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "tradingservice"
    / "services"
    / "engines"
    / "advanced_trading_engine.py"
)
spec = importlib.util.spec_from_file_location("advanced_trading_engine", MODULE_PATH)
advanced_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(advanced_module)
AdvancedTradingEngine = advanced_module.AdvancedTradingEngine


class StubDataProvider:
    """Simple in-memory provider for deterministic price history."""

    def __init__(self) -> None:
        self.frames: Dict[str, pd.DataFrame] = {}

    def set_history(self, symbol: str, frame: pd.DataFrame) -> None:
        self.frames[symbol] = frame

    def get_historical_data(self, symbol: str, *_args, **_kwargs):
        return self.frames.get(symbol)


def _price_history(length: int = 40, start_price: float = 100.0) -> pd.DataFrame:
    closes = [start_price + idx for idx in range(length)]
    return pd.DataFrame({"close": closes})


def test_analyze_market_returns_latest_signal(monkeypatch):
    """Engine should surface latest action/price/confidence when signals exist."""

    monkeypatch.setattr(advanced_module, "DataProvider", StubDataProvider)

    engine = AdvancedTradingEngine()
    engine.watch_list = ["AAPL"]

    engine.data_provider.set_history("AAPL", _price_history())

    class StubStrategy:
        def __init__(self, frame: pd.DataFrame) -> None:
            self.frame = frame

        def generate_signals(self, _data: pd.DataFrame) -> pd.DataFrame:
            return self.frame

    engine.strategy = StubStrategy(
        pd.DataFrame([{"Signal": "BUY", "Confidence": 0.85}])
    )

    signals = engine.analyze_market()

    assert "AAPL" in signals
    result = signals["AAPL"]
    assert result["action"] == "BUY"
    assert result["confidence"] == pytest.approx(0.85)
    assert result["price"] == pytest.approx(engine.data_provider.frames["AAPL"]["close"].iloc[-1])


def test_analyze_market_handles_missing_signal_column(monkeypatch, caplog):
    """Missing Signal column should be logged and skipped without raising."""

    monkeypatch.setattr(advanced_module, "DataProvider", StubDataProvider)

    engine = AdvancedTradingEngine()
    engine.watch_list = ["AAPL"]
    engine.data_provider.set_history("AAPL", _price_history())

    class MissingSignalStrategy:
        def generate_signals(self, _data: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame([{"Confidence": 0.9}])

    engine.strategy = MissingSignalStrategy()

    with caplog.at_level(logging.DEBUG, logger="AdvancedTrading"):
        signals = engine.analyze_market()

    assert "AAPL" not in signals
    assert any("Missing required columns" in record.message for record in caplog.records)


def test_analyze_market_ignores_nan_rows(monkeypatch):
    """Rows with NaN signals should be ignored so valid signals still surface."""

    monkeypatch.setattr(advanced_module, "DataProvider", StubDataProvider)

    engine = AdvancedTradingEngine()
    engine.watch_list = ["MSFT"]
    engine.data_provider.set_history("MSFT", _price_history())

    class NaNStrategy:
        def generate_signals(self, _data: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame(
                [
                    {"Signal": float("nan"), "Confidence": 0.9},
                    {"Signal": "SELL", "Confidence": 0.25},
                ]
            )

    engine.strategy = NaNStrategy()

    signals = engine.analyze_market()

    assert "MSFT" in signals
    assert signals["MSFT"]["action"] == "SELL"


def test_analyze_market_accepts_custom_required_columns(monkeypatch):
    """Engine should honour caller-provided required columns."""

    monkeypatch.setattr(advanced_module, "DataProvider", StubDataProvider)

    engine = AdvancedTradingEngine()
    engine.watch_list = ["TSLA"]
    engine.data_provider.set_history("TSLA", _price_history())

    class LowerCaseStrategy:
        def generate_signals(self, _data: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame([{"signal": "BUY", "Confidence": 0.6}])

    engine.strategy = LowerCaseStrategy()

    signals = engine.analyze_market(required_columns=("signal",))

    assert "TSLA" in signals
    assert signals["TSLA"]["action"] == "BUY"
