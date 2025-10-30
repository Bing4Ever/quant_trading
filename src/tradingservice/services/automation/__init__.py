"""
Automation Services - 自动化服务

提供定时调度、实时监控和报告生成功能。
"""

from .scheduler import AutoTradingScheduler, ScheduleFrequency, TaskStatus, ScheduledTask
from .automation_models import MarketData, TradingSignal
from .realtime_provider import RealTimeDataProvider, PollingDataProvider
from .signal_monitor import SignalMonitor
from .real_time_monitor import RealTimeMonitor
from .report_generator import ReportGenerator, AutoReportScheduler

__all__ = [
    'AutoTradingScheduler',
    'ScheduleFrequency',
    'TaskStatus',
    'ScheduledTask',
    'RealTimeMonitor',
    'RealTimeDataProvider',
    'PollingDataProvider',
    'SignalMonitor',
    'MarketData',
    'TradingSignal',
    'ReportGenerator',
    'AutoReportScheduler',
]
