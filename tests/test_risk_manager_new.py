#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risk Management System Test Suite - Testing VaR, position limits, and risk monitoring"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradingagent.modules.risk_management.risk_manager import RiskManager, RiskMonitor, RiskCalculator
from src.common.logger import TradingLogger
from src.common.notification import NotificationManager


# Mock NotificationManager for testing
class MockNotificationManager:
    def send_notification(self, message, level="info"):
        """Mock notification method for testing purposes"""
        pass


class TestRiskCalculator(unittest.TestCase):
    """Test suite for RiskCalculator class"""

    def setUp(self):
        """Set up test fixtures"""
        self.calculator = RiskCalculator()

        # Create sample portfolio data
        self.sample_returns = pd.Series(
            [0.02, -0.01, 0.015, -0.025, 0.01, 0.005, -0.015, 0.02, -0.01, 0.03]
        )

        self.sample_positions = {
            "AAPL": {"quantity": 100, "price": 150.0, "value": 15000},
            "MSFT": {"quantity": 50, "price": 280.0, "value": 14000},
            "GOOGL": {"quantity": 10, "price": 2500.0, "value": 25000},
        }

    def test_calculate_var(self):
        """Test VaR calculation"""
        var_95 = self.calculator.calculate_var(
            self.sample_returns, confidence_level=0.95
        )
        var_99 = self.calculator.calculate_var(
            self.sample_returns, confidence_level=0.99
        )

        self.assertIsInstance(var_95, float)
        self.assertIsInstance(var_99, float)
        self.assertGreater(abs(var_99), abs(var_95))  # 99% VaR should be higher

    def test_calculate_max_drawdown(self):
        """Test maximum drawdown calculation"""
        cumulative_returns = (1 + self.sample_returns).cumprod()
        max_dd = self.calculator.calculate_max_drawdown(cumulative_returns)

        self.assertIsInstance(max_dd, float)
        self.assertLessEqual(max_dd, 0)  # Drawdown should be negative or zero

    def test_calculate_concentration_risk(self):
        """Test concentration risk calculation"""
        total_value = sum(pos["value"] for pos in self.sample_positions.values())
        concentrations = self.calculator.calculate_concentration_risk(
            self.sample_positions
        )

        self.assertIsInstance(concentrations, dict)
        for symbol, concentration in concentrations.items():
            self.assertGreaterEqual(concentration, 0)
            self.assertLessEqual(concentration, 1)

        # Check that concentrations sum to 1
        total_concentration = sum(concentrations.values())
        self.assertAlmostEqual(total_concentration, 1.0, places=5)


