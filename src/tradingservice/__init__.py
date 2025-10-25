"""
Trading Service Package - 上层业务编排层

提供核心交易服务和业务逻辑，包括：
- API 层：对外接口（REST API、WebSocket等）
- Service 层：业务编排（自动化、模拟、引擎、编排）
"""

__version__ = "2.0.0"

# 从 services 导入主要组件
from .services.orchestration import TaskManager, Task, TaskStatus
from .services.automation import AutoTradingScheduler, RealTimeMonitor, ReportGenerator
from .services.simulation import SimulationEnvironment, SimulationConfig, SimulationMode
from .services.engines import AdvancedTradingEngine, QuickTradingEngine, LiveTradingEngine
from .services.analysis import PerformanceAnalyzer, BacktestAnalytics

# Data Access Layer (新架构 - 推荐使用)
from .dataaccess import (
    get_backtest_repository,
    get_optimization_repository,
    get_favorite_repository,
    get_strategy_comparison_repository
)

# Legacy Storage (已废弃，保留用于兼容性)
# BacktestDatabase 已迁移至 services.analysis.BacktestAnalytics
# 使用 get_backtest_repository() 进行数据访问
BacktestDatabase = None

__all__ = [
    # Orchestration
    'TaskManager',
    'Task',
    'TaskStatus',
    # Automation
    'AutoTradingScheduler',
    'RealTimeMonitor',
    'ReportGenerator',
    # Simulation
    'SimulationEnvironment',
    'SimulationConfig',
    'SimulationMode',
    # Engines
    'AdvancedTradingEngine',
    'QuickTradingEngine',
    'LiveTradingEngine',
    # Analysis
    'PerformanceAnalyzer',
    'BacktestAnalytics',
    # Data Access (新架构 - 推荐)
    'get_backtest_repository',
    'get_optimization_repository',
    'get_favorite_repository',
    'get_strategy_comparison_repository',
    # Storage (已废弃，保留兼容性)
    'BacktestDatabase',
]
