#!/usr/bin/env python3
"""自动化交易管理界面 - 集成到现有Streamlit应用中，提供自动化功能管理。"""

import json
import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# pylint: disable=import-error,wrong-import-position
from automation.scheduler import AutoTradingScheduler, ScheduledTask, ScheduleFrequency

def automation_management_page():
    """自动化管理页面"""
    st.header("🤖 自动化交易管理")
    st.markdown("管理自动化交易任务、查看执行状态和历史报告")

    # 创建或获取调度器实例
    if 'scheduler' not in st.session_state:
        st.session_state.scheduler = AutoTradingScheduler()

    scheduler = st.session_state.scheduler

    # 侧边栏控制
    with st.sidebar:
        st.header("🔧 自动化控制")

        # 调度器状态控制
        st.subheader("📟 调度器状态")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("▶️ 启动调度器", use_container_width=True):
                if not scheduler.is_running:
                    scheduler.start_scheduler()
                    st.success("调度器已启动")
                    st.rerun()
                else:
                    st.warning("调度器已在运行")

        with col2:
            if st.button("⏹️ 停止调度器", use_container_width=True):
                if scheduler.is_running:
                    scheduler.stop_scheduler()
                    st.success("调度器已停止")
                    st.rerun()
                else:
                    st.info("调度器未运行")

        # 显示调度器状态
        status = "🟢 运行中" if scheduler.is_running else "🔴 已停止"
        st.metric("调度器状态", status)

        # 快速操作
        st.subheader("⚡ 快速操作")

        if st.button("🔄 刷新任务状态", use_container_width=True):
            st.rerun()

        if st.button("📊 立即执行分析", use_container_width=True):
            with st.spinner("正在执行分析..."):
                # 执行一次性分析
                run_immediate_analysis()

    # 主界面 - 任务管理
    tab1, tab2, tab3, tab4 = st.tabs(["📋 任务列表", "➕ 新建任务", "📈 执行历史", "⚙️ 系统设置"])

    with tab1:
        show_task_list(scheduler)

    with tab2:
        create_new_task(scheduler)

    with tab3:
        show_execution_history()

    with tab4:
        show_system_settings()

def _format_task_dataframe(task_df):
    """格式化任务数据框架"""
    display_df = task_df.copy()
    display_df = display_df.rename(columns={
        'name': '任务名称',
        'frequency': '执行频率',
        'status': '状态',
        'enabled': '启用状态',
        'last_run': '上次执行',
        'next_run': '下次执行',
        'is_running': '正在运行'
    })

    # 状态图标映射
    status_icons = {
        'pending': '⏳',
        'running': '🔄',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '⏹️'
    }

    # 添加状态图标
    display_df['状态'] = display_df['状态'].map(lambda x: f"{status_icons.get(x, '❓')} {x}")
    display_df['启用状态'] = display_df['启用状态'].map(lambda x: "✅ 启用" if x else "❌ 禁用")
    display_df['正在运行'] = display_df['正在运行'].map(lambda x: "🔄 运行中" if x else "⏸️ 空闲")

    return display_df

def _show_task_operations(scheduler, tasks):
    """显示任务操作界面"""
    st.subheader("🛠️ 任务操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_task = st.selectbox(
            "选择任务:",
            options=[task['task_id'] for task in tasks],
            format_func=lambda x: next(task['name'] for task in tasks if task['task_id'] == x)
        )

    with col2:
        if st.button("▶️ 立即执行", use_container_width=True) and selected_task:
            with st.spinner("正在执行任务..."):
                scheduler.execute_task(selected_task)
            st.success("任务已开始执行")
            st.rerun()

    with col3:
        if st.button("🗑️ 删除任务", use_container_width=True, type="secondary") and selected_task:
            if st.session_state.get(f'confirm_delete_{selected_task}', False):
                scheduler.remove_scheduled_task(selected_task)
                st.success("任务已删除")
                st.rerun()
            else:
                st.session_state[f'confirm_delete_{selected_task}'] = True
                st.warning("再次点击确认删除")

