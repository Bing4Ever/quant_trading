# 📐 架构设计 V2.0 - 分层架构

## 🎯 架构定义

### **TradingAgent** = 底层可执行逻辑
负责具体的交易执行、数据获取、信号生成等底层操作。

### **TradingService** = 上层业务逻辑
负责业务流程编排、任务调度、报告生成等上层管理。

---

## 📦 模块结构

```
src/
├── tradingagent/          # 底层可执行逻辑
│   ├── __init__.py
│   ├── broker.py           # 经纪商接口（模拟/实盘）
│   ├── executor.py         # 订单执行器
│   ├── signal_generator.py # 交易信号生成器
│   ├── data_provider.py    # 数据提供器
│   └── risk_controller.py  # 风险控制器
│
└── tradingservice/        # 上层业务逻辑
    ├── __init__.py
    ├── task_manager.py     # 任务管理器（核心）
    ├── scheduler.py        # 任务调度器（待迁移）
    ├── strategy_orchestrator.py  # 策略编排器（待实现）
    ├── report_service.py   # 报告服务（待迁移）
    └── monitor_service.py  # 监控服务（待迁移）
```

---

## 🔄 分层关系

```
┌─────────────────────────────────────────┐
│          API Layer (FastAPI)            │
│         api/routes/*.py                 │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Business Logic Layer               │
│      src/tradingservice/                │
│  - 任务管理 (TaskManager)                │
│  - 任务调度 (Scheduler)                  │
│  - 策略编排 (StrategyOrchestrator)       │
│  - 报告生成 (ReportService)              │
│  - 监控预警 (MonitorService)             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Execution Layer                    │
│      src/tradingagent/                  │
│  - 经纪商接口 (Broker)                   │
│  - 订单执行 (Executor)                   │
│  - 信号生成 (SignalGenerator)           │
│  - 数据获取 (DataProvider)               │
│  - 风险控制 (RiskController)             │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      External Services                  │
│  - 数据源 (yfinance, alpha_vantage)     │
│  - 经纪商API                            │
│  - 通知服务                              │
└─────────────────────────────────────────┘
```

---

## 📋 TradingAgent 模块详解

### 1. **broker.py** - 经纪商接口
```python
# 抽象接口
class BrokerInterface(ABC):
    - connect() / disconnect()
    - submit_order() / cancel_order()
    - get_account_balance()
    - get_positions()
    - get_current_price()

# 模拟实现
class SimulationBroker(BrokerInterface):
    - 模拟交易执行
    - 模拟持仓管理
    - 用于回测和测试

# 实盘实现
class AlpacaBroker(BrokerInterface):
    - 连接实际经纪商API
    - 真实订单提交
    - 实盘数据获取
```

**职责**：
- ✅ 提供统一的交易接口抽象
- ✅ 封装不同经纪商的API差异
- ✅ 支持模拟和实盘两种模式

---

### 2. **executor.py** - 订单执行器
```python
class OrderExecutor:
    - execute_signal()        # 执行交易信号
    - cancel_order()          # 取消订单
    - update_order_status()   # 更新订单状态
    - get_order_statistics()  # 获取订单统计
    - get_account_info()      # 获取账户信息
```

**职责**：
- ✅ 将交易信号转换为订单
- ✅ 管理订单生命周期
- ✅ 跟踪订单状态
- ✅ 提供账户和订单统计

---

### 3. **signal_generator.py** - 信号生成器
```python
class SignalGenerator:
    - generate_signal()        # 生成单个信号
    - generate_batch_signals() # 批量生成信号
    - filter_signals()         # 过滤信号
    - get_signal_statistics()  # 获取信号统计
```

**职责**：
- ✅ 根据策略结果生成交易信号
- ✅ 信号过滤和优先级排序
- ✅ 信号历史记录和统计

---

### 4. **data_provider.py** - 数据提供器
```python
class DataProvider:
    - get_historical_data()    # 获取历史数据
    - get_latest_data()        # 获取最新数据
    - get_current_price()      # 获取当前价格
    - get_stock_info()         # 获取股票信息
    - clear_cache()            # 清空缓存

class RealTimeDataProvider(DataProvider):
    - subscribe()              # 订阅实时数据
    - unsubscribe()            # 取消订阅
    - get_subscribed_prices()  # 获取订阅价格
```

**职责**：
- ✅ 从各种数据源获取市场数据
- ✅ 数据缓存管理
- ✅ 实时数据订阅（可选）

---

### 5. **risk_controller.py** - 风险控制器
```python
class RiskController:
    - validate_signal()         # 验证单个信号
    - validate_batch_signals()  # 批量验证信号
    - get_risk_metrics()        # 获取风险指标
    - get_position_suggestions()# 获取持仓建议

class RiskLimits:
    - max_position_size         # 单个持仓最大占比
    - max_total_exposure        # 最大总仓位
    - max_single_trade_size     # 单笔交易最大占比
    - max_daily_loss            # 最大日亏损
    - max_drawdown              # 最大回撤
    - min_cash_reserve          # 最小现金储备
```

