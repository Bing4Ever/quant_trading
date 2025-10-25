#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""策略参数优化器 - 使用Grid Search寻找最优参数组合"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from itertools import product
from typing import Any, Dict, List

import pandas as pd

from src.tradingagent.modules.strategies import MeanReversionStrategy
from src.tradingservice.services.engines import LiveTradingEngine


class ParameterOptimizer:
    """参数优化器 - 使用Grid Search寻找最优参数"""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.optimization_results = []

    def define_parameter_grid(self) -> Dict[str, List[Any]]:
        """定义参数搜索空间"""
        return {
            "bb_period": [10, 15, 20, 25, 30],           # 布林带周期
            "rsi_period": [7, 10, 14, 21, 28],           # RSI周期
            "rsi_oversold": [20, 25, 30, 35],            # RSI超卖阈值
            "rsi_overbought": [65, 70, 75, 80],          # RSI超买阈值
        }

    def generate_parameter_combinations(self, param_grid: Dict[str, List[Any]]) -> List[Dict[str, Any]]:
        """生成所有参数组合"""
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())

        combinations = []
        for combo in product(*param_values):
            param_dict = dict(zip(param_names, combo))
            # 确保RSI超卖阈值小于超买阈值
            if param_dict["rsi_oversold"] < param_dict["rsi_overbought"]:
                combinations.append(param_dict)

        return combinations

    def run_single_backtest(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """运行单次回测"""
        try:
            # 创建策略
            strategy = MeanReversionStrategy(
                bb_period=params["bb_period"],
                rsi_period=params["rsi_period"],
                rsi_oversold=params["rsi_oversold"],
                rsi_overbought=params["rsi_overbought"],
            )

            # 创建交易引擎
            engine = LiveTradingEngine()
            engine.strategy = strategy

            # 运行回测
            results = engine.run_backtest_analysis(symbol)

            if results:
                return {
                    "params": params,
                    "sharpe_ratio": results.get("sharpe_ratio", 0),
                    "total_return": results.get("total_return", 0),
                    "max_drawdown": results.get("max_drawdown", 0),
                    "win_rate": results.get("win_rate", 0),
                    "total_trades": results.get("total_trades", 0),
                    "volatility": results.get("volatility", 0),
                    "success": True
                }
            return {
                "params": params,
                "sharpe_ratio": -999,
                "success": False
            }

        except Exception as e:
            return {
                "params": params,
                "sharpe_ratio": -999,
                "error": str(e),
                "success": False
            }

    def _execute_parallel_backtests(self, symbol, param_combinations):
        """Execute backtests in parallel and collect results."""
        results = []
        completed = 0
        start_time = time.time()
        total_combinations = len(param_combinations)

        # 使用线程池并行执行回测
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_params = {
                executor.submit(self.run_single_backtest, symbol, params): params
                for params in param_combinations
            }

            # 收集结果
            for future in as_completed(future_to_params):
                result = future.result()
                results.append(result)
                completed += 1

                # 显示进度
                if completed % 10 == 0 or completed == total_combinations:
                    elapsed = time.time() - start_time
                    progress = completed / total_combinations * 100
                    eta = (elapsed / completed * (total_combinations - completed)) if completed > 0 else 0
                    print(f"⏳ 进度: {completed}/{total_combinations} ({progress:.1f}%) - "
                          f"已用时: {elapsed:.1f}s - 预计剩余: {eta:.1f}s")

        return results

    def optimize_parameters(self, symbol: str, custom_param_grid: Dict[str, List[Any]] = None) -> pd.DataFrame:
        """
        执行参数优化

        Args:
            symbol: 股票代码
            custom_param_grid: 自定义参数网格，如果为None则使用默认网格

        Returns:
            优化结果DataFrame，按夏普比率降序排列
        """
        print(f"🔍 开始为 {symbol} 进行参数优化...")

        # 使用自定义网格或默认网格
        param_grid = custom_param_grid if custom_param_grid else self.define_parameter_grid()

        # 生成所有参数组合
        param_combinations = self.generate_parameter_combinations(param_grid)
        total_combinations = len(param_combinations)

        print(f"📊 总共需要测试 {total_combinations} 种参数组合")
        print(f"⚡ 使用 {self.max_workers} 个线程并行处理")

        # 执行并行回测
        results = self._execute_parallel_backtests(symbol, param_combinations)

        # 转换为DataFrame
        df_results = pd.DataFrame(results)

        # 过滤成功的结果并按夏普比率排序
        successful_results = df_results[df_results['success']].copy()

        if successful_results.empty:
            print("❌ 没有成功的回测结果")
            return pd.DataFrame()

        # 按夏普比率降序排序
        successful_results = successful_results.sort_values('sharpe_ratio', ascending=False)

        # 保存结果
        self.optimization_results = successful_results

        print("✅ 参数优化完成！")
        print(f"📈 最佳夏普比率: {successful_results.iloc[0]['sharpe_ratio']:.3f}")
        print(f"🎯 最佳参数组合: {successful_results.iloc[0]['params']}")

        return successful_results

    def get_top_n_results(self, n: int = 10) -> pd.DataFrame:
        """获取前N个最佳结果"""
        if not hasattr(self, 'optimization_results') or self.optimization_results.empty:
            return pd.DataFrame()

        return self.optimization_results.head(n)

    def get_best_parameters(self) -> Dict[str, Any]:
        """获取最佳参数组合"""
        if not hasattr(self, 'optimization_results') or self.optimization_results.empty:
            return {}

        return self.optimization_results.iloc[0]['params']

    def save_optimization_results(self, symbol: str) -> bool:
        """保存优化结果到数据库"""
        if not hasattr(self, 'optimization_results') or self.optimization_results.empty:
            return False

        try:
            # Import here to avoid circular imports
            # pylint: disable=import-outside-toplevel
            from src.tradingservice import get_backtest_repository

            repo = get_backtest_repository()
            saved_count = 0

            # 保存前10个最佳结果
            top_results = self.optimization_results.head(10)

            for _, row in top_results.iterrows():
                params = row['params']

                # 准备结果数据
                results = {
                    'total_return': row['total_return'],
                    'sharpe_ratio': row['sharpe_ratio'],
                    'max_drawdown': row['max_drawdown'],
                    'win_rate': row['win_rate'],
                    'total_trades': row['total_trades'],
                    'volatility': row['volatility']
                }

                # 准备回测配置
                backtest_config = {
                    'start_date': None,
                    'end_date': None,
                    'initial_capital': 100000,
                    'commission': 0.001,
                    'slippage': 0.0005,
                    'data_source': 'yfinance',
                    'backtest_mode': 'optimization',
                    'optimization_used': True,
                    'optimization_method': 'GridSearch',
                    'parameter_space_size': len(self.optimization_results),
                    'optimization_target': 'sharpe_ratio',
                    'optimization_rank': saved_count + 1
                }

                # 保存到数据库
                from src.tradingservice.dataaccess.models import BacktestResult
                
                backtest_record = BacktestResult(
                    symbol=symbol,
                    strategy_name="MeanReversionStrategy",
                    strategy_params=params,
                    total_return=results['total_return'],
                    sharpe_ratio=results['sharpe_ratio'],
                    max_drawdown=results['max_drawdown'],
                    win_rate=results['win_rate'],
                    total_trades=results['total_trades'],
                    volatility=results['volatility'],
                    backtest_config=backtest_config,
                    notes=f"参数优化结果 #{saved_count + 1} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                backtest_id = repo.add(backtest_record)

                if backtest_id:
                    saved_count += 1

            print(f"✅ 已保存 {saved_count} 个优化结果到数据库")
            return saved_count > 0

        except Exception as e:
            print(f"❌ 保存优化结果失败: {e}")
            return False

    def export_results(self, filename: str = None) -> str:
        """导出优化结果到CSV文件"""
        if not hasattr(self, 'optimization_results') or self.optimization_results.empty:
            return ""

        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"parameter_optimization_{timestamp}.csv"

        # 准备导出数据
        export_data = []
        for _, row in self.optimization_results.iterrows():
            params = row['params']
            export_row = {
                'bb_period': params['bb_period'],
                'rsi_period': params['rsi_period'],
                'rsi_oversold': params['rsi_oversold'],
                'rsi_overbought': params['rsi_overbought'],
                'sharpe_ratio': row['sharpe_ratio'],
                'total_return': row['total_return'],
                'max_drawdown': row['max_drawdown'],
                'win_rate': row['win_rate'],
                'total_trades': row['total_trades'],
                'volatility': row['volatility']
            }
            export_data.append(export_row)

        df_export = pd.DataFrame(export_data)
        df_export.to_csv(filename, index=False, encoding='utf-8-sig')

        print(f"📁 优化结果已导出到: {filename}")
        return filename

    def analyze_parameter_sensitivity(self) -> Dict[str, pd.DataFrame]:
        """分析参数敏感性"""
        if not hasattr(self, 'optimization_results') or self.optimization_results.empty:
            return {}

        sensitivity_analysis = {}

        # 为每个参数分析其对夏普比率的影响
        param_names = ['bb_period', 'rsi_period', 'rsi_oversold', 'rsi_overbought']

        for param_name in param_names:
            param_values = []
            sharpe_values = []

            for _, row in self.optimization_results.iterrows():
                param_values.append(row['params'][param_name])
                sharpe_values.append(row['sharpe_ratio'])

            df_sensitivity = pd.DataFrame({
                param_name: param_values,
                'sharpe_ratio': sharpe_values
            })

            # 按参数值分组，计算平均夏普比率
            sensitivity_summary = df_sensitivity.groupby(param_name)['sharpe_ratio'].agg([
                'mean', 'std', 'count', 'min', 'max'
            ]).round(3)

            sensitivity_analysis[param_name] = sensitivity_summary

        return sensitivity_analysis

    def quick_optimize(self, symbol: str) -> Dict[str, Any]:
        """快速优化 - 使用较小的参数空间"""
        quick_grid = {
            "bb_period": [15, 20, 25],
            "rsi_period": [10, 14, 21],
            "rsi_oversold": [25, 30, 35],
            "rsi_overbought": [65, 70, 75],
        }

        print("⚡ 执行快速参数优化...")
        results = self.optimize_parameters(symbol, quick_grid)

        if not results.empty:
            return self.get_best_parameters()
        return {}


class OptimizationResultsAnalyzer:
    """优化结果分析器"""

    @staticmethod
    def create_results_summary(results_df: pd.DataFrame) -> Dict[str, Any]:
        """创建结果摘要"""
        if results_df.empty:
            return {}

        return {
            "total_combinations": len(results_df),
            "best_sharpe": results_df.iloc[0]['sharpe_ratio'],
            "worst_sharpe": results_df.iloc[-1]['sharpe_ratio'],
            "avg_sharpe": results_df['sharpe_ratio'].mean(),
            "std_sharpe": results_df['sharpe_ratio'].std(),
            "best_params": results_df.iloc[0]['params'],
            "positive_sharpe_count": len(results_df[results_df['sharpe_ratio'] > 0]),
            "sharpe_above_1_count": len(results_df[results_df['sharpe_ratio'] > 1.0])
        }

    @staticmethod
    def find_robust_parameters(results_df: pd.DataFrame, top_n: int = 10) -> Dict[str, Any]:
        """寻找稳健的参数组合（在前N名中出现频率高的参数值）"""
        if results_df.empty or len(results_df) < top_n:
            return {}

        top_results = results_df.head(top_n)

        robust_analysis = {}
        param_names = ['bb_period', 'rsi_period', 'rsi_oversold', 'rsi_overbought']

        for param_name in param_names:
            param_values = [row['params'][param_name] for _, row in top_results.iterrows()]
            value_counts = pd.Series(param_values).value_counts()
            robust_analysis[param_name] = {
                'most_common': value_counts.index[0],
                'frequency': value_counts.iloc[0],
                'all_counts': value_counts.to_dict()
            }

        return robust_analysis
