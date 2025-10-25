#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器模块 - 上层业务逻辑

提供统一的任务管理接口，整合调度、执行、监控等功能。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

from src.tradingagent import (
    OrderExecutor,
    SignalGenerator,
    DataManager,
    RiskController,
    SimulationBroker,
    TradingSignal
)


logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class Task:
    """任务数据类"""
    task_id: str
    name: str
    symbols: List[str]
    strategies: List[str]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'task_id': self.task_id,
            'name': self.name,
            'symbols': self.symbols,
            'strategies': self.strategies,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error': self.error
        }


class TaskManager:
    """任务管理器 - 业务逻辑层核心"""
    
    def __init__(
        self,
        broker: Optional[Any] = None,
        initial_capital: float = 100000.0
    ):
        """
        初始化任务管理器
        
        Args:
            broker: 经纪商接口，如果为None则使用模拟经纪商
            initial_capital: 初始资金（用于模拟交易）
        """
        # 初始化底层组件
        self.broker = broker or SimulationBroker(initial_capital=initial_capital)
        self.data_manager = DataManager()
        self.signal_generator = SignalGenerator()
        self.executor = OrderExecutor(self.broker)
        self.risk_controller = RiskController(self.broker)
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        
        # 连接经纪商
        if not self.broker.is_connected():
            self.broker.connect()
        
        logger.info("任务管理器初始化完成")
    
    def create_task(
        self,
        task_id: str,
        name: str,
        symbols: List[str],
        strategies: List[str]
    ) -> Task:
        """
        创建新任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            symbols: 股票代码列表
            strategies: 策略列表
            
        Returns:
            Task: 任务对象
        """
        task = Task(
            task_id=task_id,
            name=name,
            symbols=symbols,
            strategies=strategies,
            status=TaskStatus.PENDING
        )
        
        self.tasks[task_id] = task
        logger.info(f"创建任务: {name} ({task_id})")
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            Task: 任务对象
        """
        return self.tasks.get(task_id)
    
    def list_tasks(
        self,
        status_filter: Optional[TaskStatus] = None
    ) -> List[Task]:
        """
        列出所有任务
        
        Args:
            status_filter: 状态过滤
            
        Returns:
            List[Task]: 任务列表
        """
        tasks = list(self.tasks.values())
        
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        
        return tasks
    
    def execute_task(self, task_id: str) -> bool:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        if task.status == TaskStatus.RUNNING:
            logger.warning(f"任务正在运行: {task_id}")
            return False
        
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            
            logger.info(f"开始执行任务: {task.name}")
            
            # TODO: 实现具体的任务执行逻辑
            # 1. 获取数据
            # 2. 运行策略分析
            # 3. 生成交易信号
            # 4. 风险验证
            # 5. 执行订单
            
            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = {'message': '任务执行完成'}
            
            logger.info(f"任务执行完成: {task.name}")
            return True
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.error = str(e)
            logger.error(f"任务执行失败: {task.name} - {e}")
            return False
    
    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            logger.warning(f"任务已结束: {task_id}")
            return False
        
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.now()
        
        logger.info(f"任务已取消: {task.name}")
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """
        删除任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否成功
        """
        if task_id in self.tasks:
            task = self.tasks.pop(task_id)
            logger.info(f"删除任务: {task.name}")
            return True
        else:
            logger.error(f"任务不存在: {task_id}")
            return False
    
    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要
        
        Returns:
            Dict: 账户摘要信息
        """
        account_info = self.executor.get_account_info()
        risk_metrics = self.risk_controller.get_risk_metrics()
        order_stats = self.executor.get_order_statistics()
        signal_stats = self.signal_generator.get_signal_statistics()
        
        return {
            'account': account_info,
            'risk': risk_metrics,
            'orders': order_stats,
            'signals': signal_stats
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_tasks = len(self.tasks)
        status_counts = {}
        
        for status in TaskStatus:
            count = sum(1 for t in self.tasks.values() if t.status == status)
            status_counts[status.value] = count
        
        return {
            'total_tasks': total_tasks,
            'status_breakdown': status_counts,
            'account_summary': self.get_account_summary()
        }