**职责**：
- ✅ 交易前风险检查
- ✅ 持仓风险监控
- ✅ 风险指标计算
- ✅ 持仓调整建议

---

## 📊 TradingService 模块详解

### 1. **task_manager.py** - 任务管理器 ⭐核心
```python
class TaskManager:
    # 初始化所有底层组件
    - broker
    - data_provider
    - signal_generator
    - executor
    - risk_controller
    
    # 任务管理方法
    - create_task()      # 创建任务
    - execute_task()     # 执行任务
    - cancel_task()      # 取消任务
    - delete_task()      # 删除任务
    - list_tasks()       # 列出任务
    - get_statistics()   # 获取统计
```

**职责**：
- ✅ 整合所有底层组件
- ✅ 提供统一的任务管理接口
- ✅ 协调数据-策略-信号-执行流程
- ✅ 提供业务层统计和报告

---

### 2. **scheduler.py** - 任务调度器（待迁移）
从 `automation/scheduler.py` 迁移并改造

**职责**：
- ⏰ 定时任务调度
- 📅 支持多种执行频率
- 🔄 任务持久化和恢复

---

### 3. **strategy_orchestrator.py** - 策略编排器（待实现）
```python
class StrategyOrchestrator:
    - run_single_strategy()    # 运行单个策略
    - run_multiple_strategies()# 运行多个策略
    - aggregate_results()      # 聚合策略结果
    - compare_strategies()     # 比较策略表现
```

**职责**：
- 🎯 策略选择和运行
- 📊 多策略结果聚合
- 🔀 策略权重分配

---

### 4. **report_service.py** - 报告服务（待迁移）
从 `automation/report_generator.py` 迁移并改造

**职责**：
- 📄 生成交易报告
- 📈 性能分析报告
- 📧 报告发送和通知

---

### 5. **monitor_service.py** - 监控服务（待迁移）
从 `automation/real_time_monitor.py` 迁移并改造

**职责**：
- 📡 实时市场监控
- ⚠️ 异常预警
- 📊 性能监控

---

## 🔧 使用示例

### 底层使用（TradingAgent）
```python
from src.tradingagent import (
    SimulationBroker,
    OrderExecutor,
    SignalGenerator,
    DataProvider,
    RiskController
)

# 初始化组件
broker = SimulationBroker(initial_capital=100000)
broker.connect()

executor = OrderExecutor(broker)
signal_gen = SignalGenerator()
data_provider = DataProvider()
risk_ctrl = RiskController(broker)

# 获取数据
data = data_provider.get_latest_data('AAPL', days=30)

# 生成信号
signal = signal_gen.generate_signal(
    symbol='AAPL',
    strategy_name='mean_reversion',
    strategy_result={'signal': 1, 'confidence': 0.85},
    quantity=100
)

# 风险验证
is_valid, reason = risk_ctrl.validate_signal(signal)

# 执行订单
if is_valid:
    order_id = executor.execute_signal(signal)
```

### 上层使用（TradingService）
```python
from src.tradingservice import TaskManager

# 初始化任务管理器（自动初始化所有底层组件）
task_mgr = TaskManager(initial_capital=100000)

# 创建任务
task = task_mgr.create_task(
    task_id='daily_scan_001',
    name='每日市场扫描',
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    strategies=['mean_reversion', 'momentum']
)

# 执行任务
task_mgr.execute_task('daily_scan_001')

# 获取统计
stats = task_mgr.get_statistics()
print(stats)
```

---

## 🚀 迁移计划

### 阶段1：基础框架 ✅
- [x] 创建 src/tradingagent/ 模块
- [x] 创建 src/tradingservice/ 模块
- [x] 实现核心底层组件
- [x] 实现任务管理器

### 阶段2：功能迁移（进行中）
- [ ] 迁移 scheduler.py
- [ ] 迁移 report_generator.py
- [ ] 迁移 real_time_monitor.py
- [ ] 实现 strategy_orchestrator.py

### 阶段3：整合测试
- [ ] 编写单元测试
- [ ] 编写集成测试
- [ ] 性能测试
- [ ] 更新文档

### 阶段4：API适配
- [ ] 更新 API routes 使用新架构
- [ ] 更新 Streamlit UI 使用新架构
- [ ] 向后兼容性处理

---

## 📝 设计原则

1. **单一职责**: 每个模块只负责一件事
2. **依赖倒置**: 上层依赖抽象接口，不依赖具体实现
3. **开闭原则**: 对扩展开放，对修改关闭
4. **接口隔离**: 提供清晰的接口定义
5. **可测试性**: 所有组件都可独立测试

---

## 🎯 优势

✅ **清晰的分层**: 底层执行与上层业务分离
✅ **易于测试**: 每个组件都可独立测试
✅ **易于扩展**: 新增策略或功能不影响现有代码
✅ **易于维护**: 模块职责明确，代码组织清晰
✅ **支持多种模式**: 模拟交易和实盘交易统一接口

---

**版本**: 2.0  
**创建日期**: 2025-10-23  
**更新日期**: 2025-10-23