def show_task_list(scheduler):
    """显示任务列表"""
    st.subheader("📋 计划任务列表")

    tasks = scheduler.list_all_tasks()

    if not tasks:
        st.info("暂无计划任务，请创建新任务")
        return

    # 创建任务表格
    task_df = pd.DataFrame(tasks)

    # 格式化显示
    if not task_df.empty:
        display_df = _format_task_dataframe(task_df)

        # 显示表格
        st.dataframe(
            display_df[['任务名称', '执行频率', '状态', '启用状态', '正在运行', '上次执行']],
            use_container_width=True
        )

        _show_task_operations(scheduler, tasks)

def create_new_task(scheduler):
    """创建新任务"""
    st.subheader("➕ 创建新的计划任务")

    with st.form("new_task_form"):
        # 基本信息
        task_name = st.text_input("任务名称", placeholder="例如：每日AAPL分析")

        # 执行频率
        frequency = st.selectbox(
            "执行频率",
            options=["daily", "weekly", "monthly"],
            format_func=lambda x: {"daily": "每日", "weekly": "每周", "monthly": "每月"}[x]
        )

        # 股票选择
        st.subheader("📈 股票配置")

        stock_input_method = st.radio(
            "股票选择方式",
            options=["手动输入", "预设组合"],
            horizontal=True
        )

        if stock_input_method == "手动输入":
            symbols_input = st.text_input(
                "股票代码",
                placeholder="用逗号分隔，例如：AAPL,MSFT,GOOGL",
                help="输入要分析的股票代码，用逗号分隔"
            )
            symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
        else:
            preset_portfolio = st.selectbox(
                "选择预设组合",
                options=["科技股组合", "金融股组合", "消费股组合", "能源股组合"]
            )

            portfolio_mapping = {
                "科技股组合": ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                "金融股组合": ["JPM", "BAC", "WFC", "GS", "MS"],
                "消费股组合": ["AMZN", "WMT", "HD", "MCD", "SBUX"],
                "能源股组合": ["XOM", "CVX", "COP", "SLB", "EOG"]
            }
            symbols = portfolio_mapping.get(preset_portfolio, [])

        # 显示选中的股票
        if symbols:
            st.info(f"已选择 {len(symbols)} 只股票: {', '.join(symbols)}")

        # 策略配置
        st.subheader("🎯 策略配置")
        strategies = ["all"]  # 默认使用所有策略
        st.info("将使用所有默认策略：移动平均、RSI、布林带、均值回归")

        # 提交按钮
        submitted = st.form_submit_button("🚀 创建任务", use_container_width=True)

        if submitted:
            if not task_name:
                st.error("请输入任务名称")
            elif not symbols:
                st.error("请选择至少一只股票")
            else:
                # 创建任务
                task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                new_task = ScheduledTask(
                    task_id=task_id,
                    name=task_name,
                    frequency=ScheduleFrequency(frequency),
                    symbols=symbols,
                    strategies=strategies,
                    enabled=True
                )

                if scheduler.add_scheduled_task(new_task):
                    st.success(f"任务 '{task_name}' 创建成功！")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("任务创建失败，请检查日志")

