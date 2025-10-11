#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""策略测试脚本 - 测试交易策略的信号生成和回测功能"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.mean_reversion_strategy import MeanReversionStrategy
from strategies.moving_average_strategy import MovingAverageStrategy
from data import DataFetcher
from backtesting import BacktestEngine
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("StrategyTest")


def create_sample_data():
    """创建样本测试数据"""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    rng = np.random.default_rng(42)

    # 生成模拟价格数据
    base_price = 100
    returns = rng.normal(0.001, 0.02, 100)
    prices = [base_price]

    for ret in returns:
        prices.append(prices[-1] * (1 + ret))

    data = pd.DataFrame(
        {
            "date": dates,
            "open": prices[:-1],
            "high": [p * (1 + abs(rng.normal(0, 0.01))) for p in prices[:-1]],
            "low": [p * (1 - abs(rng.normal(0, 0.01))) for p in prices[:-1]],
            "close": prices[1:],
            "volume": rng.integers(1000000, 5000000, 100),
        }
    )

    return data


def test_mean_reversion_strategy():
    """测试均值回归策略"""
    print("=" * 50)
    print("测试均值回归策略")
    print("=" * 50)

    # 创建策略实例
    strategy = MeanReversionStrategy(
        bb_period=20, bb_std=2.0, rsi_period=14, rsi_oversold=30, rsi_overbought=70
    )

    # 生成测试数据
    data = create_sample_data()

    # 生成信号
    signals = strategy.generate_signals(data)

    print(f"生成了 {len(signals)} 个信号")
    print(f"信号列: {signals.columns.tolist()}")

    # 统计信号
    signal_counts = signals["signal"].value_counts()
    print("\n信号统计:")
    for signal_type, count in signal_counts.items():
        print(f"  {signal_type}: {count} 次")

    # 显示最后几个信号
    print("\n最后5个信号:")
    print(signals[["signal", "bb_upper", "bb_middle", "bb_lower", "rsi"]].tail())

    return signals


def test_moving_average_strategy():
    """测试移动平均策略"""
    print("\n" + "=" * 50)
    print("测试移动平均策略")
    print("=" * 50)

    # 创建策略实例
    strategy = MovingAverageStrategy(short_window=10, long_window=20)

    # 生成测试数据
    data = create_sample_data()

    # 生成信号
    signals = strategy.generate_signals(data)

    print(f"生成了 {len(signals)} 个信号")
    print(f"信号列: {signals.columns.tolist()}")

    # 统计信号
    signal_counts = signals["signal"].value_counts()
    print("\n信号统计:")
    for signal_type, count in signal_counts.items():
        print(f"  {signal_type}: {count} 次")

    # 显示最后几个信号
    print("\n最后5个信号:")
    print(signals[["signal", "short_ma", "long_ma"]].tail())

    return signals


def test_strategy_comparison():
    """比较不同策略的表现"""
    print("\n" + "=" * 50)
    print("策略对比测试")
    print("=" * 50)

    # 创建测试数据
    data = create_sample_data()

    # 创建策略
    mean_reversion = MeanReversionStrategy()
    moving_average = MovingAverageStrategy()

    # 生成信号
    mr_signals = mean_reversion.generate_signals(data)
    ma_signals = moving_average.generate_signals(data)

    # 统计交易信号
    mr_trades = len(mr_signals[mr_signals["signal"].isin(["BUY", "SELL"])])
    ma_trades = len(ma_signals[ma_signals["signal"].isin(["BUY", "SELL"])])

    print(f"均值回归策略交易信号: {mr_trades} 个")
    print(f"移动平均策略交易信号: {ma_trades} 个")

    # 计算信号频率
    mr_frequency = mr_trades / len(mr_signals) * 100
    ma_frequency = ma_trades / len(ma_signals) * 100

    print(f"均值回归策略信号频率: {mr_frequency:.1f}%")
    print(f"移动平均策略信号频率: {ma_frequency:.1f}%")


def test_backtesting_integration():
    """测试回测集成"""
    print("\n" + "=" * 50)
    print("回测集成测试")
    print("=" * 50)

    try:
        # 创建回测引擎和策略
        BacktestEngine()
        MeanReversionStrategy()

        # 生成测试数据
        data = create_sample_data()

        print(f"使用 {len(data)} 天的测试数据进行回测")
        print("回测引擎创建成功")
        print("策略实例化成功")

        # 可以在这里添加更多的回测测试逻辑

    except ImportError as e:
        print(f"回测集成测试失败 - 导入错误: {e}")
    except ValueError as e:
        print(f"回测集成测试失败 - 数值错误: {e}")
    except RuntimeError as e:
        print(f"回测集成测试失败 - 运行时错误: {e}")


def test_real_data_integration():
    """测试真实数据集成"""
    print("\n" + "=" * 50)
    print("真实数据集成测试")
    print("=" * 50)

    try:
        # 创建数据获取器
        data_fetcher = DataFetcher()

        # 尝试获取真实数据 (使用较短的时间窗口避免API限制)
        symbol = "AAPL"
        start_date = "2024-10-01"
        end_date = "2024-10-10"

        print(f"尝试获取 {symbol} 的数据...")
        data = data_fetcher.fetch_stock_data(symbol, start_date, end_date)

        if not data.empty:
            print(f"成功获取 {len(data)} 天的真实数据")

            # 测试策略
            strategy = MeanReversionStrategy()
            signals = strategy.generate_signals(data)

            print(f"生成了 {len(signals)} 个信号")

            # 显示最新信号
            if not signals.empty:
                latest_signal = signals.iloc[-1]
                print(f"最新信号: {latest_signal['signal']}")
        else:
            print("未能获取到真实数据，可能是网络或API问题")

    except ImportError as e:
        print(f"真实数据测试失败 - 导入错误: {e}")
    except ConnectionError as e:
        print(f"真实数据测试失败 - 网络错误: {e}")
    except ValueError as e:
        print(f"真实数据测试失败 - 数值错误: {e}")
    except RuntimeError as e:
        print(f"真实数据测试失败 - 运行时错误: {e}")


def main():
    """主测试函数"""
    print("开始策略测试")

    # 运行各项测试
    test_mean_reversion_strategy()
    test_moving_average_strategy()
    test_strategy_comparison()
    test_backtesting_integration()
    test_real_data_integration()

    print("\n" + "=" * 50)
    print("策略测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
