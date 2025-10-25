"""
Favorite Repository - 收藏股票仓储

提供收藏股票的数据访问操作
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from src.common.dataaccess import BaseRepository
from ..models.favorite_stock import FavoriteStock

logger = logging.getLogger(__name__)


class FavoriteRepository(BaseRepository[FavoriteStock]):
    """收藏股票仓储"""
    
    def __init__(self, session: Session):
        super().__init__(FavoriteStock, session)
    
    def add_favorite(
        self,
        symbol: str,
        name: Optional[str] = None,
        sector: Optional[str] = None,
        notes: Optional[str] = None
    ) -> int:
        """添加收藏股票"""
        try:
            # 检查是否已存在
            existing = self.find_one_by(symbol=symbol)
            if existing:
                logger.warning(f"股票 {symbol} 已在收藏列表中")
                return existing.id
            
            favorite = FavoriteStock(
                symbol=symbol,
                name=name,
                sector=sector,
                notes=notes
            )
            favorite = self.add(favorite)
            logger.info(f"已添加收藏股票: {symbol}")
            return favorite.id
        except Exception as e:
            logger.error(f"添加收藏股票失败: {str(e)}")
            self.rollback()
            raise
    
    def remove_favorite(self, symbol: str) -> bool:
        """移除收藏股票"""
        try:
            favorite = self.find_one_by(symbol=symbol)
            if favorite:
                self.delete(favorite)
                logger.info(f"已移除收藏股票: {symbol}")
                return True
            return False
        except Exception as e:
            logger.error(f"移除收藏股票失败: {str(e)}")
            self.rollback()
            raise
    
    def is_favorite(self, symbol: str) -> bool:
        """检查是否已收藏"""
        return self.exists(symbol=symbol)
    
    def get_all_favorites(self) -> List[FavoriteStock]:
        """获取所有收藏股票"""
        return self.get_all()
