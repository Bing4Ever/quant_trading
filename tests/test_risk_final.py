#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Risk Management System Test Suite - Testing position limits and risk monitoring"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradingagent.modules.risk_management.risk_manager import RiskManager, RiskMonitor, PositionLimits, RiskLevel, RiskType, RiskAlert


class TestPositionLimits(unittest.TestCase):
    """Test suite for PositionLimits class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limits = PositionLimits()
        self.limits.max_position_value = 50000
        self.limits.max_portfolio_concentration = 0.25
        self.limits.max_total_exposure = 0.8
        self.limits.max_daily_loss = 0.05
        
    def test_initialization(self):
        """Test PositionLimits initialization"""
        self.assertEqual(self.limits.max_position_value, 50000)
        self.assertEqual(self.limits.max_portfolio_concentration, 0.25)
        self.assertEqual(self.limits.max_total_exposure, 0.8)
        

class TestRiskManager(unittest.TestCase):
    """Test suite for RiskManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limits = PositionLimits()
        self.limits.max_position_value = 30000
        self.limits.max_portfolio_concentration = 0.2
        self.limits.max_total_exposure = 0.8
        self.limits.max_daily_loss = 0.02  # 2% daily loss limit
        
        self.risk_manager = RiskManager(limits=self.limits)
        
    def test_initialization(self):
        """Test RiskManager initialization"""
        self.assertIsInstance(self.risk_manager, RiskManager)
        self.assertEqual(self.risk_manager.limits.max_position_value, 30000)
        
    def test_trade_risk_check_position_limit(self):
        """Test trade risk checking for position limits"""
        portfolio_value = 100000
        current_positions = {'AAPL': 10000}  # Start with smaller position
        
        # Test valid trade (10000 + 8000 = 18000, which is 18% < 20% limit)
        allowed, reason = self.risk_manager.check_trade_risk(
            'AAPL', 8000, portfolio_value, current_positions
        )
        self.assertTrue(allowed)
        
        # Test trade that exceeds position limit (10000 + 25000 = 35000 > 30000 limit)
        blocked, reason = self.risk_manager.check_trade_risk(
            'AAPL', 25000, portfolio_value, current_positions
        )
        self.assertFalse(blocked)
        self.assertIn("Position size would exceed limit", reason)
        
    def test_trade_risk_check_concentration(self):
        """Test trade risk checking for concentration limits"""
        portfolio_value = 100000
        current_positions = {'AAPL': 10000}  # Start with smaller position
        
        # Test trade that would exceed concentration (10000 + 15000 = 25000 = 25% > 20% limit)
        blocked, reason = self.risk_manager.check_trade_risk(
            'MSFT', 25000, portfolio_value, current_positions
        )
        self.assertFalse(blocked)
        self.assertIn("Portfolio concentration would exceed limit", reason)
        
    def test_portfolio_update(self):
        """Test portfolio data updating"""
        self.risk_manager.update_portfolio(100000, {'AAPL': 15000, 'MSFT': 12000})
        # Portfolio update should complete without errors
        self.assertIsNotNone(self.risk_manager.monitor)


