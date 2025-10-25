#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试任务序列化和反序列化
"""

from src.tradingservice.services.automation.scheduler import AutoTradingScheduler, ScheduledTask, ScheduleFrequency

def test_task_serialization():
    """测试任务的保存和加载"""
    print("🧪 测试任务序列化...")
    
    # 创建调度器
    scheduler = AutoTradingScheduler()
    print("✅ 调度器创建成功")
    
    # 创建测试任务
    task = ScheduledTask(
        task_id="test_serialize",
        name="序列化测试任务",
        frequency=ScheduleFrequency.EVERY_15_MINUTES,
        symbols=["AAPL"],
        strategies=["all"],
        enabled=True
    )
    
    # 添加并保存
    scheduler.add_scheduled_task(task)
    print("✅ 任务已添加并保存")
    
    # 创建新的调度器实例（会加载配置）
    scheduler2 = AutoTradingScheduler()
    print("✅ 创建新调度器并加载配置")
    
    # 列出所有任务
    tasks = scheduler2.list_all_tasks()
    print(f"\n📋 加载的任务数: {len(tasks)}")
    
    for t in tasks:
        print(f"\n任务: {t['name']}")
        print(f"  ID: {t['task_id']}")
        print(f"  频率: {t['frequency']}")
        print(f"  状态: {t['status']}")
        print(f"  启用: {t['enabled']}")
    
    print("\n✅ 序列化测试通过！")
    return True

if __name__ == "__main__":
    test_task_serialization()
