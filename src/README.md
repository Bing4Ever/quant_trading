# 📂 src/ 目录说明

## 🎯 目录结构

```
src/
├── tradingagent/          # 底层可执行逻辑
│   ├── __init__.py
│   ├── broker.py           # 经纪商接口
│   ├── executor.py         # 订单执行器
│   ├── signal_generator.py # 信号生成器
│   ├── data_provider.py    # 数据提供器
│   └── risk_controller.py  # 风险控制器
│
└── tradingservice/        # 上层业务逻辑
    ├── __init__.py
    └── task_manager.py     # 任务管理器
```

---

## 🔧 TradingAgent - 底层可执行逻辑

### broker.py - 经纪商接口
**职责**: 提供统一的交易接口，支持模拟和实盘交易

**核心类**:
- `BrokerInterface`: 抽象基类，定义统一接口
- `SimulationBroker`: 模拟交易实现（用于回测和测试）
- `LiveBroker`: 实盘交易实现（待完善）
- `Order`: 订单数据类
- `Position`: 持仓数据类

**主要功能**:
- ✅ 连接/断开经纪商
- ✅ 提交/取消订单
- ✅ 查询订单状态
- ✅ 获取账户余额
- ✅ 获取持仓信息
- ✅ 获取实时价格

---

### executor.py - 订单执行器
**职责**: 管理订单的生成、提交、跟踪

**核心类**:
- `OrderExecutor`: 订单执行器
- `TradingSignal`: 交易信号数据类

**主要功能**:
- ✅ 执行交易信号
- ✅ 取消订单
- ✅ 更新订单状态
- ✅ 获取订单统计
- ✅ 获取账户信息

---

### signal_generator.py - 信号生成器
**职责**: 根据策略结果生成交易信号

**核心类**:
- `SignalGenerator`: 信号生成器

**主要功能**:
- ✅ 生成单个交易信号
- ✅ 批量生成信号
- ✅ 过滤和排序信号
- ✅ 信号统计

---

### data_provider.py - 数据提供器
**职责**: 从各种数据源获取市场数据

**核心类**:
- `DataProvider`: 数据提供器基类
- `RealTimeDataProvider`: 实时数据提供器

**主要功能**:
- ✅ 获取历史数据
- ✅ 获取最新数据
- ✅ 获取当前价格
- ✅ 批量获取价格
- ✅ 获取股票信息
- ✅ 数据缓存管理
- ✅ 实时数据订阅

---

### risk_controller.py - 风险控制器
**职责**: 交易前风险检查和持仓风险监控

**核心类**:
- `RiskController`: 风险控制器
- `RiskLimits`: 风险限制配置

**主要功能**:
- ✅ 验证交易信号
- ✅ 批量风险验证
- ✅ 计算风险指标
- ✅ 持仓调整建议

**风险检查项**:
- 单笔交易规模限制
- 现金充足性检查
- 持仓集中度控制
- 总仓位限制
- 每日亏损限制
- 回撤控制

---

## 🎯 TradingService - 上层业务逻辑

### task_manager.py - 任务管理器
**职责**: 整合所有底层组件，提供统一的任务管理接口

**核心类**:
- `TaskManager`: 任务管理器
- `Task`: 任务数据类
- `TaskStatus`: 任务状态枚举

**主要功能**:
- ✅ 创建任务
- ✅ 执行任务
- ✅ 取消任务
- ✅ 删除任务
- ✅ 列出任务
- ✅ 获取统计信息
- ✅ 账户摘要

**特点**:
- 🚀 开箱即用，自动初始化所有底层组件
- 📊 提供统一的业务层接口
- 🔄 协调数据-策略-信号-执行流程

---

## 📖 使用示例

### 底层使用 (TradingAgent)
```python
from src.tradingagent import (
    SimulationBroker,
    OrderExecutor,
    SignalGenerator,
    DataProvider,
    RiskController
)

# 手动初始化各个组件
broker = SimulationBroker(initial_capital=100000)
broker.connect()

executor = OrderExecutor(broker)
signal_gen = SignalGenerator()
data_provider = DataProvider()
risk_ctrl = RiskController(broker)

# 使用各个组件...
```

### 上层使用 (TradingService)
```python
from src.tradingservice import TaskManager

# 一键初始化（自动创建所有底层组件）
task_mgr = TaskManager(initial_capital=100000)

# 创建并执行任务
task = task_mgr.create_task(
    task_id='task_001',
    name='市场扫描',
    symbols=['AAPL', 'MSFT'],
    strategies=['mean_reversion']
)

task_mgr.execute_task('task_001')
```

---

## 🔄 与现有代码的关系

### 待迁移模块
以下模块将逐步迁移到 `src/tradingservice/`:

1. `automation/scheduler.py` → `src/tradingservice/scheduler.py`
2. `automation/report_generator.py` → `src/tradingservice/report_service.py`
3. `automation/real_time_monitor.py` → `src/tradingservice/monitor_service.py`

### 策略整合
`strategies/` 目录的策略将通过新的 `strategy_orchestrator.py` 进行编排和管理。

---

## 🚀 快速开始

### 1. 运行示例
```bash
python examples/example_new_architecture.py
```

### 2. 查看文档
```bash
# 架构文档
docs/ARCHITECTURE_V2.md

# API文档（待更新）
docs/API_SUMMARY.md
```

### 3. 运行测试
```bash
# 底层组件测试
pytest tests/test_tradingagent.py

# 业务逻辑测试
pytest tests/test_tradingservice.py
```

---

## 📝 设计原则

1. **分层清晰**: 底层执行与上层业务分离
2. **职责单一**: 每个模块只负责一件事
3. **易于测试**: 所有组件可独立测试
4. **易于扩展**: 新增功能不影响现有代码
5. **接口统一**: 提供清晰的API定义

---

## 🎯 优势

✅ **清晰的架构**: 底层/上层职责明确
✅ **易于维护**: 模块组织清晰
✅ **易于测试**: 每个组件独立可测
✅ **易于扩展**: 支持插件式扩展
✅ **支持多模式**: 模拟/实盘统一接口

---

## 📚 相关文档

- [架构设计 V2.0](../docs/ARCHITECTURE_V2.md)
- [使用示例](../examples/example_new_architecture.py)
- [API文档](../docs/API_SUMMARY.md)
- [快速入门](../docs/QUICKSTART.md)

---

**版本**: 1.0.0  
**创建日期**: 2025-10-23  
**最后更新**: 2025-10-23
