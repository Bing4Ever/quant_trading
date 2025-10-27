"""
订单执行器模块 - 底层订单执行逻辑

负责订单的生成、提交、跟踪和管理。
"""

import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ...core import (
    IBroker,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position,
    TradingSignal,
)


logger = logging.getLogger(__name__)


class OrderExecutor:
    """订单执行器"""

    def __init__(self, broker: IBroker):
        """
        初始化订单执行器

        Args:
            broker: 经纪商接口实例
        """
        self.broker = broker
        self.pending_orders: Dict[str, Order] = {}
        self.completed_orders: List[Order] = []
        self.failed_orders: List[Order] = []

        logger.info("订单执行器初始化完成")

    def execute_signal(self, signal: TradingSignal) -> Optional[str]:
        """
        执行交易信号

        Args:
            signal: 交易信号

        Returns:
            str: 订单ID，如果失败则返回None
        """
        try:
            # 生成订单
            order = self._signal_to_order(signal)

            # 提交订单
            success = self.broker.submit_order(order)

            if success:
                self.pending_orders[order.order_id] = order
                logger.info(
                    f"订单提交成功: {order.order_id} - {signal.action} {signal.quantity} {signal.symbol}"
                )
                return order.order_id
            else:
                self.failed_orders.append(order)
                logger.error(
                    f"订单提交失败: {signal.action} {signal.quantity} {signal.symbol}"
                )
                return None

        except Exception as e:
            logger.error(f"执行交易信号失败: {e}")
            return None

    def _signal_to_order(self, signal: TradingSignal) -> Order:
        """
        将交易信号转换为订单

        Args:
            signal: 交易信号

        Returns:
            Order: 订单对象
        """
        order_id = self._generate_order_id()

        side = OrderSide.BUY if signal.action.lower() == "buy" else OrderSide.SELL

        order = Order(
            order_id=order_id,
            symbol=signal.symbol,
            side=side,
            quantity=signal.quantity,
            order_type=signal.order_type,
            price=signal.price,
            strategy=signal.strategy,
            timestamp=signal.timestamp,
        )

        return order

    def _generate_order_id(self) -> str:
        """生成唯一订单ID"""
        return f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单

        Args:
            order_id: 订单ID

        Returns:
            bool: 是否成功
        """
        try:
            success = self.broker.cancel_order(order_id)

            if success and order_id in self.pending_orders:
                order = self.pending_orders.pop(order_id)
                order.status = OrderStatus.CANCELLED
                self.completed_orders.append(order)
                logger.info(f"订单已取消: {order_id}")

            return success

        except Exception as e:
            logger.error(f"取消订单失败: {e}")
            return False

    def update_order_status(self, order_id: str) -> Optional[OrderStatus]:
        """
        更新订单状态

        Args:
            order_id: 订单ID

        Returns:
            OrderStatus: 当前状态，如果订单不存在则返回None
        """
        try:
            order = self.broker.get_order_status(order_id)

            if order is None:
                return None

            # 如果订单已完成，从待处理列表移到完成列表
            if order.status in [
                OrderStatus.FILLED,
                OrderStatus.CANCELLED,
                OrderStatus.REJECTED,
            ]:
                if order_id in self.pending_orders:
                    self.pending_orders.pop(order_id)
                    self.completed_orders.append(order)

            return order.status

        except Exception as e:
            logger.error(f"更新订单状态失败: {e}")
            return None

    def update_all_pending_orders(self) -> Dict[str, OrderStatus]:
        """
        更新所有待处理订单的状态

        Returns:
            Dict: 订单ID到状态的映射
        """
        results = {}

        for order_id in list(self.pending_orders.keys()):
            status = self.update_order_status(order_id)
            if status:
                results[order_id] = status

        return results

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        获取订单信息

        Args:
            order_id: 订单ID

        Returns:
            Order: 订单对象
        """
        # 先查待处理订单
        if order_id in self.pending_orders:
            return self.pending_orders[order_id]

        # 再查完成订单
        for order in self.completed_orders:
            if order.order_id == order_id:
                return order

        # 最后查失败订单
        for order in self.failed_orders:
            if order.order_id == order_id:
                return order

        return None

    def get_pending_orders(self) -> List[Order]:
        """获取所有待处理订单"""
        return list(self.pending_orders.values())

    def get_completed_orders(self) -> List[Order]:
        """获取所有已完成订单"""
        return self.completed_orders.copy()

    def get_failed_orders(self) -> List[Order]:
        """获取所有失败订单"""
        return self.failed_orders.copy()

    def get_order_statistics(self) -> Dict[str, Any]:
        """
        获取订单统计信息

        Returns:
            Dict: 统计信息
        """
        total_orders = (
            len(self.pending_orders)
            + len(self.completed_orders)
            + len(self.failed_orders)
        )

        filled_orders = sum(
            1 for order in self.completed_orders if order.status == OrderStatus.FILLED
        )

        cancelled_orders = sum(
            1
            for order in self.completed_orders
            if order.status == OrderStatus.CANCELLED
        )

        return {
            "total_orders": total_orders,
            "pending_orders": len(self.pending_orders),
            "filled_orders": filled_orders,
            "cancelled_orders": cancelled_orders,
            "failed_orders": len(self.failed_orders),
        }

    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息

        Returns:
            Dict: 账户信息
        """
        try:
            balance = self.broker.get_account_balance()
            positions = self.broker.get_positions()

            return {
                "balance": balance,
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "quantity": pos.quantity,
                        "average_price": pos.average_price,
                        "current_price": pos.current_price,
                        "market_value": pos.market_value,
                        "unrealized_pnl": pos.unrealized_pnl,
                        "unrealized_pnl_percent": pos.unrealized_pnl_percent,
                    }
                    for pos in positions
                ],
            }

        except Exception as e:
            logger.error(f"获取账户信息失败: {e}")
            return {"balance": {}, "positions": []}