class TestRiskManager(unittest.TestCase):
    """Test suite for RiskManager class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock logger and notification manager
        self.mock_logger = Mock(spec=TradingLogger)
        self.mock_notifier = Mock(spec=NotificationManager)

        self.risk_config = {
            "max_portfolio_var": 0.05,
            "max_position_size": 0.3,
            "max_daily_loss": 0.02,
            "max_drawdown": 0.15,
            "concentration_limit": 0.25,
            "correlation_threshold": 0.8,
        }

        self.risk_manager = RiskManager(
            config=self.risk_config,
            logger=self.mock_logger,
            notifier=self.mock_notifier,
        )

    def test_initialization(self):
        """Test RiskManager initialization"""
        self.assertIsInstance(self.risk_manager, RiskManager)
        self.assertEqual(self.risk_manager.config["max_portfolio_var"], 0.05)
        self.assertIsInstance(self.risk_manager.calculator, RiskCalculator)

    def test_validate_position_size(self):
        """Test position size validation"""
        portfolio_value = 100000

        # Valid position
        valid_result = self.risk_manager.validate_position_size(
            "AAPL", 20000, portfolio_value
        )
        self.assertTrue(valid_result["allowed"])

        # Position too large
        invalid_result = self.risk_manager.validate_position_size(
            "AAPL", 40000, portfolio_value
        )
        self.assertFalse(invalid_result["allowed"])
        self.assertIn("Position size exceeds limit", invalid_result["reason"])

    def test_check_daily_loss_limit(self):
        """Test daily loss limit checking"""
        # Setup mock portfolio data
        self.risk_manager.portfolio_data = {"daily_pnl": -1500, "initial_value": 100000}

        result = self.risk_manager.check_daily_loss_limit()
        self.assertTrue(result["within_limit"])

        # Test excessive loss
        self.risk_manager.portfolio_data["daily_pnl"] = -3000
        result = self.risk_manager.check_daily_loss_limit()
        self.assertFalse(result["within_limit"])

    def test_calculate_portfolio_risk(self):
        """Test portfolio risk calculation"""
        # Mock portfolio data
        positions = {
            "AAPL": {"quantity": 100, "price": 150.0, "value": 15000},
            "MSFT": {"quantity": 50, "price": 280.0, "value": 14000},
        }

        returns_data = pd.DataFrame(
            {
                "AAPL": [0.01, -0.02, 0.015, -0.01, 0.02],
                "MSFT": [0.005, -0.015, 0.01, -0.005, 0.025],
            }
        )

        risk_metrics = self.risk_manager.calculate_portfolio_risk(
            positions, returns_data
        )

        self.assertIn("var_95", risk_metrics)
        self.assertIn("var_99", risk_metrics)
        self.assertIn("concentration_risk", risk_metrics)
        self.assertIn("total_exposure", risk_metrics)

    def test_should_block_trade(self):
        """Test trade blocking logic"""
        trade_signal = {
            "symbol": "AAPL",
            "quantity": 100,
            "price": 150.0,
            "side": "buy",
        }

        # Mock current portfolio
        current_portfolio = {"AAPL": {"quantity": 50, "price": 148.0, "value": 7400}}

        result = self.risk_manager.should_block_trade(
            trade_signal, current_portfolio, 100000
        )

        self.assertIsInstance(result, dict)
        self.assertIn("block", result)
        self.assertIn("reason", result)


class TestRiskMonitor(unittest.TestCase):
    """Test suite for RiskMonitor class"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_risk_manager = Mock(spec=RiskManager)
        self.mock_logger = Mock(spec=TradingLogger)

        self.monitor = RiskMonitor(
            risk_manager=self.mock_risk_manager,
            logger=self.mock_logger,
            check_interval=1,  # 1 second for testing
        )

    def test_initialization(self):
        """Test RiskMonitor initialization"""
        self.assertIsInstance(self.monitor, RiskMonitor)
        self.assertEqual(self.monitor.check_interval, 1)
        self.assertFalse(self.monitor.is_running)

    def test_start_stop_monitoring(self):
        """Test starting and stopping the monitoring thread"""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.is_running)

        # Let it run for a short time
        time.sleep(2)

        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.is_running)


