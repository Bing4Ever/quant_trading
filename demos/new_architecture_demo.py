#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新架构使用示例

演示如何使用 TradingAgent (底层) 和 TradingService (上层) 模块
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def example_1_tradingagent_basic():
    """示例1: 使用 TradingAgent 底层组件"""
    print("=" * 60)
    print("示例1: TradingAgent 底层组件使用")
    print("=" * 60)
    
    from src.tradingagent import (
        SimulationBroker,
        OrderExecutor,
        SignalGenerator,
        DataProvider,
        RiskController,
        RiskLimits
    )
    
    # 1. 初始化经纪商（模拟）
    print("\n[1] 初始化模拟经纪商...")
    broker = SimulationBroker(initial_capital=100000.0, commission_rate=0.001)
    broker.connect()
    print(f"✓ 连接状态: {broker.is_connected()}")
    
    # 2. 初始化其他组件
    print("\n[2] 初始化组件...")
    executor = OrderExecutor(broker)
    signal_gen = SignalGenerator()
    data_provider = DataProvider()
    risk_ctrl = RiskController(broker, RiskLimits())
    print("✓ 所有组件初始化完成")
    
    # 3. 获取市场数据
    print("\n[3] 获取市场数据...")
    data = data_provider.get_latest_data('AAPL', days=30)
    if data is not None and not data.empty:
        print(f"✓ 获取到 {len(data)} 条数据")
        print(f"  最新价格: ${data['close'].iloc[-1]:.2f}")
    else:
        print("✗ 未获取到数据")
        return
    
    # 4. 生成交易信号（模拟策略结果）
    print("\n[4] 生成交易信号...")
    strategy_result = {
        'signal': 1,  # 买入信号
        'confidence': 0.85,
        'reason': '均值回归策略：价格低于均线'
    }
    
    signal = signal_gen.generate_signal(
        symbol='AAPL',
        strategy_name='mean_reversion',
        strategy_result=strategy_result,
        quantity=100
    )
    
    if signal:
        print(f"✓ 信号生成: {signal.action.upper()} {signal.quantity} {signal.symbol}")
        print(f"  置信度: {signal.confidence:.2%}")
    
    # 5. 风险验证
    print("\n[5] 风险验证...")
    is_valid, reason = risk_ctrl.validate_signal(signal)
    print(f"  验证结果: {'✓ 通过' if is_valid else '✗ 不通过'}")
    print(f"  原因: {reason}")
    
    # 6. 执行订单（如果通过风险验证）
    if is_valid and signal:
        print("\n[6] 执行订单...")
        order_id = executor.execute_signal(signal)
        if order_id:
            print(f"✓ 订单已提交: {order_id}")
            
            # 7. 查询订单状态
            print("\n[7] 查询订单状态...")
            status = executor.update_order_status(order_id)
            print(f"  订单状态: {status.value if status else 'Unknown'}")
    
    # 8. 查看账户信息
    print("\n[8] 账户信息...")
    account = executor.get_account_info()
    balance = account.get('balance', {})
    print(f"  现金: ${balance.get('cash', 0):,.2f}")
    print(f"  总权益: ${balance.get('equity', 0):,.2f}")
    
    # 9. 风险指标
    print("\n[9] 风险指标...")
    risk_metrics = risk_ctrl.get_risk_metrics()
    print(f"  现金比例: {risk_metrics.get('cash_ratio', 0):.2%}")
    print(f"  总仓位: {risk_metrics.get('total_exposure', 0):.2%}")
    print(f"  当前回撤: {risk_metrics.get('current_drawdown', 0):.2%}")
    
    print("\n" + "=" * 60)
    print("示例1完成!")
    print("=" * 60)


