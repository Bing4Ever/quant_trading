"""
自动化测试脚本清单（独立于主 pytest 套件）。

此处的脚本依赖桩对象或合成数据，以在无真实集成的情况下验证服务行为。
"""

from __future__ import annotations

AUTOMATION_TEST_SCRIPTS = [
    {
        "path": "tests/automation/test_chart_generator.py",
        "description": (
            "使用合成 OHLCV 数据验证 InteractiveChartGenerator 能生成 Matplotlib 图像。"
        ),
        "command": "pytest tests/automation/test_chart_generator.py",
    },
    {
        "path": "tests/automation/test_task_manager_reconcile.py",
        "description": (
            "通过内存经纪商桩验证 TaskManager.reconcile_orders 会产出终态订单更新。"
        ),
        "command": "pytest tests/automation/test_task_manager_reconcile.py",
    },
    {
        "path": "tests/automation/test_live_runtime.py",
        "description": (
            "利用桩化经纪商与数据源校验 LiveTradingRuntime 的组合逻辑，无需外部服务。"
        ),
        "command": "pytest tests/automation/test_live_runtime.py",
    },
]

__all__ = ["AUTOMATION_TEST_SCRIPTS"]
