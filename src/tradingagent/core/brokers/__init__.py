#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker helpers and factory registrations used across the trading agent.
"""

from __future__ import annotations

from typing import Any, Dict

from .broker_factory import BrokerFactory, BrokerBuilder
from .simulation_broker import SimulationBroker
from .alpaca_broker import AlpacaBroker
from .alpha_vantage_broker import AlphaVantageBroker
from .yfinance_broker import YFinanceBroker


def _simulation_builder(**kwargs: Dict[str, Any]) -> SimulationBroker:
    """Create a SimulationBroker with any supplied overrides."""
    return SimulationBroker(**kwargs)


def _alpaca_builder(**kwargs: Dict[str, Any]) -> AlpacaBroker:
    """?z,??? Alpaca ?^,?+?rz?_<a?,"""
    api_key = kwargs.pop("api_key", None)
    api_secret = kwargs.pop("api_secret", None)

    if not api_key or not api_secret:
        missing = []
        if not api_key:
            missing.append("api_key")
        if not api_secret:
            missing.append("api_secret")
        raise ValueError(
            f"Alpaca broker requires credentials ({', '.join(missing)}). "
            "Supply them via configuration or environment variables."
        )

    def _clean_credential(value: str, label: str) -> str:
        cleaned = value.strip()
        if cleaned != value:
            raise ValueError(f"{label} contains surrounding whitespace.")
        if not cleaned.isalnum():
            raise ValueError(
                f"{label} must be alphanumeric and cannot include special characters."
            )
        return cleaned

    api_key = _clean_credential(api_key, "api_key")
    api_secret = _clean_credential(api_secret, "api_secret")

    allowed_kwargs = {"paper", "data_feed", "default_time_in_force", "base_url"}
    broker_kwargs = {k: v for k, v in kwargs.items() if k in allowed_kwargs}

    return AlpacaBroker(
        api_key=api_key,
        api_secret=api_secret,
        **broker_kwargs,
    )

def _yfinance_builder(**kwargs: Dict[str, Any]) -> YFinanceBroker:
    """Return a configured YFinanceBroker instance."""
    allowed = {"auto_adjust", "prepost"}
    params = {k: v for k, v in kwargs.items() if k in allowed}
    return YFinanceBroker(**params)


def _alpha_vantage_builder(**kwargs: Dict[str, Any]) -> AlphaVantageBroker:
    """Create an AlphaVantageBroker after validating API credentials."""
    api_key = kwargs.get("api_key") or kwargs.get("alpha_vantage_api_key")
    if not api_key:
        raise ValueError("Alpha Vantage broker requires an 'api_key'.")
    return AlphaVantageBroker(api_key=api_key)


# Register built-in brokers
BrokerFactory.register("simulation", _simulation_builder, is_default=True)
BrokerFactory.register("alpaca", _alpaca_builder)
BrokerFactory.register("yfinance", _yfinance_builder)
BrokerFactory.register("alpha_vantage", _alpha_vantage_builder)

__all__ = [
    "BrokerFactory",
    "BrokerBuilder",
    "SimulationBroker",
    "AlpacaBroker",
    "YFinanceBroker",
    "AlphaVantageBroker",
]
