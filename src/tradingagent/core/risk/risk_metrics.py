"""
Risk Metrics Module

This module provides implementations of various risk metrics
used in quantitative trading and portfolio analysis.
"""

import pandas as pd
import numpy as np


class RiskMetrics:
    """
    Collection of risk metrics for financial analysis.
    """

    @staticmethod
    def value_at_risk(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calculate Value at Risk (VaR)

        Args:
            returns: Series of returns
            confidence_level: Confidence level (default 5%)

        Returns:
            VaR value
        """
        return np.percentile(returns.dropna(), confidence_level * 100)

    @staticmethod
    def expected_shortfall(returns: pd.Series, confidence_level: float = 0.05) -> float:
        """
        Calculate Expected Shortfall (Conditional VaR)

        Args:
            returns: Series of returns
            confidence_level: Confidence level (default 5%)

        Returns:
            Expected Shortfall value
        """
        var = RiskMetrics.value_at_risk(returns, confidence_level)
        return returns[returns <= var].mean()

    @staticmethod
    def maximum_drawdown(prices: pd.Series) -> dict:
        """
        Calculate Maximum Drawdown

        Args:
            prices: Series of prices or cumulative returns

        Returns:
            dict: {'max_drawdown': float, 'peak': date, 'trough': date}
        """
        cumulative = prices.cumprod() if (prices < 0).any() else prices
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_dd = drawdown.min()
        peak_idx = drawdown.idxmin()

        # Find the peak before the maximum drawdown
        peak_before = running_max.loc[:peak_idx].idxmax()

        return {"max_drawdown": max_dd, "peak": peak_before, "trough": peak_idx}

    @staticmethod
    def sharpe_ratio(
        returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sharpe Ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods per year

        Returns:
            Sharpe ratio
        """
        excess_returns = returns - (risk_free_rate / periods_per_year)
        return (excess_returns.mean() / excess_returns.std()) * np.sqrt(
            periods_per_year
        )

    @staticmethod
    def sortino_ratio(
        returns: pd.Series, risk_free_rate: float = 0.02, periods_per_year: int = 252
    ) -> float:
        """
        Calculate Sortino Ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            periods_per_year: Number of periods per year

        Returns:
            Sortino ratio
        """
        excess_returns = returns - (risk_free_rate / periods_per_year)
        downside_returns = excess_returns[excess_returns < 0]
        downside_std = downside_returns.std()

        if downside_std == 0:
            return np.inf

        return (excess_returns.mean() / downside_std) * np.sqrt(periods_per_year)

    @staticmethod
    def calmar_ratio(returns: pd.Series) -> float:
        """
        Calculate Calmar Ratio

        Args:
            returns: Series of returns

        Returns:
            Calmar ratio
        """
        annual_return = (1 + returns).prod() ** (252 / len(returns)) - 1
        cumulative = (1 + returns).cumprod()
        max_dd = RiskMetrics.maximum_drawdown(cumulative)["max_drawdown"]

        if max_dd == 0:
            return np.inf

        return annual_return / abs(max_dd)

    @staticmethod
    def beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
        """
        Calculate Beta

        Args:
            asset_returns: Series of asset returns
            market_returns: Series of market returns

        Returns:
            Beta value
        """
        covariance = np.cov(asset_returns.dropna(), market_returns.dropna())[0][1]
        market_variance = np.var(market_returns.dropna())

        return covariance / market_variance if market_variance != 0 else 0

    @staticmethod
    def tracking_error(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
        """
        Calculate Tracking Error

        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns

        Returns:
            Tracking error
        """
        return (asset_returns - benchmark_returns).std() * np.sqrt(252)

    @staticmethod
    def information_ratio(
        asset_returns: pd.Series, benchmark_returns: pd.Series
    ) -> float:
        """
        Calculate Information Ratio

        Args:
            asset_returns: Series of asset returns
            benchmark_returns: Series of benchmark returns

        Returns:
            Information ratio
        """
        excess_returns = asset_returns - benchmark_returns
        tracking_err = RiskMetrics.tracking_error(asset_returns, benchmark_returns)

        if tracking_err == 0:
            return np.inf

        return (excess_returns.mean() * 252) / tracking_err