def test_risk_scenario_integration():
    """Integration test for various risk scenarios"""
    print("\n" + "=" * 60)
    print("RISK MANAGEMENT INTEGRATION TESTS")
    print("=" * 60)

    # Initialize components
    logger = Mock(spec=TradingLogger)
    notifier = Mock(spec=NotificationManager)

    config = {
        "max_portfolio_var": 0.05,
        "max_position_size": 0.25,
        "max_daily_loss": 0.02,
        "max_drawdown": 0.15,
        "concentration_limit": 0.3,
    }

    risk_manager = RiskManager(config=config, logger=logger, notifier=notifier)

    print("\n1. Testing Position Size Validation")
    print("-" * 40)

    # Test various position sizes
    portfolio_value = 100000
    test_positions = [
        ("AAPL", 15000),  # 15% - should pass
        ("MSFT", 30000),  # 30% - should fail
        ("GOOGL", 20000),  # 20% - should pass
    ]

    for symbol, position_value in test_positions:
        result = risk_manager.validate_position_size(
            symbol, position_value, portfolio_value
        )
        status = "✅ ALLOWED" if result["allowed"] else "❌ BLOCKED"
        percentage = (position_value / portfolio_value) * 100
        print(f"{symbol}: ${position_value:,} ({percentage:.1f}%) - {status}")
        if not result["allowed"]:
            print(f"   Reason: {result['reason']}")

    print("\n2. Testing Portfolio Risk Calculation")
    print("-" * 40)

    # Create sample portfolio and returns
    positions = {
        "AAPL": {"quantity": 100, "price": 150.0, "value": 15000},
        "MSFT": {"quantity": 50, "price": 280.0, "value": 14000},
        "GOOGL": {"quantity": 8, "price": 2500.0, "value": 20000},
    }

    # Generate sample returns data
    np.random.seed(42)  # For reproducible results
    returns_data = pd.DataFrame(
        {
            "AAPL": np.random.normal(0.001, 0.02, 100),
            "MSFT": np.random.normal(0.0005, 0.018, 100),
            "GOOGL": np.random.normal(0.0008, 0.025, 100),
        }
    )

    risk_metrics = risk_manager.calculate_portfolio_risk(positions, returns_data)

    print(f"Portfolio VaR (95%): {risk_metrics['var_95']:.4f}")
    print(f"Portfolio VaR (99%): {risk_metrics['var_99']:.4f}")
    print(f"Total Exposure: ${risk_metrics['total_exposure']:,.2f}")
    print("Concentration Risk:")
    for symbol, concentration in risk_metrics["concentration_risk"].items():
        print(f"  {symbol}: {concentration:.2%}")

    print("\n3. Testing Daily Loss Monitoring")
    print("-" * 40)

    # Test different daily P&L scenarios
    daily_scenarios = [
        -500,  # Small loss
        -1500,  # Moderate loss
        -2500,  # Large loss (should trigger alert)
    ]

    for daily_pnl in daily_scenarios:
        risk_manager.portfolio_data = {
            "daily_pnl": daily_pnl,
            "initial_value": portfolio_value,
        }

        result = risk_manager.check_daily_loss_limit()
        status = "✅ OK" if result["within_limit"] else "⚠️ ALERT"
        loss_pct = abs(daily_pnl) / portfolio_value * 100
        print(f"Daily P&L: ${daily_pnl:,} ({loss_pct:.2f}%) - {status}")

        if not result["within_limit"]:
            print(f"   Alert: {result['message']}")

    print("\n4. Testing Trade Blocking Logic")
    print("-" * 40)

    # Test trade scenarios
    trade_scenarios = [
        {
            "symbol": "TSLA",
            "quantity": 100,
            "price": 200.0,
            "side": "buy",
        },  # New position
        {
            "symbol": "AAPL",
            "quantity": 200,
            "price": 155.0,
            "side": "buy",
        },  # Large addition
    ]

    current_portfolio = positions.copy()

    for trade in trade_scenarios:
        result = risk_manager.should_block_trade(
            trade, current_portfolio, portfolio_value
        )
        status = "❌ BLOCKED" if result["block"] else "✅ ALLOWED"
        trade_value = trade["quantity"] * trade["price"]
        print(f"{trade['symbol']} {trade['side']} ${trade_value:,} - {status}")
        if result["block"]:
            print(f"   Reason: {result['reason']}")


def run_risk_monitor_demo():
    """Demonstrate risk monitoring in action"""
    print("\n" + "=" * 60)
    print("RISK MONITORING DEMONSTRATION")
    print("=" * 60)

    logger = Mock(spec=TradingLogger)
    notifier = Mock(spec=NotificationManager)

    # Create risk manager with strict limits for demo
    config = {
        "max_portfolio_var": 0.03,  # Strict 3% VaR limit
        "max_position_size": 0.2,  # 20% position limit
        "max_daily_loss": 0.015,  # 1.5% daily loss limit
        "max_drawdown": 0.1,  # 10% drawdown limit
        "concentration_limit": 0.25,  # 25% concentration limit
    }

    risk_manager = RiskManager(config=config, logger=logger, notifier=notifier)
    monitor = RiskMonitor(risk_manager=risk_manager, logger=logger, check_interval=2)

    print("\nStarting risk monitoring...")
    monitor.start_monitoring()

    print("Risk monitoring active for 5 seconds...")
    time.sleep(5)

    print("Stopping risk monitoring...")
    monitor.stop_monitoring()
    print("Risk monitoring stopped.")


def main():
    """Run all risk management tests"""
    print("=" * 60)
    print("COMPREHENSIVE RISK MANAGEMENT TEST SUITE")
    print("=" * 60)

    # Run unit tests
    print("\nRunning Unit Tests...")
    print("=" * 40)

    test_suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)

    # Run integration tests
    test_risk_scenario_integration()

    # Run monitoring demonstration
    run_risk_monitor_demo()

    print("\n" + "=" * 60)
    print("RISK MANAGEMENT TESTS COMPLETED")
    print("=" * 60)

    if test_result.wasSuccessful():
        print("✅ All tests passed successfully!")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
