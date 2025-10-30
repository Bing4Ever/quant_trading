# Live Trading Roadmap Snapshot

## Latest Update · 2025-10-30
- RealTimeMonitor now forwards high-confidence signals straight into the TaskManager → OrderExecutor chain, using the shared broker instance from the simulation/live runtime.
- Signal metadata is normalised (reason/target price) and guard-clauses added to prevent null rows, keeping downstream execution resilient.
- Added focused unit tests around realtime execution (`test_real_time_monitor.py`) and the minute-frame builder (`test_signal_monitor.py`) to protect the new wiring.

## Current Focus
- Stabilise the realtime automation pipeline around TaskManager execution.
- Finish wiring strategy signal generation and risk checks into the Alpaca execution path.
- Instrument the pipeline with actionable logging and notifications.

## Completed
- Assessed existing architecture and identified gaps to reach live trading.
- Chosen Alpaca (paper) as the first live-broker target ahead of an IBKR integration.
- Outlined a four-stage plan covering execution, data, monitoring, and a 30-day mock run.
- Implemented `AlpacaBroker` with `alpaca-py`, env-based credentials, and a connectivity check script.
- Added Alpaca support to the shared `DataFetcher` and refactored `MultiStrategyRunner` to consume the unified provider.
- Refactored realtime services to remove direct broker/data API couplings inside `tradingservice`, consolidated models, and attached TaskManager for unified execution.
- Introduced unit coverage for realtime monitor execution flow and intraday data reconstruction to prevent regressions.

## Next Steps
1. Replace remaining yfinance/legacy data fetches with the shared `DataFetcher`, including live environments.
2. Wire the realtime TaskManager pathway into the Alpaca-backed live runner, including order fill reconciliation.
3. Add logging and notification hooks around order lifecycle, failures, and P&L swings.
4. Automate a daily paper-trading schedule and collect performance/risk reports for the 30-day rehearsal.

## Notes
- IBKR integration remains a future milestone once the Alpaca loop proves stable.
- All new broker-facing code must include sandbox/paper toggles to simplify testing.
- Maintain mocks for unit tests to avoid live API dependencies during CI.
- Alpaca integration standardises on `alpaca-py`; old `alpaca-trade-api` helpers are deprecated.
