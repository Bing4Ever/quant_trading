"""
Signal Module - 信号生成模块

负责将策略分析结果转换为标准化交易信号。
"""

from .signal_generator import SignalGenerator

__all__ = [
    'SignalGenerator',
]
