# Live Trading Roadmap Snapshot

## Current Focus
- Deliver the first end-to-end trading loop using Alpaca Paper API.
- Finish wiring strategy signal generation and risk checks into the Alpaca execution path.
- Instrument the pipeline with actionable logging and notifications.

## Completed
- Assessed existing architecture and identified gaps to reach live trading.
- Chosen Alpaca (paper) as the first live-broker target ahead of an IBKR integration.
- Outlined a four-stage plan covering execution, data, monitoring, and a 30-day mock run.
- Implemented `AlpacaBroker` with `alpaca-py`, env-based credentials, and a connectivity check script.
- Added Alpaca support to the shared `DataFetcher` and refactored `MultiStrategyRunner` to consume the unified provider.

## Next Steps
1. Replace remaining yfinance/legacy data fetches with the shared `DataFetcher`, including live environments.
2. Build the live orchestrator: strategy signals → risk filters → Alpaca order execution → fill/position reconciliation.
3. Add logging and notification hooks around order lifecycle, failures, and P&L swings.
4. Automate a daily paper-trading schedule and collect performance/risk reports for the 30-day rehearsal.

## Notes
- IBKR integration remains a future milestone once the Alpaca loop proves stable.
- All new broker-facing code must include sandbox/paper toggles to simplify testing.
- Maintain mocks for unit tests to avoid live API dependencies during CI.
- Alpaca integration standardises on `alpaca-py`; old `alpaca-trade-api` helpers are deprecated.
