# Live Trading Roadmap Snapshot

## Latest Update · 2025-10-31
- AutoTradingScheduler now routes every scheduled run through TaskManager and persists execution/order/risk payloads to the automation repository for audit.
- Trading-window enforcement is configurable via `automation.trading_window`, so operations can block off-window runs while still logging and notifying the skip reason.
- Execution reports and notifications now reuse the persisted summary payload, keeping downstream analytics and alerts aligned.

## Current Focus
- Stabilise the realtime automation pipeline around TaskManager execution.
- Finish wiring strategy signal generation and risk checks into the Alpaca execution path.
- Instrument the pipeline with actionable logging and notifications.

## Completed
- Assessed existing architecture and identified gaps to reach live trading.
- Chosen Alpaca (paper) as the first live-broker target ahead of an IBKR integration.
- Outlined a four-stage plan covering execution, data, monitoring, and a 30-day mock run.
- Implemented `AlpacaBroker` with `alpaca-trade-api`, env-based credentials, and a connectivity check script.
- Added Alpaca support to the shared `DataFetcher` and refactored `MultiStrategyRunner` to consume the unified provider.
- Refactored realtime services to remove direct broker/data API couplings inside `tradingservice`, consolidated models, and attached TaskManager for unified execution.
- Introduced unit coverage for realtime monitor execution flow and intraday data reconstruction to prevent regressions.
- AutoTradingScheduler executes via TaskManager, persists executions/orders/risk snapshots, and reuses the shared summary for notifications and reports.
- Added configurable trading-window enforcement (timezone, weekday, holiday, grace period) with graceful skip logging when out-of-window.

## Next Steps
**Week of 2025-11-03 (operational hardening)**
1. Expose the scheduler execution history through API/WebSocket endpoints so dashboards and post-trade analytics can consume the same payload.
2. Layer configurable broker risk limits (per-symbol/portfolio) on top of the trading-window guard before orders leave the system.
3. Harden observability for Azure deployment: align `/api/scheduler` with `AutoTradingScheduler`, surface persisted status fields, and document the start/stop automation window plus alerting flows.

## Notes
- IBKR integration remains a future milestone once the Alpaca loop proves stable.
- All new broker-facing code must include sandbox/paper toggles to simplify testing.
- Maintain mocks for unit tests to avoid live API dependencies during CI.
- Alpaca integration standardises on `alpaca-trade-api`; the legacy helpers have been removed.


当前状态

AutoTradingScheduler 调度闭环已打通：每次调度通过 TaskManager 执行并把执行/订单/风险快照落到 automation 仓储。
交易窗口校验已可配置：automation.trading_window 支持设置时区、周内交易日、节假日和缓冲时间，窗口外自动跳过但记录原因。
报告/通知复用持久化的汇总结构，确保下游分析、告警一致。
下一步

暴露调度执行历史（API / WebSocket），供实时看板和事后分析直接读取持久化数据。
在交易窗口之上增加可配置的经纪商风控限额（单品种、组合级），做到出单前双重校验。
Azure 运维侧加固：/api/scheduler 对齐新状态字段，完善开始/停止窗口和告警文档，确保运维自动化透明。


Minimal Loop

AutoTradingScheduler now owns scheduling, trading-window enforcement, broker-risk prechecks, TaskManager delegation, report generation, notifications, and persistence, giving you a full task → execution → audit loop inside one service (src/tradingservice/services/automation/scheduler.py (line 75), src/tradingservice/services/automation/scheduler.py (line 405), src/tradingservice/services/automation/scheduler.py (line 434), src/tradingservice/services/automation/scheduler.py (line 459), src/tradingservice/services/automation/scheduler.py (line 667)).
TaskManager stitches together broker connections, data fetchers, multi-strategy evaluation, signal generation, risk controls, and order execution before returning a normalized summary, so each scheduled run actually touches market data and brokers (src/tradingservice/services/orchestration/task_manager.py (line 41), src/tradingservice/services/orchestration/task_manager.py (line 139), src/tradingservice/services/orchestration/task_manager.py (line 267), src/tradingservice/services/orchestration/task_manager.py (line 335), src/tradingservice/services/orchestration/task_manager.py (line 468)).
Execution outcomes (signals, orders, risk snapshots, payloads) are stored through the scheduler execution repository, which the API reuses to expose history, closing the monitoring/observability loop (src/tradingservice/services/automation/scheduler.py (line 667), src/tradingservice/services/automation/scheduler.py (line 769), src/tradingservice/api/services/scheduler_service.py (line 114)).
Documentation confirms the roadmap milestone: TaskManager backs every AutoTradingScheduler run, and trading-window/risk skips still log and notify, so skips remain observable (docs/LIVE_TRADING_ROADMAP.md).
Entry Points

