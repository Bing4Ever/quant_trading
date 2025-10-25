#!/usr:bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Controller Interface - 风险控制器接口定义

定义风险控制器的抽象接口。
"""

from abc import ABC, abstractmethod
from typing import Tuple, List, Dict, Any

from ..models import TradingSignal


class IRiskController(ABC):
    """风险控制器接口"""
    
    @abstractmethod
    def validate_signal(self, signal: TradingSignal) -> Tuple[bool, str]:
        """
        验证交易信号是否符合风险限制
        
        Args:
            signal: 交易信号
            
        Returns:
            Tuple[bool, str]: (是否通过, 原因说明)
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def get_risk_metrics(self) -> Dict[str, Any]:
        """
        获取风险指标
        
        Returns:
            Dict: 风险指标
        """
        pass
