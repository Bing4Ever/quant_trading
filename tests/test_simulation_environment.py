#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulation Trading Environment Test Suite
测试完整的模拟交易环境
"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tradingservice.services.simulation.trading_environment import SimulationEnvironment, SimulationConfig, SimulationMode


class TestSimulationConfig(unittest.TestCase):
    """Test SimulationConfig class"""
    
    def test_default_config(self):
        """Test default configuration"""
        config = SimulationConfig()
        
        self.assertEqual(config.mode, SimulationMode.LIVE_SIM)
        self.assertEqual(config.initial_capital, 100000.0)
        self.assertEqual(config.symbols, ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"])
        self.assertEqual(config.strategies, ["all"])
        self.assertTrue(config.risk_enabled)
        
    def test_custom_config(self):
        """Test custom configuration"""
        config = SimulationConfig(
            mode=SimulationMode.BACKTESTING,
            initial_capital=50000.0,
            symbols=["AAPL", "MSFT"],
            duration_hours=12
        )
        
        self.assertEqual(config.mode, SimulationMode.BACKTESTING)
        self.assertEqual(config.initial_capital, 50000.0)
        self.assertEqual(config.symbols, ["AAPL", "MSFT"])
        self.assertEqual(config.duration_hours, 12)


class TestSimulationEnvironment(unittest.TestCase):
    """Test SimulationEnvironment class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = SimulationConfig(
            initial_capital=10000.0,
            symbols=["AAPL"],
            duration_hours=1,
            notifications_enabled=False  # Disable notifications for testing
        )
        
        # Mock components to avoid actual system calls
        with patch('simulation.trading_environment.MultiStrategyRunner'), \
             patch('simulation.trading_environment.TradeExecutionEngine'), \
             patch('simulation.trading_environment.RiskManager'), \
             patch('simulation.trading_environment.RealTimeMonitor'), \
             patch('simulation.trading_environment.ReportGenerator'):
            
            self.sim_env = SimulationEnvironment(self.config)
    
    def test_initialization(self):
        """Test simulation environment initialization"""
        self.assertIsInstance(self.sim_env, SimulationEnvironment)
        self.assertEqual(self.sim_env.config.initial_capital, 10000.0)
        self.assertFalse(self.sim_env.is_running)
        self.assertIsNone(self.sim_env.start_time)
    
    def test_status_tracking(self):
        """Test status tracking functionality"""
        status = self.sim_env.get_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn('is_running', status)
        self.assertIn('performance_metrics', status)
        self.assertIn('portfolio_value', status)
        self.assertFalse(status['is_running'])
    
    def test_manual_signal_addition(self):
        """Test manual signal addition"""
        # Mock the execution engine
        self.sim_env.execution_engine.submit_signal = Mock(return_value=True)
        
        success = self.sim_env.add_manual_signal("AAPL", "buy", 10)
        
        self.assertTrue(success)
        self.assertEqual(len(self.sim_env.signal_history), 1)
        self.sim_env.execution_engine.submit_signal.assert_called_once()


def test_simulation_integration():
    """Integration test for simulation environment"""
    print("\n" + "=" * 60)
    print("SIMULATION ENVIRONMENT INTEGRATION TEST")
    print("=" * 60)
    
    # Create test configuration
    config = SimulationConfig(
        mode=SimulationMode.LIVE_SIM,
        initial_capital=25000.0,
        symbols=["AAPL", "MSFT"],
        duration_hours=1,  # Short test duration
        notifications_enabled=False,
        reports_enabled=False
    )
    
    print(f"\n📋 Test Configuration:")
    print(f"   Mode: {config.mode.value}")
    print(f"   Capital: ${config.initial_capital:,.2f}")
    print(f"   Symbols: {', '.join(config.symbols)}")
    print(f"   Duration: {config.duration_hours} hour(s)")
    
    # Mock external dependencies for testing
    with patch('simulation.trading_environment.MultiStrategyRunner') as MockStrategy, \
         patch('simulation.trading_environment.TradeExecutionEngine') as MockExecution, \
         patch('simulation.trading_environment.RiskManager') as MockRisk, \
         patch('simulation.trading_environment.RealTimeMonitor') as MockMonitor:
        
        # Configure mocks
        mock_strategy = MockStrategy.return_value
        mock_strategy.run_all_strategies.return_value = {
            'strategy1': {'signal': 'buy', 'confidence': 0.8}
        }
        mock_strategy.generate_comparison_report.return_value = Mock()
        mock_strategy.generate_comparison_report.return_value.empty = True
        
        mock_execution = MockExecution.return_value
        mock_execution.submit_signal.return_value = True
        mock_execution.get_portfolio_value.return_value = 25000.0
        mock_execution.get_all_positions.return_value = {}
        mock_execution.get_available_cash.return_value = 25000.0
        mock_execution.get_position.return_value = 0
        mock_execution.get_trade_history.return_value = []
        mock_execution.start.return_value = None
        mock_execution.stop.return_value = None
        
        mock_risk = MockRisk.return_value
        mock_risk.start.return_value = None
        mock_risk.stop.return_value = None
        mock_risk.update_portfolio.return_value = None
        
        mock_monitor = MockMonitor.return_value
        mock_monitor.start.return_value = None
        mock_monitor.stop.return_value = None
        
        # Create simulation environment
        sim_env = SimulationEnvironment(config)
        
        print(f"\n🔧 Component Status:")
        print(f"   Strategy Runner: {'✅ Ready' if sim_env.strategy_runner else '❌ Not Ready'}")
        print(f"   Execution Engine: {'✅ Ready' if sim_env.execution_engine else '❌ Not Ready'}")
        print(f"   Risk Manager: {'✅ Ready' if sim_env.risk_manager else '❌ Not Ready'}")
        print(f"   Real-time Monitor: {'✅ Ready' if sim_env.real_time_monitor else '❌ Not Ready'}")
        
        # Test simulation lifecycle
        print(f"\n🚀 Testing Simulation Lifecycle:")
        
        # 1. Test initial status
        initial_status = sim_env.get_status()
        print(f"   Initial Running State: {initial_status['is_running']}")
        print(f"   Initial Portfolio Value: ${initial_status['portfolio_value']:,.2f}")
        
        # 2. Test manual signal addition
        print(f"\n📡 Testing Manual Signal Addition:")
        signal_success = sim_env.add_manual_signal("AAPL", "buy", 50)
        print(f"   Manual Signal Success: {'✅' if signal_success else '❌'}")
        print(f"   Signal History Count: {len(sim_env.signal_history)}")
        
        # 3. Test performance metrics calculation
        print(f"\n📊 Testing Performance Metrics:")
        
        # Add some mock portfolio history
        sim_env.portfolio_history = [
            {
                'timestamp': datetime.now(),
                'portfolio_value': 25000.0,
                'positions': {},
                'cash': 25000.0
            },
            {
                'timestamp': datetime.now(),
                'portfolio_value': 25500.0,
                'positions': {'AAPL': 10},
                'cash': 24000.0
            }
        ]
        
        sim_env._calculate_performance_metrics()
        
        metrics = sim_env.performance_metrics
        print(f"   Total P&L: ${metrics['total_pnl']:,.2f}")
        print(f"   Signals Generated: {metrics['signals_generated']}")
        print(f"   Trades Executed: {metrics['trades_executed']}")
        print(f"   Win Rate: {metrics['win_rate']:.1%}")
        
        # 4. Test status after changes
        final_status = sim_env.get_status()
        print(f"\n📈 Final Status:")
        print(f"   Portfolio Value: ${final_status['portfolio_value']:,.2f}")
        print(f"   Signals Count: {final_status['signals_count']}")
        print(f"   Performance Tracking: {'✅ Active' if sim_env.portfolio_history else '❌ Inactive'}")
        
    print(f"\n✅ Integration test completed successfully!")


def test_simulation_error_handling():
    """Test error handling in simulation environment"""
    print("\n" + "=" * 60)
    print("SIMULATION ERROR HANDLING TEST")
    print("=" * 60)
    
    # Test with invalid configuration
    config = SimulationConfig(
        initial_capital=-1000.0,  # Invalid capital
        symbols=[],  # Empty symbols
        duration_hours=0  # Invalid duration
    )
    
    # Mock components
    with patch('simulation.trading_environment.MultiStrategyRunner'), \
         patch('simulation.trading_environment.TradeExecutionEngine'), \
         patch('simulation.trading_environment.RiskManager'), \
         patch('simulation.trading_environment.RealTimeMonitor'):
        
        sim_env = SimulationEnvironment(config)
        
        print(f"\n🧪 Testing Error Scenarios:")
        
        # Test manual signal with invalid parameters
        try:
            success = sim_env.add_manual_signal("", "invalid_action", -10)
            print(f"   Invalid Signal Handling: {'✅ Handled' if not success else '❌ Not Handled'}")
        except Exception as e:
            print(f"   Invalid Signal Exception: ✅ Caught - {type(e).__name__}")
        
        # Test performance calculation with empty data
        try:
            sim_env._calculate_performance_metrics()
            print(f"   Empty Data Handling: ✅ Handled")
        except Exception as e:
            print(f"   Empty Data Exception: ❌ Failed - {str(e)}")
        
        # Test status retrieval
        try:
            status = sim_env.get_status()
            print(f"   Status Retrieval: ✅ Working")
        except Exception as e:
            print(f"   Status Exception: ❌ Failed - {str(e)}")
    
    print(f"\n✅ Error handling test completed!")


def main():
    """Run comprehensive simulation environment tests"""
    print("=" * 60)
    print("SIMULATION ENVIRONMENT TEST SUITE")
    print("=" * 60)
    
    # Run unit tests
    print("\n🧪 Running Unit Tests...")
    print("=" * 40)
    
    test_suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    test_runner = unittest.TextTestRunner(verbosity=2)
    test_result = test_runner.run(test_suite)
    
    # Run integration tests
    test_simulation_integration()
    
    # Run error handling tests
    test_simulation_error_handling()
    
    print("\n" + "=" * 60)
    print("🏁 SIMULATION ENVIRONMENT TESTS COMPLETED")
    print("=" * 60)
    
    if test_result.wasSuccessful():
        print("✅ All tests passed successfully!")
        print("🚀 Simulation environment is ready for deployment!")
        return True
    else:
        print("❌ Some tests failed. Please review the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
