#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制器模块 - 底层风险控制逻辑

负责持仓风险、订单风险、资金管理等风险控制功能。
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

from ...core import IBroker, Position, Order, OrderSide, TradingSignal


logger = logging.getLogger(__name__)


@dataclass
class RiskLimits:
    """风险限制配置"""
    max_position_size: float = 0.1  # 单个持仓最大占比（10%）
    max_total_exposure: float = 0.8  # 最大总仓位（80%）
    max_single_trade_size: float = 0.05  # 单笔交易最大占比（5%）
    max_daily_loss: float = 0.02  # 最大日亏损（2%）
    max_drawdown: float = 0.1  # 最大回撤（10%）
    min_cash_reserve: float = 0.1  # 最小现金储备（10%）


class RiskController:
    """风险控制器"""
    
    def __init__(self, broker: IBroker, risk_limits: Optional[RiskLimits] = None):
        """
        初始化风险控制器
        
        Args:
            broker: 经纪商接口
            risk_limits: 风险限制配置
        """
        self.broker = broker
        self.risk_limits = risk_limits or RiskLimits()
        
        # 初始权益用于计算回撤
        balance = self.broker.get_account_balance()
        self.initial_equity = balance.get('equity', 0)
        self.peak_equity = self.initial_equity
        
        # 当日交易统计
        self.daily_trades: List[Order] = []
        self.daily_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        logger.info("风险控制器初始化完成")
        logger.info(f"初始权益: ${self.initial_equity:,.2f}")
        logger.info(f"风险限制: {self.risk_limits}")
    
    def validate_signal(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        验证交易信号是否符合风险限制
        
        Args:
            signal: 交易信号
            
        Returns:
            Tuple[bool, str]: (是否通过, 原因说明)
        """
        try:
            # 重置每日统计（如果是新的一天）
            self._reset_daily_stats_if_needed()
            
            # 获取账户信息
            balance = self.broker.get_account_balance()
            equity = balance.get('equity', 0)
            cash = balance.get('cash', 0)
            
            if equity == 0:
                return False, "账户权益为0"
            
            # 获取当前价格
            current_price = self.broker.get_current_price(signal.symbol)
            if not current_price:
                return False, f"无法获取 {signal.symbol} 的当前价格"
            
            # 计算交易金额
            trade_value = current_price * signal.quantity
            
            # 1. 检查单笔交易规模
            trade_ratio = trade_value / equity
            if trade_ratio > self.risk_limits.max_single_trade_size:
                return False, (
                    f"单笔交易规模过大: {trade_ratio:.2%} > "
                    f"{self.risk_limits.max_single_trade_size:.2%}"
                )
            
            # 2. 检查买入时的现金是否足够
            if signal.action.lower() == 'buy':
                commission = trade_value * 0.001  # 假设0.1%手续费
                total_cost = trade_value + commission
                
                if total_cost > cash:
                    return False, f"现金不足: 需要 ${total_cost:,.2f}, 可用 ${cash:,.2f}"
                
                # 检查现金储备
                remaining_cash = cash - total_cost
                if remaining_cash / equity < self.risk_limits.min_cash_reserve:
                    return False, (
                        f"现金储备不足: {remaining_cash / equity:.2%} < "
                        f"{self.risk_limits.min_cash_reserve:.2%}"
                    )
            
            # 3. 检查持仓集中度（买入时）
            if signal.action.lower() == 'buy':
                positions = self.broker.get_positions()
                
                # 计算买入后的持仓占比
                future_position_value = trade_value
                for pos in positions:
                    if pos.symbol == signal.symbol:
                        future_position_value += pos.market_value
                
                future_position_ratio = future_position_value / equity
                if future_position_ratio > self.risk_limits.max_position_size:
                    return False, (
                        f"持仓占比过高: {future_position_ratio:.2%} > "
                        f"{self.risk_limits.max_position_size:.2%}"
                    )
            
            # 4. 检查总仓位（买入时）
            if signal.action.lower() == 'buy':
                positions = self.broker.get_positions()
                total_position_value = sum(pos.market_value for pos in positions) + trade_value
                total_exposure = total_position_value / equity
                
                if total_exposure > self.risk_limits.max_total_exposure:
                    return False, (
                        f"总仓位过高: {total_exposure:.2%} > "
                        f"{self.risk_limits.max_total_exposure:.2%}"
                    )
            
            # 5. 检查每日亏损限制
            daily_loss_ratio = abs(self.daily_pnl) / self.initial_equity
            if self.daily_pnl < 0 and daily_loss_ratio > self.risk_limits.max_daily_loss:
                return False, (
                    f"超过每日最大亏损: {daily_loss_ratio:.2%} > "
                    f"{self.risk_limits.max_daily_loss:.2%}"
                )
            
            # 6. 检查回撤
            drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
            if drawdown > self.risk_limits.max_drawdown:
                return False, (
                    f"超过最大回撤: {drawdown:.2%} > "
                    f"{self.risk_limits.max_drawdown:.2%}"
                )
            
            # 所有检查通过
            return True, "风险检查通过"
            
        except Exception as e:
            logger.error(f"风险验证失败: {e}")
            return False, f"风险验证异常: {str(e)}"
    
    def validate_batch_signals(
        self,
        signals: List[TradingSignal]
    ) -> List[Tuple[TradingSignal, bool, str]]:
        """
        批量验证交易信号
        
        Args:
            signals: 信号列表
            
        Returns:
            List[Tuple]: (信号, 是否通过, 原因) 列表
        """
        results = []
        
        for signal in signals:
            is_valid, reason = self.validate_signal(signal)
            results.append((signal, is_valid, reason))
        
        passed = sum(1 for _, is_valid, _ in results if is_valid)
        logger.info(f"批量风险验证: {passed}/{len(signals)} 通过")
        
        return results
    
    def _reset_daily_stats_if_needed(self):
        """检查并重置每日统计"""
        today = datetime.now().date()
        if today != self.last_reset_date:
            logger.info(f"重置每日统计 ({self.last_reset_date} -> {today})")
            self.daily_trades.clear()
            self.daily_pnl = 0.0
            self.last_reset_date = today
    
    def update_peak_equity(self):
        """更新峰值权益"""
        balance = self.broker.get_account_balance()
        equity = balance.get('equity', 0)
        
        if equity > self.peak_equity:
            self.peak_equity = equity
            logger.info(f"更新峰值权益: ${equity:,.2f}")
    
    def record_trade(self, order: Order):
        """
        记录交易（用于每日统计）
        
        Args:
            order: 订单
        """
        self._reset_daily_stats_if_needed()
        self.daily_trades.append(order)
        logger.debug(f"记录交易: {order.order_id}")
    
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        获取风险指标
        
        Returns:
            Dict: 风险指标
        """
        try:
            balance = self.broker.get_account_balance()
            equity = balance.get('equity', 0)
            cash = balance.get('cash', 0)
            
            positions = self.broker.get_positions()
            
            # 计算总持仓价值
            total_position_value = sum(pos.market_value for pos in positions)
            
            # 计算各项指标
            cash_ratio = cash / equity if equity > 0 else 0
            exposure = total_position_value / equity if equity > 0 else 0
            drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
            daily_loss_ratio = abs(self.daily_pnl) / self.initial_equity if self.initial_equity > 0 else 0
            
            # 找出最大持仓
            max_position_ratio = 0
            max_position_symbol = ""
            if equity > 0:
                for pos in positions:
                    ratio = pos.market_value / equity
                    if ratio > max_position_ratio:
                        max_position_ratio = ratio
                        max_position_symbol = pos.symbol
            
            return {
                'equity': equity,
                'cash': cash,
                'cash_ratio': cash_ratio,
                'total_exposure': exposure,
                'current_drawdown': drawdown,
                'peak_equity': self.peak_equity,
                'daily_pnl': self.daily_pnl,
                'daily_loss_ratio': daily_loss_ratio,
                'daily_trades_count': len(self.daily_trades),
                'max_position_symbol': max_position_symbol,
                'max_position_ratio': max_position_ratio,
                'risk_limits': {
                    'max_position_size': self.risk_limits.max_position_size,
                    'max_total_exposure': self.risk_limits.max_total_exposure,
                    'max_single_trade_size': self.risk_limits.max_single_trade_size,
                    'max_daily_loss': self.risk_limits.max_daily_loss,
                    'max_drawdown': self.risk_limits.max_drawdown,
                    'min_cash_reserve': self.risk_limits.min_cash_reserve
                }
            }
            
        except Exception as e:
            logger.error(f"获取风险指标失败: {e}")
            return {}
    
    def get_position_suggestions(self) -> Dict[str, Any]:
        """
        获取持仓建议
        
        Returns:
            Dict: 持仓调整建议
        """
        try:
            balance = self.broker.get_account_balance()
            equity = balance.get('equity', 0)
            
            positions = self.broker.get_positions()
            
            suggestions = {
                'reduce_positions': [],  # 需要减仓的股票
                'can_increase': [],  # 可以加仓的股票
                'warnings': []  # 风险警告
            }
            
            for pos in positions:
                position_ratio = pos.market_value / equity if equity > 0 else 0
                
                # 检查是否超过单个持仓限制
                if position_ratio > self.risk_limits.max_position_size:
                    target_value = equity * self.risk_limits.max_position_size
                    reduce_quantity = int(
                        (pos.market_value - target_value) / pos.current_price
                    )
                    suggestions['reduce_positions'].append({
                        'symbol': pos.symbol,
                        'current_ratio': position_ratio,
                        'target_ratio': self.risk_limits.max_position_size,
                        'reduce_quantity': reduce_quantity,
                        'reason': '持仓占比过高'
                    })
                elif position_ratio < self.risk_limits.max_position_size * 0.5:
                    # 可以考虑加仓
                    available_ratio = self.risk_limits.max_position_size - position_ratio
                    suggestions['can_increase'].append({
                        'symbol': pos.symbol,
                        'current_ratio': position_ratio,
                        'available_ratio': available_ratio,
                        'reason': '持仓占比较低，可考虑加仓'
                    })
            
            # 添加风险警告
            metrics = self.get_risk_metrics()
            
            if metrics.get('current_drawdown', 0) > self.risk_limits.max_drawdown * 0.8:
                suggestions['warnings'].append({
                    'type': 'drawdown',
                    'message': f"回撤接近限制: {metrics['current_drawdown']:.2%}"
                })
            
            if metrics.get('total_exposure', 0) > self.risk_limits.max_total_exposure * 0.9:
                suggestions['warnings'].append({
                    'type': 'exposure',
                    'message': f"总仓位较高: {metrics['total_exposure']:.2%}"
                })
            
            return suggestions
            
        except Exception as e:
            logger.error(f"生成持仓建议失败: {e}")
            return {
                'reduce_positions': [],
                'can_increase': [],
                'warnings': []
            }
