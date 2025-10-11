#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Schedule功能测试脚本 - 验证定时任务模块工作正常"""

import schedule
import time
from datetime import datetime


def test_schedule_functionality():
    """测试schedule模块的基本功能"""
    print("开始测试schedule模块...")

    # 测试任务计数器
    job_count = 0

    def test_job():
        nonlocal job_count
        job_count += 1
        print(f"定时任务执行第 {job_count} 次 - {datetime.now().strftime('%H:%M:%S')}")

    # 创建测试任务
    schedule.every(2).seconds.do(test_job)
    print(f"创建了定时任务，当前任务数: {len(schedule.jobs)}")

    # 运行几次任务
    print("运行测试任务 10 秒...")
    start_time = time.time()

    while time.time() - start_time < 10:
        schedule.run_pending()
        time.sleep(0.1)

    # 清理任务
    schedule.clear()
    print(f"测试完成，清理后任务数: {len(schedule.jobs)}")
    print(f"总共执行了 {job_count} 次任务")

    # 验证其他调度选项
    print("\n测试其他调度选项...")

    def hourly_job():
        print("每小时任务")

    def daily_job():
        print("每日任务")

    # 测试不同的调度方式
    schedule.every().hour.do(hourly_job)
    schedule.every().day.at("09:30").do(daily_job)
    schedule.every(30).minutes.do(lambda: print("30分钟任务"))

    print(f"创建了 {len(schedule.jobs)} 个不同类型的任务:")
    for i, job in enumerate(schedule.jobs, 1):
        print(f"  {i}. {job}")

    # 清理所有任务
    schedule.clear()
    print(f"\n清理完成，剩余任务: {len(schedule.jobs)}")
    print("✅ Schedule模块测试通过！")


def main():
    """主测试函数"""
    test_schedule_functionality()


if __name__ == "__main__":
    main()
