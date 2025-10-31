#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AlpacaBroker - 使用 alpaca-py 实现的 Alpaca 券商封装。

提供 `IBroker` 兼容接口, 支持在 Paper/Live 环境下完成委托、查询与行情获取。
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Dict, List, Optional

from ..interfaces.broker import IBroker
from ..models.enums import OrderSide, OrderStatus, OrderType
from ..models.order import Order
from ..models.position import Position

logger = logging.getLogger(__name__)

try:  # pragma: no cover - 导入失败仅在未安装依赖时发生
    from alpaca.common.exceptions import APIError
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockLatestTradeRequest
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import (
        OrderSide as AlpacaOrderSide,
        OrderType as AlpacaOrderType,
        TimeInForce,
    )
    from alpaca.trading.requests import (
        LimitOrderRequest,
        MarketOrderRequest,
        StopLimitOrderRequest,
        StopOrderRequest,
    )

    _ALPACA_AVAILABLE = True
except ImportError:  # pragma: no cover
    APIError = Exception  # type: ignore
    TradingClient = None  # type: ignore
    StockHistoricalDataClient = None  # type: ignore
    StockLatestTradeRequest = None  # type: ignore
    DataFeed = None  # type: ignore
    LimitOrderRequest = None  # type: ignore
    MarketOrderRequest = None  # type: ignore
    StopLimitOrderRequest = None  # type: ignore
    StopOrderRequest = None  # type: ignore
    TimeInForce = None  # type: ignore
    AlpacaOrderSide = None  # type: ignore
    AlpacaOrderType = None  # type: ignore
    _ALPACA_AVAILABLE = False

__all__ = ["AlpacaBroker"]


