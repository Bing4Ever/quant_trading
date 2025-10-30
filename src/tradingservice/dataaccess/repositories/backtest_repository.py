"""
 回测结果仓储层。

 封装回测记录的增删查改与常用查询逻辑。
"""

import json
import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from src.common.dataaccess import BaseRepository
from src.tradingservice.dataaccess.models.backtest_result import BacktestResult

logger = logging.getLogger(__name__)


class BacktestRepository(BaseRepository[BacktestResult]):
    """面向回测结果的仓储封装。"""

    def __init__(self, session: Session):
        super().__init__(BacktestResult, session)

    def save_result(
        self,
        symbol: str,
        strategy_name: str,
        strategy_params: Dict,
        results: Dict,
        backtest_config: Optional[Dict] = None,
        notes: str = "",
    ) -> int:
        """
        持久化一条新的回测结果。

        Args:
            symbol: 回测标的。
            strategy_name: 所使用的策略名称。
            strategy_params: 调用时使用的策略参数。
            results: 回测产出的绩效指标。
            backtest_config: 回测配置详情。
            notes: 自定义备注。

        Returns:
            数据库生成的主键 ID。
        """
        try:
            payload = BacktestResult(
                symbol=symbol,
                strategy_name=strategy_name,
                strategy_params=json.dumps(strategy_params, ensure_ascii=False),
                backtest_config=json.dumps(backtest_config or {}, ensure_ascii=False),
                total_return=results.get("total_return", 0.0),
                annualized_return=results.get("annualized_return", 0.0),
                sharpe_ratio=results.get("sharpe_ratio", 0.0),
                max_drawdown=results.get("max_drawdown", 0.0),
                volatility=results.get("volatility", 0.0),
                win_rate=results.get("win_rate", 0.0),
                total_trades=results.get("total_trades", 0),
                avg_trade_return=results.get("avg_trade_return", 0.0),
                notes=notes,
            )

            record = self.add(payload)
            logger.info("Stored backtest result with id=%s", record.id)
            return record.id

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to persist backtest result: %s", exc)
            self.rollback()
            raise

    def get_history(
        self,
        symbol: Optional[str] = None,
        strategy_name: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict]:
        """
        查询历史回测记录。

        Args:
            symbol: 可选的标的过滤条件。
            strategy_name: 可选的策略过滤条件。
            limit: 返回结果数量上限。

        Returns:
            回测记录的序列化列表。
        """
        query = self.session.query(BacktestResult)

        if symbol:
            query = query.filter(BacktestResult.symbol == symbol)

        if strategy_name:
            query = query.filter(BacktestResult.strategy_name == strategy_name)

        results = query.order_by(BacktestResult.created_at.desc()).limit(limit).all()
        return [self._to_dict(result) for result in results]

    def get_best_results(
        self, metric: str = "total_return", limit: int = 10
    ) -> List[Dict]:
        """
        按指定指标获取表现最好的回测结果。

        Args:
            metric: 排序所依据的指标列名。
            limit: 返回结果数量上限。

        Returns:
            按指标倒序排列的回测记录。
        """
        order_column = getattr(BacktestResult, metric, BacktestResult.total_return)

        results = (
            self.session.query(BacktestResult)
            .order_by(order_column.desc())
            .limit(limit)
            .all()
        )
        return [self._to_dict(result) for result in results]

    def get_by_strategy(self, strategy_name: str, limit: int = 50) -> List[Dict]:
        """
        获取指定策略的回测历史。

        Args:
            strategy_name: 目标策略。
            limit: 返回结果数量上限。

        Returns:
            该策略对应的回测记录列表。
        """
        results = (
            self.session.query(BacktestResult)
            .filter(BacktestResult.strategy_name == strategy_name)
            .order_by(BacktestResult.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._to_dict(result) for result in results]

    def _to_dict(self, result: BacktestResult) -> Dict:
        """将 BacktestResult ORM 实例转换为可序列化字典。"""
        return {
            "id": result.id,
            "symbol": result.symbol,
            "strategy_name": result.strategy_name,
            "strategy_params": (
                json.loads(result.strategy_params) if result.strategy_params else {}
            ),
            "backtest_config": (
                json.loads(result.backtest_config) if result.backtest_config else {}
            ),
            "total_return": result.total_return,
            "annualized_return": result.annualized_return,
            "sharpe_ratio": result.sharpe_ratio,
            "max_drawdown": result.max_drawdown,
            "volatility": result.volatility,
            "win_rate": result.win_rate,
            "total_trades": result.total_trades,
            "avg_trade_return": result.avg_trade_return,
            "created_at": (
                result.created_at.isoformat() if result.created_at else None
            ),
            "notes": result.notes,
        }
