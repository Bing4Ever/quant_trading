#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据获取测试脚本 - 测试不同数据源的数据获取功能"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from data import DataFetcher

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("DataTest")


def test_data_fetcher_initialization():
    """
    测试数据获取器初始化

    Returns:
        DataFetcher: 初始化成功的数据获取器实例，失败时返回None
    """
    print("=" * 50)
    print("测试数据获取器初始化")
    print("=" * 50)

    try:
        data_fetcher = DataFetcher()
        print("✅ 数据获取器初始化成功")
        return data_fetcher
    except (ImportError, AttributeError, ValueError) as e:
        print(f"❌ 数据获取器初始化失败: {e}")
        return None


def test_stock_data_fetching(data_fetcher):
    """
    测试股票数据获取

    Args:
        data_fetcher: 数据获取器实例

    Returns:
        DataFrame: 获取的股票数据，失败时返回None
    """
    print("\n" + "=" * 50)
    print("测试股票数据获取")
    print("=" * 50)

    if not data_fetcher:
        print("❌ 无法测试，数据获取器未初始化")
        return None

    # 测试参数
    symbol = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    try:
        print(f"获取 {symbol} 从 {start_str} 到 {end_str} 的数据...")
        data = data_fetcher.fetch_stock_data(symbol, start_str, end_str)

        if not data.empty:
            print(f"✅ 成功获取 {len(data)} 天的数据")
            print(f"数据列: {data.columns.tolist()}")
            print("\n数据样本:")
            print(data.head(3))
            print("\n数据统计:")
            print(data.describe())
            return data
        else:
            print("❌ 获取到空数据")
            return None

    except (ValueError, KeyError, AttributeError, TypeError) as e:
        print(f"❌ 数据获取失败: {e}")
        return None


def test_multiple_symbols(data_fetcher):
    """
    测试多个股票数据获取

    Args:
        data_fetcher: 数据获取器实例

    Returns:
        dict: 包含各股票数据的字典
    """
    print("\n" + "=" * 50)
    print("测试多个股票数据获取")
    print("=" * 50)

    if not data_fetcher:
        print("❌ 无法测试，数据获取器未初始化")
        return {}

    symbols = ["AAPL", "MSFT", "GOOGL"]
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # 更短的时间窗口

    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    results = {}

    for symbol in symbols:
        try:
            print(f"获取 {symbol} 数据...")
            data = data_fetcher.fetch_stock_data(symbol, start_str, end_str)

            if not data.empty:
                results[symbol] = data
                print(f"  ✅ {symbol}: {len(data)} 天数据")
            else:
                print(f"  ❌ {symbol}: 空数据")

        except (ValueError, KeyError, AttributeError, TypeError) as e:
            print(f"  ❌ {symbol}: 获取失败 - {e}")

    print(f"\n总计成功获取 {len(results)} 个股票的数据")
    return results


def _check_required_columns(data):
    """检查必需列"""
    required_columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = [col for col in required_columns if col not in data.columns]

    if missing_columns:
        print(f"❌ 缺少必需列: {missing_columns}")
        return False
    else:
        print("✅ 所有必需列都存在")
        return True


def _check_data_completeness(data):
    """检查数据完整性"""
    null_counts = data.isnull().sum()
    if null_counts.sum() > 0:
        print("⚠️ 发现空值:")
        for col, count in null_counts.items():
            if count > 0:
                print(f"  {col}: {count} 个空值")
        return False
    else:
        print("✅ 无空值")
        return True


def _check_price_logic(data):
    """检查价格逻辑"""
    if "High" in data.columns and "Low" in data.columns:
        invalid_high_low = (data["High"] < data["Low"]).sum()
        if invalid_high_low > 0:
            print(f"❌ {invalid_high_low} 天的最高价低于最低价")
            return False
        else:
            print("✅ 价格逻辑正确")
            return True
    return True


def _check_price_ranges(data):
    """检查价格范围"""
    if "Close" in data.columns:
        close_prices = data["Close"]
        if (close_prices <= 0).any():
            print("❌ 发现非正价格")
            return False
        else:
            print("✅ 价格范围正常")

        # 价格变化统计
        if len(close_prices) > 1:
            daily_returns = close_prices.pct_change().dropna()
            extreme_moves = (abs(daily_returns) > 0.2).sum()
            if extreme_moves > 0:
                print(f"⚠️ {extreme_moves} 天的日收益率超过20%")
            else:
                print("✅ 日收益率变化正常")
    return True


def test_data_quality(data):
    """
    测试数据质量

    Args:
        data: 要检查的数据DataFrame
    """
    print("\n" + "=" * 50)
    print("测试数据质量")
    print("=" * 50)

    if data is None or data.empty:
        print("❌ 无数据可供质量检查")
        return

    # 分别检查各个方面
    _check_required_columns(data)
    _check_data_completeness(data)
    _check_price_logic(data)
    _check_price_ranges(data)


def test_data_caching():
    """测试数据缓存功能"""
    print("\n" + "=" * 50)
    print("测试数据缓存")
    print("=" * 50)

    try:
        data_fetcher = DataFetcher()
        symbol = "AAPL"

        # 第一次获取
        start_time = datetime.now()
        data1 = data_fetcher.fetch_stock_data(symbol, "2024-10-01", "2024-10-05")
        first_duration = (datetime.now() - start_time).total_seconds()

        # 第二次获取（应该更快如果有缓存）
        start_time = datetime.now()
        data2 = data_fetcher.fetch_stock_data(symbol, "2024-10-01", "2024-10-05")
        second_duration = (datetime.now() - start_time).total_seconds()

        print(f"第一次获取用时: {first_duration:.2f} 秒")
        print(f"第二次获取用时: {second_duration:.2f} 秒")

        if not data1.empty and not data2.empty:
            if data1.equals(data2):
                print("✅ 两次获取的数据一致")
            else:
                print("⚠️ 两次获取的数据不一致")

    except (ValueError, AttributeError, TypeError) as e:
        print(f"❌ 缓存测试失败: {e}")


def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 50)
    print("测试错误处理")
    print("=" * 50)

    data_fetcher = DataFetcher()

    # 测试无效股票代码
    try:
        print("测试无效股票代码...")
        data = data_fetcher.fetch_stock_data(
            "INVALID_SYMBOL", "2024-10-01", "2024-10-05"
        )
        if data.empty:
            print("✅ 无效代码正确返回空数据")
        else:
            print("⚠️ 无效代码返回了数据")
    except (ValueError, KeyError, AttributeError, TypeError) as e:
        print(f"✅ 无效代码触发异常（正常）: {e}")

    # 测试无效日期格式
    try:
        print("测试无效日期格式...")
        data = data_fetcher.fetch_stock_data("AAPL", "invalid-date", "2024-10-05")
        print("⚠️ 无效日期格式未触发异常")
    except (ValueError, TypeError) as e:
        print(f"✅ 无效日期格式触发异常（正常）: {e}")


def main():
    """主测试函数 - 运行所有数据获取测试"""
    print("开始数据获取测试")

    # 运行各项测试
    data_fetcher = test_data_fetcher_initialization()
    sample_data = test_stock_data_fetching(data_fetcher)
    test_multiple_symbols(data_fetcher)
    test_data_quality(sample_data)
    test_data_caching()
    test_error_handling()

    print("\n" + "=" * 50)
    print("数据获取测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
