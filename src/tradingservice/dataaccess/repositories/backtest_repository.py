"""
Backtest Repository - 回测结果仓储

提供回测结果的数据访问操作
"""

import json
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.common.dataaccess import BaseRepository
from ..models.backtest_result import BacktestResult

logger = logging.getLogger(__name__)


class BacktestRepository(BaseRepository[BacktestResult]):
    """回测结果仓储 - 继承 BaseRepository 获得基础 CRUD 能力"""
    
    def __init__(self, session: Session):
        super().__init__(BacktestResult, session)
    
    def save_result(
        self,
        symbol: str,
        strategy_name: str,
        strategy_params: Dict,
        results: Dict,
        backtest_config: Optional[Dict] = None,
        notes: str = ""
    ) -> int:
        """
        保存回测结果
        
        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            strategy_params: 策略参数
            results: 回测结果（包含各项指标）
            backtest_config: 回测配置
            notes: 备注
            
        Returns:
            保存的结果ID
        """
        try:
            # 创建实体
            result = BacktestResult(
                symbol=symbol,
                strategy_name=strategy_name,
                strategy_params=json.dumps(strategy_params, ensure_ascii=False),
                backtest_config=json.dumps(backtest_config or {}, ensure_ascii=False),
                total_return=results.get('total_return', 0),
                annualized_return=results.get('annualized_return', 0),
                sharpe_ratio=results.get('sharpe_ratio', 0),
                max_drawdown=results.get('max_drawdown', 0),
                volatility=results.get('volatility', 0),
                win_rate=results.get('win_rate', 0),
                total_trades=results.get('total_trades', 0),
                avg_trade_return=results.get('avg_trade_return', 0),
                notes=notes
            )
            
            # 保存
            result = self.add(result)
            logger.info(f"回测结果已保存，ID: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {str(e)}")
            self.rollback()
            raise
    
    def get_history(
        self,
        symbol: Optional[str] = None,
        strategy_name: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        获取回测历史记录
        
        Args:
            symbol: 股票代码（可选）
            strategy_name: 策略名称（可选）
            limit: 限制返回数量
            
        Returns:
            回测历史列表（字典格式）
        """
        query = self.session.query(BacktestResult)
        
        if symbol:
            query = query.filter(BacktestResult.symbol == symbol)
        
        if strategy_name:
            query = query.filter(BacktestResult.strategy_name == strategy_name)
        
        results = query.order_by(BacktestResult.created_at.desc()).limit(limit).all()
        
        # 转换为字典
        return [self._to_dict(r) for r in results]
    
    def get_best_results(
        self,
        metric: str = 'total_return',
        limit: int = 10
    ) -> List[Dict]:
        """
        获取最佳回测结果
        
        Args:
            metric: 排序指标（total_return, sharpe_ratio等）
            limit: 返回数量
            
        Returns:
            最佳结果列表
        """
        # 根据指标排序
        order_column = getattr(BacktestResult, metric, BacktestResult.total_return)
        
        results = (self.session.query(BacktestResult)
                   .order_by(order_column.desc())
                   .limit(limit)
                   .all())
        
        return [self._to_dict(r) for r in results]
    
    def get_by_strategy(self, strategy_name: str, limit: int = 50) -> List[Dict]:
        """
        获取某策略的所有回测结果
        
        Args:
            strategy_name: 策略名称
            limit: 限制返回数量
            
        Returns:
            回测结果列表
        """
        results = (self.session.query(BacktestResult)
                   .filter(BacktestResult.strategy_name == strategy_name)
                   .order_by(BacktestResult.created_at.desc())
                   .limit(limit)
                   .all())
        
        return [self._to_dict(r) for r in results]
    
    def _to_dict(self, result: BacktestResult) -> Dict:
        """
        将模型转换为字典
        
        Args:
            result: BacktestResult 实例
            
        Returns:
            字典格式的结果
        """
        return {
            'id': result.id,
            'symbol': result.symbol,
            'strategy_name': result.strategy_name,
            'strategy_params': json.loads(result.strategy_params) if result.strategy_params else {},
            'backtest_config': json.loads(result.backtest_config) if result.backtest_config else {},
            'total_return': result.total_return,
            'annualized_return': result.annualized_return,
            'sharpe_ratio': result.sharpe_ratio,
            'max_drawdown': result.max_drawdown,
            'volatility': result.volatility,
            'win_rate': result.win_rate,
            'total_trades': result.total_trades,
            'avg_trade_return': result.avg_trade_return,
            'created_at': result.created_at.isoformat() if result.created_at else None,
            'notes': result.notes
        }
