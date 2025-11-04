#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 自动化交易调度器模块 - 提供定时任务调度功能
# NOSONAR - 文件级禁用 SonarQube 检查

import sys
import os
import time
import threading
import json
from datetime import datetime, time as dt_time, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import schedule
from src.common.logger import setup_logger
from src.common.notification import NotificationManager
from config import config as app_config
from src.tradingservice.dataaccess import get_scheduler_execution_repository
from src.tradingservice.services.orchestration import (
    TaskManager as OrchestrationTaskManager,
    TaskStatus as OrchestrationTaskStatus,
)

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - fallback for Python < 3.9
    ZoneInfo = None  # type: ignore[assignment]
# 添加项目根路径到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScheduleFrequency(Enum):
    """调度频率枚举"""

    MINUTE = "minute"  # 每分钟
    EVERY_5_MINUTES = "5min"  # 每5分钟
    EVERY_15_MINUTES = "15min"  # 每15分钟
    EVERY_30_MINUTES = "30min"  # 每30分钟
    HOUR = "hour"  # 每小时
    EVERY_2_HOURS = "2hours"  # 每2小时
    EVERY_4_HOURS = "4hours"  # 每4小时
    DAILY = "daily"  # 每日
    WEEKLY = "weekly"  # 每周
    MONTHLY = "monthly"  # 每月


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

    DEFAULT_WINDOW_START = dt_time(9, 30)
    DEFAULT_WINDOW_END = dt_time(16, 0)

    def __init__(self, config_file: str = "config/scheduler_config.json"):
        """
        初始化调度器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.logger = setup_logger("AutoTradingScheduler")
        self.notification_manager = NotificationManager()
        self.task_manager = OrchestrationTaskManager()
        self.execution_repo_factory = get_scheduler_execution_repository
        self.trading_window_config = self._load_trading_window_config()

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
                        # 转换字符串为枚举类型
                        if "frequency" in task_data and isinstance(
                            task_data["frequency"], str
                        ):
                            task_data["frequency"] = ScheduleFrequency(
                                task_data["frequency"]
                            )
                        if "status" in task_data and isinstance(
                            task_data["status"], str
                        ):
                            task_data["status"] = TaskStatus(task_data["status"])

                        # 转换日期时间字符串
                        if "last_run" in task_data and isinstance(
                            task_data["last_run"], str
                        ):
                            task_data["last_run"] = datetime.fromisoformat(
                                task_data["last_run"]
                            )
                        if "next_run" in task_data and isinstance(
                            task_data["next_run"], str
                        ):
                            task_data["next_run"] = datetime.fromisoformat(
                                task_data["next_run"]
                            )

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
                        "frequency": (
                            task.frequency.value
                            if isinstance(task.frequency, ScheduleFrequency)
                            else task.frequency
                        ),
                        "symbols": task.symbols,
                        "strategies": task.strategies,
                        "enabled": task.enabled,
                        "last_run": (
                            task.last_run.isoformat() if task.last_run else None
                        ),
                        "next_run": (
                            task.next_run.isoformat() if task.next_run else None
                        ),
                        "status": (
                            task.status.value
                            if isinstance(task.status, TaskStatus)
                            else task.status
                        ),
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

    def pause_task(self, task_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID

        Returns:
            是否暂停成功
        """
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                task.enabled = False
                self.save_config()
                self.logger.info("暂停任务: %s", task.name)
                return True

            self.logger.warning("任务不存在: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("暂停任务失败: %s", str(e))
            return False

    def resume_task(self, task_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID

        Returns:
            是否恢复成功
        """
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                task.enabled = True

                # 如果调度器正在运行，重新调度该任务
                if self.is_running:
                    self._schedule_task(task)

                self.save_config()
                self.logger.info("恢复任务: %s", task.name)
                return True

            self.logger.warning("任务不存在: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("恢复任务失败: %s", str(e))
            return False

    def _schedule_task(self, task: ScheduledTask):
        """为任务设置调度"""
        if not task.enabled:
            return

        def job_func():
            self.execute_task(task.task_id)

        if task.frequency == ScheduleFrequency.MINUTE:
            schedule.every().minute.do(job_func)
        elif task.frequency == ScheduleFrequency.EVERY_5_MINUTES:
            schedule.every(5).minutes.do(job_func)
        elif task.frequency == ScheduleFrequency.EVERY_15_MINUTES:
            schedule.every(15).minutes.do(job_func)
        elif task.frequency == ScheduleFrequency.EVERY_30_MINUTES:
            schedule.every(30).minutes.do(job_func)
        elif task.frequency == ScheduleFrequency.HOUR:
            schedule.every().hour.do(job_func)
        elif task.frequency == ScheduleFrequency.EVERY_2_HOURS:
            schedule.every(2).hours.do(job_func)
        elif task.frequency == ScheduleFrequency.EVERY_4_HOURS:
            schedule.every(4).hours.do(job_func)
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

            within_window, window_reason = self._is_within_trading_window()
            if not within_window:
                task.last_run = datetime.now()
                task.status = TaskStatus.PENDING
                skip_summary = {
                    "symbol_count": 0,
                    "executed_signals": 0,
                    "rejected_signals": 0,
                    "total_signals": 0,
                    "orders": 0,
                    "task_errors": [window_reason],
                    "skipped": True,
                    "skip_reason": window_reason,
                }
                task.results = {
                    "status": "skipped",
                    "reason": window_reason,
                    "timestamp": task.last_run.isoformat(),
                }
                self.logger.warning(
                    "任务 %s 因交易窗口限制被跳过: %s", task.name, window_reason
                )
                self._persist_execution_result(
                    scheduled_task=task,
                    orchestrated_task=None,
                    execution_summary=skip_summary,
                )
                return

            task.status = TaskStatus.RUNNING
            task.last_run = datetime.now()

            orchestrated_task = self.task_manager.get_task(task.task_id)
            if orchestrated_task is None:
                orchestrated_task = self.task_manager.create_task(
                    task_id=task.task_id,
                    name=task.name,
                    symbols=task.symbols,
                    strategies=task.strategies,
                )
            else:
                orchestrated_task.name = task.name
                orchestrated_task.symbols = task.symbols
                orchestrated_task.strategies = task.strategies
                orchestrated_task.status = OrchestrationTaskStatus.PENDING
                orchestrated_task.error = None
                orchestrated_task.result = None

            execution_success = self.task_manager.execute_task(task.task_id)
            orchestrated_task = self.task_manager.get_task(task.task_id)

            if not execution_success or orchestrated_task is None:
                raise RuntimeError("TaskManager execution failed")

            if orchestrated_task.status == OrchestrationTaskStatus.FAILED:
                failure_reason = orchestrated_task.error or "TaskManager reported failure"
                raise RuntimeError(failure_reason)

            task.results = orchestrated_task.result or {}
            task.status = TaskStatus.COMPLETED

            execution_summary = self._create_results_summary(task.results)
            self._persist_execution_result(
                scheduled_task=task,
                orchestrated_task=orchestrated_task,
                execution_summary=execution_summary,
            )

            report_file = self._generate_report(task, summary=execution_summary)

            self.notification_manager.send_task_completion_notification(
                task_name=task.name,
                results_summary=execution_summary,
                report_file=report_file,
            )

            self.logger.info("任务执行完成: %s", task.name)

        except (RuntimeError, ValueError, AttributeError, OSError) as e:
            task.status = TaskStatus.FAILED
            error_message = str(e)
            self.logger.error("任务执行失败: %s - %s", task.name, error_message)

            self.notification_manager.send_error_notification(
                task_name=task.name, error_message=error_message
            )

        finally:
            # 清理线程引用
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # 保存配置
            self.save_config()

    def _load_trading_window_config(self) -> Dict[str, Any]:
        """Load trading window configuration from global config."""
        section = app_config.get("automation.trading_window", {})
        if not isinstance(section, dict):
            return {"enabled": False}

        enabled = bool(section.get("enabled", False))
        timezone_name = section.get("timezone", "America/New_York")

        tzinfo = None
        if ZoneInfo is not None and timezone_name:
            try:
                tzinfo = ZoneInfo(timezone_name)
            except Exception:  # pragma: no cover - defensive logging
                self.logger.warning("无法解析交易时区 %s，使用本地时间。", timezone_name)
                tzinfo = None

        weekdays_raw = section.get("weekdays", [0, 1, 2, 3, 4])
        weekdays: List[int] = []
        for value in weekdays_raw:
            try:
                casted = int(value)
                if 0 <= casted <= 6:
                    weekdays.append(casted)
            except (TypeError, ValueError):
                continue
        if not weekdays:
            weekdays = [0, 1, 2, 3, 4]

        start_time = self._parse_time_string(section.get("start"), self.DEFAULT_WINDOW_START)
        end_time = self._parse_time_string(section.get("end"), self.DEFAULT_WINDOW_END)

        grace_minutes = section.get("grace_minutes", 0)
        try:
            grace_minutes = int(grace_minutes)
        except (TypeError, ValueError):
            grace_minutes = 0

        holidays = self._parse_holiday_list(section.get("holidays"))

        return {
            "enabled": enabled,
            "timezone_name": timezone_name,
            "timezone": tzinfo,
            "weekdays": sorted(set(weekdays)),
            "start_time": start_time,
            "end_time": end_time,
            "grace": max(grace_minutes, 0),
            "holidays": holidays,
        }

    def _is_within_trading_window(self) -> Tuple[bool, str]:
        """Check whether current time is within the configured trading window."""
        config = getattr(self, "trading_window_config", None)
        if not config or not config.get("enabled", False):
            return True, ""

        tzinfo = config.get("timezone")
        now = datetime.now(tzinfo) if tzinfo else datetime.now()

        weekdays: List[int] = config.get("weekdays", [])
        if weekdays and now.weekday() not in weekdays:
            return False, "当前日期不在允许的交易日范围内"

        holidays = config.get("holidays", set())
        if holidays and now.date() in holidays:
            return False, f"{now.date().isoformat()} 属于配置的休市日期"

        start_time: Optional[dt_time] = config.get("start_time")
        end_time: Optional[dt_time] = config.get("end_time")
        if not start_time or not end_time:
            return True, ""

        start_dt = datetime.combine(now.date(), start_time, tzinfo=tzinfo)
        end_dt = datetime.combine(now.date(), end_time, tzinfo=tzinfo)

        if end_dt <= start_dt:
            self.logger.warning("交易窗口结束时间小于或等于开始时间，忽略窗口检查。")
            return True, ""

        grace = config.get("grace", 0)
        if grace:
            delta = timedelta(minutes=grace)
            start_dt -= delta
            end_dt += delta

        if start_dt <= now < end_dt:
            return True, ""

        tz_label = config.get("timezone_name") or ("local" if tzinfo is None else str(tzinfo))
        reason = (
            f"当前时间 {now.strftime('%H:%M')} ({tz_label}) 不在允许的交易窗口 "
            f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        )
        return False, reason

    @staticmethod
    def _parse_time_string(value: Optional[Any], default: dt_time) -> dt_time:
        """Convert HH:MM strings into time objects with defaults."""
        if isinstance(value, dt_time):
            return value
        text = str(value).strip() if value is not None else ""
        if not text:
            return default
        parts = text.split(":")
        try:
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            return dt_time(hour=hour, minute=minute)
        except (ValueError, IndexError):
            return default

    @staticmethod
    def _parse_holiday_list(values: Optional[Any]) -> set:
        """Parse optional holiday strings into date set."""
        holidays = set()
        if not values:
            return holidays
        iterable = values if isinstance(values, (list, tuple, set)) else [values]
        for entry in iterable:
            try:
                date_obj = datetime.fromisoformat(str(entry)).date()
                holidays.add(date_obj)
            except ValueError:
                continue
        return holidays

    def _persist_execution_result(
        self,
        *,
        scheduled_task: ScheduledTask,
        orchestrated_task: Any,
        execution_summary: Dict[str, Any],
    ) -> None:
        """Persist execution details to the data access layer."""
        factory = getattr(self, "execution_repo_factory", None)
        if not callable(factory):
            return

        payload = getattr(orchestrated_task, "result", None)
        if not isinstance(payload, dict):
            payload = scheduled_task.results if isinstance(scheduled_task.results, dict) else {}

        symbol_details = payload.get("symbols") if isinstance(payload, dict) else {}
        account_snapshot = payload.get("account_snapshot") if isinstance(payload, dict) else None
        risk_snapshot = payload.get("risk_snapshot") if isinstance(payload, dict) else None
        orders_raw = payload.get("orders") if isinstance(payload, dict) else []
        orders_list = list(orders_raw) if isinstance(orders_raw, (list, tuple)) else []
        signals_section = payload.get("signals") if isinstance(payload, dict) else {}

        executed_signals = len(signals_section.get("executed", [])) if isinstance(signals_section, dict) else 0
        rejected_signals = len(signals_section.get("rejected", [])) if isinstance(signals_section, dict) else 0
        total_signals = signals_section.get("total") if isinstance(signals_section, dict) else None
        if total_signals is None:
            total_signals = executed_signals + rejected_signals

        summary_payload = dict(execution_summary or {})
        summary_payload.setdefault("executed_signals", executed_signals)
        summary_payload.setdefault("rejected_signals", rejected_signals)
        summary_payload.setdefault("total_signals", total_signals)
        summary_payload.setdefault("orders", len(orders_list))

        task_errors: List[str] = []
        for source in (
            summary_payload.get("task_errors"),
            payload.get("task_errors") if isinstance(payload, dict) else None,
        ):
            if isinstance(source, (list, tuple, set)):
                task_errors.extend(str(item) for item in source if item)
            elif source:
                task_errors.append(str(source))
        orchestration_error = getattr(orchestrated_task, "error", None)
        if orchestration_error:
            task_errors.append(str(orchestration_error))
        # remove duplicates while preserving order
        seen = set()
        deduped_errors = []
        for error in task_errors:
            if error not in seen:
                seen.add(error)
                deduped_errors.append(error)
        summary_payload["task_errors"] = deduped_errors

        scheduler_status = self._status_to_str(scheduled_task.status)
        orchestration_status = self._status_to_str(getattr(orchestrated_task, "status", None))

        started_at = getattr(orchestrated_task, "started_at", None)
        if started_at is None and isinstance(payload, dict):
            started_at = self._parse_datetime(payload.get("started_at"))
        if started_at is None:
            started_at = getattr(scheduled_task, "last_run", None)

        completed_at = getattr(orchestrated_task, "completed_at", None)
        if completed_at is None and isinstance(payload, dict):
            completed_at = self._parse_datetime(payload.get("completed_at"))
        if completed_at is None:
            completed_at = getattr(scheduled_task, "last_run", None)

        try:
            repository = factory()
        except Exception as factory_error:  # pragma: no cover - defensive logging
            self.logger.error("初始化调度执行仓储失败: %s", factory_error)
            return

        try:
            repository.record_execution(
                task_id=scheduled_task.task_id,
                task_name=scheduled_task.name,
                scheduler_status=scheduler_status,
                orchestration_status=orchestration_status,
                started_at=started_at,
                completed_at=completed_at,
                execution_summary=summary_payload,
                payload=payload,
                symbol_details=symbol_details if isinstance(symbol_details, dict) else {},
                account_snapshot=account_snapshot if isinstance(account_snapshot, dict) else {},
                risk_snapshot=risk_snapshot if isinstance(risk_snapshot, dict) else None,
                task_errors=deduped_errors,
                orders=orders_list,
            )
        except Exception as persist_error:  # pragma: no cover - defensive logging
            self.logger.error("持久化调度执行结果失败: %s", persist_error)
        finally:
            try:
                repository.close()
            except Exception:  # pragma: no cover - defensive close
                pass

    def _generate_report(self, task: ScheduledTask, summary: Optional[Dict[str, Any]] = None) -> str:
        """
        生成任务报告

        Args:
            task: 任务对象
            summary: 已计算的执行摘要

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
                "summary": summary or self._create_results_summary(task.results),
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

        if isinstance(results, dict) and "symbols" in results and "signals" in results:
            symbol_details = results.get("symbols") or {}
            signals = results.get("signals") or {}
            executed_signals = len(signals.get("executed", []))
            rejected_signals = len(signals.get("rejected", []))
            total_signals = signals.get("total")
            if total_signals is None:
                total_signals = executed_signals + rejected_signals
            orders = results.get("orders") or []
            raw_task_errors = results.get("task_errors") or []
            if isinstance(raw_task_errors, (list, tuple, set)):
                task_errors = [str(err) for err in raw_task_errors if err]
            elif raw_task_errors:
                task_errors = [str(raw_task_errors)]
            else:
                task_errors = []

            symbol_breakdown: Dict[str, Any] = {}
            for symbol, payload in symbol_details.items():
                symbol_signals = payload.get("signals") or []
                symbol_orders = payload.get("orders") or []
                symbol_breakdown[symbol] = {
                    "signals": len(symbol_signals),
                    "orders": len(symbol_orders),
                    "errors": payload.get("errors") or [],
                }

            return {
                "symbol_count": len(symbol_details),
                "executed_signals": executed_signals,
                "rejected_signals": rejected_signals,
                "total_signals": total_signals,
                "orders": len(orders),
                "task_errors": task_errors,
                "symbols": symbol_breakdown,
                "account_snapshot": results.get("account_snapshot"),
                "risk_snapshot": results.get("risk_snapshot"),
            }

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

    @staticmethod
    def _status_to_str(status: Any) -> str:
        """Convert enum-like status objects to plain strings."""
        if hasattr(status, "value"):
            return str(getattr(status, "value"))
        if status is None:
            return "unknown"
        return str(status)

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Best-effort conversion of assorted datetime representations."""
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(float(value))
            except (ValueError, OSError):
                return None
        if isinstance(value, str):
            candidate = value.strip()
            if not candidate:
                return None
            candidate = candidate.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(candidate)
            except ValueError:
                return None
        return None

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

        # 处理 frequency 可能是字符串或枚举的情况
        frequency_value = (
            task.frequency.value
            if isinstance(task.frequency, ScheduleFrequency)
            else task.frequency
        )
        status_value = (
            task.status.value if isinstance(task.status, TaskStatus) else task.status
        )

        return {
            "task_id": task.task_id,
            "name": task.name,
            "frequency": frequency_value,
            "status": status_value,
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