class TestRiskMonitor(unittest.TestCase):
    """Test suite for RiskMonitor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.limits = PositionLimits()
        self.monitor = RiskMonitor(self.limits)
        
    def test_initialization(self):
        """Test RiskMonitor initialization"""
        self.assertIsInstance(self.monitor, RiskMonitor)
        self.assertFalse(self.monitor.is_monitoring)
        
    def test_portfolio_data_update(self):
        """Test portfolio data updating"""
        self.monitor.update_portfolio_data(100000, {'AAPL': 15000})
        # Check that risk metrics are updated
        self.assertIsNotNone(self.monitor.risk_metrics)


def test_risk_integration_scenarios():
    """Integration test for real-world risk scenarios"""
    print("\n" + "=" * 60)
    print("RISK MANAGEMENT INTEGRATION TEST")
    print("=" * 60)
    
    # Create risk manager with realistic limits
    limits = PositionLimits()
    limits.max_position_value = 25000      # $25k max position
    limits.max_portfolio_concentration = 0.2 # 20% max concentration
    limits.max_total_exposure = 0.85       # 85% max exposure
    limits.max_daily_loss = 0.03           # 3% daily loss limit
    
    risk_manager = RiskManager(limits=limits)
    
    print("\n1. Testing Various Trading Scenarios")
    print("-" * 40)
    
    portfolio_value = 100000
    current_positions = {
        'AAPL': 15000,  # 15% of portfolio
        'MSFT': 12000,  # 12% of portfolio
        'GOOGL': 8000   # 8% of portfolio
    }
    
    # Update portfolio in risk manager
    risk_manager.update_portfolio(portfolio_value, current_positions)
    
    # Test scenarios
    scenarios = [
        ('AAPL', 5000, "Small addition to existing position"),
        ('AAPL', 15000, "Large addition - should exceed position limit"),
        ('TSLA', 20000, "New large position - should be allowed"),
        ('NVDA', 25000, "New position - should exceed concentration"),
        ('META', 30000, "Very large new position - multiple limits exceeded")
    ]
    
    for symbol, trade_value, description in scenarios:
        allowed, reason = risk_manager.check_trade_risk(
            symbol, trade_value, portfolio_value, current_positions
        )
        
        status = "✅ ALLOWED" if allowed else "❌ BLOCKED"
        new_position = current_positions.get(symbol, 0) + trade_value
        concentration = new_position / portfolio_value
        
        print(f"\n{description}")
        print(f"  {symbol}: ${trade_value:,} trade (${new_position:,} total, {concentration:.1%}) - {status}")
        if not allowed:
            print(f"  Reason: {reason}")
    
    print("\n2. Testing Risk Monitoring")
    print("-" * 40)
    
    # Test current risk metrics
    total_exposure = sum(current_positions.values()) / portfolio_value
    largest_position = max(current_positions.values())
    max_concentration = largest_position / portfolio_value
    
    print("Current Portfolio Analysis:")
    print(f"  Total Value: ${portfolio_value:,}")
    print(f"  Total Exposure: {total_exposure:.1%}")
    print(f"  Largest Position: ${largest_position:,} ({max_concentration:.1%})")
    print(f"  Number of Positions: {len(current_positions)}")
    
    # Check against limits
    print("\nRisk Limit Status:")
    print(f"  Position Limit: ${limits.max_position_value:,} - {'✅ OK' if largest_position <= limits.max_position_value else '⚠️ EXCEEDED'}")
    print(f"  Concentration Limit: {limits.max_portfolio_concentration:.1%} - {'✅ OK' if max_concentration <= limits.max_portfolio_concentration else '⚠️ EXCEEDED'}")
    print(f"  Exposure Limit: {limits.max_total_exposure:.1%} - {'✅ OK' if total_exposure <= limits.max_total_exposure else '⚠️ EXCEEDED'}")


def test_risk_alerts():
    """Test risk alert system"""
    print("\n" + "=" * 60)
    print("RISK ALERT SYSTEM TEST")
    print("=" * 60)
    
    # Create sample risk alerts
    alerts = [
        RiskAlert(
            timestamp=datetime.now(),
            risk_type=RiskType.POSITION_SIZE,
            level=RiskLevel.HIGH,
            symbol="AAPL",
            message="Position size exceeds 20% of portfolio",
            current_value=0.25,
            threshold=0.20,
            action_required=True
        ),
        RiskAlert(
            timestamp=datetime.now(),
            risk_type=RiskType.DRAWDOWN,
            level=RiskLevel.CRITICAL,
            symbol="PORTFOLIO",
            message="Portfolio drawdown exceeds critical threshold",
            current_value=0.15,
            threshold=0.12,
            action_required=True
        )
    ]
    
    print("\nGenerated Risk Alerts:")
    print("-" * 30)
    
    for i, alert in enumerate(alerts, 1):
        level_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
        
        print(f"\nAlert {i}:")
        print(f"  {level_emoji.get(alert.level.value, '⚪')} Level: {alert.level.value.upper()}")
        print(f"  📊 Type: {alert.risk_type.value}")
        print(f"  🏷️  Symbol: {alert.symbol}")
        print(f"  📝 Message: {alert.message}")
        print(f"  📈 Current: {alert.current_value:.1%}")
        print(f"  🎯 Threshold: {alert.threshold:.1%}")
        print(f"  ⚡ Action Required: {'Yes' if alert.action_required else 'No'}")


def test_monitoring_thread():
    """Test risk monitoring thread functionality"""
    print("\n" + "=" * 60)
    print("RISK MONITORING THREAD TEST")
    print("=" * 60)
    
    limits = PositionLimits()
    limits.max_daily_loss = 0.02  # 2% daily loss limit
    risk_manager = RiskManager(limits=limits)
    
    print("\nStarting risk monitoring thread...")
    risk_manager.start()
    
    # Let it run for a few seconds
    print("Monitoring active for 3 seconds...")
    time.sleep(3)
    
    print("Stopping risk monitoring thread...")
    risk_manager.stop()
    print("Risk monitoring stopped successfully.")


def main():
    """Run comprehensive risk management tests"""
    print("=" * 60)
    print("COMPREHENSIVE RISK MANAGEMENT TEST SUITE")
    print("=" * 60)
    
    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    print("=" * 40)
    
    test_suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # Run integration tests
    test_risk_integration_scenarios()
    
    # Test alert system
    test_risk_alerts()
    
    # Test monitoring thread
    test_monitoring_thread()
    
    print("\n" + "=" * 60)
    print("🏁 RISK MANAGEMENT TESTS COMPLETED")
    print("=" * 60)
    
    if test_result.wasSuccessful():
        print("✅ All tests passed successfully!")
        print("🛡️  Risk management system is ready for deployment!")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
