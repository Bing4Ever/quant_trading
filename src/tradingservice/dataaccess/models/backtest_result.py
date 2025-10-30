"""
回测结果 ORM 模型。

用于存储单次回测的核心绩效指标与配置参数。
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from src.common.dataaccess import OrmBase


class BacktestResult(OrmBase):
    """回测表现快照的持久化对象。"""

    __tablename__ = "backtest_results"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 策略元数据
    symbol = Column(String(20), nullable=False, index=True, comment="Ticker symbol")
    strategy_name = Column(String(100), nullable=False, comment="Strategy name")
    strategy_params = Column(
        Text, comment="Serialized strategy parameters (JSON formatted)"
    )
    backtest_config = Column(
        Text, comment="Serialized backtest configuration (JSON formatted)"
    )

    # 绩效指标
    total_return = Column(Float, comment="Total return for the backtest period")
    annualized_return = Column(Float, comment="Annualized return percentage")
    sharpe_ratio = Column(Float, comment="Sharpe ratio")
    max_drawdown = Column(Float, comment="Maximum drawdown")
    volatility = Column(Float, comment="Return volatility")
    win_rate = Column(Float, comment="Winning trade percentage")
    total_trades = Column(Integer, comment="Number of trades executed")
    avg_trade_return = Column(Float, comment="Average return per trade")

    # 审计信息
    created_at = Column(
        DateTime, default=datetime.now, comment="Record creation timestamp"
    )
    notes = Column(Text, comment="Additional notes")

    def __repr__(self) -> str:
        return (
            f"<BacktestResult(id={self.id}, symbol={self.symbol}, "
            f"strategy={self.strategy_name})>"
        )
