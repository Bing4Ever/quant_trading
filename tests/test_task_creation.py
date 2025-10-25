#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动化任务创建功能
"""

from src.tradingservice.services.automation.scheduler import AutoTradingScheduler, ScheduledTask, ScheduleFrequency

def test_create_task():
    """测试创建任务"""
    print("🧪 测试自动化任务创建...")
    
    # 创建调度器
    scheduler = AutoTradingScheduler()
    print("✅ 调度器创建成功")
    
    # 创建测试任务
    task = ScheduledTask(
        task_id="test_task_001",
        name="测试任务 - AAPL分析",
        frequency=ScheduleFrequency.DAILY,
        symbols=["AAPL", "MSFT"],
        strategies=["all"],
        enabled=True
    )
    
    # 添加任务
    success = scheduler.add_scheduled_task(task)
    
    if success:
        print("✅ 任务创建成功！")
        print(f"   任务ID: {task.task_id}")
        print(f"   任务名称: {task.name}")
        print(f"   执行频率: {task.frequency.value}")
        print(f"   监控股票: {', '.join(task.symbols)}")
        
        # 查看所有任务
        all_tasks = list(scheduler.scheduled_tasks.values())
        print(f"\n📋 当前任务总数: {len(all_tasks)}")
        
        for t in all_tasks:
            print(f"   - {t.name} ({t.task_id})")
    else:
        print("❌ 任务创建失败")
        return False
    
    print("\n🎉 测试完成！")
    return True

if __name__ == "__main__":
    test_create_task()
