# 📈 交互式图表生成器
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime, timedelta
import yfinance as yf
import platform


# 设置中文字体
def setup_chinese_font():
    """设置matplotlib中文字体"""
    try:
        if platform.system() == "Windows":
            # Windows系统字体
            font_names = ["Microsoft YaHei", "SimHei", "KaiTi", "FangSong"]
        elif platform.system() == "Darwin":  # macOS
            font_names = ["PingFang SC", "Heiti SC", "STHeiti"]
        else:  # Linux
            font_names = ["DejaVu Sans", "WenQuanYi Micro Hei", "Droid Sans Fallback"]

        # 尝试设置字体
        for font_name in font_names:
            try:
                plt.rcParams["font.sans-serif"] = [font_name]
                plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
                return font_name
            except:
                continue

        # 如果都不行，使用默认设置
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        return "DejaVu Sans"

    except Exception as e:
        print(f"⚠️ 字体设置失败: {e}")
        return None


# 初始化时设置字体
setup_chinese_font()


class InteractiveChartGenerator:
    """交互式图表生成器"""

    def __init__(self):
        # 确保中文字体设置
        setup_chinese_font()

        self.colors = {
            "primary": "#1f77b4",
            "secondary": "#ff7f0e",
            "success": "#2ca02c",
            "danger": "#d62728",
            "warning": "#ff7f0e",
            "info": "#17a2b8",
        }

    def create_price_signal_chart(self, symbol, results=None, strategy_params=None):
        """创建价格和信号图表"""
        try:
            # 确保中文字体设置生效
            setup_chinese_font()

            # 获取价格数据
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1y")

            if data.empty:
                print(f"❌ 无法获取 {symbol} 的数据")
                return None

            # 计算技术指标
            data = self._calculate_indicators(data, strategy_params)

            # 创建图表
            fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(15, 12))
            fig.suptitle(
                f"{symbol} 价格走势与交易信号分析", fontsize=16, fontweight="bold"
            )

            # 1. 价格图表 + 布林带
            ax1.plot(
                data.index,
                data["Close"],
                label="收盘价",
                color=self.colors["primary"],
                linewidth=2,
            )

            if "BB_Upper" in data.columns:
                ax1.plot(
                    data.index,
                    data["BB_Upper"],
                    label="布林带上轨",
                    color=self.colors["danger"],
                    alpha=0.7,
                )
                ax1.plot(
                    data.index,
                    data["BB_Lower"],
                    label="布林带下轨",
                    color=self.colors["danger"],
                    alpha=0.7,
                )
                ax1.plot(
                    data.index,
                    data["BB_Middle"],
                    label="布林带中轨",
                    color=self.colors["warning"],
                    alpha=0.7,
                )
                ax1.fill_between(
                    data.index,
                    data["BB_Upper"],
                    data["BB_Lower"],
                    alpha=0.1,
                    color=self.colors["warning"],
                )

            # 添加买卖信号
            buy_signals, sell_signals = self._generate_signals(data, strategy_params)
            if len(buy_signals) > 0:
                ax1.scatter(
                    buy_signals.index,
                    buy_signals["Close"],
                    color=self.colors["success"],
                    s=150,  # 增大标记点
                    marker="^",
                    label="买入信号",
                    zorder=5,
                    edgecolors='white',  # 添加白色边框
                    linewidth=2
                )
                print(f"✅ 显示 {len(buy_signals)} 个买入信号")
            else:
                print("⚠️ 没有检测到买入信号")
                
            if len(sell_signals) > 0:
                ax1.scatter(
                    sell_signals.index,
                    sell_signals["Close"],
                    color=self.colors["danger"],
                    s=150,  # 增大标记点
                    marker="v",
                    label="卖出信号",
                    zorder=5,
                    edgecolors='white',  # 添加白色边框
                    linewidth=2
                )
                print(f"✅ 显示 {len(sell_signals)} 个卖出信号")
            else:
                print("⚠️ 没有检测到卖出信号")

            ax1.set_title("价格走势与布林带", fontweight="bold")
            ax1.set_ylabel("价格 ($)")
            ax1.legend()
            ax1.grid(True, alpha=0.3)

            # 2. RSI指标
            if "RSI" in data.columns:
                ax2.plot(
                    data.index,
                    data["RSI"],
                    label="RSI",
                    color=self.colors["info"],
                    linewidth=2,
                )
                ax2.axhline(
                    y=70,
                    color=self.colors["danger"],
                    linestyle="--",
                    alpha=0.7,
                    label="超买线(70)",
                )
                ax2.axhline(
                    y=30,
                    color=self.colors["success"],
                    linestyle="--",
                    alpha=0.7,
                    label="超卖线(30)",
                )
                ax2.fill_between(
                    data.index, 70, 100, alpha=0.1, color=self.colors["danger"]
                )
                ax2.fill_between(
                    data.index, 0, 30, alpha=0.1, color=self.colors["success"]
                )

            ax2.set_title("RSI 相对强弱指标", fontweight="bold")
            ax2.set_ylabel("RSI")
            ax2.set_ylim(0, 100)
            ax2.legend()
            ax2.grid(True, alpha=0.3)

            # 3. 成交量
            ax3.bar(
                data.index, data["Volume"], alpha=0.7, color=self.colors["secondary"]
            )
            ax3.set_title("成交量", fontweight="bold")
            ax3.set_ylabel("成交量")
            ax3.set_xlabel("日期")
            ax3.grid(True, alpha=0.3)

            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 图表生成失败: {str(e)}")
            return None

    def create_performance_chart(self, results, symbol):
        """创建性能分析图表"""
        try:
            # 确保中文字体设置生效
            setup_chinese_font()

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle(f"{symbol} 策略性能分析", fontsize=16, fontweight="bold")

            # 1. 关键指标雷达图
            metrics = ["收益率", "夏普比率", "胜率", "风险控制"]
            values = [
                max(0, min(results.get("total_return", 0) * 5, 1)),
                max(0, min(results.get("sharpe_ratio", 0) / 3, 1)),
                results.get("win_rate", 0),
                max(0, 1 + results.get("max_drawdown", 0)),
            ]

            angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]

            ax1.remove()
            ax1 = fig.add_subplot(2, 2, 1, projection="polar")
            ax1.plot(angles, values, "o-", linewidth=2, color=self.colors["primary"])
            ax1.fill(angles, values, alpha=0.25, color=self.colors["primary"])
            ax1.set_xticks(angles[:-1])
            ax1.set_xticklabels(metrics)
            ax1.set_ylim(0, 1)
            ax1.set_title("性能雷达图", pad=20)

            # 2. 收益分布
            np.random.seed(42)
            returns_sim = np.random.normal(
                results.get("total_return", 0) / 250, 0.02, 250
            )
            ax2.hist(returns_sim, bins=30, alpha=0.7, color=self.colors["success"])
            ax2.axvline(
                returns_sim.mean(),
                color=self.colors["danger"],
                linestyle="--",
                label=f"平均: {returns_sim.mean():.2%}",
            )
            ax2.set_title("收益分布")
            ax2.set_xlabel("日收益率")
            ax2.set_ylabel("频次")
            ax2.legend()

            # 3. 风险收益图
            risk = abs(results.get("max_drawdown", 0))
            return_val = results.get("total_return", 0)
            ax3.scatter(
                risk, return_val, s=200, color=self.colors["primary"], alpha=0.7
            )
            ax3.scatter(
                0.1, 0.08, s=100, color=self.colors["warning"], alpha=0.7, label="基准"
            )
            ax3.annotate(
                f"{symbol}\\n策略",
                xy=(risk, return_val),
                xytext=(10, 10),
                textcoords="offset points",
            )
            ax3.set_title("风险-收益分析")
            ax3.set_xlabel("最大回撤")
            ax3.set_ylabel("总收益率")
            ax3.legend()
            ax3.grid(True, alpha=0.3)

            # 4. 指标对比
            metrics_names = ["总收益", "夏普比率", "最大回撤", "胜率"]
            strategy_values = [
                results.get("total_return", 0),
                results.get("sharpe_ratio", 0) / 3,  # 标准化
                abs(results.get("max_drawdown", 0)),
                results.get("win_rate", 0),
            ]
            benchmark_values = [0.08, 1 / 3, 0.1, 0.5]  # 基准值

            x = np.arange(len(metrics_names))
            width = 0.35

            ax4.bar(
                x - width / 2,
                strategy_values,
                width,
                label="策略",
                color=self.colors["primary"],
            )
            ax4.bar(
                x + width / 2,
                benchmark_values,
                width,
                label="基准",
                color=self.colors["secondary"],
            )
            ax4.set_title("策略 vs 基准对比")
            ax4.set_ylabel("标准化数值")
            ax4.set_xticks(x)
            ax4.set_xticklabels(metrics_names, rotation=45)
            ax4.legend()

            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 性能图表生成失败: {str(e)}")
            return None

    def create_comparison_chart(self, comparison_results):
        """创建多股票对比图表"""
        try:
            # 确保中文字体设置生效
            setup_chinese_font()

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle("多股票策略表现对比", fontsize=16, fontweight="bold")

            symbols = list(comparison_results.keys())
            returns = [comparison_results[s]["总收益率"] for s in symbols]
            sharpe_ratios = [comparison_results[s]["夏普比率"] for s in symbols]
            drawdowns = [abs(comparison_results[s]["最大回撤"]) for s in symbols]
            win_rates = [comparison_results[s]["胜率"] for s in symbols]

            colors = [
                self.colors["primary"],
                self.colors["secondary"],
                self.colors["success"],
                self.colors["danger"],
            ][: len(symbols)]

            # 1. 收益率对比
            bars1 = ax1.bar(symbols, returns, color=colors, alpha=0.8)
            ax1.set_title("总收益率对比")
            ax1.set_ylabel("收益率")
            ax1.grid(True, alpha=0.3)
            for bar, ret in zip(bars1, returns):
                height = bar.get_height()
                ax1.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.001,
                    f"{ret:.2%}",
                    ha="center",
                    va="bottom",
                )

            # 2. 风险收益散点图
            ax2.scatter(drawdowns, returns, s=200, c=colors, alpha=0.7)
            ax2.set_title("风险-收益分析")
            ax2.set_xlabel("最大回撤")
            ax2.set_ylabel("总收益率")
            ax2.grid(True, alpha=0.3)
            for i, symbol in enumerate(symbols):
                ax2.annotate(
                    symbol,
                    (drawdowns[i], returns[i]),
                    xytext=(5, 5),
                    textcoords="offset points",
                )

            # 3. 夏普比率对比
            bars3 = ax3.bar(symbols, sharpe_ratios, color=colors, alpha=0.8)
            ax3.set_title("夏普比率对比")
            ax3.set_ylabel("夏普比率")
            ax3.axhline(y=1.0, color=self.colors["danger"], linestyle="--", alpha=0.7)
            ax3.grid(True, alpha=0.3)
            for bar, sharpe in zip(bars3, sharpe_ratios):
                height = bar.get_height()
                ax3.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    f"{sharpe:.2f}",
                    ha="center",
                    va="bottom",
                )

            # 4. 胜率对比
            bars4 = ax4.bar(symbols, win_rates, color=colors, alpha=0.8)
            ax4.set_title("胜率对比")
            ax4.set_ylabel("胜率")
            ax4.axhline(y=0.5, color=self.colors["danger"], linestyle="--", alpha=0.7)
            ax4.grid(True, alpha=0.3)
            for bar, wr in zip(bars4, win_rates):
                height = bar.get_height()
                ax4.text(
                    bar.get_x() + bar.get_width() / 2.0,
                    height + 0.02,
                    f"{wr:.1%}",
                    ha="center",
                    va="bottom",
                )

            plt.tight_layout()
            return fig

        except Exception as e:
            print(f"❌ 对比图表生成失败: {str(e)}")
            return None

    def _calculate_indicators(self, data, strategy_params=None):
        """计算技术指标"""
        bb_period = strategy_params.get("bb_period", 20) if strategy_params else 20
        rsi_period = strategy_params.get("rsi_period", 14) if strategy_params else 14

        # 布林带
        data["BB_Middle"] = data["Close"].rolling(window=bb_period).mean()
        bb_std = data["Close"].rolling(window=bb_period).std()
        data["BB_Upper"] = data["BB_Middle"] + (bb_std * 2)
        data["BB_Lower"] = data["BB_Middle"] - (bb_std * 2)

        # RSI
        delta = data["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        data["RSI"] = 100 - (100 / (1 + rs))

        return data

    def _generate_signals(self, data, strategy_params=None):
        """生成买卖信号"""
        rsi_oversold = (
            strategy_params.get("rsi_oversold", 30) if strategy_params else 30
        )
        rsi_overbought = (
            strategy_params.get("rsi_overbought", 70) if strategy_params else 70
        )

        # 放宽买入信号条件: RSI < 超卖阈值 或 价格接近布林带下轨
        buy_condition1 = data["RSI"] < rsi_oversold
        buy_condition2 = (data["Close"] <= data["BB_Lower"] * 1.02)  # 价格在下轨102%以内
        buy_condition = buy_condition1 | buy_condition2  # 满足其一即可
        
        # 放宽卖出信号条件: RSI > 超买阈值 或 价格接近布林带上轨
        sell_condition1 = data["RSI"] > rsi_overbought
        sell_condition2 = (data["Close"] >= data["BB_Upper"] * 0.98)  # 价格在上轨98%以上
        sell_condition = sell_condition1 | sell_condition2  # 满足其一即可

        buy_signals = data[buy_condition]
        sell_signals = data[sell_condition]
        
        print(f"🔍 信号统计: 买入信号 {len(buy_signals)} 个, 卖出信号 {len(sell_signals)} 个")

        return buy_signals, sell_signals

    def save_chart(self, fig, filename, output_dir="charts"):
        """保存图表"""
        import os

        os.makedirs(output_dir, exist_ok=True)

        filepath = os.path.join(
            output_dir, f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        )
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        plt.close(fig)

        return filepath


if __name__ == "__main__":
    # 测试代码
    chart_gen = InteractiveChartGenerator()

    # 测试数据
    test_results = {
        "total_return": 0.12,
        "sharpe_ratio": 1.5,
        "max_drawdown": -0.08,
        "win_rate": 0.6,
    }

    # 生成图表
    fig = chart_gen.create_performance_chart(test_results, "AAPL")
    if fig:
        chart_path = chart_gen.save_chart(fig, "AAPL_performance")
        print(f"图表已保存: {chart_path}")
