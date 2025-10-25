#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略参数优化回测演示
演示 Strategy.optimize_parameters → BacktestEngine 的调用流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.tradingagent.modules.data_provider import DataFetcher
from src.tradingagent.modules.strategies import MeanReversionStrategy


def demo_strategy_optimization():
    """演示策略参数优化中的回测调用"""
    print("🎯 策略参数优化回测演示")
    print("=" * 60)
    
    # 获取数据
    print("📊 获取市场数据...")
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data('AAPL', '2023-01-01', '2024-01-01')
    
    if data.empty:
        print("❌ 无法获取数据")
        return
    
    print(f"✅ 获取到 {len(data)} 天的数据")
    
    # 创建策略
    print("\n🎯 创建均值回归策略...")
    strategy = MeanReversionStrategy()
    
    # 运行参数优化 (这里会多次调用回测)
    print("\n🔄 运行参数优化...")
    print("   调用流程: Strategy.optimize_parameters → 多次 BacktestEngine.run_backtest")
    print("   注意: 这个过程会运行多个回测，可能需要一些时间...")
    
    try:
        # 使用较小的参数范围来节省时间
        optimization_results = strategy.optimize_parameters(
            data,
            bb_period_range=(15, 25),      # 布林带周期: 15-25
            rsi_period_range=(10, 16),     # RSI周期: 10-16  
            rsi_threshold_range=(25, 35)   # RSI阈值: 25-35
        )
        
        print("✅ 参数优化完成")
        
        # 显示最优参数
        best_params = optimization_results.get('best_parameters', {})
        best_return = optimization_results.get('best_return', 0)
        
        print("\n📋 优化结果:")
        print(f"   最优收益率: {best_return:.2%}")
        print("   最优参数:")
        for param, value in best_params.items():
            print(f"     {param}: {value}")
        
        # 显示尝试的参数组合数量
        all_results = optimization_results.get('all_results', [])
        print("\n📊 统计信息:")
        print(f"   测试的参数组合: {len(all_results)} 个")
        print("   每个组合都运行了一次完整的回测")
        
    except Exception as e:
        print(f"❌ 参数优化失败: {e}")
        return
    
    print("\n" + "=" * 60)
    print("🎉 策略参数优化演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo_strategy_optimization()