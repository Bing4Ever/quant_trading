"""
Data manager for storing and retrieving market data.

重构版本：使用 ORM 和 Repository 模式替代直接的 SQLite 操作
"""

from pathlib import Path
from typing import List, Dict
from datetime import datetime
import logging
import pandas as pd
from config import config
from .data_fetcher import DataFetcher

logger = logging.getLogger(__name__)


class DataManager:
    """
    市场数据管理器 - 负责缓存和检索市场数据

    使用 Repository 模式访问数据库，提供统一的数据管理接口。
    """

    def __init__(self, data_dir: str = None, db_path: str = None):
        """
        初始化数据管理器

        Args:
            data_dir: 数据文件目录（已废弃，保留用于兼容性）
            db_path: 数据库文件路径（可选，默认使用配置）
        """
        # 数据获取器
        self.data_fetcher = DataFetcher()

        # 数据库路径（从配置或参数获取）
        if db_path is None:
            # 从配置读取，移除 sqlite:/// 前缀
            db_url = config.get(
                "market_data.database_url", "sqlite:///data/market_data.db"
            )
            if db_url.startswith("sqlite:///"):
                db_path = db_url.replace("sqlite:///", "")
            else:
                db_path = "data/market_data.db"

        self.db_path = Path(db_path)

        # 初始化 Repository（延迟加载，每次使用时获取新的 session）
        self._repository = None

        logger.info(f"数据管理器已初始化: db={self.db_path}")

    def _get_repository(self):
        """
        获取 MarketDataRepository 实例

        每次调用都返回新的 repository（带新的 session），避免 session 冲突。

        Returns:
            MarketDataRepository 实例
        """
        from src.tradingagent.dataaccess import get_engine

        engine = get_engine(str(self.db_path))
        session = engine.get_session()

        from src.tradingagent.dataaccess.repositories import MarketDataRepository

        return MarketDataRepository(session)

    def get_stock_data(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        force_update: bool = False,
    ) -> pd.DataFrame:
        """
        获取股票数据，自动处理缓存和更新

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            force_update: 强制从外部更新数据

        Returns:
            DataFrame 包含 OHLCV 数据
        """
        try:
            repository = self._get_repository()

            # 检查是否需要更新数据
            if force_update or repository.needs_update(symbol, end_date):
                self._update_stock_data(symbol, start_date, end_date, repository)

            # 从缓存获取数据
            data = repository.get_stock_data(symbol, start_date, end_date)

            # 关闭 session
            repository.session.close()

            return data

        except Exception as e:
            logger.error(f"获取股票数据失败 {symbol}: {e}")
            return pd.DataFrame()

    def _update_stock_data(
        self,
        symbol: str,
        start_date: datetime = None,
        end_date: datetime = None,
        repository=None,
    ):
        """
        从外部数据源更新股票数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            repository: MarketDataRepository 实例（可选）
        """
        try:
            # 从外部获取数据
            data = self.data_fetcher.fetch_stock_data(symbol, start_date, end_date)

            if data is None or data.empty:
                logger.warning(f"未获取到股票数据: {symbol}")
                return

            # 获取或创建 repository
            if repository is None:
                repository = self._get_repository()
                should_close = True
            else:
                should_close = False

            # 保存到数据库
            repository.save_stock_data(symbol, data)

            # 更新时间戳
            repository.update_timestamp(symbol)

            # 关闭 session（如果是新创建的）
            if should_close:
                repository.session.close()

            logger.info(f"已更新股票数据: {symbol}, 记录数: {len(data)}")

        except Exception as e:
            logger.error(f"更新股票数据失败 {symbol}: {e}")
            import traceback

            traceback.print_exc()

    def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: datetime = None,
        end_date: datetime = None,
        force_update: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个股票的数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            force_update: 强制更新

        Returns:
            字典，key 为股票代码，value 为 DataFrame
        """
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_data(
                symbol, start_date, end_date, force_update
            )
        return results

    def create_price_matrix(
        self,
        symbols: List[str],
        column: str = "Close",
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> pd.DataFrame:
        """
        创建价格矩阵（多股票对比）

        Args:
            symbols: 股票代码列表
            column: 价格列名 ('Open', 'High', 'Low', 'Close')
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            DataFrame，index 为日期，columns 为股票代码
        """
        data_dict = self.get_multiple_stocks(symbols, start_date, end_date)

        price_data = {}
        for symbol, data in data_dict.items():
            if not data.empty and column in data.columns:
                price_data[symbol] = data[column]

        if not price_data:
            return pd.DataFrame()

        return pd.DataFrame(price_data)

    def get_cached_symbols(self) -> List[str]:
        """
        获取所有已缓存的股票代码

        Returns:
            股票代码列表
        """
        try:
            repository = self._get_repository()
            symbols = repository.get_cached_symbols()
            repository.session.close()
            return symbols
        except Exception as e:
            logger.error(f"获取缓存股票列表失败: {e}")
            return []

    def clear_old_data(self, symbol: str = None, days: int = 365):
        """
        清理旧数据（保留最近 N 天）

        Args:
            symbol: 股票代码（None 表示清理所有）
            days: 保留天数
        """
        try:
            repository = self._get_repository()

            if symbol:
                repository.delete_old_data(symbol, days)
                logger.info(f"已清理旧数据: {symbol}, 保留 {days} 天")
            else:
                # 清理所有股票的旧数据
                symbols = repository.get_cached_symbols()
                for sym in symbols:
                    repository.delete_old_data(sym, days)
                logger.info(f"已清理所有股票旧数据, 保留 {days} 天")

            repository.session.close()

        except Exception as e:
            logger.error(f"清理旧数据失败: {e}")
