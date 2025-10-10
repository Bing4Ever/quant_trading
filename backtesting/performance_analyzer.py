"""
Performance Analyzer for Backtesting Results

This module provides tools for analyzing trading strategy performance,
calculating key metrics and generating performance reports.

Classes:
    PerformanceAnalyzer: Main class for performance analysis and reporting
"""

from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

class PerformanceAnalyzer:
    """
    Analyze and visualize trading strategy performance.

    This class provides comprehensive performance analysis including:
    - Risk-adjusted returns
    - Drawdown analysis
    - Sharpe ratio and other key metrics
    - Visualization tools
    """

    def __init__(
        self, returns: pd.Series, benchmark_returns: Optional[pd.Series] = None
    ):
        """
        Initialize Performance Analyzer.

        Args:
            returns: Series of strategy returns
            benchmark_returns: Optional benchmark returns for comparison
        """
        self.returns = returns
        self.benchmark_returns = benchmark_returns
        self.risk_free_rate = 0.02  # Default 2% annual risk-free rate

    def calculate_metrics(self) -> Dict[str, float]:
        """
        Calculate comprehensive performance metrics.

        Returns:
            Dictionary containing various performance metrics
        """
        if len(self.returns) == 0:
            return {}

        metrics = {}

        # Basic return metrics
        metrics["total_return"] = (1 + self.returns).prod() - 1
        metrics["annualized_return"] = self._annualized_return()
        metrics["volatility"] = self._annualized_volatility()

        # Risk-adjusted metrics
        metrics["sharpe_ratio"] = self._sharpe_ratio()
        metrics["sortino_ratio"] = self._sortino_ratio()

        # Drawdown metrics
        drawdown_series = self._calculate_drawdown()
        metrics["max_drawdown"] = drawdown_series.min()
        metrics["avg_drawdown"] = drawdown_series[drawdown_series < 0].mean()

        # Win/Loss metrics
        positive_returns = self.returns[self.returns > 0]
        negative_returns = self.returns[self.returns < 0]

        metrics["win_rate"] = (
            len(positive_returns) / len(self.returns) if len(self.returns) > 0 else 0
        )
        metrics["avg_win"] = positive_returns.mean() if len(positive_returns) > 0 else 0
        metrics["avg_loss"] = (
            negative_returns.mean() if len(negative_returns) > 0 else 0
        )
        metrics["profit_factor"] = (
            abs(positive_returns.sum() / negative_returns.sum())
            if negative_returns.sum() != 0
            else float("inf")
        )

        # Additional metrics
        metrics["calmar_ratio"] = (
            metrics["annualized_return"] / abs(metrics["max_drawdown"])
            if metrics["max_drawdown"] != 0
            else float("inf")
        )
        metrics["skewness"] = self.returns.skew()
        metrics["kurtosis"] = self.returns.kurtosis()

        return metrics

    def _annualized_return(self) -> float:
        """Calculate annualized return."""
        if len(self.returns) == 0:
            return 0.0
        total_return = (1 + self.returns).prod() - 1
        periods_per_year = 252  # Trading days
        years = len(self.returns) / periods_per_year
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0.0

    def _annualized_volatility(self) -> float:
        """Calculate annualized volatility."""
        if len(self.returns) == 0:
            return 0.0
        return self.returns.std() * np.sqrt(252)

    def _sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio."""
        excess_return = self._annualized_return() - self.risk_free_rate
        volatility = self._annualized_volatility()
        return excess_return / volatility if volatility != 0 else 0.0

    def _sortino_ratio(self) -> float:
        """Calculate Sortino ratio."""
        excess_return = self._annualized_return() - self.risk_free_rate
        downside_returns = self.returns[self.returns < 0]
        downside_vol = (
            downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        )
        return excess_return / downside_vol if downside_vol != 0 else 0.0

    def _calculate_drawdown(self) -> pd.Series:
        """Calculate drawdown series."""
        if len(self.returns) == 0:
            return pd.Series()
        cumulative = (1 + self.returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown

    def plot_performance(self, figsize: Tuple[int, int] = (15, 10)) -> None:
        """
        Create comprehensive performance plots.

        Args:
            figsize: Figure size for the plots
        """
        if len(self.returns) == 0:
            print("No data to plot")
            return

        _, axes = plt.subplots(2, 2, figsize=figsize)

        # Cumulative returns
        cumulative = (1 + self.returns).cumprod()
        axes[0, 0].plot(
            cumulative.index, cumulative.values, label="Strategy", linewidth=2
        )
        if self.benchmark_returns is not None:
            benchmark_cumulative = (1 + self.benchmark_returns).cumprod()
            axes[0, 0].plot(
                benchmark_cumulative.index,
                benchmark_cumulative.values,
                label="Benchmark",
                linewidth=2,
                alpha=0.7,
            )
        axes[0, 0].set_title("Cumulative Returns")
        axes[0, 0].set_ylabel("Cumulative Return")
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)

        # Drawdown
        drawdown = self._calculate_drawdown()
        axes[0, 1].fill_between(
            drawdown.index, drawdown.values, 0, alpha=0.7, color="red"
        )
        axes[0, 1].set_title("Drawdown")
        axes[0, 1].set_ylabel("Drawdown")
        axes[0, 1].grid(True, alpha=0.3)

        # Monthly returns heatmap
        if len(self.returns) > 30:  # Only if we have enough data
            monthly_returns = self.returns.groupby(
                [self.returns.index.year, self.returns.index.month]
            ).sum()
            monthly_table = monthly_returns.unstack(level=1)
            if not monthly_table.empty:
                sns.heatmap(
                    monthly_table,
                    annot=True,
                    fmt=".2%",
                    center=0,
                    cmap="RdYlGn",
                    ax=axes[1, 0],
                )
                axes[1, 0].set_title("Monthly Returns Heatmap")
            else:
                axes[1, 0].text(
                    0.5,
                    0.5,
                    "Insufficient data for heatmap",
                    ha="center",
                    va="center",
                    transform=axes[1, 0].transAxes,
                )
        else:
            axes[1, 0].text(
                0.5,
                0.5,
                "Insufficient data for heatmap",
                ha="center",
                va="center",
                transform=axes[1, 0].transAxes,
            )

        # Return distribution
        axes[1, 1].hist(self.returns, bins=50, alpha=0.7, density=True)
        axes[1, 1].axvline(
            self.returns.mean(),
            color="red",
            linestyle="--",
            label=f"Mean: {self.returns.mean():.4f}",
        )
        axes[1, 1].set_title("Return Distribution")
        axes[1, 1].set_xlabel("Daily Returns")
        axes[1, 1].set_ylabel("Density")
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def generate_report(self) -> str:
        """
        Generate a comprehensive text report.

        Returns:
            Formatted string report
        """
        metrics = self.calculate_metrics()

        report = """
=== PERFORMANCE ANALYSIS REPORT ===

RETURN METRICS:
Total Return:           {total_return:.2%}
Annualized Return:      {annualized_return:.2%}
Volatility:             {volatility:.2%}

RISK-ADJUSTED METRICS:
Sharpe Ratio:           {sharpe_ratio:.4f}
Sortino Ratio:          {sortino_ratio:.4f}
Calmar Ratio:           {calmar_ratio:.4f}

DRAWDOWN ANALYSIS:
Maximum Drawdown:       {max_drawdown:.2%}
Average Drawdown:       {avg_drawdown:.2%}

WIN/LOSS ANALYSIS:
Win Rate:               {win_rate:.2%}
Average Win:            {avg_win:.4f}
Average Loss:           {avg_loss:.4f}
Profit Factor:          {profit_factor:.2f}

DISTRIBUTION METRICS:
Skewness:               {skewness:.4f}
Kurtosis:               {kurtosis:.4f}

=== END REPORT ===
        """.format(
            **metrics
        )

        return report

    def save_report(self, filename: str) -> None:
        """
        Save performance report to file.

        Args:
            filename: Output filename
        """
        report = self.generate_report()
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {filename}")
