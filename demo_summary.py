#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回测模块调用流程总结演示 - 展示项目中回测模块的各种调用方式"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"🎯 {title}")
    print('='*60)


def demo_call_flow_summary():
    """回测调用流程总结"""
    print("🚀 量化交易系统 - 回测模块调用流程总结")
    
    print_section("1. 直接调用 BacktestEngine (最基本)")
    print("代码示例:")
    print("""
    from backtesting import BacktestEngine
    from strategies import MeanReversionStrategy
    
    engine = BacktestEngine(initial_capital=100000)
    strategy = MeanReversionStrategy()
    results = engine.run_backtest(strategy, data)
    """)
    print("✅ 刚才的 demo_backtest.py 演示了这种方式")
    
    print_section("2. 实时交易引擎中的回测 (LiveTradingEngine)")
    print("调用链: LiveTradingEngine → BacktestEngine → PerformanceAnalyzer")
    print("代码位置: trading/live_trading_engine.py")
    print("""
    def run_backtest_analysis(self, symbol):
        engine = BacktestEngine(initial_capital=100000)
        results = engine.run_backtest(self.strategy, data)
        
        returns = pd.Series(engine.daily_returns)
        analyzer = PerformanceAnalyzer(returns)
        report = analyzer.generate_report()
    """)
    print("✅ 刚才的 demo_live_backtest.py 演示了这种方式")
    
    print_section("3. 策略基类中的回测 (BaseStrategy)")
    print("调用链: Strategy.backtest → 内部简单回测逻辑")
    print("代码位置: strategies/base_strategy.py")
    print("""
    def backtest(self, data, initial_capital=100000):
        signals = self.generate_signals(data)
        # 简化的回测逻辑...
    """)
    
    print_section("4. 策略参数优化中的回测 (MeanReversionStrategy)")
    print("调用链: Strategy.optimize_parameters → 多次 Strategy.backtest")
    print("代码位置: strategies/mean_reversion_strategy.py")
    print("""
    def optimize_parameters(self, market_data, ...):
        for bb_period in range(...):
            for rsi_period in range(...):
                backtest_results = self.backtest(market_data)
                # 评估参数组合...
    """)
    print("注意: 这会运行数十次回测来找最优参数")
    
    print_section("5. 单元测试中的回测 (TestBacktesting)")
    print("调用链: pytest → TestBacktesting → BacktestEngine")
    print("代码位置: tests/test_basic.py")
    print("""
    def test_simple_backtest(self):
        engine = BacktestEngine(initial_capital=10000)
        results = engine.run_backtest(strategy, data)
        assert "total_return" in results
    """)
    
    print_section("6. Jupyter笔记本中的回测")
    print("调用链: Jupyter → BacktestEngine (交互式)")
    print("代码位置: notebooks/strategy_example.ipynb")
    print("""
    backtest_engine = BacktestEngine(initial_capital=100000)
    results = backtest_engine.run_backtest(strategy, data)
    """)
    
    print_section("7. 主程序菜单系统")
    print("调用链: main.py → 用户选择 → 各种交易引擎 → 回测功能")
    print("流程: 用户启动 → 选择引擎 → 选择回测 → 执行回测")
    
    print_section("总结")
    print("📊 回测模块被调用的场景:")
    print("   1. ✅ 直接策略验证 (demo_backtest.py)")
    print("   2. ✅ 实时交易分析 (demo_live_backtest.py)")  
    print("   3. 🔄 参数优化 (demo_optimization.py - 需要较长时间)")
    print("   4. 🧪 单元测试验证")
    print("   5. 📓 研究分析 (Jupyter)")
    print("   6. 🖥️ 用户交互 (主程序菜单)")
    
    print("\n🎯 核心设计优势:")
    print("   - 模块化: 回测引擎独立，可被多处调用")
    print("   - 一致性: 所有地方使用相同的回测逻辑")
    print("   - 灵活性: 支持不同的调用方式和参数")
    print("   - 完整性: 从简单测试到复杂优化的全覆盖")
    
    print(f"\n{'='*60}")
    print("🎉 回测模块调用流程演示完成！")
    print('='*60)


if __name__ == "__main__":
    demo_call_flow_summary()