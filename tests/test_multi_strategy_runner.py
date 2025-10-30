import numpy as np
import pandas as pd
import pytest

from src.tradingagent.modules.strategies.multi_strategy_runner import (
    MultiStrategyRunner,
)


@pytest.fixture
def sample_market_data():
    """Synthetic OHLCV data for testing."""
    index = pd.date_range("2024-01-01", periods=120, freq="D")
    base = np.linspace(100, 120, len(index))
    prices = base + np.sin(np.arange(len(index))) * 0.5

    return pd.DataFrame(
        {
            "Open": prices - 0.2,
            "High": prices + 0.3,
            "Low": prices - 0.4,
            "Close": prices,
            "Adj Close": prices,
            "Volume": np.full(len(index), 1_000),
        },
        index=index,
    )


def test_get_market_data_normalizes_columns(monkeypatch, sample_market_data):
    """Ensure OHLCV columns are normalised regardless of provider."""

    def fake_fetch(self, symbol, start_date=None, end_date=None, interval="1d"):
        return sample_market_data.copy()

    monkeypatch.setattr(
        "src.tradingagent.modules.strategies.multi_strategy_runner.DataFetcher.fetch_stock_data",
        fake_fetch,
    )

    runner = MultiStrategyRunner()
    data = runner.get_market_data("AAPL", period="1mo", interval="1d")

    assert {"open", "high", "low", "close", "volume"}.issubset(data.columns)


def test_run_all_strategies_returns_results(monkeypatch, sample_market_data):
    """Running the runner should return StrategyResult objects per strategy."""

    def fake_fetch(self, symbol, start_date=None, end_date=None, interval="1d"):
        return sample_market_data.copy()

    monkeypatch.setattr(
        "src.tradingagent.modules.strategies.multi_strategy_runner.DataFetcher.fetch_stock_data",
        fake_fetch,
    )

    runner = MultiStrategyRunner()
    results = runner.run_all_strategies("AAPL", period="1mo", interval="1d")

    assert results, "Expected results for all strategies"
    for name, result in results.items():
        assert result.symbol == "AAPL"
        assert result.strategy_name == name


def test_strategy_alias_shares_same_instance():
    """Alias (e.g., 'ma') should reference the same strategy object."""
    runner = MultiStrategyRunner()
    main_strategy = runner.strategies.get("moving_average")
    assert main_strategy is not None, "Moving average strategy missing"

    alias_strategy = runner.strategies.get("ma")
    assert alias_strategy is main_strategy, "Alias should map to the same instance"
