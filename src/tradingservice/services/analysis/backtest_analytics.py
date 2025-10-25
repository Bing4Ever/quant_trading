"""
Backtest Analytics - 回测数据分析工具

提供回测结果的深度分析功能，包括参数敏感性分析、性能报告生成等。
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any
from ...dataaccess import get_backtest_repository, get_optimization_repository

logger = logging.getLogger(__name__)


class BacktestAnalytics:
    """
    回测数据分析工具
    
    使用 Repository 层访问数据，提供各种分析功能。
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化分析工具
        
        Args:
            db_path: 数据库路径（可选，用于兼容旧接口）
        """
        # 注意：db_path 参数保留用于兼容性，但实际使用默认配置
        if db_path:
            logger.warning(f"db_path 参数已废弃，将使用默认配置。传入值: {db_path}")
        
        self._backtest_repo = None
        self._optimization_repo = None
    
    def _get_backtest_repository(self):
        """获取回测仓储"""
        if self._backtest_repo is None:
            self._backtest_repo = get_backtest_repository()
        return self._backtest_repo
    
    def _get_optimization_repository(self):
        """获取优化仓储"""
        if self._optimization_repo is None:
            self._optimization_repo = get_optimization_repository()
        return self._optimization_repo
    
    def analyze_parameter_sensitivity(
        self, 
        symbol: str, 
        parameter_name: str
    ) -> Optional[pd.DataFrame]:
        """
        分析参数敏感性
        
        分析某个参数对性能指标的影响，帮助优化参数选择。
        
        Args:
            symbol: 股票代码
            parameter_name: 参数名称
            
        Returns:
            DataFrame 包含统计分析结果，如果无数据则返回 None
            
        Example:
            analytics = BacktestAnalytics()
            df = analytics.analyze_parameter_sensitivity('AAPL', 'bb_period')
            print(df)
        """
        try:
            repo = self._get_optimization_repository()
            
            # 获取优化历史数据
            records = repo.get_parameter_history(symbol, parameter_name)
            
            if not records:
                logger.warning(f"未找到参数优化数据: {symbol}, {parameter_name}")
                return None
            
            # 转换为 DataFrame
            data = []
            for record in records:
                data.append({
                    'parameter_value': record.parameter_value,
                    'performance_metric': record.performance_metric,
                    'metric_type': record.metric_type,
                    'created_at': record.created_at
                })
            
            df = pd.DataFrame(data)
            
            # 按参数值分组分析
            analysis = df.groupby('parameter_value').agg({
                'performance_metric': ['mean', 'std', 'count'],
                'created_at': 'max'
            }).round(4)
            
            # 重命名列
            analysis.columns = ['_'.join(col).strip() for col in analysis.columns.values]
            
            logger.info(f"参数敏感性分析完成: {symbol}, {parameter_name}, 记录数: {len(df)}")
            return analysis
            
        except Exception as e:
            logger.error(f"参数敏感性分析失败: {e}")
            return None
    
    def generate_performance_report(self, symbol: str) -> str:
        """
        生成性能分析报告
        
        生成包含统计指标的文本报告。
        
        Args:
            symbol: 股票代码
            
        Returns:
            格式化的文本报告
            
        Example:
            analytics = BacktestAnalytics()
            report = analytics.generate_performance_report('AAPL')
            print(report)
        """
        try:
            repo = self._get_backtest_repository()
            
            # 获取历史回测数据
            history = repo.get_backtest_history(symbol, limit=100)
            
            if not history:
                return f"📊 {symbol} 性能分析报告\n\n⚠️ 暂无历史数据"
            
            # 转换为 DataFrame
            data = []
            for record in history:
                data.append({
                    'total_return': record.total_return,
                    'sharpe_ratio': record.sharpe_ratio,
                    'max_drawdown': record.max_drawdown,
                    'win_rate': record.win_rate,
                    'total_trades': record.total_trades
                })
            
            df = pd.DataFrame(data)
            
            # 计算统计指标
            performance_stats = {
                'total_tests': len(df),
                'avg_return': df['total_return'].mean() if not df['total_return'].isna().all() else 0,
                'best_return': df['total_return'].max() if not df['total_return'].isna().all() else 0,
                'worst_return': df['total_return'].min() if not df['total_return'].isna().all() else 0,
                'avg_sharpe': df['sharpe_ratio'].mean() if not df['sharpe_ratio'].isna().all() else 0,
                'stability': df['total_return'].std() if not df['total_return'].isna().all() else 0,
                'success_rate': (df['total_return'] > 0).mean() if not df['total_return'].isna().all() else 0
            }
            
            # 生成报告
            report = f"""