CLI launcher: python main.py opens the engine selection menu and lets you start the trading engines ad hoc (main.py (line 19), main.py (line 48), main.py (line 86), main.py (line 110)).
Standalone automation: python src/tradingservice/services/automation/scheduler.py boots the AutoTradingScheduler loop directly (src/tradingservice/services/automation/scheduler.py (line 1118)).
REST API: uvicorn src.tradingservice.api.main:app --host 0.0.0.0 --port 8000 (or run the module) to expose /api/scheduler, /api/tasks, /api/strategies, etc.; startup wires in the same scheduler instance via dependency injection (src/tradingservice/api/main.py (line 50), src/tradingservice/api/main.py (line 116), src/tradingservice/api/main.py (line 202), src/tradingservice/api/dependencies.py (line 17)).
Execution Flow

Configuration & bootstrap: AutoTradingScheduler loads config/scheduler_config.json, instantiates NotificationManager, TaskManager, and the execution repository, and registers tasks before the scheduling thread begins (src/tradingservice/services/automation/scheduler.py (line 86), src/tradingservice/services/automation/scheduler.py (line 1020)).
Guard rails: Every run first checks trading-window constraints, then broker risk preconditions; violations mark the run as skipped but still persist context and notify ops (src/tradingservice/services/automation/scheduler.py (line 405), src/tradingservice/services/automation/scheduler.py (line 434)).
Task orchestration: When a run is allowed, Scheduler syncs the metadata with TaskManager and calls TaskManager.execute_task, which clears prior state, runs the selected strategies via MultiStrategyRunner, generates signals, sizes trades, checks limits, submits orders through OrderExecutor, and records broker/risk feedback (src/tradingservice/services/orchestration/task_manager.py (line 139), src/tradingservice/services/orchestration/task_manager.py (line 267), src/tradingservice/services/orchestration/task_manager.py (line 335), src/tradingservice/services/orchestration/task_manager.py (line 468), src/tradingservice/services/orchestration/task_manager.py (line 514)).
Reporting & audit: The execution summary, per-symbol details, orders, and risk snapshots are persisted with SchedulerExecutionRepository, attached to notifications, and later queried by /api/scheduler/executions (src/tradingservice/services/automation/scheduler.py (line 667), src/tradingservice/api/services/scheduler_service.py (line 114), src/tradingservice/api/models/scheduler_models.py (line 47)).
Control surface: FastAPI routes let you start/stop/restart the scheduler, inspect status, list executions, or manage tasks (start/stop via SchedulerService, CRUD via TaskService), so ops can drive the same loop remotely (src/tradingservice/api/routes/scheduler.py (line 15), src/tradingservice/api/services/task_service.py (line 13)).
Next Steps

Finish the roadmap items: expose scheduler execution history via WebSocket/dashboard feeds, layer broker risk limits on top of the new guardrails, and harden /api/scheduler/Azure observability as outlined in docs/LIVE_TRADING_ROADMAP.md.
Track last_execution/next_execution in SchedulerService responses and avoid the current delete/recreate pattern in TaskService.update_task to preserve task IDs during edits.
Add automated smoke tests for the scheduler-to-TaskManager integration (mock broker/data providers) so regressions in the closed loop are caught early.
This setup already achieves the minimal closed loop (schedule → trade → persist/notify); the items above will make it production-proof.