def example_2_tradingservice_highlevel():
    """示例2: 使用 TradingService 上层业务逻辑"""
    print("\n\n")
    print("=" * 60)
    print("示例2: TradingService 上层业务逻辑")
    print("=" * 60)
    
    from src.tradingservice import TaskManager, TaskStatus
    
    # 1. 初始化任务管理器（自动初始化所有底层组件）
    print("\n[1] 初始化任务管理器...")
    task_mgr = TaskManager(initial_capital=100000.0)
    print("✓ 任务管理器初始化完成（包含所有底层组件）")
    
    # 2. 创建任务
    print("\n[2] 创建交易任务...")
    task = task_mgr.create_task(
        task_id='daily_scan_001',
        name='每日市场扫描',
        symbols=['AAPL', 'MSFT', 'GOOGL'],
        strategies=['mean_reversion', 'momentum', 'rsi']
    )
    print(f"✓ 任务创建成功: {task.name}")
    print(f"  任务ID: {task.task_id}")
    print(f"  监控股票: {', '.join(task.symbols)}")
    print(f"  使用策略: {', '.join(task.strategies)}")
    
    # 3. 列出所有任务
    print("\n[3] 列出所有任务...")
    tasks = task_mgr.list_tasks()
    print(f"✓ 当前共有 {len(tasks)} 个任务")
    for t in tasks:
        print(f"  - {t.name} ({t.status.value})")
    
    # 4. 执行任务
    print("\n[4] 执行任务...")
    success = task_mgr.execute_task('daily_scan_001')
    if success:
        print("✓ 任务执行成功")
    else:
        print("✗ 任务执行失败")
    
    # 5. 查看任务状态
    print("\n[5] 查看任务状态...")
    task = task_mgr.get_task('daily_scan_001')
    if task:
        print(f"  状态: {task.status.value}")
        print(f"  创建时间: {task.created_at}")
        print(f"  开始时间: {task.started_at}")
        print(f"  完成时间: {task.completed_at}")
    
    # 6. 获取系统统计
    print("\n[6] 系统统计...")
    stats = task_mgr.get_statistics()
    print(f"  总任务数: {stats['total_tasks']}")
    print(f"  状态分布:")
    for status, count in stats['status_breakdown'].items():
        print(f"    - {status}: {count}")
    
    # 7. 账户摘要
    print("\n[7] 账户摘要...")
    summary = task_mgr.get_account_summary()
    
    account = summary.get('account', {})
    balance = account.get('balance', {})
    print(f"  账户余额:")
    print(f"    现金: ${balance.get('cash', 0):,.2f}")
    print(f"    总权益: ${balance.get('equity', 0):,.2f}")
    
    orders = summary.get('orders', {})
    print(f"  订单统计:")
    print(f"    总订单: {orders.get('total_orders', 0)}")
    print(f"    待处理: {orders.get('pending_orders', 0)}")
    print(f"    已完成: {orders.get('filled_orders', 0)}")
    
    signals = summary.get('signals', {})
    print(f"  信号统计:")
    print(f"    总信号: {signals.get('total_signals', 0)}")
    print(f"    买入信号: {signals.get('buy_signals', 0)}")
    print(f"    卖出信号: {signals.get('sell_signals', 0)}")
    
    print("\n" + "=" * 60)
    print("示例2完成!")
    print("=" * 60)


def example_3_comparison():
    """示例3: 对比说明"""
    print("\n\n")
    print("=" * 60)
    print("示例3: TradingAgent vs TradingService 对比")
    print("=" * 60)
    
    print("""
🔧 TradingAgent (底层可执行逻辑)
───────────────────────────────
适用场景:
  • 需要精细控制交易流程
  • 自定义策略逻辑
  • 单元测试和调试
  • 集成到其他系统

特点:
  ✓ 灵活性高
  ✓ 可定制性强
  ✓ 每个组件独立使用
  ✗ 需要手动组装
  ✗ 代码量较多

使用步骤:
  1. 初始化各个组件（broker, executor, etc.）
  2. 手动调用各组件方法
  3. 自己编排业务流程
  4. 处理错误和异常

───────────────────────────────

🎯 TradingService (上层业务逻辑)
───────────────────────────────
适用场景:
  • 快速开发交易应用
  • 标准化的交易流程
  • API和UI集成
  • 生产环境使用

特点:
  ✓ 开箱即用
  ✓ 业务流程封装好
  ✓ 代码简洁
  ✗ 灵活性相对较低
  ✗ 定制需要修改源码

使用步骤:
  1. 初始化TaskManager（自动初始化所有组件）
  2. 创建任务
  3. 执行任务
  4. 查看结果

───────────────────────────────

💡 建议
───────────────────────────────
• 普通用户: 使用 TradingService
• 高级用户: 使用 TradingAgent
• API开发: 使用 TradingService
• 策略研究: 使用 TradingAgent
• 生产环境: TradingService + 自定义扩展
    """)
    
    print("=" * 60)
    print("示例3完成!")
    print("=" * 60)


def main():
    """主函数"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "新架构使用示例 - TradingAgent & TradingService" + " " * 6 + "║")
    print("╚" + "=" * 58 + "╝")
    
    try:
        # 运行示例1: TradingAgent 底层使用
        example_1_tradingagent_basic()
        
        # 运行示例2: TradingService 上层使用
        example_2_tradingservice_highlevel()
        
        # 运行示例3: 对比说明
        example_3_comparison()
        
        print("\n\n✅ 所有示例运行完成!")
        print("\n📚 更多信息请查看: docs/ARCHITECTURE_V2.md")
        
    except Exception as e:
        print(f"\n❌ 示例运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
