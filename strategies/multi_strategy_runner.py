"""
多策略运行器
整合多个交易策略，实现并行执行和结果比较
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import concurrent.futures
import logging
from dataclasses import dataclass, field

from .base_strategy import BaseStrategy
from .mean_reversion_strategy import MeanReversionStrategy
from .moving_average_strategy import MovingAverageStrategy


@dataclass
class StrategyResult:
    """策略执行结果"""
    strategy_name: str
    symbol: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int
    avg_trade_return: float
    volatility: float
    calmar_ratio: float
    sortino_ratio: float
    trades: List[Dict] = field(default_factory=list)
    signals: pd.DataFrame = field(default_factory=pd.DataFrame)
    portfolio_value: pd.Series = field(default_factory=pd.Series)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MultiStrategyRunner:
    """多策略运行器"""
    
    def __init__(self):
        self.strategies = self._initialize_strategies()
        self.results: Dict[str, StrategyResult] = {}
        self.logger = logging.getLogger(__name__)
        
    def _initialize_strategies(self) -> Dict[str, BaseStrategy]:
        """初始化默认策略"""
        strategies = {}
        
        try:
            # 移动平均策略
            strategies["移动平均"] = MovingAverageStrategy(
                short_window=10,
                long_window=30
            )
            
            # 均值回归策略
            strategies["均值回归"] = MeanReversionStrategy(
                bb_period=20,
                bb_std=2.0,
                rsi_period=14,
                rsi_oversold=30,
                rsi_overbought=70
            )
            
            # RSI策略 (如果存在)
            try:
                from .rsi_strategy import RSIStrategy
                strategies["RSI"] = RSIStrategy(
                    period=14,
                    oversold=30,
                    overbought=70
                )
            except ImportError:
                self.logger.info("RSI策略模块未找到，跳过")
            
            # 布林带策略 (如果存在)
            try:
                from .bollinger_bands import BollingerBandsStrategy
                strategies["布林带"] = BollingerBandsStrategy(
                    period=20,
                    std_dev=2.0
                )
            except ImportError:
                self.logger.info("布林带策略模块未找到，跳过")
                
        except Exception as e:
            self.logger.error(f"策略初始化失败: {e}")
            
        return strategies
    
    def add_strategy(self, name: str, strategy: BaseStrategy):
        """添加自定义策略"""
        self.strategies[name] = strategy
        self.logger.info(f"添加策略: {name}")
    
    def remove_strategy(self, name: str):
        """移除策略"""
        if name in self.strategies:
            del self.strategies[name]
            self.logger.info(f"移除策略: {name}")
    
    def get_market_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """获取市场数据"""
        try:
            # 下载数据
            data = yf.download(symbol, period=period, interval=interval)
            
            if data.empty:
                raise ValueError(f"无法获取 {symbol} 的数据")
            
            # 标准化列名 (处理yfinance大小写问题)
            if hasattr(data.columns, 'levels'):
                # 多级索引情况
                data.columns = data.columns.get_level_values(0)
            
            # 确保列名为标准格式 (小写，适配BaseStrategy)
            standard_columns = {
                'Open': 'open',
                'High': 'high', 
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Adj Close': 'adj_close'
            }
            
            # 重命名为小写列名
            data = data.rename(columns=standard_columns)
            
            # 确保必要的列存在
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in data.columns]
            
            if missing_columns:
                raise ValueError(f"数据缺少必要列: {missing_columns}")
            
            # 移除缺失值
            data = data.dropna()
            
            if len(data) < 20:  # 降低最小数据点要求
                raise ValueError(f"数据点太少: {len(data)} < 20")
                
            return data
            
        except Exception as e:
            self.logger.error(f"获取市场数据失败 {symbol}: {e}")
            raise
    
    def run_single_strategy(self, strategy_name: str, strategy: BaseStrategy, 
                           symbol: str, data: pd.DataFrame) -> StrategyResult:
        """运行单个策略"""
        try:
            self.logger.info(f"运行策略: {strategy_name} on {symbol}")
            
            # 验证数据
            if not strategy.validate_data(data):
                raise ValueError(f"数据验证失败: {strategy_name}")
            
            # 生成信号
            signals = strategy.generate_signals(data)
            
            if signals.empty:
                raise ValueError(f"未生成有效信号: {strategy_name}")
            
            # 运行回测
            backtest_results = strategy.backtest(data)
            
            # 从结果中提取数据
            portfolio_value = pd.Series(backtest_results.get('portfolio_values', []))
            trades = []  # BaseStrategy当前不返回交易详情
            
            # 如果策略有自定义的backtest方法，尝试使用
            if hasattr(strategy, 'backtest') and callable(getattr(strategy, 'backtest')):
                try:
                    # 检查方法签名
                    import inspect
                    sig = inspect.signature(strategy.backtest)
                    params = list(sig.parameters.keys())
                    
                    if 'signals' in params:
                        # 有signals参数的新式backtest
                        portfolio_value, trades = strategy.backtest(data, signals)
                except:
                    # 使用标准回测结果
                    pass
            
            # 计算性能指标
            metrics = strategy.calculate_performance_metrics(portfolio_value, trades)
            
            # 创建结果对象
            result = StrategyResult(
                strategy_name=strategy_name,
                symbol=symbol,
                total_return=metrics.get('total_return', 0),
                sharpe_ratio=metrics.get('sharpe_ratio', 0),
                max_drawdown=metrics.get('max_drawdown', 0),
                win_rate=metrics.get('win_rate', 0),
                total_trades=len(trades),
                avg_trade_return=metrics.get('avg_trade_return', 0),
                volatility=metrics.get('volatility', 0),
                calmar_ratio=metrics.get('calmar_ratio', 0),
                sortino_ratio=metrics.get('sortino_ratio', 0),
                trades=trades,
                signals=signals,
                portfolio_value=portfolio_value,
                metadata={
                    'strategy_params': strategy.get_parameters(),
                    'data_period': f"{data.index[0]} to {data.index[-1]}",
                    'data_points': len(data)
                }
            )
            
            self.logger.info(f"策略 {strategy_name} 完成: 收益率={result.total_return:.2%}")
            return result
            
        except Exception as e:
            self.logger.error(f"策略 {strategy_name} 执行失败: {e}")
            # 返回空结果
            return StrategyResult(
                strategy_name=strategy_name,
                symbol=symbol,
                total_return=0,
                sharpe_ratio=0,
                max_drawdown=0,
                win_rate=0,
                total_trades=0,
                avg_trade_return=0,
                volatility=0,
                calmar_ratio=0,
                sortino_ratio=0
            )
    
    def run_all_strategies(self, symbol: str, period: str = "1y", 
                          selected_strategies: List[str] = None) -> Dict[str, StrategyResult]:
        """运行所有策略"""
        try:
            # 获取市场数据
            data = self.get_market_data(symbol, period)
            
            # 确定要运行的策略
            if selected_strategies:
                strategies_to_run = {name: strategy for name, strategy in self.strategies.items() 
                                   if name in selected_strategies}
            else:
                strategies_to_run = self.strategies
            
            if not strategies_to_run:
                raise ValueError("没有可运行的策略")
            
            results = {}
            
            # 并行执行策略
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # 提交所有任务
                future_to_strategy = {
                    executor.submit(
                        self.run_single_strategy, 
                        name, 
                        strategy, 
                        symbol, 
                        data
                    ): name 
                    for name, strategy in strategies_to_run.items()
                }
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_strategy):
                    strategy_name = future_to_strategy[future]
                    try:
                        result = future.result()
                        results[strategy_name] = result
                    except Exception as e:
                        self.logger.error(f"策略 {strategy_name} 执行异常: {e}")
                        # 添加失败的结果
                        results[strategy_name] = StrategyResult(
                            strategy_name=strategy_name,
                            symbol=symbol,
                            total_return=0,
                            sharpe_ratio=0,
                            max_drawdown=0,
                            win_rate=0,
                            total_trades=0,
                            avg_trade_return=0,
                            volatility=0,
                            calmar_ratio=0,
                            sortino_ratio=0
                        )
            
            # 保存结果
            self.results = results
            
            self.logger.info(f"多策略分析完成: {len(results)} 个策略, 股票: {symbol}")
            return results
            
        except Exception as e:
            self.logger.error(f"多策略运行失败: {e}")
            raise
    
    def generate_comparison_report(self) -> pd.DataFrame:
        """生成策略比较报告"""
        if not self.results:
            return pd.DataFrame()
        
        try:
            comparison_data = []
            
            for strategy_name, result in self.results.items():
                comparison_data.append({
                    '策略名称': strategy_name,
                    '总收益率': f"{result.total_return:.2%}",
                    '夏普比率': f"{result.sharpe_ratio:.3f}",
                    '最大回撤': f"{result.max_drawdown:.2%}",
                    '胜率': f"{result.win_rate:.1%}",
                    '交易次数': result.total_trades,
                    '平均交易收益': f"{result.avg_trade_return:.2%}",
                    '波动率': f"{result.volatility:.2%}",
                    '卡尔玛比率': f"{result.calmar_ratio:.3f}",
                    '索提诺比率': f"{result.sortino_ratio:.3f}"
                })
            
            df = pd.DataFrame(comparison_data)
            
            # 按夏普比率排序
            df['_sharpe_float'] = [self.results[name].sharpe_ratio for name in df['策略名称']]
            df = df.sort_values('_sharpe_float', ascending=False)
            df = df.drop('_sharpe_float', axis=1)
            
            return df
            
        except Exception as e:
            self.logger.error(f"生成比较报告失败: {e}")
            return pd.DataFrame()
    
    def get_best_strategy(self) -> Tuple[str, StrategyResult]:
        """获取最佳策略"""
        if not self.results:
            return None, None
        
        # 基于夏普比率选择最佳策略
        best_strategy_name = max(self.results.keys(), 
                               key=lambda x: self.results[x].sharpe_ratio)
        
        return best_strategy_name, self.results[best_strategy_name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.results:
            return {}
        
        # 计算统计信息
        total_returns = [result.total_return for result in self.results.values()]
        sharpe_ratios = [result.sharpe_ratio for result in self.results.values()]
        max_drawdowns = [result.max_drawdown for result in self.results.values()]
        
        return {
            'strategy_count': len(self.results),
            'avg_return': np.mean(total_returns),
            'best_return': max(total_returns),
            'worst_return': min(total_returns),
            'avg_sharpe': np.mean(sharpe_ratios),
            'best_sharpe': max(sharpe_ratios),
            'avg_drawdown': np.mean(max_drawdowns),
            'worst_drawdown': min(max_drawdowns),
            'best_strategy': self.get_best_strategy()[0]
        }
    
    def export_results(self, filename: str = None) -> str:
        """导出结果到文件"""
        if not self.results:
            raise ValueError("没有结果可导出")
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"multi_strategy_results_{timestamp}.xlsx"
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # 比较报告
                comparison_df = self.generate_comparison_report()
                comparison_df.to_excel(writer, sheet_name='策略比较', index=False)
                
                # 每个策略的详细结果
                for strategy_name, result in self.results.items():
                    # 交易记录
                    if result.trades:
                        trades_df = pd.DataFrame(result.trades)
                        trades_df.to_excel(writer, sheet_name=f'{strategy_name}_交易', index=False)
                    
                    # 信号记录
                    if not result.signals.empty:
                        result.signals.to_excel(writer, sheet_name=f'{strategy_name}_信号')
                    
                    # 组合价值
                    if not result.portfolio_value.empty:
                        portfolio_df = pd.DataFrame({
                            'Date': result.portfolio_value.index,
                            'Portfolio_Value': result.portfolio_value.values
                        })
                        portfolio_df.to_excel(writer, sheet_name=f'{strategy_name}_组合价值', index=False)
            
            self.logger.info(f"结果已导出到: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"导出失败: {e}")
            raise
    
    def clear_results(self):
        """清除结果"""
        self.results.clear()
        self.logger.info("结果已清除")


# 工具函数
def create_default_runner() -> MultiStrategyRunner:
    """创建默认的多策略运行器"""
    return MultiStrategyRunner()


def quick_analysis(symbol: str, period: str = "1y") -> Dict[str, StrategyResult]:
    """快速分析函数"""
    runner = create_default_runner()
    return runner.run_all_strategies(symbol, period)