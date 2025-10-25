# 🎬 演示程序集

本目录包含完整的功能演示程序，展示系统的各种能力。

## 📋 演示列表

### 🏗️ 架构演示
- **new_architecture_demo.py** - 新架构使用演示
  - 展示 TradingAgent（底层）和 TradingService（上层）的使用
  - 对比两种架构的区别和使用场景
  - 完整的端到端工作流程

### 📊 回测演示
- **backtest_demo.py** - 回测流程演示
  - 数据获取 → 策略执行 → 回测引擎 → 性能分析 → 结果报告
  - 完整的回测工作流程
  
- **live_backtest_demo.py** - 实时回测演示
  - 实时数据回测
  - 模拟实盘环境

### ⚙️ 优化演示
- **optimization_demo.py** - 参数优化演示
  - 策略参数优化
  - 多目标优化
  - 最优参数选择

### 📈 总结演示
- **summary_demo.py** - 系统功能总结
  - 系统能力概览
  - 各模块功能展示

## 🚀 使用方法

### 运行单个演示
```bash
# 架构演示
python demos/new_architecture_demo.py

# 回测演示
python demos/backtest_demo.py

# 优化演示
python demos/optimization_demo.py
```

### 在代码中导入
```python
from demos.new_architecture_demo import (
    example_1_tradingagent_basic,
    example_2_tradingservice_highlevel
)

# 运行特定演示
example_1_tradingagent_basic()
```

## 🎯 演示特点

- ✅ **完整的工作流程** - 从数据获取到结果展示
- ✅ **详细的注释** - 每个步骤都有说明
- ✅ **可直接运行** - 开箱即用
- ✅ **教学友好** - 适合学习和理解系统

## 📚 与其他目录的区别

| 目录 | 用途 | 特点 |
|------|------|------|
| **demos/** | 演示程序 | 完整流程，教学导向 |
| **scripts/** | 工具脚本 | 实用功能，任务导向 |
| **tests/** | 测试代码 | 单元测试，验证导向 |
| **examples/** | ~~已移除~~ | ~~代码示例~~ |

## 💡 建议

- **新手入门**: 从 `new_architecture_demo.py` 开始
- **学习回测**: 运行 `backtest_demo.py`
- **策略优化**: 查看 `optimization_demo.py`
- **系统概览**: 运行 `summary_demo.py`

## 📖 相关文档

- [架构文档](../docs/ARCHITECTURE_V2.md)
- [快速开始](../docs/QUICKSTART.md)
- [API文档](../docs/API.md)
