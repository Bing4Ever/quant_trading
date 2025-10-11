#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试风险指标计算"""

import unittest
import pandas as pd
import numpy as np
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from risk_management.risk_metrics import RiskMetrics


class TestRiskMetrics(unittest.TestCase):
    """测试风险指标计算"""

    def setUp(self) -> None:
        """设置测试环境"""
        self.risk_metrics = RiskMetrics()

        # 创建测试数据
        rng = np.random.default_rng(42)
        dates = pd.date_range("2023-01-01", periods=252, freq="D")
        self.returns = pd.Series(rng.normal(0.001, 0.02, 252), index=dates)
        self.prices = pd.Series(100 * (1 + self.returns).cumprod(), index=dates)

        # 基准数据
        self.benchmark_returns = pd.Series(rng.normal(0.0008, 0.015, 252), index=dates)

    def test_volatility_calculation(self) -> None:
        """测试波动率计算"""
        vol = self.risk_metrics.calculate_volatility(self.returns)
        self.assertIsInstance(vol, float)
        self.assertGreater(vol, 0)

    def test_var_calculation(self) -> None:
        """测试VaR计算"""
        var_hist = self.risk_metrics.calculate_var(self.returns, method="historical")
        var_param = self.risk_metrics.calculate_var(self.returns, method="parametric")

        self.assertIsInstance(var_hist, float)
        self.assertIsInstance(var_param, float)
        self.assertLess(var_hist, 0)  # VaR应该是负数

    def test_cvar_calculation(self) -> None:
        """测试CVaR计算"""
        cvar = self.risk_metrics.calculate_cvar(self.returns)
        self.assertIsInstance(cvar, float)
        self.assertLess(cvar, 0)  # CVaR应该是负数

    def test_sharpe_ratio(self) -> None:
        """测试夏普比率"""
        sharpe = self.risk_metrics.calculate_sharpe_ratio(self.returns)
        self.assertIsInstance(sharpe, float)

    def test_sortino_ratio(self) -> None:
        """测试索提诺比率"""
        sortino = self.risk_metrics.calculate_sortino_ratio(self.returns)
        self.assertIsInstance(sortino, float)

    def test_max_drawdown(self) -> None:
        """测试最大回撤"""
        dd_info = self.risk_metrics.calculate_max_drawdown(self.prices)

        self.assertIn("max_drawdown", dd_info)
        self.assertIn("start_date", dd_info)
        self.assertIn("end_date", dd_info)
        self.assertGreaterEqual(dd_info["max_drawdown"], 0)

    def test_beta_calculation(self) -> None:
        """测试贝塔系数"""
        beta = self.risk_metrics.calculate_beta(self.returns, self.benchmark_returns)
        self.assertIsInstance(beta, float)

    def test_tracking_error(self) -> None:
        """测试跟踪误差"""
        te = self.risk_metrics.calculate_tracking_error(
            self.returns, self.benchmark_returns
        )
        self.assertIsInstance(te, float)
        self.assertGreaterEqual(te, 0)

    def test_information_ratio(self) -> None:
        """测试信息比率"""
        ir = self.risk_metrics.calculate_information_ratio(
            self.returns, self.benchmark_returns
        )
        self.assertIsInstance(ir, float)

    def test_correlation_matrix(self) -> None:
        """测试相关性矩阵"""
        returns_df = pd.DataFrame(
            {"asset1": self.returns, "asset2": self.benchmark_returns}
        )

        corr_matrix = self.risk_metrics.calculate_correlation_matrix(returns_df)
        self.assertIsInstance(corr_matrix, pd.DataFrame)
        self.assertEqual(corr_matrix.shape, (2, 2))

    def test_portfolio_risk_decomposition(self) -> None:
        """测试投资组合风险分解"""
        weights = np.array([0.6, 0.4])
        cov_matrix = np.array([[0.04, 0.02], [0.02, 0.09]])

        decomp = self.risk_metrics.calculate_portfolio_risk_decomposition(
            weights, cov_matrix
        )

        self.assertIn("portfolio_volatility", decomp)
        self.assertIn("marginal_contribution", decomp)
        self.assertIn("risk_contribution", decomp)

    def test_stress_scenarios(self) -> None:
        """测试压力测试"""
        scenarios = {"market_crash": -0.2, "mild_correction": -0.1, "black_swan": -0.3}

        results = self.risk_metrics.calculate_stress_scenarios(self.returns, scenarios)

        self.assertIsInstance(results, dict)
        self.assertIn("market_crash", results)

    def test_risk_report(self) -> None:
        """测试综合风险报告"""
        report = self.risk_metrics.generate_risk_report(
            self.returns, self.prices, self.benchmark_returns
        )

        self.assertIn("basic_stats", report)
        self.assertIn("risk_measures", report)
        self.assertIn("relative_risk", report)

        # 检查基本统计
        basic_stats = report["basic_stats"]
        self.assertIn("total_return", basic_stats)
        self.assertIn("volatility", basic_stats)
        self.assertIn("sharpe_ratio", basic_stats)

        # 检查风险指标
        risk_measures = report["risk_measures"]
        self.assertIn("var_95", risk_measures)
        self.assertIn("max_drawdown", risk_measures)

    def test_empty_data_handling(self) -> None:
        """测试空数据处理"""
        empty_series = pd.Series([], dtype=float)

        vol = self.risk_metrics.calculate_volatility(empty_series)
        self.assertEqual(vol, 0.0)

        var = self.risk_metrics.calculate_var(empty_series)
        self.assertEqual(var, 0.0)

        sharpe = self.risk_metrics.calculate_sharpe_ratio(empty_series)
        self.assertEqual(sharpe, 0.0)


if __name__ == "__main__":
    unittest.main()
