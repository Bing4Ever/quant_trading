#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""参数优化结果可视化组件"""

from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns


class OptimizationVisualizer:
    """参数优化结果可视化器"""

    # Constants for chart labels
    TOTAL_RETURN_LABEL = '总收益率 (%)'
    MAX_DRAWDOWN_LABEL = '最大回撤 (%)'

    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
        plt.rcParams['axes.unicode_minus'] = False

        # 设置样式
        plt.style.use('seaborn-v0_8')

    def plot_optimization_heatmap(self, results_df: pd.DataFrame, param_x: str, param_y: str) -> Optional[plt.Figure]:
        """
        绘制参数优化热力图

        Args:
            results_df: 优化结果DataFrame
            param_x: X轴参数名
            param_y: Y轴参数名
        """
        if results_df.empty:
            return None

        try:
            # 提取参数值
            x_values = [row['params'][param_x] for _, row in results_df.iterrows()]
            y_values = [row['params'][param_y] for _, row in results_df.iterrows()]
            sharpe_values = results_df['sharpe_ratio'].values

            # 创建数据透视表
            df_pivot = pd.DataFrame({
                param_x: x_values,
                param_y: y_values,
                'sharpe_ratio': sharpe_values
            })

            # 计算每个参数组合的平均夏普比率
            heatmap_data = df_pivot.groupby([param_x, param_y])['sharpe_ratio'].mean().unstack()

            # 创建热力图
            fig, ax = plt.subplots(figsize=(12, 8))

            sns.heatmap(
                heatmap_data,
                annot=True,
                fmt='.3f',
                cmap='RdYlGn',
                center=0,
                ax=ax,
                cbar_kws={'label': '夏普比率'}
            )

            ax.set_title(f'参数优化热力图: {param_x} vs {param_y}', fontsize=16, pad=20)
            ax.set_xlabel(param_x, fontsize=12)
            ax.set_ylabel(param_y, fontsize=12)

            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 热力图生成失败: {e}")
            return None

    def plot_parameter_sensitivity(self, sensitivity_analysis: Dict[str, pd.DataFrame]) -> Optional[plt.Figure]:
        """绘制参数敏感性分析图"""
        if not sensitivity_analysis:
            return None

        try:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            axes = axes.ravel()

            param_names = list(sensitivity_analysis.keys())
            param_labels = {
                'bb_period': '布林带周期',
                'rsi_period': 'RSI周期',
                'rsi_oversold': 'RSI超卖阈值',
                'rsi_overbought': 'RSI超买阈值'
            }

            for i, param_name in enumerate(param_names):
                if i < 4:
                    df = sensitivity_analysis[param_name]

                    # 绘制条形图
                    chart_bars = axes[i].bar(df.index, df['mean'],
                                     yerr=df['std'],
                                     capsize=5,
                                     alpha=0.7,
                                     color='skyblue',
                                     edgecolor='navy')

                    axes[i].set_title(f'{param_labels.get(param_name, param_name)}敏感性分析',
                                    fontsize=12)
                    axes[i].set_xlabel(param_labels.get(param_name, param_name))
                    axes[i].set_ylabel('平均夏普比率')
                    axes[i].grid(True, alpha=0.3)

                    # 标注数值
                    for chart_bar, mean_val in zip(chart_bars, df['mean']):
                        height = chart_bar.get_height()
                        axes[i].text(chart_bar.get_x() + chart_bar.get_width()/2., height + 0.01,
                                   f'{mean_val:.3f}', ha='center', va='bottom', fontsize=9)

            plt.suptitle('参数敏感性分析', fontsize=16, y=0.98)
            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 敏感性分析图生成失败: {e}")
            return None

    def plot_sharpe_distribution(self, results_df: pd.DataFrame) -> Optional[plt.Figure]:
        """绘制夏普比率分布图"""
        if results_df.empty:
            return None

        try:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

            sharpe_values = results_df['sharpe_ratio'].values

            # 直方图
            ax1.hist(sharpe_values, bins=30, alpha=0.7, color='lightblue', edgecolor='black')
            ax1.axvline(sharpe_values.mean(), color='red', linestyle='--',
                       label=f'平均值: {sharpe_values.mean():.3f}')
            ax1.axvline(np.median(sharpe_values), color='green', linestyle='--',
                       label=f'中位数: {np.median(sharpe_values):.3f}')
            ax1.set_title('夏普比率分布直方图')
            ax1.set_xlabel('夏普比率')
            ax1.set_ylabel('频次')
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 箱线图
            ax2.boxplot(sharpe_values, vert=True)
            ax2.set_title('夏普比率箱线图')
            ax2.set_ylabel('夏普比率')
            ax2.grid(True, alpha=0.3)

            # 添加统计信息
            stats_text = f"""
            总数: {len(sharpe_values)}
            最大值: {sharpe_values.max():.3f}
            最小值: {sharpe_values.min():.3f}
            标准差: {sharpe_values.std():.3f}
            正值比例: {(sharpe_values > 0).sum() / len(sharpe_values) * 100:.1f}%
            >1.0比例: {(sharpe_values > 1.0).sum() / len(sharpe_values) * 100:.1f}%
            """
            ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
                    verticalalignment='top', bbox={'boxstyle': 'round', 'facecolor': 'wheat', 'alpha': 0.8})

            plt.suptitle('夏普比率统计分析', fontsize=16)
            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 分布图生成失败: {e}")
            return None

    def create_interactive_3d_plot(self, results_df: pd.DataFrame) -> Optional[go.Figure]:
        """创建交互式3D散点图"""
        if results_df.empty:
            return None

        try:
            # 提取数据
            bb_periods = [row['params']['bb_period'] for _, row in results_df.iterrows()]
            rsi_periods = [row['params']['rsi_period'] for _, row in results_df.iterrows()]
            sharpe_ratios = results_df['sharpe_ratio'].values
            total_returns = results_df['total_return'].values

            # 创建3D散点图
            fig = go.Figure(data=go.Scatter3d(
                x=bb_periods,
                y=rsi_periods,
                z=sharpe_ratios,
                mode='markers',
                marker={
                    'size': 8,
                    'color': total_returns,
                    'colorscale': 'RdYlGn',
                    'colorbar': {'title': "总收益率"},
                    'opacity': 0.8
                },
                text=[f'BB:{bb}, RSI:{rsi}<br>夏普:{sharpe:.3f}<br>收益:{ret:.3f}'
                      for bb, rsi, sharpe, ret in zip(bb_periods, rsi_periods, sharpe_ratios, total_returns)],
                hovertemplate='%{text}<extra></extra>'
            ))

            fig.update_layout(
                title='参数优化3D可视化',
                scene={
                    'xaxis_title': '布林带周期',
                    'yaxis_title': 'RSI周期',
                    'zaxis_title': '夏普比率'
                },
                width=800,
                height=600
            )

            return fig

        except Exception as e:
            print(f"❌ 3D图生成失败: {e}")
            return None

    def _prepare_top_combinations_data(self, top_results):
        """Prepare data for top combinations visualization."""
        combination_labels = []
        sharpe_ratios = []
        total_returns = []
        max_drawdowns = []

        for i, (_, row) in enumerate(top_results.iterrows()):
            params = row['params']
            label = f"#{i+1}\nBB:{params['bb_period']}\nRSI:{params['rsi_period']}"
            combination_labels.append(label)
            sharpe_ratios.append(row['sharpe_ratio'])
            total_returns.append(row['total_return'])
            max_drawdowns.append(abs(row['max_drawdown']))

        return combination_labels, sharpe_ratios, total_returns, max_drawdowns

    def _create_top_combinations_charts(self, axes, *, combination_labels, sharpe_ratios,
                                       total_returns, max_drawdowns, top_n):
        """Create individual charts for top combinations analysis."""
        # 夏普比率
        bars1 = axes[0, 0].bar(range(top_n), sharpe_ratios, color='lightblue', alpha=0.8)
        axes[0, 0].set_title('前10名参数组合 - 夏普比率')
        axes[0, 0].set_ylabel('夏普比率')
        axes[0, 0].set_xticks(range(top_n))
        axes[0, 0].set_xticklabels(combination_labels, rotation=45, ha='right')
        axes[0, 0].grid(True, alpha=0.3)

        # 添加数值标签
        for chart_bar, value in zip(bars1, sharpe_ratios):
            height = chart_bar.get_height()
            axes[0, 0].text(chart_bar.get_x() + chart_bar.get_width()/2., height,
                    f'{value:.3f}', ha='center', va='bottom')

        # 总收益率
        axes[0, 1].bar(range(top_n), [r*100 for r in total_returns], color='lightgreen', alpha=0.8)
        axes[0, 1].set_title('前10名参数组合 - 总收益率')
        axes[0, 1].set_ylabel(self.TOTAL_RETURN_LABEL)
        axes[0, 1].set_xticks(range(top_n))
        axes[0, 1].set_xticklabels(combination_labels, rotation=45, ha='right')
        axes[0, 1].grid(True, alpha=0.3)

        # 最大回撤
        axes[1, 0].bar(range(top_n), [d*100 for d in max_drawdowns], color='lightcoral', alpha=0.8)
        axes[1, 0].set_title('前10名参数组合 - 最大回撤')
        axes[1, 0].set_ylabel(self.MAX_DRAWDOWN_LABEL)
        axes[1, 0].set_xticks(range(top_n))
        axes[1, 0].set_xticklabels(combination_labels, rotation=45, ha='right')
        axes[1, 0].grid(True, alpha=0.3)

        # 风险收益散点图
        axes[1, 1].scatter([r*100 for r in total_returns], sharpe_ratios,
                   s=100, alpha=0.7, c=range(top_n), cmap='viridis')
        axes[1, 1].set_xlabel(self.TOTAL_RETURN_LABEL)
        axes[1, 1].set_ylabel('夏普比率')
        axes[1, 1].set_title('风险-收益关系图')
        axes[1, 1].grid(True, alpha=0.3)

        # 添加序号标签
        for i, (ret, sharpe) in enumerate(zip(total_returns, sharpe_ratios)):
            axes[1, 1].annotate(f'#{i+1}', (ret*100, sharpe), xytext=(5, 5),
                       textcoords='offset points', fontsize=8)

    def plot_top_combinations(self, results_df: pd.DataFrame, top_n: int = 10) -> Optional[plt.Figure]:
        """绘制前N名参数组合对比图"""
        if results_df.empty or len(results_df) < top_n:
            return None

        try:
            top_results = results_df.head(top_n)

            # 准备数据
            combination_labels, sharpe_ratios, total_returns, max_drawdowns = \
                self._prepare_top_combinations_data(top_results)

            # 创建子图
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))

            # 创建图表
            self._create_top_combinations_charts(
                axes,
                combination_labels=combination_labels,
                sharpe_ratios=sharpe_ratios,
                total_returns=total_returns,
                max_drawdowns=max_drawdowns,
                top_n=top_n
            )

            plt.suptitle(f'前{top_n}名参数组合分析', fontsize=16)
            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 前N名组合图生成失败: {e}")
            return None
