"""
Presentation Services - 展示层服务

提供数据可视化、报告生成等展示相关功能
"""

from .report_generator import BacktestReportGenerator
from .chart_generator import InteractiveChartGenerator

__all__ = [
    'BacktestReportGenerator',
    'InteractiveChartGenerator'
]
