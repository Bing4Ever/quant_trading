#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
信号生成器模块 - 底层交易信号生成逻辑

负责根据策略和市场数据生成交易信号。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...core import TradingSignal, OrderType


logger = logging.getLogger(__name__)


class SignalGenerator:
    """交易信号生成器"""
    
    def __init__(self):
        """初始化信号生成器"""
        self.signal_history: List[TradingSignal] = []
        logger.info("信号生成器初始化完成")
    
    def generate_signal(
        self,
        symbol: str,
        strategy_name: str,
        strategy_result: Dict[str, Any],
        quantity: int = 100,
        order_type: OrderType = OrderType.MARKET
    ) -> Optional[TradingSignal]:
        """
        根据策略结果生成交易信号
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            strategy_result: 策略分析结果
            quantity: 交易数量
            order_type: 订单类型
            
        Returns:
            TradingSignal: 交易信号，如果不应该交易则返回None
        """
        try:
            # 提取策略信号
            signal_value = strategy_result.get('signal', 0)
            confidence = strategy_result.get('confidence', 0.0)
            reason = strategy_result.get('reason', '')
            
            # 判断交易动作
            if signal_value > 0:
                action = 'buy'
            elif signal_value < 0:
                action = 'sell'
            else:
                # 持有信号，不生成交易
                return None
            
            # 获取价格（如果是限价单）
            price = None
            if order_type == OrderType.LIMIT:
                price = strategy_result.get('target_price')
            
            # 创建交易信号
            signal = TradingSignal(
                symbol=symbol,
                strategy=strategy_name,
                action=action,
                quantity=quantity,
                price=price,
                order_type=order_type,
                timestamp=datetime.now(),
                reason=reason,
                confidence=confidence
            )
            
            # 记录信号
            self.signal_history.append(signal)
            logger.info(
                f"生成交易信号: {action.upper()} {quantity} {symbol} "
                f"[{strategy_name}] (置信度: {confidence:.2%})"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"生成交易信号失败: {e}")
            return None
    
    def generate_batch_signals(
        self,
        symbols: List[str],
        strategy_results: Dict[str, Dict[str, Any]],
        quantity: int = 100,
        order_type: OrderType = OrderType.MARKET
    ) -> List[TradingSignal]:
        """
        批量生成交易信号
        
        Args:
            symbols: 股票代码列表
            strategy_results: 策略结果字典 {symbol: {strategy: result}}
            quantity: 交易数量
            order_type: 订单类型
            
        Returns:
            List[TradingSignal]: 交易信号列表
        """
        signals = []
        
        for symbol in symbols:
            if symbol not in strategy_results:
                continue
            
            symbol_results = strategy_results[symbol]
            
            for strategy_name, result in symbol_results.items():
                signal = self.generate_signal(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    strategy_result=result,
                    quantity=quantity,
                    order_type=order_type
                )
                
                if signal:
                    signals.append(signal)
        
        logger.info(f"批量生成 {len(signals)} 个交易信号")
        return signals
    
    def filter_signals(
        self,
        signals: List[TradingSignal],
        min_confidence: float = 0.0,
        max_signals: Optional[int] = None
    ) -> List[TradingSignal]:
        """
        过滤交易信号
        
        Args:
            signals: 信号列表
            min_confidence: 最小置信度阈值
            max_signals: 最大信号数量
            
        Returns:
            List[TradingSignal]: 过滤后的信号列表
        """
        # 按置信度过滤
        filtered = [s for s in signals if s.confidence >= min_confidence]
        
        # 按置信度排序（降序）
        filtered.sort(key=lambda s: s.confidence, reverse=True)
        
        # 限制数量
        if max_signals:
            filtered = filtered[:max_signals]
        
        logger.info(f"过滤信号: {len(signals)} -> {len(filtered)}")
        return filtered
    
    def get_signal_statistics(self) -> Dict[str, Any]:
        """
        获取信号统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.signal_history:
            return {
                'total_signals': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'strategies': {},
                'symbols': {}
            }
        
        buy_signals = sum(1 for s in self.signal_history if s.action == 'buy')
        sell_signals = sum(1 for s in self.signal_history if s.action == 'sell')
        
        # 按策略统计
        strategies = {}
        for signal in self.signal_history:
            if signal.strategy not in strategies:
                strategies[signal.strategy] = {'buy': 0, 'sell': 0}
            strategies[signal.strategy][signal.action] += 1
        
        # 按股票统计
        symbols = {}
        for signal in self.signal_history:
            if signal.symbol not in symbols:
                symbols[signal.symbol] = {'buy': 0, 'sell': 0}
            symbols[signal.symbol][signal.action] += 1
        
        return {
            'total_signals': len(self.signal_history),
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'strategies': strategies,
            'symbols': symbols
        }
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的信号
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[Dict]: 信号字典列表
        """
        recent = self.signal_history[-limit:] if self.signal_history else []
        return [s.to_dict() for s in recent]
    
    def clear_history(self):
        """清空信号历史"""
        self.signal_history.clear()
        logger.info("信号历史已清空")