class AlpacaBroker(IBroker):
    """基于 alpaca-py 的 Alpaca 券商实现。"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        *,
        paper: bool = True,
        data_feed: str = "iex",
        default_time_in_force: str = "gtc",
    ) -> None:
        """
        初始化券商实例。

        Args:
            api_key: Alpaca API Key
            api_secret: Alpaca API Secret
            paper: 是否使用 Paper 环境
            data_feed: 行情源 (iex/sip/delayed_sip/otc/...)
            default_time_in_force: 默认委托有效期
        """
        if not _ALPACA_AVAILABLE:
            raise ImportError(
                "alpaca-py 未安装, 请运行 `pip install alpaca-py` 后再试。"
            )

        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper
        self._default_tif = default_time_in_force.lower()
        self._data_feed = self._parse_data_feed(data_feed)

        self._trading_client: Optional[TradingClient] = None
        self._data_client: Optional[StockHistoricalDataClient] = None
        self._connected = False

    # ------------------------------------------------------------------ #
    # 基础连接
    # ------------------------------------------------------------------ #
    def connect(self) -> bool:
        """建立与 Alpaca 的连接。"""
        try:
            self._trading_client = TradingClient(
                self.api_key, self.api_secret, paper=self.paper
            )
            self._data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.api_secret,
                sandbox=self.paper,
            )
            # 触发一次账户查询验证凭据
            self._trading_client.get_account()
            self._connected = True
            logger.info("AlpacaBroker 已连接 (paper=%s)", self.paper)
            return True
        except APIError as exc:  # pragma: no cover - 依赖外部服务
            logger.error("连接 Alpaca 失败: %s", exc)
            self._connected = False
            self._trading_client = None
            self._data_client = None
            return False

    def disconnect(self) -> bool:
        """断开连接 (REST 客户端无需显式断连)。"""
        self._trading_client = None
        self._data_client = None
        self._connected = False
        logger.info("AlpacaBroker 已断开")
        return True

    def is_connected(self) -> bool:
        """返回当前连接状态。"""
        return self._connected

    # ------------------------------------------------------------------ #
    # 交易接口
    # ------------------------------------------------------------------ #
    def submit_order(self, order: Order) -> bool:
        """提交订单至 Alpaca。"""
        client = self._ensure_trading_client()

        side = (
            AlpacaOrderSide.BUY
            if order.side == OrderSide.BUY
            else AlpacaOrderSide.SELL
        )
        tif = self._map_time_in_force(getattr(order, "time_in_force", None))
        quantity = abs(order.quantity)
        stop_price = getattr(order, "stop_price", None)

        try:
            request = self._build_order_request(
                order_type=order.order_type,
                symbol=order.symbol,
                quantity=quantity,
                side=side,
                time_in_force=tif,
                limit_price=order.price,
                stop_price=stop_price,
                client_order_id=order.order_id,
            )
            response = client.submit_order(order_data=request)

            self._update_order_from_response(order, response)
            return True
        except APIError as exc:  # pragma: no cover
            logger.error("Alpaca 提交订单失败: %s", exc)
            order.status = OrderStatus.REJECTED
            return False

    def cancel_order(self, order_id: str) -> bool:
        """撤销指定订单。"""
        client = self._ensure_trading_client()
        try:
            remote = client.get_order_by_client_id(order_id)
            remote_id = getattr(remote, "id", None)
            if not remote_id:
                raise ValueError("无法获取 Alpaca 订单编号")
            client.cancel_order_by_id(remote_id)
            return True
        except APIError as exc:  # pragma: no cover
            logger.warning("撤销订单失败 (%s): %s", order_id, exc)
            return False
        except ValueError as exc:  # pragma: no cover - 兜底
            logger.warning("撤销订单失败 (%s): %s", order_id, exc)
            return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """查询订单状态并转换为内部模型。"""
        client = self._ensure_trading_client()
        try:
            remote = client.get_order_by_client_id(order_id)
        except APIError as exc:  # pragma: no cover
            logger.error("查询订单失败 (%s): %s", order_id, exc)
            return None

        local = Order(
            order_id=remote.client_order_id or remote.id,
            symbol=remote.symbol,
            side=self._map_order_side(remote.side),
            quantity=int(Decimal(remote.qty)),
            order_type=self._map_order_type(remote.order_type),
            price=float(remote.limit_price) if remote.limit_price else None,
            timestamp=remote.submitted_at,
            strategy=getattr(remote, "client_order_id", "") or "",
        )
        self._update_order_from_response(local, remote)
        return local

    # ------------------------------------------------------------------ #
    # 账户/持仓/行情
    # ------------------------------------------------------------------ #
    def get_account_balance(self) -> Dict[str, float]:
        """返回账户资金信息。"""
        client = self._ensure_trading_client()
        try:
            account = client.get_account()
        except APIError as exc:  # pragma: no cover
            logger.error("获取账户信息失败: %s", exc)
            return {"cash": 0.0, "equity": 0.0, "buying_power": 0.0}

        return {
            "cash": float(account.cash),
            "equity": float(account.equity),
            "buying_power": float(account.buying_power),
        }

    def get_positions(self) -> List[Position]:
        """返回当前持仓列表。"""
        client = self._ensure_trading_client()
        try:
            remote_positions = client.get_all_positions()
        except APIError as exc:  # pragma: no cover
            logger.error("获取持仓失败: %s", exc)
            return []

        positions: List[Position] = []
        for pos in remote_positions:
            quantity = int(Decimal(pos.qty))
            avg_price = float(pos.avg_entry_price)
            current_price = float(pos.current_price)
            market_value = float(pos.market_value)
            unrealized_pnl = float(pos.unrealized_pl)
            unrealized_pct = float(pos.unrealized_plpc or 0) * 100.0

            positions.append(
                Position(
                    symbol=pos.symbol,
                    quantity=quantity,
                    average_price=avg_price,
                    current_price=current_price,
                    market_value=market_value,
                    unrealized_pnl=unrealized_pnl,
                    unrealized_pnl_percent=unrealized_pct,
                )
            )

        return positions

    def get_current_price(self, symbol: str) -> Optional[float]:
        """获取最新成交价。"""
        data_client = self._ensure_data_client()
        try:
            request = StockLatestTradeRequest(
                symbol_or_symbols=symbol, feed=self._data_feed
            )
            response = data_client.get_stock_latest_trade(request)
        except APIError as exc:  # pragma: no cover
            logger.warning("获取最新价格失败 (%s): %s", symbol, exc)
            return None

        trade = response.get(symbol) if isinstance(response, dict) else response
        if not trade:
            return None
        return float(trade.price)

    # ------------------------------------------------------------------ #
    # 工具方法
    # ------------------------------------------------------------------ #
    def _ensure_trading_client(self) -> TradingClient:
        if not self._connected or self._trading_client is None:
            raise RuntimeError("AlpacaBroker 未连接, 请先调用 connect()")
        return self._trading_client

    def _ensure_data_client(self) -> StockHistoricalDataClient:
        if not self._connected or self._data_client is None:
            raise RuntimeError("AlpacaBroker 未连接, 请先调用 connect()")
        return self._data_client

    def _parse_data_feed(self, feed: str) -> DataFeed:
        feed_value = feed.lower()
        try:
            return DataFeed(feed_value)  # type: ignore[arg-type]
        except (ValueError, AttributeError):
            logger.warning("未知数据源 '%s', 将回退到 IEX", feed)
            return DataFeed.IEX  # type: ignore[return-value]

    def _map_time_in_force(self, value: Optional[str]) -> TimeInForce:
        raw = (value or self._default_tif).lower()
        mapping = {
            "gtc": getattr(TimeInForce, "GTC"),
            "day": getattr(TimeInForce, "DAY"),
            "fok": getattr(TimeInForce, "FOK", getattr(TimeInForce, "GTC")),
            "ioc": getattr(TimeInForce, "IOC", getattr(TimeInForce, "GTC")),
            "opg": getattr(TimeInForce, "OPG", getattr(TimeInForce, "GTC")),
            "cls": getattr(TimeInForce, "CLS", getattr(TimeInForce, "GTC")),
        }
        return mapping.get(raw, getattr(TimeInForce, "GTC"))

    def _build_order_request(  # pylint: disable=too-many-arguments
        self,
        *,
        order_type: OrderType,
        symbol: str,
        quantity: int,
        side: AlpacaOrderSide,
        time_in_force: TimeInForce,
        limit_price: Optional[float],
        stop_price: Optional[float],
        client_order_id: str,
    ):
        if order_type == OrderType.MARKET:
            return MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=time_in_force,
                client_order_id=client_order_id,
            )

        if order_type == OrderType.LIMIT:
            if limit_price is None:
                raise ValueError("Limit order 需要提供价格")
            return LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=time_in_force,
                limit_price=Decimal(str(limit_price)),
                client_order_id=client_order_id,
            )

        if order_type == OrderType.STOP:
            if stop_price is None:
                raise ValueError("Stop order 需要提供止损价格")
            return StopOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=time_in_force,
                stop_price=Decimal(str(stop_price)),
                client_order_id=client_order_id,
            )

        if order_type == OrderType.STOP_LIMIT:
            if limit_price is None or stop_price is None:
                raise ValueError("Stop-Limit order 需要同时提供限价与止损价格")
            return StopLimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=time_in_force,
                limit_price=Decimal(str(limit_price)),
                stop_price=Decimal(str(stop_price)),
                client_order_id=client_order_id,
            )

        raise ValueError(f"暂不支持的订单类型: {order_type}")

    def _update_order_from_response(self, order: Order, response) -> None:
        status_value = getattr(response.status, "value", str(response.status))
        order.status = self._map_order_status(status_value)
        order.filled_quantity = int(Decimal(response.filled_qty or "0"))
        order.filled_price = (
            float(response.filled_avg_price)
            if response.filled_avg_price is not None
            else None
        )
        order.timestamp = getattr(response, "submitted_at", order.timestamp)

    @staticmethod
    def _map_order_status(status: str) -> OrderStatus:
        mapping = {
            "new": OrderStatus.PENDING,
            "accepted": OrderStatus.PENDING,
            "pending_new": OrderStatus.PENDING,
            "partially_filled": getattr(OrderStatus, "PARTIAL_FILLED", OrderStatus.FILLED),
            "filled": OrderStatus.FILLED,
            "done_for_day": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "pending_cancel": OrderStatus.CANCELLED,
            "pending_replace": OrderStatus.PENDING,
            "replaced": OrderStatus.FILLED,
            "rejected": OrderStatus.REJECTED,
            "expired": OrderStatus.CANCELLED,
            "stopped": OrderStatus.CANCELLED,
            "suspended": OrderStatus.CANCELLED,
        }
        return mapping.get(status.lower(), OrderStatus.PENDING)

    @staticmethod
    def _map_order_type(order_type: AlpacaOrderType) -> OrderType:
        value = getattr(order_type, "value", str(order_type)).lower()
        mapping = {
            "market": OrderType.MARKET,
            "limit": OrderType.LIMIT,
            "stop": OrderType.STOP,
            "stop_limit": OrderType.STOP_LIMIT,
        }
        return mapping.get(value, OrderType.MARKET)

    @staticmethod
    def _map_order_side(side: AlpacaOrderSide) -> OrderSide:
        value = getattr(side, "value", str(side)).lower()
        return OrderSide.BUY if value == "buy" else OrderSide.SELL
