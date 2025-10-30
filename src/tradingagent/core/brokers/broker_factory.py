#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Broker factory utilities.

提供一个注册表, 用于将券商标识映射到生成具体 ``IBroker`` 实例的构造函数, 方便后续通过配置切换券商。
"""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

from ..interfaces import IBroker

BrokerBuilder = Callable[..., IBroker]


class BrokerFactory:
    """券商工厂, 负责按标识创建对应的券商实例。"""

    _registry: Dict[str, BrokerBuilder] = {}
    _default_id: Optional[str] = None

    @classmethod
    def register(
        cls,
        broker_id: str,
        builder: BrokerBuilder,
        *,
        is_default: bool = False,
    ) -> None:
        """
        注册券商构造器。

        Args:
            broker_id: 券商标识 (例如 ``"simulation"`` 或 ``"alpaca"``)。
            builder: 可调用对象, 返回一个 ``IBroker`` 实例。
            is_default: 是否将该券商设为默认值。
        """
        key = broker_id.lower()
        cls._registry[key] = builder
        if is_default or cls._default_id is None:
            cls._default_id = key

    @classmethod
    def unregister(cls, broker_id: str) -> None:
        """
        注销券商构造器。

        Args:
            broker_id: 需要移除的券商标识。
        """
        key = broker_id.lower()
        cls._registry.pop(key, None)
        if cls._default_id == key:
            cls._default_id = next(iter(cls._registry), None)

    @classmethod
    def set_default(cls, broker_id: str) -> None:
        """设置默认券商标识。"""
        key = broker_id.lower()
        if key not in cls._registry:
            raise ValueError(f"Unknown broker '{broker_id}'")
        cls._default_id = key

    @classmethod
    def get_default_id(cls) -> Optional[str]:
        """返回当前默认券商标识。"""
        return cls._default_id

    @classmethod
    def create(cls, broker_id: Optional[str] = None, **kwargs) -> IBroker:
        """
        按券商标识创建实例。

        Args:
            broker_id: 注册时使用的标识, 为空时采用默认值。
            **kwargs: 传递给构造器的额外参数。

        Returns:
            构造出的 ``IBroker`` 实例。

        Raises:
            ValueError: 当标识不存在或注册表为空时抛出。
        """
        key = (broker_id or cls._default_id or "").lower()
        if not key:
            raise ValueError("No broker registered and no identifier provided.")

        try:
            builder = cls._registry[key]
        except KeyError as exc:
            raise ValueError(f"Unknown broker '{broker_id}'") from exc

        return builder(**kwargs)

    @classmethod
    def registered_brokers(cls) -> Iterable[str]:
        """返回已注册的券商标识列表。"""
        return tuple(cls._registry.keys())


__all__ = ["BrokerFactory", "BrokerBuilder"]
