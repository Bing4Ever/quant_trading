#!/usr/bin/env python3
"""统一测试运行器"""

import sys
import unittest
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestExecutionError(Exception):
    """测试执行错误"""


def run_test_module(test_name: str, test_function) -> bool:
    """运行单个测试模块"""
    print(f"\n{'='*60}")
    print(f"运行测试: {test_name}")
    print(f"{'='*60}")

    try:
        start_time = time.time()
        test_function()
        duration = time.time() - start_time
        print(f"✅ {test_name} 测试完成，用时: {duration:.2f} 秒")
        return True
    except (ImportError, TestExecutionError) as e:
        print(f"❌ {test_name} 测试失败: {e}")
        return False


def create_unittest_runner(test_class):
    """创建unittest运行器"""

    def runner():
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            raise TestExecutionError(
                f"测试失败: {len(result.failures)} 失败, {len(result.errors)} 错误"
            )

    return runner


def run_risk_manager_tests(test_results: dict) -> None:
    """运行风险管理测试"""
    try:
        from tests.test_risk_manager import main as test_risk_manager

        test_results["风险管理"] = run_test_module("风险管理", test_risk_manager)
    except ImportError as e:
        print(f"❌ 无法导入风险管理测试: {e}")
        test_results["风险管理"] = False


def run_portfolio_tests(test_results: dict) -> None:
    """运行投资组合测试"""
    test_name = "投资组合管理"
    try:
        from tests.test_portfolio_manager import TestPortfolioManager

        test_portfolio = create_unittest_runner(TestPortfolioManager)
        test_results[test_name] = run_test_module(test_name, test_portfolio)
    except ImportError as e:
        print(f"❌ 无法导入投资组合管理测试: {e}")
        test_results[test_name] = False


def run_risk_metrics_tests(test_results: dict) -> None:
    """运行风险指标测试"""
    try:
        from tests.test_risk_metrics import TestRiskMetrics

        test_risk_metrics = create_unittest_runner(TestRiskMetrics)
        test_results["风险指标"] = run_test_module("风险指标", test_risk_metrics)
    except ImportError as e:
        print(f"❌ 无法导入风险指标测试: {e}")
        test_results["风险指标"] = False


def run_strategy_tests(test_results: dict) -> None:
    """运行策略测试"""
    try:
        from tests.test_strategies import main as test_strategies

        test_results["交易策略"] = run_test_module("交易策略", test_strategies)
    except ImportError as e:
        print(f"❌ 无法导入策略测试: {e}")
        test_results["交易策略"] = False


def run_data_tests(test_results: dict) -> None:
    """运行数据测试"""
    try:
        from tests.test_data import main as test_data

        test_results["数据模块"] = run_test_module("数据模块", test_data)
    except ImportError as e:
        print(f"❌ 无法导入数据测试: {e}")
        test_results["数据模块"] = False


def run_dependency_tests(test_results: dict) -> None:
    """运行依赖测试"""
    try:
        from tests.test_schedule import main as test_schedule

        test_results["依赖检查"] = run_test_module("依赖检查", test_schedule)
    except ImportError as e:
        print(f"❌ 无法导入依赖测试: {e}")
        test_results["依赖检查"] = False


def print_test_summary(test_results: dict) -> bool:
    """打印测试汇总"""
    print(f"\n{'='*60}")
    print("📊 测试结果汇总:")
    print(f"{'='*60}")

    success_count = 0
    total_count = len(test_results)

    for test_name, test_success in test_results.items():
        status = "✅ 通过" if test_success else "❌ 失败"
        print(f"{test_name:20} {status}")
        if test_success:
            success_count += 1

    print(f"\n总计: {success_count}/{total_count} 测试通过")

    overall_success = success_count == total_count
    if overall_success:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查详细输出")

    return overall_success


def run_all_tests() -> bool:
    """运行所有测试"""
    print("🚀 开始运行所有测试...")

    test_results = {}

    # 运行各种测试
    run_risk_manager_tests(test_results)
    run_portfolio_tests(test_results)
    run_risk_metrics_tests(test_results)
    run_strategy_tests(test_results)
    run_data_tests(test_results)
    run_dependency_tests(test_results)

    return print_test_summary(test_results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
