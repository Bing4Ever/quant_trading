# 🖥️ Streamlit 可视化界面
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 导入自定义模块
try:
    from trading.live_trading_engine import LiveTradingEngine
    from strategies.mean_reversion_strategy import MeanReversionStrategy
    from strategies.multi_strategy_runner import MultiStrategyRunner
    from visualization.report_generator import BacktestReportGenerator
    from visualization.chart_generator import InteractiveChartGenerator
    from data.database import BacktestDatabase
    from optimization.parameter_optimizer import ParameterOptimizer
    from optimization.optimization_visualizer import OptimizationVisualizer
    from automation.streamlit_automation import automation_management_page
except ImportError as e:
    st.error(f"模块导入失败: {e}")
    
    # 提供备用函数定义
def automation_management_page():
    st.header("🤖 自动化交易管理")
    
    # 子页面导航
    sub_tab1, sub_tab2, sub_tab3 = st.tabs(["📊 实时监控", "⏰ 自动化调度", "📋 任务管理"])
    
    with sub_tab1:
        # 实时监控页面
        try:
            from automation.streamlit_realtime import real_time_monitor_page
            real_time_monitor_page()
        except ImportError as e:
            st.error(f"实时监控模块加载失败: {e}")
            st.info("正在开发中，请确保已安装必要的依赖")
    
    with sub_tab2:
        # 自动化调度页面
        try:
            from automation.streamlit_automation import automation_scheduler_page
            automation_scheduler_page()
        except ImportError as e:
            st.error(f"自动化调度模块加载失败: {e}")
            st.info("正在开发中...")
    
    with sub_tab3:
        # 任务管理页面
        automation_task_management_page()

def automation_task_management_page():
    """自动化任务管理页面"""
    st.subheader("📋 自动化任务管理")
    
    # 显示当前开发进度
    st.info("📈 自动化开发进度")
    
    # 任务进度
    progress_data = [
        {"任务": "自动化交易调度器", "状态": "✅ 已完成", "进度": 100},
        {"任务": "实时数据监控系统", "状态": "🔄 进行中", "进度": 80},
        {"任务": "自动报告生成器", "状态": "📋 待开发", "进度": 0},
        {"任务": "交易信号自动执行", "状态": "📋 待开发", "进度": 0},
        {"任务": "风险管理系统", "状态": "📋 待开发", "进度": 0},
        {"任务": "消息通知系统", "状态": "✅ 已完成", "进度": 100},
        {"任务": "交易日志系统", "状态": "✅ 已完成", "进度": 100},
        {"任务": "模拟交易环境", "状态": "📋 待开发", "进度": 0},
    ]
    
    import pandas as pd
    df = pd.DataFrame(progress_data)
    
    # 显示进度表格
    st.dataframe(df, use_container_width=True)
    
    # 总体进度
    total_progress = sum(item["进度"] for item in progress_data) / len(progress_data)
    st.progress(total_progress / 100)
    st.caption(f"总体进度: {total_progress:.1f}%")
    
    # 下一步计划
    st.subheader("🎯 下一步开发计划")
    
    st.markdown("""
    ### 🔄 当前正在开发：实时数据监控系统
    
    **已完成功能:**
    - ✅ 基础监控框架
    - ✅ 多数据源支持 (yfinance, Alpha Vantage)
    - ✅ 信号监控系统
    - ✅ 通知系统集成
    
    **正在开发:**
    - 🔄 Streamlit实时界面
    - 🔄 多策略信号整合
    - 🔄 性能优化
    
    **下一步:**
    1. 完成实时监控UI界面
    2. 开发自动报告生成器
    3. 实现交易信号自动执行
    4. 构建风险管理系统
    """)
    
    # 手动触发开发任务
    st.subheader("🛠️ 开发工具")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔧 创建新模块", use_container_width=True):
            st.info("开发者工具：用于快速创建新的自动化模块")
    
    with col2:
        if st.button("📊 性能测试", use_container_width=True):
            st.info("系统性能测试和基准测试")
    
    with col3:
        if st.button("🔍 调试模式", use_container_width=True):
            st.info("启用详细的调试日志和错误追踪")

