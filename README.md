# 量化交易系统 (Quantitative Trading System)

一个全面的基于Python的量化交易框架，用于开发、测试和部署算法交易策略。

## ✨ 特性

- **📊 数据管理**: 自动化市场数据获取和存储
- **🔄 策略开发**: 交易策略实现框架
- **📈 回测引擎**: 强大的回测和性能分析
- **⚠️ 风险管理**: 高级风险评估和仓位管理
- **📊 投资组合优化**: 现代投资组合理论实现
- **🤖 机器学习**: 与ML模型集成进行信号生成

## 🏗️ 项目结构

```
quant_trading/
├── data/               # 市场数据管理
├── strategies/         # 交易策略实现
├── backtesting/       # 回测框架
├── risk_management/   # 风险评估工具
├── portfolio/         # 投资组合优化
├── utils/             # 工具函数
├── config/            # 配置文件
├── tests/             # 单元测试
├── notebooks/         # Jupyter分析笔记本
└── requirements.txt   # Python依赖
```

## 🚀 快速开始

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   ```bash
   copy config\config.example.yaml config\config.yaml
   # 编辑config.yaml文件，添加你的API密钥和偏好设置
   ```

3. **运行示例**
   ```bash
   python main.py
   ```

4. **启动Jupyter分析**
   ```bash
   jupyter lab
   # 打开 notebooks/strategy_example.ipynb
   ```

## 📊 配置说明

将 `config/config.example.yaml` 复制到 `config/config.yaml` 并更新：
- 市场数据API密钥 (Alpha Vantage, Yahoo Finance等)
- 数据库连接配置
- 风险管理参数
- 交易偏好设置

## 🔄 策略开发

通过继承基础策略类来创建新策略：

```python
from strategies.base_strategy import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        # 实现你的交易逻辑
        pass
```

## 📈 回测示例

对策略进行回测：

```python
from backtesting.backtest_engine import BacktestEngine
from strategies.my_strategy import MyStrategy

engine = BacktestEngine()
results = engine.run_backtest(MyStrategy(), start_date='2020-01-01')
```

## ⚠️ 风险管理

框架包含全面的风险管理功能：
- 基于波动率的仓位管理
- 最大回撤限制
- 风险价值(VaR)计算
- 投资组合相关性分析

## 🧪 测试

运行测试套件：

```bash
pytest tests/
```

运行覆盖率测试：

```bash
pytest --cov=. tests/
```

## 🤝 贡献

1. Fork 仓库
2. 创建功能分支
3. 为新功能添加测试
4. 确保所有测试通过
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件。

## ⚠️ 免责声明

本软件仅用于教育和研究目的。过往表现不代表未来结果。交易涉及风险，在进行任何投资决策之前，您应该仔细考虑您的目标、经验水平和风险承受能力。