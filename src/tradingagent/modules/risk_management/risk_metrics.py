"""
风险指标计算模块 — 量化交易系统用

本模块提供全面的风险指标计算与分析功能，包括：
- 基础风险指标：波动率（Volatility）、风险价值（VaR）、条件风险价值（CVaR）
- 风险调整收益：夏普比率（Sharpe）、索提诺比率（Sortino）、信息比率（Information Ratio）
- 投资组合风险分析：贝塔（Beta）、跟踪误差（Tracking Error）、相关性矩阵
- 高级风险度量：最大回撤、风险分解（风险贡献）、压力测试场景分析

适用场景：组合风险评估、风险报告生成、产品风险分析与合规模块

说明：本模块专注于风险度量与分析，函数接受 pandas 序列 / 矩阵作为输入并返回
数值或字典结果，便于在监控、报表或回测中调用。
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy import stats


class RiskMetrics:
    """风险指标计算器"""

    def __init__(self) -> None:
        """初始化风险指标计算器"""
        self.logger = logging.getLogger('RiskMetrics')

    def calculate_volatility(self, returns: pd.Series,
                           window: Optional[int] = None) -> float:
        """
        计算波动率

        Args:
            returns: 收益率序列
            window: 滚动窗口期，None表示全样本

        Returns:
            年化波动率
        """
        if len(returns) == 0:
            return 0.0

        if window:
            vol = returns.rolling(window=window).std().iloc[-1]
        else:
            vol = returns.std()

        # 年化（假设252个交易日）
        return vol * np.sqrt(252)

    def calculate_var(self, returns: pd.Series, confidence_level: float = 0.05,
                     method: str = 'historical') -> float:
        """
        计算风险价值 (VaR)

        Args:
            returns: 收益率序列
            confidence_level: 置信水平 (例如0.05表示95%置信度)
            method: 计算方法 ('historical', 'parametric')

        Returns:
            VaR值
        """
        if len(returns) == 0:
            return 0.0

        if method == 'historical':
            return np.percentile(returns.dropna(), confidence_level * 100)

        if method == 'parametric':
            mean = returns.mean()
            std = returns.std()
            return stats.norm.ppf(confidence_level, mean, std)

        raise ValueError(f"不支持的VaR计算方法: {method}")

    def calculate_cvar(self, returns: pd.Series,
                      confidence_level: float = 0.05) -> float:
        """
        计算条件风险价值 (CVaR/Expected Shortfall)

        Args:
            returns: 收益率序列
            confidence_level: 置信水平

        Returns:
            CVaR值
        """
        if len(returns) == 0:
            return 0.0

        var = self.calculate_var(returns, confidence_level)
        return returns[returns <= var].mean()

    def calculate_sharpe_ratio(self, returns: pd.Series,
                              risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）

        Returns:
            夏普比率
        """
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252  # 日无风险利率
        if excess_returns.std() == 0:
            return 0.0

        return (excess_returns.mean() * 252) / (returns.std() * np.sqrt(252))

    def calculate_sortino_ratio(self, returns: pd.Series,
                               risk_free_rate: float = 0.02) -> float:
        """
        计算索提诺比率

        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）

        Returns:
            索提诺比率
        """
        if len(returns) == 0:
            return 0.0

        excess_returns = returns - risk_free_rate / 252
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0:
            return float('inf')

        downside_deviation = downside_returns.std() * np.sqrt(252)
        if downside_deviation == 0:
            return 0.0

        return (excess_returns.mean() * 252) / downside_deviation

    def calculate_max_drawdown(self, prices: pd.Series) -> Dict[str, float]:
        """
        计算最大回撤

        Args:
            prices: 价格序列

        Returns:
            包含最大回撤信息的字典
        """
        if len(prices) == 0:
            return {'max_drawdown': 0.0, 'start_date': None, 'end_date': None}

        # 计算累计最高价
        peak = prices.expanding().max()

        # 计算回撤
        drawdown = (prices - peak) / peak

        # 找到最大回撤
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()

        # 找到最大回撤的开始时间（峰值时间）
        start_idx = peak.loc[:max_dd_idx].idxmax()

        return {
            'max_drawdown': abs(max_dd),
            'start_date': start_idx,
            'end_date': max_dd_idx,
            'duration_days': (max_dd_idx - start_idx).days if hasattr(max_dd_idx - start_idx, 'days') else 0
        }

    def calculate_beta(self, asset_returns: pd.Series,
                      market_returns: pd.Series) -> float:
        """
        计算贝塔系数

        Args:
            asset_returns: 资产收益率
            market_returns: 市场收益率

        Returns:
            贝塔系数
        """
        if len(asset_returns) == 0 or len(market_returns) == 0:
            return 1.0

        # 对齐数据
        combined = pd.concat([asset_returns, market_returns], axis=1).dropna()
        if len(combined) < 2:
            return 1.0

        asset_ret = combined.iloc[:, 0]
        market_ret = combined.iloc[:, 1]

        covariance = np.cov(asset_ret, market_ret)[0, 1]
        market_variance = np.var(market_ret)

        if market_variance == 0:
            return 1.0

        return covariance / market_variance

    def calculate_tracking_error(self, portfolio_returns: pd.Series,
                                benchmark_returns: pd.Series) -> float:
        """
        计算跟踪误差

        Args:
            portfolio_returns: 投资组合收益率
            benchmark_returns: 基准收益率

        Returns:
            年化跟踪误差
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # 对齐数据
        combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        if len(combined) < 2:
            return 0.0

        port_ret = combined.iloc[:, 0]
        bench_ret = combined.iloc[:, 1]

        # 计算超额收益
        excess_returns = port_ret - bench_ret

        # 年化跟踪误差
        return excess_returns.std() * np.sqrt(252)

    def calculate_information_ratio(self, portfolio_returns: pd.Series,
                                   benchmark_returns: pd.Series) -> float:
        """
        计算信息比率

        Args:
            portfolio_returns: 投资组合收益率
            benchmark_returns: 基准收益率

        Returns:
            信息比率
        """
        if len(portfolio_returns) == 0 or len(benchmark_returns) == 0:
            return 0.0

        # 对齐数据
        combined = pd.concat([portfolio_returns, benchmark_returns], axis=1).dropna()
        if len(combined) < 2:
            return 0.0

        port_ret = combined.iloc[:, 0]
        bench_ret = combined.iloc[:, 1]

        # 计算超额收益
        excess_returns = port_ret - bench_ret

        if excess_returns.std() == 0:
            return 0.0

        annual_excess = excess_returns.mean() * 252
        tracking_error = excess_returns.std() * np.sqrt(252)

        return annual_excess / tracking_error

    def calculate_correlation_matrix(self, returns_df: pd.DataFrame,
                                   method: str = 'pearson') -> pd.DataFrame:
        """
        计算相关性矩阵

        Args:
            returns_df: 收益率数据框
            method: 相关性计算方法 ('pearson', 'spearman', 'kendall')

        Returns:
            相关性矩阵
        """
        if returns_df.empty:
            return pd.DataFrame()

        return returns_df.corr(method=method)

    def calculate_portfolio_risk_decomposition(self, weights: np.ndarray,
                                             cov_matrix: np.ndarray) -> Dict:
        """
        计算投资组合风险分解

        Args:
            weights: 权重向量
            cov_matrix: 协方差矩阵

        Returns:
            风险分解结果
        """
        if len(weights) == 0 or cov_matrix.size == 0:
            return {}

        # 投资组合方差
        portfolio_var = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_vol = np.sqrt(portfolio_var)

        # 边际风险贡献
        marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol

        # 风险贡献
        risk_contrib = weights * marginal_contrib

        # 风险贡献占比
        risk_contrib_pct = risk_contrib / portfolio_vol

        return {
            'portfolio_volatility': portfolio_vol,
            'marginal_contribution': marginal_contrib,
            'risk_contribution': risk_contrib,
            'risk_contribution_pct': risk_contrib_pct
        }

    def calculate_stress_scenarios(self, returns: pd.Series,
                                  scenarios: Dict[str, float]) -> Dict[str, float]:
        """
        计算压力测试场景

        Args:
            returns: 历史收益率
            scenarios: 压力场景 {'scenario_name': shock_magnitude}

        Returns:
            各场景下的损失
        """
        if len(returns) == 0:
            return {}

        current_value = 1.0  # 假设当前价值为1
        results = {}

        for scenario_name, shock in scenarios.items():
            # 简单的线性冲击模型
            stressed_return = returns.mean() + shock
            stressed_value = current_value * (1 + stressed_return)
            loss = current_value - stressed_value
            results[scenario_name] = loss

        return results

    def generate_risk_report(self, returns: pd.Series, prices: pd.Series,
                           benchmark_returns: Optional[pd.Series] = None,
                           risk_free_rate: float = 0.02) -> Dict:
        """
        生成综合风险报告

        Args:
            returns: 收益率序列
            prices: 价格序列
            benchmark_returns: 基准收益率（可选）
            risk_free_rate: 无风险利率

        Returns:
            综合风险报告
        """
        report = {
            'basic_stats': {
                'total_return': (prices.iloc[-1] / prices.iloc[0] - 1) if len(prices) > 1 else 0,
                'annualized_return': returns.mean() * 252,
                'volatility': self.calculate_volatility(returns),
                'sharpe_ratio': self.calculate_sharpe_ratio(returns, risk_free_rate),
                'sortino_ratio': self.calculate_sortino_ratio(returns, risk_free_rate)
            },
            'risk_measures': {
                'var_95': self.calculate_var(returns, 0.05),
                'var_99': self.calculate_var(returns, 0.01),
                'cvar_95': self.calculate_cvar(returns, 0.05),
                'max_drawdown': self.calculate_max_drawdown(prices)
            }
        }

        # 如果有基准数据，添加相对风险指标
        if benchmark_returns is not None:
            report['relative_risk'] = {
                'beta': self.calculate_beta(returns, benchmark_returns),
                'tracking_error': self.calculate_tracking_error(returns, benchmark_returns),
                'information_ratio': self.calculate_information_ratio(returns, benchmark_returns)
            }

        return report
