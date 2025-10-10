---
name: Strategy Contribution / 策略贡献
about: Contribute a new trading strategy / 贡献新的交易策略
title: '[STRATEGY] '
labels: 'strategy, enhancement'
assignees: ''

---

## 📈 Strategy Overview / 策略概述

**Strategy Name / 策略名称**: 

**Strategy Type / 策略类型**: 
- [ ] Trend Following / 趋势跟踪
- [ ] Mean Reversion / 均值回归
- [ ] Momentum / 动量
- [ ] Arbitrage / 套利
- [ ] Market Making / 做市
- [ ] Other / 其他: ___________

## 🧮 Strategy Logic / 策略逻辑

Describe the core logic and mathematical foundation of your strategy.
描述策略的核心逻辑和数学基础。

### Entry Signals / 入场信号
- 

### Exit Signals / 出场信号
- 

### Risk Management / 风险管理
- 

## 📊 Parameters / 参数

List all configurable parameters for the strategy:
列出策略的所有可配置参数：

| Parameter / 参数 | Default Value / 默认值 | Description / 描述 |
|------------------|------------------------|-------------------|
|                  |                        |                   |

## 📈 Performance / 性能表现

If you have backtested the strategy, please provide:
如果您已经回测了策略，请提供：

- **Testing Period / 测试期间**: 
- **Assets Tested / 测试资产**: 
- **Total Return / 总收益率**: 
- **Sharpe Ratio / 夏普比率**: 
- **Max Drawdown / 最大回撤**: 
- **Win Rate / 胜率**: 

## 💻 Code Implementation / 代码实现

```python
# Paste your strategy implementation here
# 在此粘贴您的策略实现代码

class YourStrategy(BaseStrategy):
    def __init__(self, ...):
        # Implementation
        pass
    
    def generate_signals(self, data):
        # Implementation
        pass
```

## 📚 References / 参考文献

List any academic papers, books, or other sources that inspired this strategy.
列出任何启发此策略的学术论文、书籍或其他来源。

- 
- 

## ✅ Checklist / 检查清单

- [ ] Strategy follows the BaseStrategy interface / 策略遵循BaseStrategy接口
- [ ] Code includes proper docstrings / 代码包含适当的文档字符串
- [ ] Strategy has been backtested / 策略已经过回测
- [ ] Unit tests are included / 包含单元测试
- [ ] Performance metrics are provided / 提供了性能指标
- [ ] Code follows project coding standards / 代码遵循项目编码标准

## 🤝 Contribution Agreement / 贡献协议

By submitting this strategy, I agree to:
通过提交此策略，我同意：

- [ ] License the code under MIT license / 在MIT许可证下授权代码
- [ ] Allow the strategy to be included in the project / 允许将策略包含在项目中
- [ ] Provide support for any issues related to the strategy / 为与策略相关的任何问题提供支持