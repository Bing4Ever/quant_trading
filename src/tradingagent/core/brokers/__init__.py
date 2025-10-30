#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker helpers.

提供券商工厂及内置实现注册, 方便通过标识选择不同券商。
"""

from __future__ import annotations

from typing import Any, Dict

from .broker_factory import BrokerFactory, BrokerBuilder
from .simulation_broker import SimulationBroker
from .alpaca_broker import AlpacaBroker


def _simulation_builder(**kwargs: Dict[str, Any]) -> SimulationBroker:
    """构造默认仿真券商实例。"""
    return SimulationBroker(**kwargs)


def _alpaca_builder(**kwargs: Dict[str, Any]) -> AlpacaBroker:
    """构造 Alpaca 券商实例。"""
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

    allowed_kwargs = {"paper", "data_feed", "default_time_in_force"}
    broker_kwargs = {k: v for k, v in kwargs.items() if k in allowed_kwargs}

    return AlpacaBroker(
        api_key=api_key,
        api_secret=api_secret,
        **broker_kwargs,
    )


# 注册内置券商
BrokerFactory.register("simulation", _simulation_builder, is_default=True)
BrokerFactory.register("alpaca", _alpaca_builder)

__all__ = ["BrokerFactory", "BrokerBuilder", "SimulationBroker", "AlpacaBroker"]
