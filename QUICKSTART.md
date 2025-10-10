# 量化交易系统快速入门指南

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装基础依赖
pip install pandas numpy matplotlib seaborn plotly yfinance scikit-learn pyyaml

# 安装开发工具
pip install jupyter pytest python-dotenv
```

### 2. 配置系统

```bash
# 复制配置文件
copy config\config.example.yaml config\config.yaml

# 编辑配置文件，添加你的API密钥
notepad config\config.yaml
```

### 3. 运行示例

```bash
# 运行主示例
python main.py

# 启动Jupyter Lab进行分析
jupyter lab
```

## 📊 使用示例

### 基本用法

```python
from data import DataFetcher
from strategies import MovingAverageStrategy
from backtesting import BacktestEngine

# 获取数据
fetcher = DataFetcher()
data = fetcher.fetch_stock_data('AAPL', '2022-01-01', '2023-12-31')

# 创建策略
strategy = MovingAverageStrategy(short_window=20, long_window=50)

# 运行回测
engine = BacktestEngine(initial_capital=100000)
results = engine.run_backtest(strategy, data)

print(f"总收益率: {results['total_return']:.2%}")
```

### 自定义策略

```python
from strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        # 实现你的交易逻辑
        signals = pd.DataFrame(index=data.index)
        signals['signal'] = 0  # 0=持有, 1=买入, -1=卖出
        
        # 添加你的信号生成逻辑
        # ...
        
        return signals
```

## 📁 项目结构

```
quant_trading/
├── data/              # 数据管理模块
├── strategies/        # 交易策略
├── backtesting/       # 回测引擎
├── risk_management/   # 风险管理
├── portfolio/         # 投资组合优化
├── utils/             # 工具函数
├── config/            # 配置文件
├── tests/             # 测试文件
├── notebooks/         # Jupyter笔记本
└── main.py           # 主程序入口
```

## 🔧 VS Code 任务

在VS Code中可以使用以下快捷方式：

- `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Quant Trading Example"
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Run Tests"
- `Ctrl+Shift+P` → "Tasks: Run Task" → "Start Jupyter Lab"

## 🔍 策略类型

### 1. 移动平均策略 (MovingAverageStrategy)
- 适用于趋势行情
- 基于短期和长期移动平均线交叉
- 参数：short_window, long_window

### 2. 均值回归策略 (MeanReversionStrategy)
- 适用于震荡行情
- 基于布林带和RSI指标
- 参数：bb_period, rsi_period, rsi_thresholds

## 📈 性能指标

系统自动计算以下指标：
- 总收益率 / 年化收益率
- 夏普比率
- 最大回撤
- 胜率 / 盈亏比
- Alpha / Beta (相对基准)

## ⚠️ 免责声明

本系统仅用于教育和研究目的。过往表现不代表未来结果。
交易涉及风险，请在使用真实资金前充分测试和验证策略。

## 📚 更多资源

- 查看 `notebooks/strategy_example.ipynb` 获取详细示例
- 阅读各模块的文档字符串了解API详情
- 运行 `python -m pytest tests/` 执行测试套件