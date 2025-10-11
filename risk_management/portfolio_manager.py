"""投资组合管理器 - 管理整个投资组合的风险和配置"""

from typing import Dict, List, Optional
from datetime import datetime
import logging


class PortfolioManager:
    """投资组合管理器"""
    
    def __init__(self, total_capital: float) -> None:
        """
        初始化投资组合管理器
        
        Args:
            total_capital: 总资金
        """
        self.total_capital = total_capital
        self.positions: Dict[str, Dict] = {}
        self.sector_limits: Dict[str, float] = {}  # 行业配置限制
        self.correlation_matrix: Dict[str, Dict[str, float]] = {}
        
        self.logger = logging.getLogger('PortfolioManager')
        
    def add_position(self, symbol: str, quantity: int, price: float, 
                    sector: Optional[str] = None) -> bool:
        """
        添加持仓
        
        Args:
            symbol: 股票代码
            quantity: 数量
            price: 价格
            sector: 行业分类
            
        Returns:
            是否成功添加
        """
        if not self._check_portfolio_limits(symbol, quantity, price, sector):
            return False
            
        self.positions[symbol] = {
            'quantity': quantity,
            'price': price,
            'sector': sector,
            'timestamp': datetime.now(),
            'market_value': quantity * price
        }
        
        self.logger.info("添加持仓 %s: %d股 @ $%.2f (行业: %s)", 
                        symbol, quantity, price, sector or "未分类")
        return True
        
    def remove_position(self, symbol: str) -> bool:
        """
        移除持仓
        
        Args:
            symbol: 股票代码
            
        Returns:
            是否成功移除
        """
        if symbol in self.positions:
            position = self.positions.pop(symbol)
            self.logger.info("移除持仓 %s: %d股", symbol, position['quantity'])
            return True
        return False
        
    def update_prices(self, prices: Dict[str, float]) -> None:
        """
        更新价格
        
        Args:
            prices: 价格字典 {symbol: price}
        """
        for symbol, price in prices.items():
            if symbol in self.positions:
                self.positions[symbol]['price'] = price
                self.positions[symbol]['market_value'] = (
                    self.positions[symbol]['quantity'] * price
                )
                
    def get_portfolio_value(self) -> float:
        """获取投资组合总价值"""
        return sum(pos['market_value'] for pos in self.positions.values())
        
    def get_cash_position(self) -> float:
        """获取现金头寸"""
        portfolio_value = self.get_portfolio_value()
        return self.total_capital - portfolio_value
        
    def get_sector_allocation(self) -> Dict[str, float]:
        """
        获取行业配置
        
        Returns:
            行业配置字典 {sector: percentage}
        """
        portfolio_value = self.get_portfolio_value()
        if portfolio_value == 0:
            return {}
            
        sector_values: Dict[str, float] = {}
        
        for position in self.positions.values():
            sector = position['sector'] or '未分类'
            if sector not in sector_values:
                sector_values[sector] = 0
            sector_values[sector] += position['market_value']
            
        return {
            sector: value / portfolio_value 
            for sector, value in sector_values.items()
        }
        
    def get_position_weights(self) -> Dict[str, float]:
        """
        获取个股权重
        
        Returns:
            个股权重字典 {symbol: weight}
        """
        portfolio_value = self.get_portfolio_value()
        if portfolio_value == 0:
            return {}
            
        return {
            symbol: pos['market_value'] / portfolio_value
            for symbol, pos in self.positions.items()
        }
        
    def set_sector_limit(self, sector: str, limit: float) -> None:
        """
        设置行业配置限制
        
        Args:
            sector: 行业名称
            limit: 配置限制 (0-1)
        """
        self.sector_limits[sector] = limit
        self.logger.info("设置行业限制 %s: %.1f%%", sector, limit * 100)
        
    def check_diversification(self) -> Dict[str, float]:
        """
        检查分散化程度
        
        Returns:
            分散化指标
        """
        weights = self.get_position_weights()
        
        # 计算赫芬达尔指数 (越小越分散)
        herfindahl_index = sum(w ** 2 for w in weights.values())
        
        # 有效股票数量
        effective_stocks = 1 / herfindahl_index if herfindahl_index > 0 else 0
        
        # 最大权重
        max_weight = max(weights.values()) if weights else 0
        
        return {
            'herfindahl_index': herfindahl_index,
            'effective_stocks': effective_stocks,
            'max_weight': max_weight,
            'position_count': len(self.positions)
        }
        
    def rebalance_suggestions(self, target_weights: Dict[str, float]) -> List[Dict]:
        """
        重新平衡建议
        
        Args:
            target_weights: 目标权重 {symbol: weight}
            
        Returns:
            调整建议列表
        """
        current_weights = self.get_position_weights()
        portfolio_value = self.get_portfolio_value()
        suggestions = []
        
        for symbol, target_weight in target_weights.items():
            current_weight = current_weights.get(symbol, 0)
            weight_diff = target_weight - current_weight
            
            if abs(weight_diff) > 0.01:  # 1%以上的差异
                value_diff = weight_diff * portfolio_value
                
                if symbol in self.positions:
                    current_price = self.positions[symbol]['price']
                    shares_diff = int(value_diff / current_price)
                else:
                    shares_diff = 0
                    current_price = 0
                    
                suggestions.append({
                    'symbol': symbol,
                    'action': 'BUY' if weight_diff > 0 else 'SELL',
                    'shares': abs(shares_diff),
                    'value': abs(value_diff),
                    'current_weight': current_weight,
                    'target_weight': target_weight,
                    'weight_diff': weight_diff
                })
                
        return sorted(suggestions, key=lambda x: abs(x['weight_diff']), reverse=True)
        
    def _check_portfolio_limits(self, symbol: str, quantity: int, price: float, 
                               sector: Optional[str]) -> bool:
        """检查投资组合限制"""
        # 检查单只股票权重限制
        market_value = quantity * price
        current_portfolio_value = self.get_portfolio_value()
        
        # 如果是第一个持仓或者权重检查基于总资金而不是当前投资组合价值
        if current_portfolio_value == 0:
            # 对于第一个持仓，基于总资金检查权重
            weight = market_value / self.total_capital
        else:
            # 对于后续持仓，基于预期的新投资组合价值检查权重
            new_portfolio_value = current_portfolio_value + market_value
            weight = market_value / new_portfolio_value
        
        if weight > 0.3:  # 单只股票不超过30%
            self.logger.warning("单只股票权重过高 %s: %.1f%%", symbol, weight * 100)
            return False
            
        # 检查行业配置限制
        if sector and sector in self.sector_limits:
            # 基于总资金计算行业权重，而不是当前投资组合价值
            sector_allocation = self.get_sector_allocation()
            current_sector_weight = sector_allocation.get(sector, 0)
            current_sector_value = current_sector_weight * current_portfolio_value
            
            # 计算新的行业权重（基于总资金）
            new_sector_value = current_sector_value + market_value
            new_sector_weight = new_sector_value / self.total_capital
            
            if new_sector_weight > self.sector_limits[sector]:
                self.logger.warning("行业配置超限 %s: %.1f%% (限制: %.1f%%)", 
                                  sector, new_sector_weight * 100, 
                                  self.sector_limits[sector] * 100)
                return False
                
        return True
        
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        portfolio_value = self.get_portfolio_value()
        cash_position = self.get_cash_position()
        diversification = self.check_diversification()
        sector_allocation = self.get_sector_allocation()
        
        return {
            'total_capital': self.total_capital,
            'portfolio_value': portfolio_value,
            'cash_position': cash_position,
            'cash_percentage': cash_position / self.total_capital,
            'position_count': len(self.positions),
            'diversification': diversification,
            'sector_allocation': sector_allocation,
            'largest_position': max(
                self.get_position_weights().values()
            ) if self.positions else 0
        }