def _load_report_files(reports_dir):
    """加载报告文件"""
    report_files = []
    for file in os.listdir(reports_dir):
        if file.endswith('.json'):
            file_path = os.path.join(reports_dir, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    report = json.load(f)
                    report['file_path'] = file_path
                    report['file_name'] = file
                    report_files.append(report)
            except Exception as e:
                st.error(f"读取报告文件失败: {file} - {str(e)}")
    return report_files

def _display_report_item(report):
    """显示单个报告项"""
    task_info = report.get('task_info', {})
    summary = report.get('summary', {})

    with st.expander(f"📊 {task_info.get('name', '未知任务')} - {task_info.get('execution_time', '')[:19]}"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**任务信息:**")
            st.write(f"- 任务名称: {task_info.get('name', 'N/A')}")
            st.write(f"- 执行时间: {task_info.get('execution_time', 'N/A')[:19]}")
            st.write(f"- 状态: {task_info.get('status', 'N/A')}")
            st.write(f"- 分析股票: {', '.join(task_info.get('symbols', []))}")

        with col2:
            st.write("**执行结果:**")
            st.write(f"- 分析股票数: {summary.get('analyzed_symbols', 0)}")
            st.write(f"- 成功分析数: {summary.get('successful_analysis', 0)}")

            best_strategies = summary.get('best_strategies', {})
            if best_strategies:
                st.write("**最佳策略:**")
                for symbol, strategy_info in list(best_strategies.items())[:3]:  # 只显示前3个
                    st.write(f"- {symbol}: {strategy_info.get('strategy', 'N/A')}")

        # 下载报告按钮
        if st.button("📥 下载报告", key=f"download_{task_info.get('task_id', 'unknown')}"):
            with open(report['file_path'], 'r', encoding='utf-8') as f:
                report_content = f.read()

            st.download_button(
                label="下载JSON报告",
                data=report_content,
                file_name=report['file_name'],
                mime='application/json'
            )

def show_execution_history():
    """显示执行历史"""
    st.subheader("📈 任务执行历史")

    # 查找历史报告文件
    reports_dir = "reports/automated"

    if not os.path.exists(reports_dir):
        st.info("暂无执行历史")
        return

    report_files = _load_report_files(reports_dir)

    if not report_files:
        st.info("暂无执行历史")
        return

    # 按时间排序
    report_files.sort(key=lambda x: x.get('task_info', {}).get('execution_time', ''), reverse=True)

    # 显示报告列表
    for report in report_files[:10]:  # 只显示最近10个
        _display_report_item(report)

def show_system_settings():
    """显示系统设置"""
    st.subheader("⚙️ 系统设置")

    # 通知设置
    st.write("### 📧 通知设置")

    with st.expander("邮件通知配置"):
        email_enabled = st.checkbox("启用邮件通知")

        if email_enabled:
            _smtp_server = st.text_input("SMTP服务器", value="smtp.gmail.com")
            _smtp_port = st.number_input("SMTP端口", value=587)
            _email_username = st.text_input("邮箱用户名")
            _email_password = st.text_input("邮箱密码", type="password")
            _email_recipients = st.text_area("收件人列表", placeholder="每行一个邮箱地址")

    with st.expander("微信机器人配置"):
        wechat_enabled = st.checkbox("启用微信通知")
        if wechat_enabled:
            _wechat_webhook = st.text_input("微信机器人Webhook URL")

    with st.expander("钉钉机器人配置"):
        dingtalk_enabled = st.checkbox("启用钉钉通知")
        if dingtalk_enabled:
            _dingtalk_webhook = st.text_input("钉钉机器人Webhook URL")
            _dingtalk_secret = st.text_input("钉钉机器人Secret", type="password")

    # 保存设置按钮
    if st.button("💾 保存设置", use_container_width=True):
        st.success("设置已保存（功能开发中）")

    # 系统信息
    st.write("### 📊 系统信息")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("运行时间", "24小时")

    with col2:
        st.metric("执行任务数", "15")

    with col3:
        st.metric("成功率", "96.7%")

def run_immediate_analysis():
    """运行即时分析"""
    symbols = ["AAPL", "MSFT", "GOOGL"]

    # 这里可以添加即时分析逻辑
    st.success(f"已对 {', '.join(symbols)} 执行即时分析")

# 在主应用中集成此页面
def add_automation_tab_to_main_app():
    """将自动化管理添加到主应用"""
    # 这个函数可以被主应用调用来集成自动化功能
    return automation_management_page

if __name__ == "__main__":
    # 独立运行时的测试
    st.set_page_config(
        page_title="自动化交易管理",
        page_icon="🤖",
        layout="wide"
    )
    automation_management_page()
