#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时交易引擎回测调用演示
演示 LiveTradingEngine → BacktestEngine → PerformanceAnalyzer 的完整流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from trading.live_trading_engine import LiveTradingEngine


def demo_live_trading_backtest():
    """演示实时交易引擎的回测功能"""
    print("🚀 实时交易引擎回测调用演示")
    print("=" * 60)
    
    # 创建实时交易引擎
    print("📊 创建实时交易引擎...")
    engine = LiveTradingEngine()
    
    # 运行回测分析 (这里会调用 BacktestEngine 和 PerformanceAnalyzer)
    print("🔄 运行回测分析...")
    print("   调用流程: LiveTradingEngine → BacktestEngine → PerformanceAnalyzer")
    
    # 对苹果股票进行回测
    results = engine.run_backtest_analysis("AAPL")
    
    if results:
        print("✅ 回测分析完成")
        print("📋 主要结果:")
        print(f"   总收益率: {results.get('total_return', 0):.2%}")
        print(f"   夏普比率: {results.get('sharpe_ratio', 0):.2f}")
        print(f"   最大回撤: {results.get('max_drawdown', 0):.2%}")
    else:
        print("❌ 回测分析失败")
    
    print("\n" + "=" * 60)
    print("🎉 实时交易引擎回测演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo_live_trading_backtest()