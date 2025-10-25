#!/usr/bin/env python3
"""
日志工具模块
为自动化交易系统提供完整的日志记录功能
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional

def setup_logger(name: str, 
                 log_file: Optional[str] = None,
                 level: int = logging.INFO,
                 console_output: bool = True,
                 max_bytes: int = 10*1024*1024,  # 10MB
                 backup_count: int = 5) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则自动生成
        level: 日志级别
        console_output: 是否输出到控制台
        max_bytes: 单个日志文件最大字节数
        backup_count: 备份文件数量
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 如果没有指定日志文件，自动生成
    if log_file is None:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = f"{log_dir}/{name.lower()}_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
    
    # 文件处理器（支持文件大小轮转）
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=max_bytes, 
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def setup_trading_logger(component_name: str) -> logging.Logger:
    """
    为交易系统组件设置专用日志记录器
    
    Args:
        component_name: 组件名称
        
    Returns:
        交易专用日志记录器
    """
    log_dir = "logs/trading"
    os.makedirs(log_dir, exist_ok=True)
    
    # 按日期轮转的日志文件
    log_file = f"{log_dir}/{component_name.lower()}.log"
    
    logger = logging.getLogger(f"trading.{component_name}")
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # 详细的交易日志格式
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 按天轮转的文件处理器
    file_handler = TimedRotatingFileHandler(
        log_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 保留30天的日志
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

class TradingLogger:
    """交易日志记录类"""
    
    def __init__(self, component_name: str):
        self.logger = setup_trading_logger(component_name)
        self.component_name = component_name
    
    def log_strategy_signal(self, symbol: str, strategy: str, signal: str, 
                           price: float, reason: str = ""):
        """记录策略信号"""
        self.logger.info(f"SIGNAL | {symbol} | {strategy} | {signal} | ${price:.2f} | {reason}")
    
    def log_trade_execution(self, symbol: str, action: str, quantity: int, 
                           price: float, order_id: str = ""):
        """记录交易执行"""
        self.logger.info(f"TRADE | {symbol} | {action} | {quantity} shares | ${price:.2f} | Order: {order_id}")
    
    def log_portfolio_update(self, total_value: float, cash: float, positions: dict):
        """记录投资组合更新"""
        self.logger.info(f"PORTFOLIO | Total: ${total_value:.2f} | Cash: ${cash:.2f} | Positions: {len(positions)}")
    
    def log_risk_event(self, event_type: str, symbol: str, details: str):
        """记录风险事件"""
        self.logger.warning(f"RISK | {event_type} | {symbol} | {details}")
    
    def log_system_event(self, event: str, details: str = ""):
        """记录系统事件"""
        self.logger.info(f"SYSTEM | {event} | {details}")
    
    def log_error(self, error_type: str, error_message: str, symbol: str = ""):
        """记录错误"""
        symbol_part = f" | {symbol}" if symbol else ""
        self.logger.error(f"ERROR | {error_type}{symbol_part} | {error_message}")

# 预配置的日志记录器
def get_scheduler_logger():
    """获取调度器日志记录器"""
    return setup_logger("Scheduler", "logs/scheduler.log")

def get_strategy_logger():
    """获取策略日志记录器"""
    return setup_logger("Strategy", "logs/strategy.log")

def get_data_logger():
    """获取数据日志记录器"""
    return setup_logger("Data", "logs/data.log")

def get_notification_logger():
    """获取通知日志记录器"""
    return setup_logger("Notification", "logs/notification.log")