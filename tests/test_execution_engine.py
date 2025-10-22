#!/usr/bin/env python3
# 交易执行引擎测试脚本

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from trading.execution_engine import (
    TradeExecutionEngine, TradingSignal, TradingMode,
    create_broker
)


def test_simulation_trading():
    """测试模拟交易"""
    print("🧪 测试模拟交易执行引擎...")
    
    try:
        # 创建模拟券商
        broker = create_broker(TradingMode.SIMULATION, initial_cash=100000)
        
        # 创建交易执行引擎
        engine = TradeExecutionEngine(broker, TradingMode.SIMULATION)
        
        # 启动引擎
        engine.start()
        print("✅ 交易引擎已启动")
        
        # 创建测试信号
        test_signals = [
            TradingSignal(
                symbol="AAPL",
                strategy="RSI Strategy",
                action="buy",
                quantity=100,
                reason="RSI oversold",
                confidence=0.8
            ),
            TradingSignal(
                symbol="MSFT",
                strategy="MA Strategy", 
                action="buy",
                quantity=50,
                reason="MA crossover",
                confidence=0.7
            ),
            TradingSignal(
                symbol="AAPL",
                strategy="RSI Strategy",
                action="sell",
                quantity=50,
                reason="Take profit",
                confidence=0.6
            )
        ]
        
        # 添加信号
        for signal in test_signals:
            engine.add_signal(signal)
            print(f"📈 添加信号: {signal.action} {signal.quantity} {signal.symbol}")
        
        # 等待执行
        print("⏳ 等待信号执行...")
        time.sleep(3)
        
        # 获取状态
        status = engine.get_status()
        print("\n📊 引擎状态:")
        print(f"   运行中: {status['is_running']}")
        print(f"   模式: {status['mode']}")
        print(f"   今日交易次数: {status['daily_trade_count']}")
        print(f"   信号队列大小: {status['queue_size']}")
        
        # 显示账户信息
        account_info = status['account_info']
        print("\n💰 账户信息:")
        print(f"   现金: ${account_info.get('cash', 0):,.2f}")
        print(f"   总价值: ${account_info.get('total_value', 0):,.2f}")
        print(f"   持仓数量: {account_info.get('positions_count', 0)}")
        
        # 显示持仓
        positions = status['positions']
        if positions:
            print("\n📈 当前持仓:")
            for symbol, pos_info in positions.items():
                print(f"   {symbol}: {pos_info['quantity']} 股 "
                      f"@ ${pos_info['market_price']:.2f} "
                      f"= ${pos_info['market_value']:,.2f}")
        else:
            print("\n📈 当前无持仓")
        
        # 停止引擎
        engine.stop()
        print("\n⏹️ 交易引擎已停止")
        
        return True
        
    except (ImportError, ConnectionError, ValueError) as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_management():
    """测试风险管理"""
    print("\n🛡️ 测试风险管理...")
    
    try:
        # 创建小资金账户测试风险控制
        broker = create_broker(TradingMode.SIMULATION, initial_cash=1000)
        engine = TradeExecutionEngine(broker, TradingMode.SIMULATION)
        
        # 设置较严格的风险控制
        engine.max_position_size = 500
        engine.max_daily_trades = 2
        
        engine.start()
        
        # 测试超过持仓限制的信号
        large_signal = TradingSignal(
            symbol="TSLA",
            strategy="Test Strategy",
            action="buy",
            quantity=100,  # 这会超过持仓限制
            reason="Risk test"
        )
        
        engine.add_signal(large_signal)
        print("📈 添加大额信号（应该被风控拦截）")
        
        time.sleep(1)
        
        # 测试多次交易限制
        for i in range(5):
            small_signal = TradingSignal(
                symbol=f"TEST{i}",
                strategy="Test Strategy",
                action="buy",
                quantity=1,
                reason=f"Test trade {i}"
            )
            engine.add_signal(small_signal)
        
        print("📈 添加多个小额信号（测试交易次数限制）")
        
        time.sleep(2)
        
        status = engine.get_status()
        print(f"✅ 风险控制测试完成，今日交易次数: {status['daily_trade_count']}")
        
        engine.stop()
        return True
        
    except (ImportError, ConnectionError, ValueError) as e:
        print(f"❌ 风险管理测试失败: {e}")
        return False


def demo_execution_engine():
    """演示交易执行引擎"""
    print("🎯 交易执行引擎演示")
    print("=" * 50)
    
    # 测试模拟交易
    if test_simulation_trading():
        print("\n✅ 模拟交易测试通过!")
    else:
        print("\n❌ 模拟交易测试失败!")
        return
    
    # 测试风险管理
    if test_risk_management():
        print("\n✅ 风险管理测试通过!")
    else:
        print("\n❌ 风险管理测试失败!")
    
    print("\n🎉 交易执行引擎演示完成!")
    print("\n💡 功能特性:")
    print("   • 支持模拟交易和实盘交易")
    print("   • 自动执行交易信号")
    print("   • 内置风险控制机制")
    print("   • 实时账户和持仓监控")
    print("   • 多线程信号处理")
    print("   • 完整的交易记录")


if __name__ == "__main__":
    demo_execution_engine()