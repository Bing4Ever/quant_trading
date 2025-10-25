"""
Strategy Comparison Repository - 策略对比数据仓库
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.common.dataaccess import BaseRepository
from ..models.strategy_comparison import StrategyComparison


class StrategyComparisonRepository(BaseRepository[StrategyComparison]):
    """策略对比数据仓库"""
    
    def __init__(self):
        super().__init__(StrategyComparison)
    
    def save_comparison(
        self, 
        comparison_name: str,
        symbols: List[str],
        results: Dict[str, Any],
        best_performer: str
    ) -> StrategyComparison:
        """
        保存策略对比结果
        
        Args:
            comparison_name: 对比名称
            symbols: 股票代码列表
            results: 对比结果（包含所有策略的性能指标）
            best_performer: 最佳表现者（策略名称）
            
        Returns:
            保存的对比记录
        """
        comparison = StrategyComparison(
            comparison_name=comparison_name,
            symbols=json.dumps(symbols),
            results=json.dumps(results),
            best_performer=best_performer,
            created_at=datetime.now()
        )
        return self.add(comparison)
    
    def get_comparison_history(
        self,
        comparison_name: Optional[str] = None,
        limit: int = 10
    ) -> List[StrategyComparison]:
        """
        获取对比历史记录
        
        Args:
            comparison_name: 对比名称（可选，用于筛选）
            limit: 返回记录数量
            
        Returns:
            对比记录列表
        """
        query = self.session.query(StrategyComparison)
        
        if comparison_name:
            query = query.filter(StrategyComparison.comparison_name == comparison_name)
        
        return query.order_by(StrategyComparison.created_at.desc()).limit(limit).all()
    
    def get_comparison_by_id(self, comparison_id: int) -> Optional[StrategyComparison]:
        """
        根据ID获取对比记录
        
        Args:
            comparison_id: 对比记录ID
            
        Returns:
            对比记录
        """
        return self.get_by_id(comparison_id)
    
    def parse_results(self, comparison: StrategyComparison) -> Dict[str, Any]:
        """
        解析对比结果
        
        Args:
            comparison: 对比记录
            
        Returns:
            解析后的结果字典
        """
        return json.loads(comparison.results)
    
    def parse_symbols(self, comparison: StrategyComparison) -> List[str]:
        """
        解析股票代码列表
        
        Args:
            comparison: 对比记录
            
        Returns:
            股票代码列表
        """
        return json.loads(comparison.symbols)
