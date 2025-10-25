"""
Backtest Result Model - 回测结果模型
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from src.common.dataaccess import OrmBase


class BacktestResult(OrmBase):
    """回测结果模型"""
    
    __tablename__ = 'backtest_results'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    symbol = Column(String(20), nullable=False, index=True, comment='股票代码')
    strategy_name = Column(String(100), nullable=False, comment='策略名称')
    strategy_params = Column(Text, comment='策略参数（JSON字符串）')
    backtest_config = Column(Text, comment='回测配置（JSON字符串）')
    
    # 性能指标
    total_return = Column(Float, comment='总收益率')
    annualized_return = Column(Float, comment='年化收益率')
    sharpe_ratio = Column(Float, comment='夏普比率')
    max_drawdown = Column(Float, comment='最大回撤')
    volatility = Column(Float, comment='波动率')
    win_rate = Column(Float, comment='胜率')
    total_trades = Column(Integer, comment='总交易次数')
    avg_trade_return = Column(Float, comment='平均每笔收益')
    
    # 元数据
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    notes = Column(Text, comment='备注')
    
    def __repr__(self):
        return f"<BacktestResult(id={self.id}, symbol={self.symbol}, strategy={self.strategy_name})>"
