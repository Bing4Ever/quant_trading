#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""风险管理测试脚本 - 验证止损、止盈、仓位管理等功能"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from risk_management.risk_manager import RiskManager
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("RiskTest")


def test_position_sizing():
    """测试仓位计算"""
    print("=" * 50)
    print("测试仓位计算")
    print("=" * 50)

    rm = RiskManager(max_position_size=0.2)  # 最大20%仓位

    # 测试数据
    test_cases = [
        {"symbol": "AAPL", "price": 150.0, "capital": 100000},
        {"symbol": "MSFT", "price": 300.0, "capital": 100000},
        {"symbol": "GOOGL", "price": 2500.0, "capital": 100000},
    ]

    for case in test_cases:
        shares = rm.calculate_position_size(
            case["symbol"], case["price"], case["capital"]
        )
        investment = shares * case["price"]
        percentage = investment / case["capital"]

        print(
            f"{case['symbol']}: {shares}股, 投资额: ${investment:,.2f} ({percentage:.1%})"
        )


def test_stop_loss():
    """测试止损功能"""
    print("\n" + "=" * 50)
    print("测试止损功能")
    print("=" * 50)

    rm = RiskManager(stop_loss_pct=0.05)  # 5%止损

    # 开多头仓位
    rm.open_position("AAPL", 100, 150.0)

    # 测试不同价格下的止损
    test_prices = [150.0, 145.0, 142.5, 140.0, 135.0]

    for price in test_prices:
        should_stop = rm.should_stop_loss("AAPL", price)
        loss_pct = (price - 150.0) / 150.0
        print(f"价格 ${price:.2f} (跌幅: {loss_pct:.2%}) - 是否止损: {should_stop}")


def test_take_profit():
    """测试止盈功能"""
    print("\n" + "=" * 50)
    print("测试止盈功能")
    print("=" * 50)

    rm = RiskManager(take_profit_pct=0.15)  # 15%止盈

    # 开多头仓位
    rm.open_position("MSFT", 50, 300.0)

    # 测试不同价格下的止盈
    test_prices = [300.0, 320.0, 340.0, 345.0, 360.0]

    for price in test_prices:
        should_profit = rm.should_take_profit("MSFT", price)
        profit_pct = (price - 300.0) / 300.0
        print(f"价格 ${price:.2f} (涨幅: {profit_pct:.2%}) - 是否止盈: {should_profit}")


def test_daily_loss_limit():
    """测试日亏损限制"""
    print("\n" + "=" * 50)
    print("测试日亏损限制")
    print("=" * 50)

    rm = RiskManager(max_daily_loss=0.02)  # 2%日亏损限制

    # 设置日初资金
    start_capital = 100000
    rm.update_daily_capital(start_capital)

    # 测试不同当前资金下的限制
    test_capitals = [100000, 99000, 98500, 98000, 97000]

    for capital in test_capitals:
        is_limited = rm.check_daily_loss_limit(capital)
        loss_pct = (start_capital - capital) / start_capital
        print(
            f"当前资金 ${capital:,.0f} (亏损: {loss_pct:.2%}) - 是否限制: {is_limited}"
        )


def test_portfolio_risk():
    """测试投资组合风险计算"""
    print("\n" + "=" * 50)
    print("测试投资组合风险")
    print("=" * 50)

    rm = RiskManager()

    # 开多个仓位
    rm.open_position("AAPL", 100, 150.0)  # $15,000
    rm.open_position("MSFT", 50, 300.0)  # $15,000
    rm.open_position("GOOGL", 5, 2500.0)  # $12,500

    # 当前价格
    current_prices = {"AAPL": 155.0, "MSFT": 295.0, "GOOGL": 2600.0}

    total_capital = 100000
    portfolio_risk = rm.calculate_portfolio_risk(current_prices, total_capital)

    print(f"总敞口: ${portfolio_risk['total_exposure']:,.2f}")
    print(f"敞口比率: {portfolio_risk['exposure_ratio']:.1%}")
    print(f"持仓数量: {portfolio_risk['position_count']}")

    print("\n个股风险:")
    for symbol, risk in portfolio_risk["position_risks"].items():
        print(f"  {symbol}:")
        print(f"    敞口: ${risk['exposure']:,.2f} ({risk['exposure_pct']:.1%})")
        print(
            f"    浮盈: ${risk['unrealized_pnl']:,.2f} ({risk['unrealized_pnl_pct']:.2%})"
        )


def test_complete_trading_cycle():
    """测试完整交易周期"""
    print("\n" + "=" * 50)
    print("测试完整交易周期")
    print("=" * 50)

    rm = RiskManager()
    rm.update_daily_capital(100000)

    # 1. 开仓
    print("1. 开仓 AAPL 100股 @ $150")
    rm.open_position("AAPL", 100, 150.0)

    # 2. 检查持仓
    position = rm.get_position_info("AAPL")
    print(f"持仓信息: {position}")

    # 3. 模拟价格变动和风险检查
    price_sequence = [150.0, 145.0, 142.0, 148.0, 152.0, 155.0, 173.0, 175.0]

    for price in price_sequence:
        stop_loss = rm.should_stop_loss("AAPL", price)
        take_profit = rm.should_take_profit("AAPL", price)

        print(f"价格 ${price:.2f} - 止损: {stop_loss}, 止盈: {take_profit}")

        if stop_loss or take_profit:
            # 4. 平仓
            trade_record = rm.close_position("AAPL", price)
            print(f"平仓记录: {trade_record}")
            break

    # 5. 查看交易历史
    trades = rm.get_daily_trades()
    print(f"\n当日交易记录: {len(trades)}笔")
    for trade in trades:
        print(f"  {trade}")


def main():
    """主测试函数"""
    print("开始风险管理功能测试")

    test_position_sizing()
    test_stop_loss()
    test_take_profit()
    test_daily_loss_limit()
    test_portfolio_risk()
    test_complete_trading_cycle()

    print("\n" + "=" * 50)
    print("风险管理测试完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
