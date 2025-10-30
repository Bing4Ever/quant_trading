#!/usr/bin/env python3
"""
系统自检脚本。

依次验证策略模块、自动化模块、多策略运行器以及 Streamlit 入口是否
能被正确导入并执行基础逻辑，便于快速排查环境或依赖问题。
"""

from __future__ import annotations

import sys
import traceback
from datetime import datetime
from typing import Callable, List, Tuple


# --------------------------------------------------------------------------- #
# 各项自检
# --------------------------------------------------------------------------- #
def test_strategy_imports() -> bool:
    """检查核心策略模块是否能够成功导入。"""
    print("开始检测：策略模块导入")
    try:
        from src.tradingagent.modules.strategies.base_strategy import BaseStrategy
        from src.tradingagent.modules.strategies.moving_average_strategy import (
            MovingAverageStrategy,
        )
        from src.tradingagent.modules.strategies.mean_reversion_strategy import (
            MeanReversionStrategy,
        )
        from src.tradingagent.modules.strategies.rsi_strategy import RSIStrategy
        from src.tradingagent.modules.strategies.bollinger_bands_strategy import (
            BollingerBandsStrategy,
        )
        from src.tradingagent.modules.strategies.multi_strategy_runner import (
            MultiStrategyRunner,
        )

        _ = [
            BaseStrategy,
            MovingAverageStrategy,
            MeanReversionStrategy,
            RSIStrategy,
            BollingerBandsStrategy,
            MultiStrategyRunner,
        ]
        print("✅ 策略模块导入正常")
        return True
    except Exception as exc:  # pragma: no cover - 脚本诊断使用
        print(f"❌ 策略模块导入失败：{exc}")
        traceback.print_exc()
        return False


def test_automation_imports() -> bool:
    """检查自动化调度与通知模块。"""
    print("开始检测：自动化模块导入")
    try:
        from src.tradingservice.services.automation.scheduler import (
            AutoTradingScheduler,
        )
        from src.tradingservice.services.automation.real_time_monitor import RealTimeMonitor
        from src.tradingservice.services.automation.realtime_provider import PollingDataProvider
        from src.common.logger import TradingLogger
        from src.common.notification import NotificationManager

        _ = [
            AutoTradingScheduler,
            RealTimeMonitor,
            PollingDataProvider,
            TradingLogger,
            NotificationManager,
        ]
        print("✅ 自动化模块导入正常")
        return True
    except Exception as exc:
        print(f"❌ 自动化模块导入失败：{exc}")
        traceback.print_exc()
        return False


def test_multi_strategy_runner() -> bool:
    """验证多策略运行器初始化与策略注册。"""
    print("开始检测：多策略运行器")
    try:
        from src.tradingagent.modules.strategies.multi_strategy_runner import (
            MultiStrategyRunner,
        )

        runner = MultiStrategyRunner()
        strategy_names = list(runner.strategies.keys())

        print(f"已加载策略 {len(strategy_names)} 个：{strategy_names}")
        if len(strategy_names) >= 2:
            print("✅ 多策略运行器检测通过")
            return True

        print("❌ 多策略运行器加载的策略数量不足")
        return False
    except Exception as exc:
        print(f"❌ 多策略运行器检测失败：{exc}")
        traceback.print_exc()
        return False


def test_data_fetching() -> bool:
    """验证行情下载与字段标准化。"""
    print("开始检测：行情下载")
    try:
        from src.tradingagent.modules.strategies.multi_strategy_runner import (
            MultiStrategyRunner,
        )

        runner = MultiStrategyRunner()
        data = runner.get_market_data("AAPL", period="1mo")

        print(f"已获取 {len(data)} 条 AAPL 行情数据，字段：{list(data.columns)}")
        return True
    except Exception as exc:
        print(f"❌ 行情下载检测失败：{exc}")
        traceback.print_exc()
        return False


def test_single_strategy() -> bool:
    """使用默认的移动均线策略进行一次信号生成。"""
    print("开始检测：单策略信号生成")
    try:
        from src.tradingagent.modules.strategies.multi_strategy_runner import (
            MultiStrategyRunner,
        )

        runner = MultiStrategyRunner()
        data = runner.get_market_data("AAPL", period="3mo")

        strategy = runner.strategies.get("移动均线")
        if strategy is None:
            print("❌ 未找到移动均线策略")
            return False

        signals = strategy.generate_signals(data)
        print(f"信号生成完成，样条数：{len(signals)}")
        return True
    except Exception as exc:
        print(f"❌ 单策略检测失败：{exc}")
        traceback.print_exc()
        return False


def test_streamlit_import() -> bool:
    """检测 Streamlit 入口能否导入。"""
    print("开始检测：Streamlit 入口")
    try:
        import streamlit_app  # noqa: F401

        print("✅ Streamlit 入口导入正常")
        return True
    except Exception as exc:
        print(f"❌ Streamlit 入口导入失败：{exc}")
        traceback.print_exc()
        return False


# --------------------------------------------------------------------------- #
# 主入口
# --------------------------------------------------------------------------- #
def main() -> bool:
    """依次执行所有检测项。"""
    print("系统自检开始")
    print("=" * 50)
    print(f"时间：{datetime.now():%Y-%m-%d %H:%M:%S}\n")

    tests: List[Tuple[str, Callable[[], bool]]] = [
        ("策略模块导入", test_strategy_imports),
        ("自动化模块导入", test_automation_imports),
        ("多策略运行器", test_multi_strategy_runner),
        ("行情下载", test_data_fetching),
        ("单策略信号生成", test_single_strategy),
        ("Streamlit 入口", test_streamlit_import),
    ]

    results: List[Tuple[str, bool]] = []

    for name, func in tests:
        print(f"\n{name}")
        print("-" * 30)
        try:
            success = func()
            results.append((name, success))
        except Exception as exc:
            print(f"❌ {name} 检测出现异常：{exc}")
            traceback.print_exc()
            results.append((name, False))

    print("\n检测结果汇总")
    print("=" * 50)

    passed = sum(1 for _, ok in results if ok)
    failed = len(results) - passed

    for name, ok in results:
        status = "通过" if ok else "失败"
        print(f"{name:<20} : {status}")

    print("-" * 50)
    print(f"合计项目：{len(results)}")
    print(f"通过数量：{passed}")
    print(f"失败数量：{failed}")
    print(f"通过率：{(passed / len(results) * 100):.1f}%")

    if failed == 0:
        print("\n✅ 所有自检项目均已通过，可继续后续工作。")
    else:
        print("\n⚠️ 存在检测失败项，请根据上方日志排查问题。")

    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
