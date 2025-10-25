#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试投资组合管理器"""

import unittest
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tradingagent.modules.risk_management.portfolio_manager import PortfolioManager


class TestPortfolioManager(unittest.TestCase):
    """测试投资组合管理器"""

    def setUp(self) -> None:
        """设置测试环境"""
        self.manager = PortfolioManager(total_capital=100000)

    def test_add_position(self) -> None:
        """测试添加持仓"""
        # 使用合理的持仓规模（不超过30%权重）
        result = self.manager.add_position("AAPL", 100, 150.0, "Technology")
        self.assertTrue(result)
        self.assertIn("AAPL", self.manager.positions)
        self.assertEqual(self.manager.positions["AAPL"]["quantity"], 100)

    def test_remove_position(self) -> None:
        """测试移除持仓"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0)
        result = self.manager.remove_position("AAPL")
        self.assertTrue(result)
        self.assertNotIn("AAPL", self.manager.positions)

    def test_update_prices(self) -> None:
        """测试价格更新"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0)
        self.manager.update_prices({"AAPL": 160.0})
        self.assertEqual(self.manager.positions["AAPL"]["price"], 160.0)

    def test_portfolio_value(self) -> None:
        """测试投资组合价值计算"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0)  # $15,000 (15%)
        self.manager.add_position(
            "GOOGL", 30, 200.0
        )  # $6,000 (6%) - 减少数量避免超过30%
        value = self.manager.get_portfolio_value()
        self.assertEqual(value, 21000.0)  # 100*150 + 30*200

    def test_sector_allocation(self) -> None:
        """测试行业配置"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0, "Technology")  # $15,000
        self.manager.add_position("GOOGL", 30, 200.0, "Technology")  # $6,000 - 减少数量
        self.manager.add_position("JPM", 50, 100.0, "Finance")  # $5,000

        allocation = self.manager.get_sector_allocation()
        # 总价值: $26,000, Technology: $21,000 (80.8%), Finance: $5,000 (19.2%)
        self.assertAlmostEqual(allocation["Technology"], 0.808, places=2)
        self.assertAlmostEqual(allocation["Finance"], 0.192, places=2)

    def test_position_limits(self) -> None:
        """测试持仓限制"""
        # 测试超过30%权重的持仓被拒绝（基于总资金$100,000）
        # 35,000 / 100,000 = 35% > 30%
        result = self.manager.add_position("AAPL", 233, 150.0)  # $35,000
        self.assertFalse(result)

    def test_sector_limits(self) -> None:
        """测试行业限制"""
        self.manager.set_sector_limit("Technology", 0.5)

        # 第一个持仓应该成功（15% < 50%）
        result1 = self.manager.add_position(
            "AAPL", 100, 150.0, "Technology"
        )  # $15,000 (15% of total capital)
        self.assertTrue(result1)

        # 第二个持仓应该成功（总共20% < 50%，且单个不超过30%）
        result2 = self.manager.add_position(
            "MSFT", 33, 150.0, "Technology"
        )  # $4,950 (4.95% of total capital)
        self.assertTrue(result2)

        # 第三个持仓会超过行业限制（总共会超过50%限制）
        result3 = self.manager.add_position(
            "GOOGL", 200, 150.0, "Technology"
        )  # $30,000，会让Technology超过50%
        self.assertFalse(result3)

    def test_diversification_metrics(self) -> None:
        """测试分散化指标"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0)  # $15,000
        self.manager.add_position("GOOGL", 30, 200.0)  # $6,000 - 减少数量避免超过30%

        metrics = self.manager.check_diversification()
        self.assertIn("herfindahl_index", metrics)
        self.assertIn("effective_stocks", metrics)
        self.assertIn("max_weight", metrics)

    def test_rebalance_suggestions(self) -> None:
        """测试重新平衡建议"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0)  # $15,000
        self.manager.add_position("GOOGL", 30, 200.0)  # $6,000 - 减少数量

        target_weights = {"AAPL": 0.5, "GOOGL": 0.5}
        suggestions = self.manager.rebalance_suggestions(target_weights)

        self.assertIsInstance(suggestions, list)
        if suggestions:
            self.assertIn("symbol", suggestions[0])
            self.assertIn("action", suggestions[0])

    def test_portfolio_summary(self) -> None:
        """测试投资组合摘要"""
        # 使用合理的持仓规模
        self.manager.add_position("AAPL", 100, 150.0, "Technology")  # $15,000
        summary = self.manager.get_portfolio_summary()

        self.assertIn("total_capital", summary)
        self.assertIn("portfolio_value", summary)
        self.assertIn("cash_position", summary)
        self.assertIn("diversification", summary)


if __name__ == "__main__":
    unittest.main()
