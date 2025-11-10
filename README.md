# 🚀 量化交易自动化系统 (Automated Quantitative Trading System)

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Automation](https://img.shields.io/badge/automation-80%25-orange.svg)

## Execution Flow & Entry Points

### Execution Backbone
- **Scheduler bootstrap** – `AutoTradingScheduler` loads `config/scheduler_config.json`, wires up `NotificationManager`, `TaskManager`, and the execution repository factory, then restores any persisted tasks before the scheduling thread starts (`src/tradingservice/services/automation/scheduler.py:75`, `src/tradingservice/services/automation/scheduler.py:81`, `src/tradingservice/services/automation/scheduler.py:108`).
- **Guard rails** – Each run first enforces the configurable trading window and then calls `TaskManager.check_broker_risk_preconditions()`; violations mark the run as skipped while still persisting the context for auditability (`src/tradingservice/services/automation/scheduler.py:405`, `src/tradingservice/services/automation/scheduler.py:434`).
- **Task orchestration** – When a run is approved, the scheduler syncs task metadata and invokes `TaskManager.execute_task`, which clears state, runs `MultiStrategyRunner`, generates signals, sizes trades, enforces risk, executes orders, and writes a normalized summary back to the orchestrated task (`src/tradingservice/services/orchestration/task_manager.py:41`, `src/tradingservice/services/orchestration/task_manager.py:139`, `src/tradingservice/services/orchestration/task_manager.py:267`).
- **Reporting & audit** – The scheduler extracts execution payloads (symbols, orders, risk snapshots) and persists them via `SchedulerExecutionRepository`, then reuses the same summary for report generation and notifications; the API surfaces the history through `/api/scheduler/executions` (`src/tradingservice/services/automation/scheduler.py:659`, `src/tradingservice/api/services/scheduler_service.py:114`, `src/tradingservice/api/models/scheduler_models.py:52`).

### How to Run It
- **CLI launcher** – `python main.py` opens the console menu so you can start the quick/live/advanced trading engines on demand (`main.py:19`, `main.py:48`, `main.py:86`).
- **Standalone automation** – `python src/tradingservice/services/automation/scheduler.py` boots the `AutoTradingScheduler` loop directly for unattended scheduling (`src/tradingservice/services/automation/scheduler.py:1124`).
- **REST API** – `uvicorn src.tradingservice.api.main:app --host 0.0.0.0 --port 8000` exposes `/api/scheduler`, `/api/tasks`, `/api/strategies`, etc.; application startup initializes the same scheduler instance through dependency injection so Ops can control it remotely (`src/tradingservice/api/main.py:48`, `src/tradingservice/api/main.py:87`, `src/tradingservice/api/main.py:136`).

一个面向实时交易的自动化系统：AutoTradingScheduler 负责调度、任务守护与执行闭环，TaskManager 执行策略/风控/下单，所有结果被落库并复用于通知、报表与 API。这一版本已经把“调度 → 策略执行 → 审计”闭环跑通，具备实盘前的最小可行系统。

## 🎯 当前状态

- ✅ AutoTradingScheduler 统一负责调度、交易窗口校验、经纪商风险前置检查以及 TaskManager 执行。
- ✅ TaskManager 串联数据、策略、信号、风控、下单、反馈，输出标准化 Summary。
- ✅ 执行结果（signals/orders/risk snapshot）和报告全部持久化，可通过 `/api/scheduler/executions` 读取。
- ✅ CLI、独立脚本与 FastAPI 共用同一个调度实例，便于本地/远端运维。
- ⚙️ 下一阶段聚焦可观测性、风险限额与 Azure 端到端监控（详见下方路线图）。

## 🏗️ 系统架构（精选目录）

```
quant_trading/
├── main.py                                   # CLI 启动器（选择快速/实时/高级引擎）
├── src/tradingservice/
│   ├── services/
│   │   ├── automation/scheduler.py           # AutoTradingScheduler 调度线程与执行闭环
│   │   └── orchestration/task_manager.py     # TaskManager：策略、信号、风险、下单流水线
│   ├── api/
│   │   ├── main.py                           # FastAPI 入口，注入共享调度实例
│   │   ├── routes/scheduler.py               # Scheduler 控制与历史查询
│   │   ├── services/scheduler_service.py     # API Service 层，复用执行仓储
│   │   └── models/scheduler_models.py        # 执行记录/状态响应模型
│   └── services/orchestration/...            # 策略 runner、broker/risk 适配器
├── config/
│   └── scheduler_config.json                 # 已计划任务、调度参数、窗口配置
├── docs/LIVE_TRADING_ROADMAP.md              # 最新实盘路线图与状态
└── tests/                                    # 单元与集成测试
```

## ✨ 特性

- 🤖 **自动调度闭环**：AutoTradingScheduler 统一管理任务生命周期、线程、状态与配置持久化。
- 🕒 **可配置交易窗口**：支持时区、工作日、节假日、缓冲期，窗口外自动跳过并记录原因。
- 🛡️ **双重风险防线**：运行前检查经纪商风险限额，运行中 TaskManager 风控与仓位控制。
- 📡 **策略执行流水线**：MultiStrategyRunner + SignalGenerator + OrderExecutor，输出可审计 summary。
- 📬 **通知与报告**：调度器复用执行 summary 生成报告，并向通知渠道推送成功/失败/跳过信息。
- 📜 **审计 & API**：执行记录持久化，可通过 FastAPI `/api/scheduler/executions` 或未来 WebSocket 订阅。

## 🏗️ 项目结构

```
quant_trading/
├── 📁 data/               # 市场数据管理
├── 📁 strategies/         # 交易策略实现
├── 📁 backtesting/       # 回测框架
├── 📁 risk_management/   # 风险评估工具
├── 📁 portfolio/         # 投资组合优化
├── 📁 utils/             # 工具函数
├── 📁 config/            # 配置文件
├── 📁 tests/             # 单元测试
├── 📁 notebooks/         # Jupyter分析笔记本
└── 📄 requirements.txt   # Python依赖
```

## 🚀 快速开始

### 📋 环境要求

- Python 3.8+
- pip 或 conda

### ⚡ 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/Bing4Ever/quant_trading.git
   cd quant_trading
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置系统**
   ```bash
   # Windows
   copy config\config.example.yaml config\config.yaml
   
   # Linux/Mac
   cp config/config.example.yaml config/config.yaml
   
   # 复制后，根据需要配置 API 密钥
   ```

> ⚠️ 实盘或纸面交易需要在 `.env` 中设置 `ALPACA_API_KEY`、`ALPACA_API_SECRET`，并在 `config/config.yaml` 的 `brokers` 部分启用 `alpaca`。

4. **运行示例**
   ```bash
   python main.py
   ```

5. **启动Jupyter分析环境**
   ```bash
   jupyter lab
   # 打开 notebooks/strategy_example.ipynb
   ```

### 🎯 快速示例

```python
from data import DataFetcher
from strategies import MovingAverageStrategy
from backtesting import BacktestEngine

# 获取市场数据
fetcher = DataFetcher()
data = fetcher.fetch_stock_data('AAPL', '2022-01-01', '2023-12-31')

# 创建移动平均策略
strategy = MovingAverageStrategy(short_window=20, long_window=50)

# 运行回测
engine = BacktestEngine(initial_capital=100000)
results = engine.run_backtest(strategy, data)

print(f"总收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
```

## � 内置交易策略

### 🔄 移动平均策略 (MovingAverageStrategy)
- **适用场景**: 趋势行情
- **核心逻辑**: 短期均线上穿长期均线时买入，下穿时卖出
- **参数**: `short_window`, `long_window`, `ma_type`

### 📊 均值回归策略 (MeanReversionStrategy)
- **适用场景**: 震荡行情
- **核心逻辑**: 基于布林带和RSI的超买超卖信号
- **参数**: `bb_period`, `rsi_period`, `rsi_thresholds`

### � 自定义策略

```python
from strategies.base_strategy import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def generate_signals(self, data):
        # 实现你的交易逻辑
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0  # 0=持有, 1=买入, -1=卖出
        
        # 你的策略逻辑...
        
        return signals
```

## 📊 性能分析指标

系统自动计算以下关键指标：

| 指标类别 | 具体指标 |
|---------|----------|
| **收益指标** | 总收益率、年化收益率、超额收益 |
| **风险指标** | 年化波动率、最大回撤、VaR |
| **风险调整收益** | 夏普比率、信息比率、Alpha/Beta |
| **交易统计** | 胜率、盈亏比、交易次数 |

## 🛠️ 开发工具

### VS Code 集成
项目包含VS Code任务配置，支持一键操作：
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Quant Trading Example"
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Tests"
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Start Jupyter Lab"

### 测试框架
```bash
# 运行所有测试
pytest tests/

# 运行测试并查看覆盖率
pytest --cov=. tests/

# 运行特定测试文件
pytest tests/test_basic.py -v
```

## 🗂️ 详细文档

- 📖 [快速入门指南](QUICKSTART.md) - 新手必读
- 📊 [策略开发教程](notebooks/strategy_example.ipynb) - Jupyter示例
- 🔧 [API文档](docs/) - 详细接口说明
- 📈 [回测案例](examples/) - 更多策略示例

## 🤝 贡献指南

我们欢迎各种形式的贡献！

### 🔧 开发流程
1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 📝 贡献类型
- 🐛 Bug修复
- ✨ 新功能开发
- 📚 文档改进
- 🧪 测试用例
- 💡 策略贡献

### 🎯 开发规范
- 遵循 PEP 8 代码规范
- 为新功能添加测试
- 更新相关文档
- 确保所有测试通过

## 📈 路线图（来自 docs/LIVE_TRADING_ROADMAP.md）

### 已完成
- ✅ AutoTradingScheduler 全量接入 TaskManager，统一执行/落库/通知。
- ✅ Trading window enforcement + broker 风控前置，跳过的运行同样记录在案。
- ✅ 执行 summary 重用到报告、通知与 `/api/scheduler/executions` API。

### Week of 2025-11-03（Operational Hardening）
- [ ] 将调度执行历史通过 API/WebSocket 暴露给实时看板与事后分析。
- [ ] 在交易窗口之外叠加经纪商级别风险限额（单品种/组合），做到出单前双重校验。
- [ ] 强化 Azure 运维：`/api/scheduler` 与 AutoTradingScheduler 状态对齐、暴露持久化字段，并补齐 start/stop/报警文档。

### 后续建议
- [ ] 在 SchedulerService 响应中追踪 `last_execution` / `next_execution`。
- [ ] 为 Scheduler ↔ TaskManager 集成添加自动化冒烟测试（mock broker/data）。
- [ ] 完成 IBKR 集成和更高级别实盘环境前的 30 天 mock run。

## 🌟 致谢

感谢以下开源项目的支持：
- [pandas](https://pandas.pydata.org/) - 数据处理
- [numpy](https://numpy.org/) - 数值计算
- [yfinance](https://github.com/ranaroussi/yfinance) - 市场数据
- [matplotlib](https://matplotlib.org/) - 数据可视化
- [scikit-learn](https://scikit-learn.org/) - 机器学习

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 详见许可证文件。

## ⚠️ 重要声明

**风险提示**: 本软件仅用于教育和研究目的。过往表现不代表未来结果。量化交易涉及重大金融风险，可能导致部分或全部资金损失。

**使用建议**:
- 📚 充分理解策略逻辑再使用
- 🧪 在模拟环境中充分测试
- 💰 仅使用可承受损失的资金
- 📞 如有疑问请咨询专业人士

---

## English

# 🚀 Quantitative Trading System

A comprehensive Python-based quantitative trading framework for developing, testing, and deploying algorithmic trading strategies.

### Quick Start

```bash
git clone https://github.com/Bing4Ever/quant_trading.git
cd quant_trading
pip install -r requirements.txt
python main.py
```

### Features

- 📊 **Data Management**: Automated market data fetching and storage
- 🔄 **Strategy Development**: Framework for implementing trading strategies  
- 📈 **Backtesting Engine**: Robust backtesting with performance analytics
- ⚠️ **Risk Management**: Advanced risk assessment and position sizing
- 📊 **Portfolio Optimization**: Modern portfolio theory implementations
- 🤖 **Machine Learning**: Integration with ML models for signal generation

For detailed English documentation, please refer to the code comments and docstrings.

---

<div align="center">

### 📞 联系方式 | Contact

[![GitHub](https://img.shields.io/badge/GitHub-Bing4Ever-black?style=flat&logo=github)](https://github.com/Bing4Ever)

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**

**⭐ If this project helps you, please give it a star!**

</div>


