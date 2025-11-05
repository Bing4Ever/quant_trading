#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# è‡ªåŠ¨åŒ–äº¤æ˜“è°ƒåº¦å™¨æ¨¡å— - æä¾›å®šæ—¶ä»»åŠ¡è°ƒåº¦åŠŸèƒ½
# NOSONAR - æ–‡ä»¶çº§ç¦ç”¨ SonarQube æ£€æŸ¥

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
# æ·»åŠ é¡¹ç›®æ ¹è·¯å¾„åˆ° Python è·¯å¾„
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class ScheduleFrequency(Enum):
    """è°ƒåº¦é¢‘çŽ‡æžšä¸¾"""

    MINUTE = "minute"  # æ¯åˆ†é’Ÿ
    EVERY_5_MINUTES = "5min"  # æ¯5åˆ†é’Ÿ
    EVERY_15_MINUTES = "15min"  # æ¯15åˆ†é’Ÿ
    EVERY_30_MINUTES = "30min"  # æ¯30åˆ†é’Ÿ
    HOUR = "hour"  # æ¯å°æ—¶
    EVERY_2_HOURS = "2hours"  # æ¯2å°æ—¶
    EVERY_4_HOURS = "4hours"  # æ¯4å°æ—¶
    DAILY = "daily"  # æ¯æ—¥
    WEEKLY = "weekly"  # æ¯å‘¨
    MONTHLY = "monthly"  # æ¯æœˆ


