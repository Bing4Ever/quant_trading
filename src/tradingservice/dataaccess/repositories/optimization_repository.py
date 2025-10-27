"""
Optimization Repository - 参数优化仓储

提供参数优化记录的数据访问操作
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from src.common.dataaccess import BaseRepository
from ..models.optimization_record import OptimizationRecord

logger = logging.getLogger(__name__)


class OptimizationRepository(BaseRepository[OptimizationRecord]):
    """参数优化仓储"""

    def __init__(self, session: Session):
        super().__init__(OptimizationRecord, session)

    def save_optimization(
        self,
        symbol: str,
        parameter_name: str,
        parameter_value: str,
        performance_metric: float,
        metric_type: str,
    ) -> int:
        """保存优化记录"""
        try:
            record = OptimizationRecord(
                symbol=symbol,
                parameter_name=parameter_name,
                parameter_value=parameter_value,
                performance_metric=performance_metric,
                metric_type=metric_type,
            )
            record = self.add(record)
            return record.id
        except Exception as e:
            logger.error(f"保存优化记录失败: {str(e)}")
            self.rollback()
            raise

    def get_history(
        self, symbol: str, parameter_name: Optional[str] = None
    ) -> List[OptimizationRecord]:
        """获取优化历史"""
        query = self.session.query(OptimizationRecord).filter(
            OptimizationRecord.symbol == symbol
        )

        if parameter_name:
            query = query.filter(OptimizationRecord.parameter_name == parameter_name)

        return query.order_by(OptimizationRecord.created_at.desc()).all()
