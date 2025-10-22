# 🚀 量化交易自动化系统 (Automated Quantitative Trading System)

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-v1.25+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build](https://img.shields.io/badge/build-passing-brightgreen.svg)
![Automation](https://img.shields.io/badge/automation-80%25-orange.svg)

一个专业的量化交易自动化系统，支持多策略回测分析和完整的自动化交易功能。系统已从**手动分析**升级为**自动运行 + 自动报告 + 可实盘接入**的完整自动化平台。

## 🎯 项目概述

这是一个完整的量化交易系统，具备以下核心能力：
- **🔄 多策略并行分析**: 4种交易策略同时运行比较
- **📊 实时数据监控**: 实时股价监控和交易信号检测
- **🤖 自动化任务调度**: 定时执行交易策略分析
- **📈 智能通知系统**: 重要信号自动推送
- **📋 完整日志记录**: 所有交易决策和执行记录

## 🏗️ 系统架构

```
quant_trading/
├── 📊 核心功能
│   ├── streamlit_app.py          # 主应用界面
│   ├── strategies/               # 交易策略库
│   ├── backtesting/             # 回测引擎
│   └── portfolio/               # 投资组合管理
│
├── 🤖 自动化模块 (新功能)
│   ├── automation/
│   │   ├── scheduler.py         # 自动化调度器 ✅
│   │   ├── real_time_monitor.py # 实时数据监控 ✅
│   │   ├── streamlit_realtime.py # 实时监控界面 ✅
│   │   └── streamlit_automation.py # 自动化管理界面
│   │
│   └── utils/
│       ├── logger.py            # 交易日志系统 ✅
│       └── notification.py     # 多渠道通知系统 ✅
│
└── 📁 数据存储
    ├── data/                    # 市场数据
    ├── logs/                    # 系统日志
    └── exports/                 # 导出报告
```

## ✨ 特性

- 📊 **数据管理**: 自动化市场数据获取和存储
- 🔄 **策略开发**: 交易策略实现框架
- 📈 **回测引擎**: 强大的回测和性能分析
- ⚠️ **风险管理**: 高级风险评估和仓位管理
- 📊 **投资组合优化**: 现代投资组合理论实现
- 🤖 **机器学习**: 与ML模型集成进行信号生成

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
   
   # 编辑配置文件，添加你的API密钥
   ```

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

## 📈 路线图

### Version 1.1 (计划中)
- [ ] 更多技术指标
- [ ] 机器学习策略模板
- [ ] 实时交易接口
- [ ] Web界面

### Version 1.2 (规划中)
- [ ] 加密货币支持
- [ ] 期货/期权策略
- [ ] 高频交易框架
- [ ] 云端部署支持

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