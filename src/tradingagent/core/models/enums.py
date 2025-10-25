#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enums Module - 公共枚举类型定义

定义交易系统中使用的所有枚举类型。
"""

from enum import Enum


class OrderType(Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "pending"
    PARTIAL_FILLED = "partial_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class TradingMode(Enum):
    """交易模式"""
    SIMULATION = "simulation"
    LIVE = "live"
    PAPER = "paper"