class TaskStatus(Enum):
    """ä»»åŠ¡çŠ¶æ€æžšä¸¾"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:  # pylint: disable=too-many-instance-attributes
    """è®¡åˆ’ä»»åŠ¡æ•°æ®ç±»"""

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
    """è‡ªåŠ¨åŒ–äº¤æ˜“è°ƒåº¦å™¨"""

    DEFAULT_WINDOW_START = dt_time(9, 30)
    DEFAULT_WINDOW_END = dt_time(16, 0)

    def __init__(self, config_file: str = "config/scheduler_config.json"):
        """
        åˆå§‹åŒ–è°ƒåº¦å™¨

        Args:
            config_file: é…ç½®æ–‡ä»¶è·¯å¾„
        """
        self.config_file = config_file
        self.logger = setup_logger("AutoTradingScheduler")
        self.notification_manager = NotificationManager()
        self.task_manager = OrchestrationTaskManager()
        self.execution_repo_factory = get_scheduler_execution_repository
        self.trading_window_config = self._load_trading_window_config()

        # ä»»åŠ¡å­˜å‚¨
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}

        # è°ƒåº¦å™¨çŠ¶æ€
        self.is_running = False
        self.scheduler_thread = None

        # åŠ è½½é…ç½®
        self.load_config()

        self.logger.info("AutoTradingScheduler åˆå§‹åŒ–å®Œæˆ")

    def load_config(self):
        """åŠ è½½è°ƒåº¦å™¨é…ç½®"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # æ¢å¤è®¡åˆ’ä»»åŠ¡
                for task_data in config.get("scheduled_tasks", []):
                    try:
                        # è½¬æ¢å­—ç¬¦ä¸²ä¸ºæžšä¸¾ç±»åž‹
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

                        # è½¬æ¢æ—¥æœŸæ—¶é—´å­—ç¬¦ä¸²
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
                        # å•ä¸ªä»»åŠ¡æ•°æ®ä¸å®Œæ•´æˆ–æ ¼å¼é”™è¯¯ï¼Œè·³è¿‡å¹¶è®°å½•
                        self.logger.warning(
                            "è·³è¿‡æ— æ•ˆçš„ä»»åŠ¡æ•°æ®: %s - %s", task_data, str(e)
                        )
                        continue

                self.logger.info("åŠ è½½äº† %d ä¸ªè®¡åˆ’ä»»åŠ¡", len(self.scheduled_tasks))
            else:
                # åˆ›å»ºé»˜è®¤é…ç½®
                self.create_default_config()

        except json.JSONDecodeError as e:
            # é…ç½®æ–‡ä»¶ä¸æ˜¯æœ‰æ•ˆçš„ JSON
            self.logger.error("è§£æžé…ç½®æ–‡ä»¶å¤±è´¥: %s", str(e))
            self.create_default_config()
        except (OSError, IOError) as e:
            # æ— æ³•è¯»å–æ–‡ä»¶ï¼ˆæƒé™/ä¸å­˜åœ¨ç­‰ï¼‰
            self.logger.error("è¯»å–é…ç½®æ–‡ä»¶å¤±è´¥: %s", str(e))
            self.create_default_config()

    def create_default_config(self):
        """åˆ›å»ºé»˜è®¤é…ç½®"""
        default_tasks = [
            ScheduledTask(
                task_id="daily_analysis",
                name="æ¯æ—¥å¸‚åœºåˆ†æž",
                frequency=ScheduleFrequency.DAILY,
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                strategies=["all"],
            ),
            ScheduledTask(
                task_id="weekly_report",
                name="å‘¨åº¦æŠ•èµ„æŠ¥å‘Š",
                frequency=ScheduleFrequency.WEEKLY,
                symbols=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                strategies=["all"],
            ),
        ]

        for task in default_tasks:
            self.scheduled_tasks[task.task_id] = task

        self.save_config()
        self.logger.info("åˆ›å»ºé»˜è®¤é…ç½®å®Œæˆ")

    def save_config(self):
        """ä¿å­˜é…ç½®åˆ°æ–‡ä»¶"""
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
            self.logger.error("ä¿å­˜é…ç½®å¤±è´¥: %s", str(e))

    def add_scheduled_task(self, task: ScheduledTask) -> bool:
        """
        æ·»åŠ è®¡åˆ’ä»»åŠ¡

        Args:
            task: è®¡åˆ’ä»»åŠ¡å¯¹è±¡

        Returns:
            æ˜¯å¦æ·»åŠ æˆåŠŸ
        """
        try:
            self.scheduled_tasks[task.task_id] = task
            self._schedule_task(task)
            self.save_config()

            self.logger.info("æ·»åŠ è®¡åˆ’ä»»åŠ¡: %s", task.name)
            return True

        except (AttributeError, ValueError, TypeError) as e:
            self.logger.error("æ·»åŠ è®¡åˆ’ä»»åŠ¡å¤±è´¥: %s", str(e))
            return False

    def remove_scheduled_task(self, task_id: str) -> bool:
        """
        ç§»é™¤è®¡åˆ’ä»»åŠ¡

        Args:
            task_id: ä»»åŠ¡ID

        Returns:
            æ˜¯å¦ç§»é™¤æˆåŠŸ
        """
        try:
            if task_id in self.scheduled_tasks:
                # å–æ¶ˆæ­£åœ¨è¿è¡Œçš„ä»»åŠ¡
                if task_id in self.running_tasks:
                    self.cancel_task(task_id)

                # ç§»é™¤ä»»åŠ¡
                del self.scheduled_tasks[task_id]
                self.save_config()

                self.logger.info("ç§»é™¤è®¡åˆ’ä»»åŠ¡: %s", task_id)
                return True

            self.logger.warning("ä»»åŠ¡ä¸å­˜åœ¨: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("ç§»é™¤è®¡åˆ’ä»»åŠ¡å¤±è´¥: %s", str(e))
            return False

    def pause_task(self, task_id: str) -> bool:
        """
        æš‚åœä»»åŠ¡

        Args:
            task_id: ä»»åŠ¡ID

        Returns:
            æ˜¯å¦æš‚åœæˆåŠŸ
        """
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                task.enabled = False
                self.save_config()
                self.logger.info("æš‚åœä»»åŠ¡: %s", task.name)
                return True

            self.logger.warning("ä»»åŠ¡ä¸å­˜åœ¨: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("æš‚åœä»»åŠ¡å¤±è´¥: %s", str(e))
            return False

    def resume_task(self, task_id: str) -> bool:
        """
        æ¢å¤ä»»åŠ¡

        Args:
            task_id: ä»»åŠ¡ID

        Returns:
            æ˜¯å¦æ¢å¤æˆåŠŸ
        """
        try:
            if task_id in self.scheduled_tasks:
                task = self.scheduled_tasks[task_id]
                task.enabled = True

                # å¦‚æžœè°ƒåº¦å™¨æ­£åœ¨è¿è¡Œï¼Œé‡æ–°è°ƒåº¦è¯¥ä»»åŠ¡
                if self.is_running:
                    self._schedule_task(task)

                self.save_config()
                self.logger.info("æ¢å¤ä»»åŠ¡: %s", task.name)
                return True

            self.logger.warning("ä»»åŠ¡ä¸å­˜åœ¨: %s", task_id)
            return False

        except (KeyError, AttributeError) as e:
            self.logger.error("æ¢å¤ä»»åŠ¡å¤±è´¥: %s", str(e))
            return False

    def _schedule_task(self, task: ScheduledTask):
        """ä¸ºä»»åŠ¡è®¾ç½®è°ƒåº¦"""
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
            schedule.every().day.at("09:30").do(job_func)  # å¼€ç›˜æ—¶é—´
        elif task.frequency == ScheduleFrequency.WEEKLY:
            schedule.every().monday.at("09:30").do(job_func)  # å‘¨ä¸€å¼€ç›˜
        elif task.frequency == ScheduleFrequency.MONTHLY:
            # æ³¨æ„ï¼šschedule åº“ä¸ç›´æŽ¥æ”¯æŒ monthï¼Œè¿™é‡Œç”¨ day æ›¿ä»£
            schedule.every().day.do(job_func)

    def execute_task(self, task_id: str):
        """
        æ‰§è¡ŒæŒ‡å®šä»»åŠ¡

        Args:
            task_id: ä»»åŠ¡ID
        """
        if task_id not in self.scheduled_tasks:
            self.logger.error("ä»»åŠ¡ä¸å­˜åœ¨: %s", task_id)
            return

        task = self.scheduled_tasks[task_id]

        if task_id in self.running_tasks:
            self.logger.warning("ä»»åŠ¡æ­£åœ¨è¿è¡Œ: %s", task.name)
            return

        # åˆ›å»ºä»»åŠ¡çº¿ç¨‹
        task_thread = threading.Thread(
            target=self._run_task, args=(task,), name=f"Task-{task_id}"
        )

        self.running_tasks[task_id] = task_thread
        task_thread.start()

    def _run_task(self, task: ScheduledTask):
        """
        è¿è¡Œä»»åŠ¡çš„å†…éƒ¨æ–¹æ³•

        Args:
            task: ä»»åŠ¡å¯¹è±¡
        """
        try:
            self.logger.info("å¼€å§‹æ‰§è¡Œä»»åŠ¡: %s", task.name)

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
                    "ä»»åŠ¡ %s å› äº¤æ˜“çª—å£é™åˆ¶è¢«è·³è¿‡: %s", task.name, window_reason
                )
                self._persist_execution_result(
                    scheduled_task=task,
                    orchestrated_task=None,
                    execution_summary=skip_summary,
                )
                return

            risk_ok, risk_reason, risk_context = self.task_manager.check_broker_risk_preconditions()
            if not risk_ok:
                task.last_run = datetime.now()
                task.status = TaskStatus.PENDING
                risk_context = risk_context or {}
                skip_summary = {
                    "symbol_count": len(risk_context.get("positions", {})),
                    "executed_signals": 0,
                    "rejected_signals": 0,
                    "total_signals": 0,
                    "orders": 0,
                    "task_errors": [risk_reason],
                    "skipped": True,
                    "skip_reason": risk_reason,
                    "risk_context": risk_context,
                }
                task.results = {
                    "status": "skipped",
                    "reason": risk_reason,
                    "timestamp": task.last_run.isoformat(),
                    "risk_context": risk_context,
                }
                self.logger.warning(
                    "Task %s blocked by broker risk limits: %s", task.name, risk_reason
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

            self.logger.info("ä»»åŠ¡æ‰§è¡Œå®Œæˆ: %s", task.name)

        except (RuntimeError, ValueError, AttributeError, OSError) as e:
            task.status = TaskStatus.FAILED
            error_message = str(e)
            self.logger.error("ä»»åŠ¡æ‰§è¡Œå¤±è´¥: %s - %s", task.name, error_message)

            self.notification_manager.send_error_notification(
                task_name=task.name, error_message=error_message
            )

        finally:
            # æ¸…ç†çº¿ç¨‹å¼•ç”¨
            if task.task_id in self.running_tasks:
                del self.running_tasks[task.task_id]

            # ä¿å­˜é…ç½®
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
                self.logger.warning("æ— æ³•è§£æžäº¤æ˜“æ—¶åŒº %sï¼Œä½¿ç”¨æœ¬åœ°æ—¶é—´ã€‚", timezone_name)
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
            return False, "å½“å‰æ—¥æœŸä¸åœ¨å…è®¸çš„äº¤æ˜“æ—¥èŒƒå›´å†…"

        holidays = config.get("holidays", set())
        if holidays and now.date() in holidays:
            return False, f"{now.date().isoformat()} å±žäºŽé…ç½®çš„ä¼‘å¸‚æ—¥æœŸ"

        start_time: Optional[dt_time] = config.get("start_time")
        end_time: Optional[dt_time] = config.get("end_time")
        if not start_time or not end_time:
            return True, ""

        start_dt = datetime.combine(now.date(), start_time, tzinfo=tzinfo)
        end_dt = datetime.combine(now.date(), end_time, tzinfo=tzinfo)

        if end_dt <= start_dt:
            self.logger.warning("äº¤æ˜“çª—å£ç»“æŸæ—¶é—´å°äºŽæˆ–ç­‰äºŽå¼€å§‹æ—¶é—´ï¼Œå¿½ç•¥çª—å£æ£€æŸ¥ã€‚")
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
            f"å½“å‰æ—¶é—´ {now.strftime('%H:%M')} ({tz_label}) ä¸åœ¨å…è®¸çš„äº¤æ˜“çª—å£ "
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
            self.logger.error("åˆå§‹åŒ–è°ƒåº¦æ‰§è¡Œä»“å‚¨å¤±è´¥: %s", factory_error)
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
            self.logger.error("æŒä¹…åŒ–è°ƒåº¦æ‰§è¡Œç»“æžœå¤±è´¥: %s", persist_error)
        finally:
            try:
                repository.close()
            except Exception:  # pragma: no cover - defensive close
                pass

    def get_execution_history(
        self,
        *,
        limit: int = 50,
        task_id: Optional[str] = None,
        scheduler_status: Optional[str] = None,
        orchestration_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch persisted automation execution history."""
        factory = getattr(self, "execution_repo_factory", None)
        if not callable(factory):
            return []

        repository = None
        try:
            repository = factory()
            records = repository.fetch_recent_executions(
                limit=limit,
                task_id=task_id,
                scheduler_status=scheduler_status,
                orchestration_status=orchestration_status,
            )
            return [self._serialize_execution_record(record) for record in records]
        except Exception as exc:  # pragma: no cover - defensive logging
            self.logger.error("Failed to load execution history: %s", exc)
            return []
        finally:
            if repository is not None:
                try:
                    repository.close()
                except Exception:
                    pass

    def _serialize_execution_record(self, record: Any) -> Dict[str, Any]:
        """Transform an execution ORM record into a serializable dictionary."""
        def _safe_json_load(value: Any, default: Any):
            if not value:
                return default
            try:
                return json.loads(value)
            except (TypeError, ValueError):
                return default

        def _iso(value: Any) -> Optional[str]:
            if isinstance(value, datetime):
                return value.isoformat()
            return None

        summary = _safe_json_load(getattr(record, "summary_json", None), {})
        symbol_details = _safe_json_load(getattr(record, "symbol_details_json", None), {})
        account_snapshot = _safe_json_load(getattr(record, "account_snapshot_json", None), {})
        payload = _safe_json_load(getattr(record, "payload_json", None), {})
        task_errors_raw = _safe_json_load(getattr(record, "task_errors_json", None), [])

        if isinstance(task_errors_raw, (list, tuple, set)):
            task_errors = [str(item) for item in task_errors_raw if item]
        elif task_errors_raw:
            task_errors = [str(task_errors_raw)]
        else:
            task_errors = []

        orders_payload: List[Dict[str, Any]] = []
        for order in getattr(record, "orders", []) or []:
            raw_order = _safe_json_load(getattr(order, "raw_order_json", None), {})
            orders_payload.append({
                "order_id": getattr(order, "order_id", None),
                "symbol": getattr(order, "symbol", None),
                "action": getattr(order, "action", None),
                "status": getattr(order, "status", None),
                "quantity": getattr(order, "quantity", None),
                "filled_quantity": getattr(order, "filled_quantity", None),
                "average_price": getattr(order, "average_price", None),
                "submitted_at": _iso(getattr(order, "submitted_at", None)),
                "completed_at": _iso(getattr(order, "completed_at", None)),
                "raw": raw_order,
            })

        risk_model = getattr(record, "risk_snapshot", None)
        risk_payload: Optional[Dict[str, Any]] = None
        if risk_model is not None:
            risk_payload = {
                "equity": getattr(risk_model, "equity", None),
                "cash": getattr(risk_model, "cash", None),
                "buying_power": getattr(risk_model, "buying_power", None),
                "exposure": getattr(risk_model, "exposure", None),
                "maintenance_margin": getattr(risk_model, "maintenance_margin", None),
                "captured_at": _iso(getattr(risk_model, "captured_at", None)),
                "raw": _safe_json_load(getattr(risk_model, "raw_metrics_json", None), {}),
            }

        return {
            "run_id": getattr(record, "run_id", None),
            "task_id": getattr(record, "task_id", None),
            "task_name": getattr(record, "task_name", None),
            "scheduler_status": getattr(record, "scheduler_status", None),
            "orchestration_status": getattr(record, "orchestration_status", None),
            "started_at": _iso(getattr(record, "started_at", None)),
            "completed_at": _iso(getattr(record, "completed_at", None)),
            "executed_signals": getattr(record, "executed_signals", None),
            "rejected_signals": getattr(record, "rejected_signals", None),
            "total_signals": getattr(record, "total_signals", None),
            "order_count": getattr(record, "order_count", None),
            "task_errors": task_errors,
            "summary": summary,
            "symbol_details": symbol_details,
            "account_snapshot": account_snapshot,
            "payload": payload,
            "orders": orders_payload,
            "risk_snapshot": risk_payload,
            "created_at": _iso(getattr(record, "created_at", None)),
        }

    def _generate_report(self, task: ScheduledTask, summary: Optional[Dict[str, Any]] = None) -> str:
        """
        ç”Ÿæˆä»»åŠ¡æŠ¥å‘Š

        Args:
            task: ä»»åŠ¡å¯¹è±¡
            summary: å·²è®¡ç®—çš„æ‰§è¡Œæ‘˜è¦

        Returns:
            æŠ¥å‘Šæ–‡ä»¶è·¯å¾„
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

            self.logger.info("æŠ¥å‘Šå·²ç”Ÿæˆ: %s", report_file)
            return report_file

        except (OSError, IOError, TypeError, ValueError) as e:
            self.logger.error("ç”ŸæˆæŠ¥å‘Šå¤±è´¥: %s", str(e))
            return ""

    def _create_results_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        åˆ›å»ºç»“æžœæ‘˜è¦

        Args:
            results: åˆ†æžç»“æžœ

        Returns:
            ç»“æžœæ‘˜è¦
        """
        if not results:
            return {"message": "æ— åˆ†æžç»“æžœ"}

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

        # ç»Ÿè®¡æ¯åªè‚¡ç¥¨çš„æœ€ä½³ç­–ç•¥
        for symbol, data in results.items():
            comparison = data.get("comparison", [])
            if comparison:
                best_strategy = comparison[0]  # ç¬¬ä¸€ä¸ªæ˜¯æœ€ä½³ç­–ç•¥
                summary["best_strategies"][symbol] = {
                    "strategy": best_strategy.get("ç­–ç•¥åç§°"),
                    "return": best_strategy.get("æ€»æ”¶ç›ŠçŽ‡"),
                    "sharpe": best_strategy.get("å¤æ™®æ¯”çŽ‡"),
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
        """å¯åŠ¨è°ƒåº¦å™¨"""
        if self.is_running:
            self.logger.warning("è°ƒåº¦å™¨å·²ç»åœ¨è¿è¡Œ")
            return

        self.is_running = True

        # è®¾ç½®æ‰€æœ‰ä»»åŠ¡çš„è°ƒåº¦
        for task in self.scheduled_tasks.values():
            self._schedule_task(task)

        # å¯åŠ¨è°ƒåº¦å™¨çº¿ç¨‹
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, name="SchedulerThread"
        )
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()

        self.logger.info("è‡ªåŠ¨åŒ–äº¤æ˜“è°ƒåº¦å™¨å·²å¯åŠ¨")

    def _run_scheduler(self):
        """è°ƒåº¦å™¨ä¸»å¾ªçŽ¯"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except (RuntimeError, ValueError, AttributeError) as e:
                self.logger.error("è°ƒåº¦å™¨è¿è¡Œé”™è¯¯: %s", str(e))
                time.sleep(5)

    def stop_scheduler(self):
        """åœæ­¢è°ƒåº¦å™¨"""
        self.is_running = False

        # å–æ¶ˆæ‰€æœ‰è¿è¡Œä¸­çš„ä»»åŠ¡
        for task_id in self.running_tasks:
            self.cancel_task(task_id)

        # æ¸…é™¤æ‰€æœ‰è°ƒåº¦ä»»åŠ¡
        schedule.clear()

        self.logger.info("è‡ªåŠ¨åŒ–äº¤æ˜“è°ƒåº¦å™¨å·²åœæ­¢")

    def cancel_task(self, task_id: str):
        """
        å–æ¶ˆæ­£åœ¨è¿è¡Œçš„ä»»åŠ¡

        Args:
            task_id: ä»»åŠ¡ID
        """
        if task_id in self.running_tasks:
            # æ³¨æ„ï¼šPythonçº¿ç¨‹æ— æ³•å¼ºåˆ¶ç»ˆæ­¢ï¼Œè¿™é‡Œåªæ˜¯æ ‡è®°
            if task_id in self.scheduled_tasks:
                self.scheduled_tasks[task_id].status = TaskStatus.CANCELLED
            del self.running_tasks[task_id]
            self.logger.info("ä»»åŠ¡å·²å–æ¶ˆ: %s", task_id)

    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        èŽ·å–ä»»åŠ¡çŠ¶æ€

        Args:
            task_id: ä»»åŠ¡ID

        Returns:
            ä»»åŠ¡çŠ¶æ€ä¿¡æ¯
        """
        if task_id not in self.scheduled_tasks:
            return None

        task = self.scheduled_tasks[task_id]

        # å¤„ç† frequency å¯èƒ½æ˜¯å­—ç¬¦ä¸²æˆ–æžšä¸¾çš„æƒ…å†µ
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
        åˆ—å‡ºæ‰€æœ‰ä»»åŠ¡

        Returns:
            ä»»åŠ¡åˆ—è¡¨
        """
        return [self.get_task_status(task_id) for task_id in self.scheduled_tasks]


if __name__ == "__main__":
    # ä½¿ç”¨ç¤ºä¾‹
    scheduler = AutoTradingScheduler()

    try:
        scheduler.start_scheduler()
        print("è°ƒåº¦å™¨å·²å¯åŠ¨ï¼ŒæŒ‰ Ctrl+C åœæ­¢...")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\næ­£åœ¨åœæ­¢è°ƒåº¦å™¨...")
        scheduler.stop_scheduler()
        print("è°ƒåº¦å™¨å·²åœæ­¢")
