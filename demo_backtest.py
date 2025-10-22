#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测流程演示脚本
演示完整的调用流程：用户操作 → 策略 → 回测引擎 → 性能分析 → 结果报告
"""

import sys
from pathlib import Path
import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入所需模块
from data import DataFetcher
from strategies import MeanReversionStrategy
from backtesting import BacktestEngine, PerformanceAnalyzer
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BacktestDemo')


def step1_fetch_data():
    """步骤1: 获取市场数据"""
    print("🔄 步骤1: 获取市场数据")
    print("=" * 50)
    
    # 创建数据获取器
    fetcher = DataFetcher()
    
    # 获取苹果公司的历史数据
    try:
        data = fetcher.fetch_stock_data(
            symbol='AAPL',
            start_date='2023-01-01',
            end_date='2024-01-01'
        )
        
        if not data.empty:
            print(f"✅ 成功获取 {len(data)} 天的数据")
            print(f"数据范围: {data.index[0].date()} 到 {data.index[-1].date()}")
            print(f"数据列: {list(data.columns)}")
            return data
        else:
            print("❌ 未获取到数据")
            return None
            
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return None


def step2_create_strategy():
    """步骤2: 创建交易策略"""
    print("\n🎯 步骤2: 创建交易策略")
    print("=" * 50)
    
    # 创建均值回归策略
    strategy = MeanReversionStrategy(
        bb_period=20,      # 布林带周期
        bb_std=2.0,        # 布林带标准差
        rsi_period=14,     # RSI周期
        rsi_oversold=30,   # RSI超卖阈值
        rsi_overbought=70  # RSI超买阈值
    )
    
    print("✅ 均值回归策略创建成功")
    print("策略参数:")
    print(f"  - 布林带周期: {strategy.get_parameter('bb_period')}")
    print(f"  - RSI周期: {strategy.get_parameter('rsi_period')}")
    print(f"  - RSI超卖/超买: {strategy.get_parameter('rsi_oversold')}/{strategy.get_parameter('rsi_overbought')}")
    
    return strategy


def step3_generate_signals(strategy, data):
    """步骤3: 生成交易信号"""
    print("\n📈 步骤3: 生成交易信号")
    print("=" * 50)
    
    try:
        signals = strategy.generate_signals(data)
        
        # 统计信号
        buy_signals = (signals['signal'] == 1).sum()
        sell_signals = (signals['signal'] == -1).sum()
        hold_signals = (signals['signal'] == 0).sum()
        
        print("✅ 信号生成成功")
        print("交易信号统计:")
        print(f"  - 买入信号: {buy_signals} 次")
        print(f"  - 卖出信号: {sell_signals} 次")
        print(f"  - 持有信号: {hold_signals} 次")
        print(f"  - 总信号数: {len(signals)} 个")
        
        return signals
        
    except Exception as e:
        print(f"❌ 信号生成失败: {e}")
        return None


def step4_run_backtest(strategy, data):
    """步骤4: 运行回测"""
    print("\n🚀 步骤4: 运行回测引擎")
    print("=" * 50)
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(
            initial_capital=100000,  # 初始资金10万
            commission=0.001,        # 手续费0.1%
            slippage=0.0005         # 滑点0.05%
        )
        
        print("📊 回测引擎初始化完成")
        print(f"  - 初始资金: ${engine.initial_capital:,.2f}")
        print(f"  - 手续费率: {engine.commission:.3%}")
        print(f"  - 滑点: {engine.slippage:.4%}")
        
        # 运行回测
        print("\n⏳ 正在运行回测...")
        results = engine.run_backtest(strategy, data)
        
        print("✅ 回测完成!")
        return results, engine
        
    except Exception as e:
        print(f"❌ 回测失败: {e}")
        return None, None


def step5_analyze_performance(engine):
    """步骤5: 性能分析"""
    print("\n📊 步骤5: 性能分析")
    print("=" * 50)
    
    try:
        # 创建性能分析器
        returns = pd.Series(engine.daily_returns)
        analyzer = PerformanceAnalyzer(returns)
        
        # 计算性能指标
        metrics = analyzer.calculate_metrics()
        
        print("✅ 性能分析完成")
        return metrics
        
    except Exception as e:
        print(f"❌ 性能分析失败: {e}")
        return None


def step6_generate_report(results, metrics):
    """步骤6: 生成结果报告"""
    print("\n📋 步骤6: 结果报告")
    print("=" * 60)
    
    # 基本回测结果
    print("🎯 回测基本结果:")
    print(f"  总收益率: {results.get('total_return', 0):.2%}")
    print(f"  年化收益率: {results.get('annual_return', 0):.2%}")
    print(f"  最大回撤: {results.get('max_drawdown', 0):.2%}")
    print(f"  夏普比率: {results.get('sharpe_ratio', 0):.2f}")
    print(f"  最终资金: ${results.get('final_capital', 0):,.2f}")
    
    # 交易统计
    print("\n📈 交易统计:")
    print(f"  总交易次数: {results.get('total_trades', 0)}")
    print(f"  胜率: {results.get('win_rate', 0):.1%}")
    print(f"  平均盈利: ${results.get('avg_win', 0):.2f}")
    print(f"  平均亏损: ${results.get('avg_loss', 0):.2f}")
    
    # 风险指标
    if metrics:
        print("\n⚠️ 风险指标:")
        print(f"  波动率: {metrics.get('volatility', 0):.2%}")
        print(f"  VaR (95%): {metrics.get('var_95', 0):.2%}")
        print(f"  索提诺比率: {metrics.get('sortino_ratio', 0):.2f}")


def main():
    """主函数 - 演示完整回测流程"""
    print("🚀 量化交易回测流程演示")
    print("=" * 60)
    
    # 步骤1: 获取数据
    data = step1_fetch_data()
    if data is None:
        print("❌ 演示终止：无法获取数据")
        return
    
    # 步骤2: 创建策略
    strategy = step2_create_strategy()
    
    # 步骤3: 生成信号
    signals = step3_generate_signals(strategy, data)
    if signals is None:
        print("❌ 演示终止：信号生成失败")
        return
    
    # 步骤4: 运行回测
    results, engine = step4_run_backtest(strategy, data)
    if results is None:
        print("❌ 演示终止：回测失败")
        return
    
    # 步骤5: 性能分析
    metrics = step5_analyze_performance(engine)
    
    # 步骤6: 生成报告
    step6_generate_report(results, metrics)
    
    print("\n" + "=" * 60)
    print("🎉 回测流程演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()