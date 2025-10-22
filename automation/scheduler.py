#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 自动化交易调度器模块 - 提供定时任务调度功能
# NOSONAR - 文件级禁用 SonarQube 检查

import sys
import os
import time
import threading
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

import schedule
from utils.logger import setup_logger
from utils.notification import NotificationManager
from strategies.multi_strategy_runner import MultiStrategyRunner
# 添加项目根路径到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ScheduleFrequency(Enum):
    """调度频率枚举"""

    MINUTE = "minute"
    HOUR = "hour"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class TaskStatus(Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:  # pylint: disable=too-many-instance-attributes
    """计划任务数据类"""

    task_id: str
    name: str
    frequency: ScheduleFrequency
    symbols: List[str]
    strategies: List[str]
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    results: Dict[str, Any] = None


class AutoTradingScheduler:  # pylint: disable=too-many-instance-attributes
    """自动化交易调度器"""

    def __init__(self, config_file: str = "config/scheduler_config.json"):
        """
        初始化调度器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = setup_logger("AutoTradingScheduler")
        self.notification_manager = NotificationManager()
        self.multi_strategy_runner = MultiStrategyRunner()

        # 任务存储
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}

        # 调度器状态
        self.is_running = False
        self.scheduler_thread = None

        # 加载配置
        self.load_config()

        self.logger.info("AutoTradingScheduler 初始化完成")

    def load_config(self):
        """加载调度器配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # 恢复计划任务
                for task_data in config.get("scheduled_tasks", []):
                    try:
                        task = ScheduledTask(**task_data)
                        self.scheduled_tasks[task.task_id] = task
                    except (TypeError, ValueError, KeyError) as e:
                        # 单个任务数据不完整或格式错误，跳过并记录
                        self.logger.warning(
                            "跳过无效的任务数据: %s - %s", task_data, str(e)
                        )
                        continue

                self.logger.info("加载了 %d 个计划任务", len(self.scheduled_tasks))
            else:
                # 创建默认配置
                self.create_default_config()

        except json.JSONDecodeError as e:
            # 配置文件不是有效的 JSON
            self.logger.error("解析配置文件失败: %s", str(e))
            self.create_default_config()
        except (OSError, IOError) as e:
            # 无法读取文件（权限/不存在等）
            self.logger.error("读取配置文件失败: %s", str(e))
            self.create_default_config()

    def create_default_config(self):
        """创建默认配置"""
        default_tasks = [
            ScheduledTask(
                task_id="daily_analysis",
                name="每日市场分析",
                frequency=ScheduleFrequency.DAILY,
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                strategies=["all"],
            ),
            ScheduledTask(
                task_id="weekly_report",
                name="周度投资报告",
                frequency=ScheduleFrequency.WEEKLY,
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                strategies=["all"],
            ),
        ]

        for task in default_tasks:
            self.scheduled_tasks[task.task_id] = task

        self.save_config()
        self.logger.info("创建默认配置完成")

    def save_config(self):
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            config = {
                "scheduled_tasks": [
                    {
                        "task_id": task.task_id,
                        "name": task.name,
                        "frequency": task.frequency.value,
                        "symbols": task.symbols,
                        "strategies": task.strategies,
                        "enabled": task.enabled,
                        "last_run": (
                            task.last_run.isoformat() if task.last_run else None
                        ),
                        "next_run": (
                            task.next_run.isoformat() if task.next_run else None
                        ),
                        "status": task.status.value,
                        "results": task.results,
                    }
                    for task in self.scheduled_tasks.values()
                ]
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except (OSError, IOError, TypeError) as e:
            self.logger.error("保存配置失败: %s", str(e))

    def add_scheduled_task(self, task: ScheduledTask) -> bool:
        """
        添加计划任务

        Args:
            task: 计划任务对象

        Returns:
            是否添加成功
        """
        try:
            self.scheduled_tasks[task.task_id] = task
            self._schedule_task(task)
            self.save_config()

            self.logger.info("添加计划任务: %s", task.name)
            return True

        except (AttributeError, ValueError, TypeError) as e:
            self.logger.error("添加计划任务失败: %s", str(e))
            return False

    def remove_scheduled_task(self, task_id: str) -> bool:
        """
        移除计划任务

        Args:
            task_id: 任务ID

        Returns:
            是否移除成功
        """
        try:
            if task_id in self.scheduled_tasks:
                # 取消正在运行的任务
                if task_id in self.running_tasks:
                    self.cancel_task(task_id)

                # 移除任务
                del self.scheduled_tasks[task_id]
                self.save_config()

                self.logger.info("移除计划任务: %s", task_id)
                return True

            self.logger.warning("任务不存在: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("移除计划任务失败: %s", str(e))
            return False

    def _schedule_task(self, task: ScheduledTask):
        """为任务设置调度"""
        if not task.enabled:
            return

        def job_func():
            self.execute_task(task.task_id)

        if task.frequency == ScheduleFrequency.MINUTE:
            schedule.every().minute.do(job_func)
        elif task.frequency == ScheduleFrequency.HOUR:
            schedule.every().hour.do(job_func)
        elif task.frequency == ScheduleFrequency.DAILY:
            schedule.every().day.at("09:30").do(job_func)  # 开盘时间
        elif task.frequency == ScheduleFrequency.WEEKLY:
            schedule.every().monday.at("09:30").do(job_func)  # 周一开盘
        elif task.frequency == ScheduleFrequency.MONTHLY:
            # 注意：schedule 库不直接支持 month，这里用 day 替代
            schedule.every().day.do(job_func)

    def execute_task(self, task_id: str):
        """
        执行指定任务

        Args:
            task_id: 任务ID
        """
        if task_id not in self.scheduled_tasks:
            self.logger.error("任务不存在: %s", task_id)
            return

        task = self.scheduled_tasks[task_id]

        if task_id in self.running_tasks:
            self.logger.warning("任务正在运行: %s", task.name)
            return

        # 创建任务线程
        task_thread = threading.Thread(
            target=self._run_task, args=(task,), name=f"Task-{task_id}"
        )

        self.running_tasks[task_id] = task_thread
        task_thread.start()

    def _run_task(self, task: ScheduledTask):
        """
        运行任务的内部方法

        Args:
            task: 任务对象
        """
        try:
            self.logger.info("开始执行任务: %s", task.name)

            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()

            # 执行多策略分析
            all_results = {}

            for symbol in task.symbols:
                try:
                    self.logger.info("分析股票: %s", symbol)

                    # 运行策略分析
                    results = self.multi_strategy_runner.run_all_strategies(
                        symbol, "1d"
                    )

                    if results:
                        # 生成比较报告
                        comparison_df = (
                            self.multi_strategy_runner.generate_comparison_report()
                        )

                        all_results[symbol] = {
                            "raw_results": results,
                            "comparison": (
                                comparison_df.to_dict("records")
                                if not comparison_df.empty
                                else []
                            ),
                        }

                        self.logger.info("✅ %s 分析完成", symbol)
                    else:
                        self.logger.warning("❌ %s 分析失败", symbol)

                except (ValueError, KeyError, AttributeError, RuntimeError) as e:
                    self.logger.error("分析 %s 时出错: %s", symbol, str(e))
                    continue

            # 保存结果
            task.results = all_results
            task.status = TaskStatus.COMPLETED

            # 生成报告
            report_file = self._generate_report(task)

            # 发送通知
            self.notification_manager.send_task_completion_notification(
                task_name=task.name,
                results_summary=self._create_results_summary(all_results),
                report_file=report_file,
            )

            self.logger.info("任务执行完成: %s", task.name)

        except (RuntimeError, ValueError, AttributeError, OSError) as e:
            task.status = TaskStatus.FAILED
            self.logger.error("任务执行失败: %s - %s", task.name, str(e))

            # 发送错误通知
            self.notification_manager.send_error_notification(
                task_name=task.name, error_message=str(e)
            )

        finally:
            # 清理线程引用
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 保存配置
            self.save_config()

    def _generate_report(self, task: ScheduledTask) -> str:
        """
        生成任务报告

        Args:
            task: 任务对象

        Returns:
            报告文件路径
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = "reports/automated"
            os.makedirs(report_dir, exist_ok=True)

            report_file = os.path.join(
                report_dir, "%s_%s.json" % (task.task_id, timestamp)
            )

            report_data = {
                "task_info": {
                    "task_id": task.task_id,
                    "name": task.name,
                    "execution_time": task.last_run.isoformat(),
                    "symbols": task.symbols,
                    "status": task.status.value,
                },
                "results": task.results,
                "summary": self._create_results_summary(task.results),
            }

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            self.logger.info("报告已生成: %s", report_file)
            return report_file

        except (OSError, IOError, TypeError, ValueError) as e:
            self.logger.error("生成报告失败: %s", str(e))
            return ""

    def _create_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建结果摘要

        Args:
            results: 分析结果

        Returns:
            结果摘要
        """
        if not results:
            return {"message": "无分析结果"}

        summary = {
            "analyzed_symbols": len(results),
            "successful_analysis": len(
                [r for r in results.values() if r.get("comparison")]
            ),
            "best_strategies": {},
            "overall_performance": {},
        }

        # 统计每只股票的最佳策略
        for symbol, data in results.items():
            comparison = data.get("comparison", [])
            if comparison:
                best_strategy = comparison[0]  # 第一个是最佳策略
                summary["best_strategies"][symbol] = {
                    "strategy": best_strategy.get("策略名称"),
                    "return": best_strategy.get("总收益率"),
                    "sharpe": best_strategy.get("夏普比率"),
                }

        return summary

    def start_scheduler(self):
        """启动调度器"""
        if self.is_running:
            self.logger.warning("调度器已经在运行")
            return

        self.is_running = True

        # 设置所有任务的调度
        for task in self.scheduled_tasks.values():
            self._schedule_task(task)

        # 启动调度器线程
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, name="SchedulerThread"
        )
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        self.logger.info("自动化交易调度器已启动")

    def _run_scheduler(self):
        """调度器主循环"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except (RuntimeError, ValueError, AttributeError) as e:
                self.logger.error("调度器运行错误: %s", str(e))
                time.sleep(5)

    def stop_scheduler(self):
        """停止调度器"""
        self.is_running = False

        # 取消所有运行中的任务
        for task_id in self.running_tasks:
            self.cancel_task(task_id)

        # 清除所有调度任务
        schedule.clear()

        self.logger.info("自动化交易调度器已停止")

    def cancel_task(self, task_id: str):
        """
        取消正在运行的任务

        Args:
            task_id: 任务ID
        """
        if task_id in self.running_tasks:
            # 注意：Python线程无法强制终止，这里只是标记
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].status = TaskStatus.CANCELLED
            del self.running_tasks[task_id]
            self.logger.info("任务已取消: %s", task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息
        """
        if task_id not in self.scheduled_tasks:
            return None

        task = self.scheduled_tasks[task_id]

        return {
            "task_id": task.task_id,
            "name": task.name,
            "frequency": task.frequency.value,
            "status": task.status.value,
            "enabled": task.enabled,
            "last_run": task.last_run.isoformat() if task.last_run else None,
            "next_run": task.next_run.isoformat() if task.next_run else None,
            "is_running": task_id in self.running_tasks,
        }

    def list_all_tasks(self) -> List[Dict[str, Any]]:
        """
        列出所有任务

        Returns:
            任务列表
        """
        return [self.get_task_status(task_id) for task_id in self.scheduled_tasks]


if __name__ == "__main__":
    # 使用示例
    scheduler = AutoTradingScheduler()

    try:
        scheduler.start_scheduler()
        print("调度器已启动，按 Ctrl+C 停止...")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n正在停止调度器...")
        scheduler.stop_scheduler()
        print("调度器已停止")
