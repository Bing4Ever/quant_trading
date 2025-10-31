"""
Registry of manual test scripts maintained outside the automated pytest suite.
"""

from __future__ import annotations

MANUAL_TEST_SCRIPTS = [
    {
        "path": "tests/manual/test_chart_generator_price.py",
        "description": (
            "Smoke test for InteractiveChartGenerator.create_price_signal_chart; "
            "saves a price/signal PNG for inspection."
        ),
        "default_symbol": "AAPL",
    },
]

__all__ = ["MANUAL_TEST_SCRIPTS"]