📊 {symbol} 性能分析报告

🔢 测试次数: {performance_stats['total_tests']}
📈 平均收益: {performance_stats['avg_return']:.2%}
🏆 最佳收益: {performance_stats['best_return']:.2%}
📉 最差收益: {performance_stats['worst_return']:.2%}
📊 平均夏普: {performance_stats['avg_sharpe']:.3f}
📏 收益稳定性: {performance_stats['stability']:.4f}
✅ 成功率: {performance_stats['success_rate']:.1%}
            """
            
            logger.info(f"性能报告生成完成: {symbol}")
            return report.strip()
            
        except Exception as e:
            logger.error(f"生成性能报告失败: {e}")
            return f"📊 {symbol} 性能分析报告\n\n❌ 生成失败: {str(e)}"
    
    def get_best_strategies(
        self, 
        symbol: str, 
        metric: str = 'sharpe_ratio', 
        top_n: int = 5
    ) -> pd.DataFrame:
        """
        获取最佳策略
        
        根据指定指标返回表现最好的策略。
        
        Args:
            symbol: 股票代码
            metric: 评价指标 ('sharpe_ratio', 'total_return', 'win_rate')
            top_n: 返回前 N 个
            
        Returns:
            DataFrame 包含最佳策略信息
        """
        try:
            repo = self._get_backtest_repository()
            
            # 获取最佳结果
            best_results = repo.get_best_results(symbol, metric=metric, limit=top_n)
            
            if not best_results:
                logger.warning(f"未找到回测结果: {symbol}")
                return pd.DataFrame()
            
            # 转换为 DataFrame
            data = []
            for record in best_results:
                data.append({
                    'id': record.id,
                    'strategy_name': record.strategy_name,
                    'total_return': record.total_return,
                    'sharpe_ratio': record.sharpe_ratio,
                    'max_drawdown': record.max_drawdown,
                    'win_rate': record.win_rate,
                    'total_trades': record.total_trades,
                    'created_at': record.created_at
                })
            
            df = pd.DataFrame(data)
            logger.info(f"获取最佳策略完成: {symbol}, 指标: {metric}, 数量: {len(df)}")
            return df
            
        except Exception as e:
            logger.error(f"获取最佳策略失败: {e}")
            return pd.DataFrame()
    
    def compare_strategies(
        self, 
        symbol: str, 
        strategy_names: list
    ) -> Dict[str, Any]:
        """
        比较多个策略的性能
        
        Args:
            symbol: 股票代码
            strategy_names: 策略名称列表
            
        Returns:
            字典，包含每个策略的统计信息
        """
        try:
            repo = self._get_backtest_repository()
            comparison = {}
            
            for strategy_name in strategy_names:
                results = repo.get_strategy_results(symbol, strategy_name, limit=50)
                
                if results:
                    # 转换为 DataFrame 计算统计
                    data = [{
                        'total_return': r.total_return,
                        'sharpe_ratio': r.sharpe_ratio,
                        'max_drawdown': r.max_drawdown,
                        'win_rate': r.win_rate
                    } for r in results]
                    
                    df = pd.DataFrame(data)
                    
                    comparison[strategy_name] = {
                        'count': len(df),
                        'avg_return': df['total_return'].mean(),
                        'avg_sharpe': df['sharpe_ratio'].mean(),
                        'avg_drawdown': df['max_drawdown'].mean(),
                        'avg_win_rate': df['win_rate'].mean(),
                        'stability': df['total_return'].std()
                    }
            
            logger.info(f"策略比较完成: {symbol}, 策略数: {len(comparison)}")
            return comparison
            
        except Exception as e:
            logger.error(f"策略比较失败: {e}")
            return {}
    
    def __del__(self):
        """清理资源"""
        if self._backtest_repo:
            self._backtest_repo.session.close()
        if self._optimization_repo:
            self._optimization_repo.session.close()