# 初始化数据库
@st.cache_resource
def init_database():
    return BacktestDatabase()


def stock_selector():
    """股票选择器组件"""
    st.subheader("📈 股票选择")
    
    symbol = st.text_input(
        "输入股票代码:",
        placeholder="例如: AAPL, TSLA, MSFT",
        help="输入美股股票代码"
    ).upper()
    
    # 验证股票代码
    if symbol:
        try:
            info = yf.Ticker(symbol).info
            if 'longName' in info:
                st.success(f"✅ {symbol} - {info.get('longName', '未知公司')}")
            else:
                st.warning(f"⚠️ 无法获取 {symbol} 的信息，请检查股票代码")
        except Exception:
            st.error(f"❌ 股票代码 {symbol} 无效")
    
    return symbol


def main():
    """主界面"""
    st.set_page_config(
        page_title="量化交易回测系统",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 标题
    st.title("📊 量化交易回测系统")
    
    # 页面导航 - 只保留多策略比较和自动化管理
    tab1, tab2, tab3 = st.tabs(["� 多策略比较", "🤖 自动化管理", " 历史分析"])
    
    with tab1:
        multi_strategy_comparison_page()
    
    with tab2:
        automation_management_page()
    
    with tab3:
        history_analysis_page()
    
def multi_strategy_comparison_page():
    """多策略比较页面"""
    st.header("🔄 多策略性能比较")
    st.markdown("同时运行多个交易策略，生成综合性能报告")
    
    # 侧边栏配置
    with st.sidebar:
        st.header("🔧 策略配置")
        
        # 股票选择
        st.subheader("📈 股票选择")
        symbol = st.text_input(
            "输入股票代码:",
            placeholder="例如: AAPL, TSLA, MSFT",
            help="输入美股股票代码",
            key="multi_strategy_stock_input"
        ).upper()
        
        # 验证股票代码
        if symbol:
            try:
                info = yf.Ticker(symbol).info
                if 'longName' in info:
                    st.success(f"✅ {info['longName']}")
                else:
                    st.warning("⚠️ 无法验证此股票代码")
            except:
                st.warning("⚠️ 无法验证此股票代码")
        
        # 在股票代码输入框下面直接添加checkbox
        run_analysis = st.checkbox("✅ 运行多策略回测", value=False, key="run_multi_strategy_checkbox")
        
        # 当checkbox勾选时才显示默认策略组合
        if run_analysis:
            st.info("""
            **默认策略组合：**
            - 📈 移动平均策略
            - 📊 RSI策略  
            - 📉 布林带策略
            - 🔄 均值回归策略
            """)
    
    # 主内容区域
    if symbol and run_analysis:
        st.subheader(f"📊 {symbol} 多策略回测分析")
        st.info("🔧 多策略功能正在开发中，敬请期待！")


def show_welcome_page():
    """显示欢迎页面"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("📈 支持策略", "均值回归", "技术指标驱动")
    with col2:
        st.metric("📊 分析维度", "多重指标", "风险收益分析")
    with col3:
        st.metric("🎯 回测精度", "高精度", "专业级别")

    st.markdown("---")

    st.markdown(
        """
    ## 🎯 系统功能
    
    ### 📋 核心功能
    - **策略回测**: 支持多种技术指标策略
    - **性能分析**: 收益、风险、夏普比率等指标
    - **可视化**: 交互式图表和报告
    - **参数优化**: 实时调整策略参数
    
    ### 📊 分析报告
    - **Markdown报告**: 详细的文本格式分析
    - **HTML报告**: 可视化网页报告
    - **图表分析**: 价格走势、信号、性能图表
    - **对比分析**: 多股票横向对比
    
    ### 💾 数据管理
    - **历史存储**: 保存所有回测结果
    - **趋势分析**: 策略表现历史趋势
    - **参数跟踪**: 不同参数组合的效果记录
    """
    )

    st.info("👈 请在左侧配置策略参数，然后点击运行回测开始分析！")


def run_backtest_analysis(symbol, period, strategy_params, initial_capital):
    """运行回测分析"""

    # 显示加载状态
    with st.spinner(f"正在分析 {symbol}..."):
        try:
            # 创建策略
            strategy = MeanReversionStrategy(
                bb_period=strategy_params["bb_period"],
                rsi_period=strategy_params["rsi_period"],
                rsi_oversold=strategy_params["rsi_oversold"],
                rsi_overbought=strategy_params["rsi_overbought"],
            )

            # 创建交易引擎
            engine = LiveTradingEngine()
            engine.strategy = strategy

            # 运行回测
            results = engine.run_backtest_analysis(symbol)

            if results:
                # 保存回测结果到数据库
                db = init_database()
                
                # 准备保存的结果数据
                save_results = {
                    'total_return': results.get('总收益率', results.get('total_return', 0)),
                    'sharpe_ratio': results.get('夏普比率', results.get('sharpe_ratio', 0)),
                    'max_drawdown': results.get('最大回撤', results.get('max_drawdown', 0)),
                    'win_rate': results.get('胜率', results.get('win_rate', 0)),
                    'total_trades': results.get('交易次数', results.get('total_trades', 0)),
                    'volatility': results.get('波动率', results.get('volatility', 0)),
                    'annualized_return': results.get('年化收益率', results.get('annualized_return', 0)),
                    'avg_trade_return': results.get('平均交易收益', results.get('avg_trade_return', 0))
                }
                
                # 准备回测配置信息
                from datetime import datetime, timedelta
                end_date = datetime.now()
                
                # 根据period计算开始日期
                if period == "1年":
                    start_date = end_date - timedelta(days=365)
                elif period == "2年":
                    start_date = end_date - timedelta(days=730)
                elif period == "3年":
                    start_date = end_date - timedelta(days=1095)
                elif period == "5年":
                    start_date = end_date - timedelta(days=1825)
                else:
                    start_date = end_date - timedelta(days=365)
                
                backtest_config = {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'period': period,
                    'initial_capital': initial_capital,
                    'commission': 0.001,
                    'slippage': 0.0005,
                    'data_source': 'yfinance',
                    'backtest_mode': 'manual',
                    'optimization_used': hasattr(st.session_state, 'optimized_params') and 
                                        'optimized_params' in st.session_state,
                    'streamlit_version': True,
                    'user_interface': 'streamlit_web'
                }
                
                # 保存到数据库
                backtest_id = db.save_backtest_result(
                    symbol=symbol,
                    strategy_name="MeanReversionStrategy",
                    strategy_params=strategy_params,
                    results=save_results,
                    backtest_config=backtest_config,
                    notes=f"Streamlit回测 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
                # 显示结果
                display_results(symbol, results, strategy_params)
                
                # 如果保存成功，显示提示
                if backtest_id:
                    st.sidebar.success(f"✅ 回测结果已保存 (ID: {backtest_id})")
                    
                    # 如果是收藏的股票，显示特别提示
                    if db.is_favorite(symbol):
                        st.sidebar.info(f"💾 已更新收藏股票 {symbol} 的最新回测数据")
                
            else:
                st.error("❌ 回测分析失败，请检查参数设置")

        except Exception as e:
            st.error(f"❌ 错误: {str(e)}")


def display_results(symbol, results, strategy_params):
    """显示回测结果"""

    # 标题
    st.header(f"📊 {symbol} 回测结果")

    # 核心指标展示
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_return = results.get("total_return", 0)
        delta_color = "normal" if total_return >= 0 else "inverse"
        st.metric(
            "总收益率",
            f"{total_return:.2%}",
            delta=f"{total_return:.2%}",
            delta_color=delta_color,
        )

    with col2:
        sharpe = results.get("sharpe_ratio", 0)
        st.metric(
            "夏普比率",
            f"{sharpe:.3f}",
            delta="优秀" if sharpe > 1 else "一般" if sharpe > 0 else "不佳",
        )

    with col3:
        max_dd = results.get("max_drawdown", 0)
        st.metric(
            "最大回撤",
            f"{max_dd:.2%}",
            delta=(
                "良好" if abs(max_dd) < 0.1 else "一般" if abs(max_dd) < 0.2 else "较高"
            ),
        )

    with col4:
        win_rate = results.get("win_rate", 0)
        st.metric(
            "胜率",
            f"{win_rate:.1%}",
            delta="高" if win_rate > 0.6 else "中" if win_rate > 0.4 else "低",
        )

    # 详细指标表格
    st.subheader("📋 详细指标")

    metrics_data = {
        "指标": [
            "总收益率",
            "年化收益率",
            "夏普比率",
            "最大回撤",
            "波动率",
            "胜率",
            "交易次数",
        ],
        "数值": [
            f"{results.get('total_return', 0):.2%}",
            f"{results.get('annualized_return', 0):.2%}",
            f"{results.get('sharpe_ratio', 0):.3f}",
            f"{results.get('max_drawdown', 0):.2%}",
            f"{results.get('volatility', 0):.2%}",
            f"{results.get('win_rate', 0):.1%}",
            f"{results.get('total_trades', 0)}",
        ],
    }

    df_metrics = pd.DataFrame(metrics_data)
    st.dataframe(df_metrics, use_container_width=True)

    # 生成图表
    st.subheader("📈 性能图表")

    chart_gen = InteractiveChartGenerator()

    # 价格和信号图表
    with st.spinner("生成价格信号图表..."):
        price_fig = chart_gen.create_price_signal_chart(
            symbol, results, strategy_params
        )
        if price_fig:
            st.pyplot(price_fig)

    # 性能分析图表
    with st.spinner("生成性能分析图表..."):
        perf_fig = chart_gen.create_performance_chart(results, symbol)
        if perf_fig:
            st.pyplot(perf_fig)

    # 生成报告
    st.subheader("📋 报告生成")

    col1, col2 = st.columns(2)

    # 生成报告内容
    report_gen = BacktestReportGenerator()
    
    try:
        markdown_content = report_gen.generate_markdown_report(
            results, symbol, strategy_params
        )
        html_content = report_gen.generate_html_report(
            results, symbol, strategy_params
        )
        
        # 确保HTML内容包含正确的编码声明
        if '<meta charset="utf-8">' not in html_content:
            html_content = html_content.replace('<head>', '<head>\n    <meta charset="utf-8">')
        
        with col1:
            st.download_button(
                "📥 下载Markdown报告",
                markdown_content.encode('utf-8'),
                file_name=f"{symbol}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown; charset=utf-8",
                use_container_width=True
            )

        with col2:
            st.download_button(
                "📥 下载HTML报告",
                html_content.encode('utf-8'),
                file_name=f"{symbol}_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html; charset=utf-8",
                use_container_width=True
            )
            
        st.success("✅ 报告已准备就绪，点击上方按钮下载")
        
    except Exception as e:
        st.error(f"❌ 报告生成失败: {str(e)}")
        import traceback
        st.text("错误详情:")
        st.code(traceback.format_exc())

    # 分析建议
    st.subheader("💡 分析建议")

    performance_summary = generate_performance_summary(results)
    improvement_suggestions = generate_improvement_suggestions(results)

    if results.get("total_return", 0) > 0:
        st.success(f"✅ {performance_summary}")
    else:
        st.warning(f"⚠️ {performance_summary}")

    st.info(f"💡 改进建议: {improvement_suggestions}")


def generate_performance_summary(results):
    """生成性能总结"""
    total_return = results.get("total_return", 0)
    sharpe = results.get("sharpe_ratio", 0)

    if total_return > 0.1 and sharpe > 1:
        return "策略表现优秀，收益和风险调整表现均超出预期"
    elif total_return > 0 and sharpe > 0:
        return "策略表现中等，有盈利但仍有优化空间"
    else:
        return "策略需要改进，当前参数下表现不佳"


def generate_improvement_suggestions(results):
    """生成改进建议"""
    suggestions = []

    if results.get("total_return", 0) < 0:
        suggestions.append("考虑调整策略参数")

    if results.get("sharpe_ratio", 0) < 0.5:
        suggestions.append("优化风险管理")

    if abs(results.get("max_drawdown", 0)) > 0.15:
        suggestions.append("设置止损机制")

    if results.get("win_rate", 0) < 0.4:
        suggestions.append("调整信号参数")

    if not suggestions:
        suggestions.append("当前策略表现良好")

    return "; ".join(suggestions)


# 页面路由
def history_analysis_page():
    """历史分析页面"""
    st.header("📊 历史回测分析")
    
    db = init_database()
    
    # 获取所有回测记录
    all_results = db.get_all_results()
    
    if all_results.empty:
        st.info("💡 还没有历史回测记录。")
        return
    
    # 统计信息
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总回测次数", len(all_results))
    
    with col2:
        unique_symbols = all_results['symbol'].nunique()
        st.metric("分析股票数", unique_symbols)
    
    with col3:
        avg_return = all_results['total_return'].mean()
        st.metric("平均收益率", f"{avg_return:.2%}")
    
    with col4:
        best_return = all_results['total_return'].max()
        st.metric("最佳收益率", f"{best_return:.2%}")
    
    # 按股票筛选
    st.subheader("🔍 历史记录筛选")
    
    col1, col2 = st.columns(2)
    
    with col1:
        symbols = ['全部'] + sorted(all_results['symbol'].unique().tolist())
        selected_symbol = st.selectbox("选择股票:", symbols)
    
    with col2:
        days = st.selectbox("时间范围:", 
                           ["全部", "最近7天", "最近30天", "最近90天"])
    
    # 筛选数据
    filtered_results = all_results.copy()
    
    if selected_symbol != "全部":
        filtered_results = filtered_results[
            filtered_results['symbol'] == selected_symbol
        ]
    
    if days != "全部":
        days_map = {"最近7天": 7, "最近30天": 30, "最近90天": 90}
        cutoff_date = datetime.now() - timedelta(days=days_map[days])
        filtered_results = filtered_results[
            pd.to_datetime(filtered_results['created_at']) >= cutoff_date
        ]
    
    # 显示结果表格
    if not filtered_results.empty:
        st.subheader(f"📋 回测记录 ({len(filtered_results)} 条)")
        
        # 添加详细视图选择
        view_mode = st.radio(
            "显示模式:", 
            ["简单视图", "详细视图"], 
            horizontal=True
        )
        
        if view_mode == "简单视图":
            # 格式化显示数据
            display_df = filtered_results[[
                'symbol', 'total_return', 'sharpe_ratio', 
                'max_drawdown', 'win_rate', 'total_trades', 'created_at'
            ]].copy()
            
            display_df['total_return'] = display_df['total_return'].apply(
                lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
            )
            display_df['sharpe_ratio'] = display_df['sharpe_ratio'].apply(
                lambda x: f"{x:.3f}" if pd.notna(x) else "N/A"
            )
            display_df['max_drawdown'] = display_df['max_drawdown'].apply(
                lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
            )
            display_df['win_rate'] = display_df['win_rate'].apply(
                lambda x: f"{x:.1%}" if pd.notna(x) else "N/A"
            )
            display_df['created_at'] = pd.to_datetime(
                display_df['created_at']
            ).dt.strftime('%Y-%m-%d %H:%M')
            
            display_df.columns = [
                '股票代码', '总收益率', '夏普比率', '最大回撤', 
                '胜率', '交易次数', '回测时间'
            ]
            
            st.dataframe(
                display_df, 
                use_container_width=True,
                hide_index=True
            )
        
        else:  # 详细视图
            st.info("💡 点击展开查看每条记录的详细参数配置")
            
            for idx, row in filtered_results.iterrows():
                with st.expander(
                    f"🔍 {row['symbol']} - {row['created_at']} "
                    f"(收益: {row['total_return']:.2%}, 夏普: {row['sharpe_ratio']:.3f})"
                ):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**📊 回测结果**")
                        st.write(f"总收益率: {row['total_return']:.2%}")
                        st.write(f"夏普比率: {row['sharpe_ratio']:.3f}")
                        st.write(f"最大回撤: {row['max_drawdown']:.2%}")
                        st.write(f"胜率: {row['win_rate']:.1%}")
                        st.write(f"交易次数: {row['total_trades']}")
                    
                    with col2:
                        st.write("**⚙️ 策略参数**")
                        params = row.get('strategy_params', {})
                        if params:
                            for key, value in params.items():
                                st.write(f"{key}: {value}")
                        else:
                            st.write("未保存参数信息")
                    
                    with col3:
                        st.write("**🔧 回测配置**")
                        config = row.get('backtest_config', {})
                        if config:
                            if config.get('start_date'):
                                st.write(f"📅 开始日期: {config['start_date']}")
                            if config.get('end_date'):
                                st.write(f"📅 结束日期: {config['end_date']}")
                            if config.get('period'):
                                st.write(f"📊 时间周期: {config['period']}")
                            if config.get('initial_capital'):
                                st.write(f"💰 初始资金: ${config['initial_capital']:,}")
                            if config.get('commission'):
                                st.write(f"💸 手续费率: {config['commission']:.3%}")
                            if config.get('optimization_used'):
                                st.write("🎯 参数优化: ✅")
                                if config.get('optimization_method'):
                                    st.write(f"🔍 优化方法: {config['optimization_method']}")
                                if config.get('optimization_rank'):
                                    st.write(f"🏆 优化排名: #{config['optimization_rank']}")
                                if config.get('parameter_space_size'):
                                    st.write(f"🔢 参数空间: {config['parameter_space_size']}")
                            else:
                                st.write("🎯 参数优化: ❌")
                            if config.get('backtest_mode'):
                                mode_icons = {
                                    'manual': '👤',
                                    'optimization': '🔧',
                                    'auto': '🤖',
                                    'legacy': '📜'
                                }
                                mode = config['backtest_mode']
                                icon = mode_icons.get(mode, '📋')
                                st.write(f"{icon} 回测模式: {mode}")
                            if config.get('user_interface'):
                                st.write(f"🖥️ 界面: {config['user_interface']}")
                        else:
                            st.write("⚠️ 未保存配置信息")
                        
                        # 备注信息
                        if row.get('notes'):
                            st.write("**📝 备注**")
                            st.write(row['notes'])
        
        # 性能趋势图
        if len(filtered_results) > 1:
            st.subheader("📈 性能趋势")
            
            # 按时间排序
            trend_data = filtered_results.sort_values('created_at')
            trend_data['date'] = pd.to_datetime(trend_data['created_at'])
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=trend_data['date'],
                y=trend_data['total_return'] * 100,
                mode='lines+markers',
                name='总收益率 (%)',
                line=dict(color='blue')
            ))
            
            fig.add_trace(go.Scatter(
                x=trend_data['date'],
                y=trend_data['sharpe_ratio'],
                mode='lines+markers',
                name='夏普比率',
                yaxis='y2',
                line=dict(color='red')
            ))
            
            fig.update_layout(
                title='回测性能趋势',
                xaxis_title='日期',
                yaxis_title='总收益率 (%)',
                yaxis2=dict(
                    title='夏普比率',
                    overlaying='y',
                    side='right'
                ),
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("没有符合条件的记录。")


if __name__ == "__main__":
    main()
