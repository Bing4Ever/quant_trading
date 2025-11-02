"""
Trading Service Package - 上层业务编排层

提供核心交易服务和业务逻辑，包括：
- API 层：对外接口（REST API、WebSocket等）
- Service 层：业务编排（自动化、模拟、引擎、编排）
"""

__version__ = "2.0.0"

# 从 services 导入主要组件
try:
    from .services.orchestration import TaskManager, Task, TaskStatus
except ImportError:  # pragma: no cover - optional dependency
    TaskManager = Task = TaskStatus = None
try:
    from .services.automation import AutoTradingScheduler, RealTimeMonitor, ReportGenerator
except ImportError:  # pragma: no cover
    AutoTradingScheduler = RealTimeMonitor = ReportGenerator = None
try:
    from .services.simulation import SimulationEnvironment, SimulationConfig, SimulationMode
except ImportError:  # pragma: no cover
    SimulationEnvironment = SimulationConfig = SimulationMode = None
try:
    from .services.engines import AdvancedTradingEngine, QuickTradingEngine, LiveTradingEngine
except ImportError:  # pragma: no cover
    AdvancedTradingEngine = QuickTradingEngine = LiveTradingEngine = None
try:
    from .services.analysis import PerformanceAnalyzer, BacktestAnalytics
except ImportError:  # pragma: no cover
    PerformanceAnalyzer = BacktestAnalytics = None

# Data Access Layer (新架构 - 推荐使用)
try:
    from .dataaccess import (
        get_backtest_repository,
        get_optimization_repository,
        get_favorite_repository,
        get_strategy_comparison_repository,
    )
except ImportError:  # pragma: no cover
    get_backtest_repository = get_optimization_repository = None
    get_favorite_repository = get_strategy_comparison_repository = None

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
